from web3 import Web3
from typing import Dict, List, Any, Optional
from decimal import Decimal
import aiohttp
import asyncio
import time
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class BlockchainClient:
    """Client for interacting with Polygon blockchain and analyzing trader portfolios."""
    
    def __init__(self):
        self.rpc_url = settings.polygon_rpc_url
        self.archive_url = settings.polygon_archive_url or self.rpc_url
        self.etherscan_api_key = settings.etherscan_api_key
        
        # Initialize Web3 connection with error handling
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            if not self.w3.is_connected():
                logger.warning(f"Failed to connect to Polygon RPC at {self.rpc_url}")
        except Exception as e:
            logger.error(f"Error initializing Web3 connection: {e}")
            self.w3 = None
        
        # Polymarket contract addresses (Polygon mainnet)
        self.conditional_tokens_address = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"
        self.exchange_address = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"
        self.usdc_address = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        # ERC20 ABI for token balance queries
        self.erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            }
        ]
    
    async def get_trader_portfolio(self, address: str) -> Dict[str, Any]:
        """Get comprehensive trader portfolio from blockchain."""
        if not self.w3 or not self.w3.is_address(address):
            logger.error(f"Invalid address or Web3 connection issue: {address}")
            return {
                "address": address,
                "error": "Invalid address or blockchain connection issue",
                "total_portfolio_value_usd": 0,
                "active_positions": 0,
                "positions": []
            }
        
        try:
            logger.info(f"Fetching portfolio data for trader: {address}")
            
            # Rate limiting
            await self._rate_limit()
            
            # Get basic token balances
            eth_balance_usd = await self._get_eth_balance(address)
            usdc_balance = await self._get_usdc_balance(address)
            
            # Get Polymarket positions
            positions = await self._get_polymarket_positions(address)
            
            # Calculate total position value
            positions_value = sum(
                Decimal(str(pos.get("current_value_usd", 0))) for pos in positions
            )
            
            # Calculate total portfolio value
            total_value = eth_balance_usd + usdc_balance + positions_value
            
            portfolio = {
                "address": address,
                "eth_balance_usd": float(eth_balance_usd),
                "usdc_balance": float(usdc_balance),
                "positions_value_usd": float(positions_value),
                "total_portfolio_value_usd": float(total_value),
                "active_positions": len(positions),
                "positions": positions,
                "last_updated": int(time.time())
            }
            
            logger.info(f"Portfolio analysis complete for {address}: ${total_value:.2f} total value")
            return portfolio
            
        except Exception as e:
            logger.error(f"Error getting portfolio for {address}: {e}")
            return {
                "address": address,
                "error": str(e),
                "total_portfolio_value_usd": 0,
                "active_positions": 0,
                "positions": []
            }
    
    async def get_transaction_history(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get transaction history for a trader address."""
        if not self.etherscan_api_key:
            logger.warning("No Etherscan API key configured for transaction history")
            return []
        
        url = "https://api.polygonscan.com/api"
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": min(limit, 10000),  # API limit
            "sort": "desc",
            "apikey": self.etherscan_api_key
        }
        
        try:
            await self._rate_limit()
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1":
                            transactions = data.get("result", [])
                            logger.info(f"Retrieved {len(transactions)} transactions for {address}")
                            return transactions
                        else:
                            logger.warning(f"Polygonscan API error: {data.get('message', 'Unknown error')}")
                            return []
                    else:
                        logger.error(f"Polygonscan API HTTP error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching transaction history for {address}: {e}")
            return []
    
    async def get_polymarket_positions(self, address: str) -> List[Dict[str, Any]]:
        """Get active Polymarket positions for a trader."""
        try:
            # Get transaction history
            transactions = await self.get_transaction_history(address)
            
            # Filter Polymarket-related transactions
            polymarket_txs = [
                tx for tx in transactions 
                if self._is_polymarket_transaction(tx)
            ]
            
            logger.info(f"Found {len(polymarket_txs)} Polymarket transactions for {address}")
            
            # Parse transactions to extract position data
            positions = []
            for tx in polymarket_txs:
                position = await self._parse_polymarket_transaction(tx)
                if position:
                    positions.append(position)
            
            # Aggregate positions by market
            aggregated_positions = self._aggregate_positions(positions)
            
            return aggregated_positions
            
        except Exception as e:
            logger.error(f"Error getting Polymarket positions for {address}: {e}")
            return []
    
    async def verify_market_participation(self, address: str, market_id: str) -> Dict[str, Any]:
        """Verify if a trader has participated in a specific market."""
        try:
            positions = await self.get_polymarket_positions(address)
            
            market_positions = [
                pos for pos in positions 
                if pos.get("market_id") == market_id
            ]
            
            if market_positions:
                total_position_size = sum(
                    Decimal(str(pos.get("total_position_size_usd", 0)))
                    for pos in market_positions
                )
                
                return {
                    "has_position": True,
                    "position_count": len(market_positions),
                    "total_position_size_usd": float(total_position_size),
                    "positions": market_positions
                }
            else:
                return {
                    "has_position": False,
                    "position_count": 0,
                    "total_position_size_usd": 0.0,
                    "positions": []
                }
                
        except Exception as e:
            logger.error(f"Error verifying market participation for {address} in {market_id}: {e}")
            return {
                "has_position": False,
                "error": str(e)
            }
    
    async def _get_eth_balance(self, address: str) -> Decimal:
        """Get ETH balance in USD."""
        try:
            # Rate limiting
            await self._rate_limit()
            
            balance_wei = self.w3.eth.get_balance(Web3.to_checksum_address(address))
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            
            # Get ETH price
            eth_price_usd = await self._get_eth_price()
            eth_value_usd = Decimal(str(balance_eth)) * Decimal(str(eth_price_usd))
            
            logger.debug(f"ETH balance for {address}: {balance_eth:.4f} ETH (${eth_value_usd:.2f})")
            return eth_value_usd
            
        except Exception as e:
            logger.error(f"Error getting ETH balance for {address}: {e}")
            return Decimal('0')
    
    async def _get_usdc_balance(self, address: str) -> Decimal:
        """Get USDC balance."""
        try:
            # Rate limiting
            await self._rate_limit()
            
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.usdc_address),
                abi=self.erc20_abi
            )
            
            balance = contract.functions.balanceOf(Web3.to_checksum_address(address)).call()
            decimals = contract.functions.decimals().call()
            
            # Convert to decimal format
            usdc_balance = Decimal(balance) / Decimal(10 ** decimals)
            
            logger.debug(f"USDC balance for {address}: {usdc_balance:.2f} USDC")
            return usdc_balance
            
        except Exception as e:
            logger.error(f"Error getting USDC balance for {address}: {e}")
            return Decimal('0')
    
    async def _get_polymarket_positions(self, address: str) -> List[Dict[str, Any]]:
        """Get Polymarket positions using transaction analysis."""
        try:
            # Get Polymarket transactions
            transactions = await self.get_transaction_history(address, limit=1000)
            
            # Filter and parse Polymarket transactions
            polymarket_positions = []
            for tx in transactions:
                if self._is_polymarket_transaction(tx):
                    position = await self._parse_polymarket_transaction(tx)
                    if position:
                        polymarket_positions.append(position)
            
            # Aggregate positions by market
            aggregated = self._aggregate_positions(polymarket_positions)
            
            logger.debug(f"Found {len(aggregated)} Polymarket positions for {address}")
            return aggregated
            
        except Exception as e:
            logger.error(f"Error getting Polymarket positions for {address}: {e}")
            return []
    
    def _is_polymarket_transaction(self, tx: Dict[str, Any]) -> bool:
        """Check if transaction is related to Polymarket contracts."""
        to_address = tx.get("to", "").lower()
        from_address = tx.get("from", "").lower()
        
        polymarket_addresses = {
            self.conditional_tokens_address.lower(),
            self.exchange_address.lower()
        }
        
        return (
            to_address in polymarket_addresses or
            from_address in polymarket_addresses or
            self._has_polymarket_log_topics(tx)
        )
    
    def _has_polymarket_log_topics(self, tx: Dict[str, Any]) -> bool:
        """Check if transaction has Polymarket-related log topics."""
        # This is a simplified check - in production you'd decode actual log topics
        input_data = tx.get("input", "")
        
        # Check for common Polymarket function signatures
        polymarket_signatures = [
            "0xa9059cbb",  # transfer(address,uint256)
            "0x23b872dd",  # transferFrom(address,address,uint256)
            "0x095ea7b3",  # approve(address,uint256)
        ]
        
        return any(input_data.startswith(sig) for sig in polymarket_signatures)
    
    async def _parse_polymarket_transaction(self, tx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a Polymarket transaction to extract position information."""
        try:
            # Basic transaction data
            value_wei = int(tx.get("value", "0"))
            value_eth = Decimal(value_wei) / Decimal(10**18)
            gas_used = int(tx.get("gasUsed", "0"))
            timestamp = int(tx.get("timeStamp", "0"))
            
            # Estimate USD value (simplified - real implementation would be more sophisticated)
            eth_price = await self._get_eth_price()
            value_usd = value_eth * Decimal(str(eth_price))
            
            # Only consider transactions with meaningful value
            if value_usd < Decimal('10'):  # Less than $10
                return None
            
            # Extract market info from transaction (simplified)
            # In production, you'd decode the actual contract call data
            market_id = f"market_{tx.get('blockNumber', 'unknown')}"
            
            # Determine transaction type based on function signature
            input_data = tx.get("input", "")
            transaction_type = "unknown"
            
            if input_data.startswith("0xa9059cbb"):
                transaction_type = "transfer"
            elif input_data.startswith("0x23b872dd"):
                transaction_type = "transfer_from"
            elif len(input_data) > 10:  # Has function call data
                transaction_type = "trade"
            
            position = {
                "transaction_hash": tx.get("hash"),
                "market_id": market_id,
                "position_size_usd": float(value_usd),
                "timestamp": timestamp,
                "block_number": int(tx.get("blockNumber", "0")),
                "transaction_type": transaction_type,
                "gas_used": gas_used,
                "success": tx.get("isError", "0") == "0"
            }
            
            return position
            
        except Exception as e:
            logger.error(f"Error parsing Polymarket transaction {tx.get('hash', 'unknown')}: {e}")
            return None
    
    def _aggregate_positions(self, positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate positions by market."""
        market_positions = {}
        
        for position in positions:
            market_id = position.get("market_id")
            if not market_id:
                continue
                
            if market_id not in market_positions:
                market_positions[market_id] = {
                    "market_id": market_id,
                    "total_position_size_usd": Decimal('0'),
                    "transaction_count": 0,
                    "first_entry_timestamp": position.get("timestamp"),
                    "last_entry_timestamp": position.get("timestamp"),
                    "transactions": []
                }
            
            # Update aggregated data
            market_data = market_positions[market_id]
            market_data["total_position_size_usd"] += Decimal(str(position.get("position_size_usd", 0)))
            market_data["transaction_count"] += 1
            market_data["transactions"].append(position)
            
            # Update timestamps
            if position.get("timestamp"):
                market_data["first_entry_timestamp"] = min(
                    market_data["first_entry_timestamp"] or float('inf'),
                    position["timestamp"]
                )
                market_data["last_entry_timestamp"] = max(
                    market_data["last_entry_timestamp"] or 0,
                    position["timestamp"]
                )
        
        # Convert to list and add calculated fields
        result = []
        for market_id, data in market_positions.items():
            # Only include positions with meaningful size
            if data["total_position_size_usd"] >= Decimal('50'):  # At least $50
                position_data = {
                    "market_id": market_id,
                    "total_position_size_usd": float(data["total_position_size_usd"]),
                    "current_value_usd": float(data["total_position_size_usd"]),  # Simplified - would need market data
                    "transaction_count": data["transaction_count"],
                    "first_entry_timestamp": data["first_entry_timestamp"],
                    "last_entry_timestamp": data["last_entry_timestamp"],
                    "entry_price": Decimal('0.5'),  # Placeholder - would need actual market data
                    "outcome_id": "unknown",  # Would need to decode from transaction data
                    "status": "active"  # Simplified
                }
                result.append(position_data)
        
        return sorted(result, key=lambda x: x["total_position_size_usd"], reverse=True)
    
    async def _get_eth_price(self) -> float:
        """Get current ETH price in USD."""
        try:
            # Use CoinGecko API as a reliable free source
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                url = "https://api.coingecko.com/api/v3/simple/price"
                params = {"ids": "ethereum", "vs_currencies": "usd"}
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = data.get("ethereum", {}).get("usd", 2500.0)
                        logger.debug(f"Retrieved ETH price: ${price}")
                        return float(price)
                    else:
                        logger.warning(f"Failed to get ETH price, using fallback: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error getting ETH price: {e}")
        
        # Fallback price
        return 2500.0
    
    async def _rate_limit(self):
        """Implement rate limiting for API calls."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_contract_instance(self, address: str, abi: List[Dict]) -> Any:
        """Get a Web3 contract instance."""
        if not self.w3:
            raise RuntimeError("Web3 connection not available")
        
        return self.w3.eth.contract(
            address=Web3.to_checksum_address(address),
            abi=abi
        )
    
    async def get_token_balance(self, token_address: str, wallet_address: str) -> Decimal:
        """Get balance of any ERC20 token."""
        try:
            await self._rate_limit()
            
            contract = self.get_contract_instance(token_address, self.erc20_abi)
            
            balance = contract.functions.balanceOf(
                Web3.to_checksum_address(wallet_address)
            ).call()
            decimals = contract.functions.decimals().call()
            
            return Decimal(balance) / Decimal(10 ** decimals)
            
        except Exception as e:
            logger.error(f"Error getting token balance for {token_address}: {e}")
            return Decimal('0')
    
    async def get_block_timestamp(self, block_number: int) -> int:
        """Get timestamp for a specific block."""
        try:
            await self._rate_limit()
            
            block = self.w3.eth.get_block(block_number)
            return int(block['timestamp'])
            
        except Exception as e:
            logger.error(f"Error getting block timestamp for {block_number}: {e}")
            return 0
    
    def is_connected(self) -> bool:
        """Check if blockchain connection is available."""
        return self.w3 is not None and self.w3.is_connected()