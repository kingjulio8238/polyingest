import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from app.data.blockchain_client import BlockchainClient
import time


class TestBlockchainClient:
    """Test suite for BlockchainClient functionality."""
    
    @pytest.fixture
    def mock_w3(self):
        """Mock Web3 instance for testing."""
        mock = Mock()
        mock.is_connected.return_value = True
        mock.is_address.return_value = True
        mock.to_checksum_address = lambda x: x.replace('0x', '0x').upper() if x.startswith('0x') else f'0x{x}'.upper()
        mock.eth.get_balance.return_value = 1000000000000000000  # 1 ETH in wei
        mock.from_wei.return_value = 1.0
        return mock
    
    @pytest.fixture
    def blockchain_client(self, mock_w3):
        """Create blockchain client with mocked Web3."""
        with patch('app.data.blockchain_client.Web3') as mock_web3_class:
            mock_web3_class.return_value = mock_w3
            mock_web3_class.HTTPProvider = Mock()
            mock_web3_class.to_checksum_address = mock_w3.to_checksum_address
            
            client = BlockchainClient()
            client.w3 = mock_w3
            return client
    
    @pytest.mark.asyncio
    async def test_get_trader_portfolio_success(self, blockchain_client):
        """Test successful portfolio retrieval."""
        test_address = "0x742ba4cb0d5a3c41f9c1c2e4dcb9c1f9d2c8c1f1"
        
        # Mock the async methods
        blockchain_client._get_eth_balance = AsyncMock(return_value=Decimal('2000.0'))
        blockchain_client._get_usdc_balance = AsyncMock(return_value=Decimal('5000.0'))
        blockchain_client._get_polymarket_positions = AsyncMock(return_value=[
            {
                "market_id": "test_market",
                "total_position_size_usd": 1000.0,
                "current_value_usd": 1200.0
            }
        ])
        
        result = await blockchain_client.get_trader_portfolio(test_address)
        
        assert result["address"] == test_address
        assert result["total_portfolio_value_usd"] == 8200.0  # 2000 + 5000 + 1200
        assert result["active_positions"] == 1
        assert "positions" in result
        assert result["eth_balance_usd"] == 2000.0
        assert result["usdc_balance"] == 5000.0
    
    @pytest.mark.asyncio
    async def test_get_trader_portfolio_invalid_address(self, blockchain_client):
        """Test portfolio retrieval with invalid address."""
        blockchain_client.w3.is_address.return_value = False
        
        result = await blockchain_client.get_trader_portfolio("invalid_address")
        
        assert "error" in result
        assert result["total_portfolio_value_usd"] == 0
        assert result["active_positions"] == 0
    
    @pytest.mark.asyncio
    async def test_get_transaction_history_success(self, blockchain_client):
        """Test successful transaction history retrieval."""
        test_address = "0x742ba4cb0d5a3c41f9c1c2e4dcb9c1f9d2c8c1f1"
        
        mock_response_data = {
            "status": "1",
            "result": [
                {
                    "hash": "0x123...",
                    "to": "0x4d97dcd97ec945f40cf65f87097ace5ea0476045",
                    "value": "1000000000000000000",
                    "timeStamp": "1640995200",
                    "blockNumber": "12345",
                    "gasUsed": "21000",
                    "isError": "0"
                }
            ]
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            result = await blockchain_client.get_transaction_history(test_address)
            
            assert len(result) == 1
            assert result[0]["hash"] == "0x123..."
    
    @pytest.mark.asyncio
    async def test_get_transaction_history_no_api_key(self, blockchain_client):
        """Test transaction history without API key."""
        blockchain_client.etherscan_api_key = None
        
        result = await blockchain_client.get_transaction_history("0x123...")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_polymarket_positions(self, blockchain_client):
        """Test Polymarket position retrieval."""
        test_address = "0x742ba4cb0d5a3c41f9c1c2e4dcb9c1f9d2c8c1f1"
        
        # Mock transaction history with Polymarket transactions
        mock_transactions = [
            {
                "hash": "0x123...",
                "to": "0x4d97dcd97ec945f40cf65f87097ace5ea0476045",
                "value": "1000000000000000000",
                "timeStamp": "1640995200",
                "blockNumber": "12345",
                "gasUsed": "21000",
                "isError": "0",
                "input": "0xa9059cbb"
            }
        ]
        
        blockchain_client.get_transaction_history = AsyncMock(return_value=mock_transactions)
        blockchain_client._get_eth_price = AsyncMock(return_value=2000.0)
        
        result = await blockchain_client.get_polymarket_positions(test_address)
        
        assert isinstance(result, list)
        # Should have processed the transaction
        if result:  # If the mock transaction was processed
            assert "market_id" in result[0]
            assert "total_position_size_usd" in result[0]
    
    @pytest.mark.asyncio
    async def test_verify_market_participation(self, blockchain_client):
        """Test market participation verification."""
        test_address = "0x742ba4cb0d5a3c41f9c1c2e4dcb9c1f9d2c8c1f1"
        test_market_id = "test_market"
        
        # Mock positions with matching market
        mock_positions = [
            {
                "market_id": test_market_id,
                "total_position_size_usd": 1000.0
            }
        ]
        
        blockchain_client.get_polymarket_positions = AsyncMock(return_value=mock_positions)
        
        result = await blockchain_client.verify_market_participation(test_address, test_market_id)
        
        assert result["has_position"] is True
        assert result["position_count"] == 1
        assert result["total_position_size_usd"] == 1000.0
    
    @pytest.mark.asyncio
    async def test_verify_market_participation_no_position(self, blockchain_client):
        """Test market participation verification with no position."""
        test_address = "0x742ba4cb0d5a3c41f9c1c2e4dcb9c1f9d2c8c1f1"
        test_market_id = "test_market"
        
        blockchain_client.get_polymarket_positions = AsyncMock(return_value=[])
        
        result = await blockchain_client.verify_market_participation(test_address, test_market_id)
        
        assert result["has_position"] is False
        assert result["position_count"] == 0
        assert result["total_position_size_usd"] == 0.0
    
    @pytest.mark.asyncio
    async def test_get_eth_balance(self, blockchain_client):
        """Test ETH balance retrieval."""
        test_address = "0x742ba4cb0d5a3c41f9c1c2e4dcb9c1f9d2c8c1f1"
        
        blockchain_client._get_eth_price = AsyncMock(return_value=2000.0)
        
        result = await blockchain_client._get_eth_balance(test_address)
        
        assert result == Decimal('2000.0')  # 1 ETH * $2000
    
    @pytest.mark.asyncio
    async def test_get_usdc_balance(self, blockchain_client):
        """Test USDC balance retrieval."""
        test_address = "0x742ba4cb0d5a3c41f9c1c2e4dcb9c1f9d2c8c1f1"
        
        # Mock contract calls
        mock_contract = Mock()
        mock_contract.functions.balanceOf.return_value.call.return_value = 1000000000  # 1000 USDC (6 decimals)
        mock_contract.functions.decimals.return_value.call.return_value = 6
        
        blockchain_client.w3.eth.contract.return_value = mock_contract
        
        result = await blockchain_client._get_usdc_balance(test_address)
        
        assert result == Decimal('1000.0')
    
    @pytest.mark.asyncio
    async def test_get_eth_price(self, blockchain_client):
        """Test ETH price retrieval."""
        mock_response_data = {
            "ethereum": {
                "usd": 2500.0
            }
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            result = await blockchain_client._get_eth_price()
            
            assert result == 2500.0
    
    @pytest.mark.asyncio
    async def test_get_eth_price_fallback(self, blockchain_client):
        """Test ETH price fallback when API fails."""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            result = await blockchain_client._get_eth_price()
            
            assert result == 2500.0  # Fallback price
    
    def test_is_polymarket_transaction(self, blockchain_client):
        """Test Polymarket transaction identification."""
        # Positive case
        polymarket_tx = {
            "to": "0x4d97dcd97ec945f40cf65f87097ace5ea0476045",  # Conditional Tokens
            "input": "0xa9059cbb..."
        }
        
        assert blockchain_client._is_polymarket_transaction(polymarket_tx) is True
        
        # Negative case
        regular_tx = {
            "to": "0x742ba4cb0d5a3c41f9c1c2e4dcb9c1f9d2c8c1f1",
            "input": "0x"
        }
        
        assert blockchain_client._is_polymarket_transaction(regular_tx) is False
    
    @pytest.mark.asyncio
    async def test_parse_polymarket_transaction(self, blockchain_client):
        """Test Polymarket transaction parsing."""
        test_tx = {
            "hash": "0x123...",
            "value": "1000000000000000000",  # 1 ETH
            "timeStamp": "1640995200",
            "blockNumber": "12345",
            "gasUsed": "21000",
            "isError": "0",
            "input": "0xa9059cbb"
        }
        
        blockchain_client._get_eth_price = AsyncMock(return_value=2000.0)
        
        result = await blockchain_client._parse_polymarket_transaction(test_tx)
        
        assert result is not None
        assert result["transaction_hash"] == "0x123..."
        assert result["position_size_usd"] == 2000.0  # 1 ETH * $2000
        assert result["transaction_type"] == "transfer"
    
    def test_aggregate_positions(self, blockchain_client):
        """Test position aggregation."""
        positions = [
            {
                "market_id": "market_1",
                "position_size_usd": 1000.0,
                "timestamp": 1640995200
            },
            {
                "market_id": "market_1",
                "position_size_usd": 500.0,
                "timestamp": 1640995300
            },
            {
                "market_id": "market_2",
                "position_size_usd": 2000.0,
                "timestamp": 1640995400
            }
        ]
        
        result = blockchain_client._aggregate_positions(positions)
        
        assert len(result) == 2
        
        # Find market_1 aggregated data
        market_1_data = next(pos for pos in result if pos["market_id"] == "market_1")
        assert market_1_data["total_position_size_usd"] == 1500.0
        assert market_1_data["transaction_count"] == 2
        
        # Find market_2 data
        market_2_data = next(pos for pos in result if pos["market_id"] == "market_2")
        assert market_2_data["total_position_size_usd"] == 2000.0
        assert market_2_data["transaction_count"] == 1
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, blockchain_client):
        """Test rate limiting functionality."""
        start_time = time.time()
        
        # Make multiple calls
        await blockchain_client._rate_limit()
        await blockchain_client._rate_limit()
        
        end_time = time.time()
        
        # Should have taken at least one rate limit interval
        assert end_time - start_time >= blockchain_client.min_request_interval
    
    def test_is_connected(self, blockchain_client):
        """Test connection status check."""
        assert blockchain_client.is_connected() is True
        
        blockchain_client.w3 = None
        assert blockchain_client.is_connected() is False
    
    @pytest.mark.asyncio
    async def test_get_token_balance(self, blockchain_client):
        """Test generic token balance retrieval."""
        test_token_address = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
        test_wallet_address = "0x742ba4cb0d5a3c41f9c1c2e4dcb9c1f9d2c8c1f1"
        
        # Mock contract calls
        mock_contract = Mock()
        mock_contract.functions.balanceOf.return_value.call.return_value = 500000000  # 500 tokens (6 decimals)
        mock_contract.functions.decimals.return_value.call.return_value = 6
        
        blockchain_client.get_contract_instance = Mock(return_value=mock_contract)
        
        result = await blockchain_client.get_token_balance(test_token_address, test_wallet_address)
        
        assert result == Decimal('500.0')
    
    @pytest.mark.asyncio
    async def test_get_block_timestamp(self, blockchain_client):
        """Test block timestamp retrieval."""
        test_block_number = 12345
        
        mock_block = {"timestamp": 1640995200}
        blockchain_client.w3.eth.get_block.return_value = mock_block
        
        result = await blockchain_client.get_block_timestamp(test_block_number)
        
        assert result == 1640995200


@pytest.mark.integration
class TestBlockchainClientIntegration:
    """Integration tests for BlockchainClient (requires network access)."""
    
    @pytest.mark.skip(reason="Requires actual API keys and network access")
    async def test_real_trader_portfolio(self):
        """Test with real trader address (requires API keys)."""
        client = BlockchainClient()
        
        # Use a known active trader address
        test_address = "0x742ba4cb0d5a3c41f9c1c2e4dcb9c1f9d2c8c1f1"
        
        result = await client.get_trader_portfolio(test_address)
        
        assert "address" in result
        assert "total_portfolio_value_usd" in result
        assert result["address"] == test_address
    
    @pytest.mark.skip(reason="Requires actual API keys and network access")
    async def test_real_transaction_history(self):
        """Test with real transaction history (requires API keys)."""
        client = BlockchainClient()
        
        test_address = "0x742ba4cb0d5a3c41f9c1c2e4dcb9c1f9d2c8c1f1"
        
        result = await client.get_transaction_history(test_address, limit=10)
        
        assert isinstance(result, list)
        if result:  # If the address has transactions
            assert "hash" in result[0]
            assert "timeStamp" in result[0]