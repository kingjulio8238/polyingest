from typing import Dict, Any, List, Optional
from decimal import Decimal
import asyncio
import logging
import time
from datetime import datetime, timezone

from app.agents.base_agent import BaseAgent
from app.agents.portfolio_agent import PortfolioAnalyzerAgent
from app.agents.success_rate_agent import SuccessRateAgent
from app.agents.voting_system import VotingSystem, VotingResult
from app.config import settings

logger = logging.getLogger(__name__)

class AgentCoordinator:
    """
    Main orchestration layer for the multi-agent alpha detection system.
    
    This class serves as the single point of entry for all alpha detection requests,
    coordinating the entire workflow from data preparation to final result formatting.
    """
    
    def __init__(self, vote_threshold: Optional[float] = None):
        """
        Initialize the AgentCoordinator with all analysis agents and voting system.
        
        Args:
            vote_threshold: Custom voting threshold (defaults to settings.agent_vote_threshold)
        """
        self.voting_system = VotingSystem(vote_threshold)
        self.performance_metrics = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "avg_analysis_duration": 0.0,
            "agent_health": {}
        }
        
        # Initialize and register all agents
        self._initialize_agents()
        
        logger.info(f"AgentCoordinator initialized with {len(self.voting_system.agents)} agents")
    
    def _initialize_agents(self) -> None:
        """Initialize and register all analysis agents."""
        try:
            # Initialize Portfolio Analyzer Agent
            portfolio_agent = PortfolioAnalyzerAgent()
            self.voting_system.register_agent(portfolio_agent)
            
            # Initialize Success Rate Agent
            success_rate_agent = SuccessRateAgent()
            self.voting_system.register_agent(success_rate_agent)
            
            logger.info("All analysis agents initialized and registered")
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            raise
    
    async def analyze_market(self, 
                           market_data: Dict[str, Any], 
                           traders_data: List[Dict[str, Any]], 
                           filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main analysis method that orchestrates the entire alpha detection process.
        
        Args:
            market_data: Market information and pricing data
            traders_data: List of trader performance and position data
            filters: Optional filtering criteria (min_portfolio_ratio, min_success_rate, etc.)
            
        Returns:
            Comprehensive alpha analysis result following CLAUDE.md API specification
        """
        start_time = time.time()
        analysis_id = f"{market_data.get('id', 'unknown')}_{int(start_time)}"
        
        logger.info(f"Starting alpha analysis {analysis_id} for market {market_data.get('id')}")
        
        try:
            # Update performance tracking
            self.performance_metrics["total_analyses"] += 1
            
            # Validate and prepare data
            validated_market_data = self.prepare_market_data(market_data)
            filtered_traders_data = self.filter_traders(traders_data, filters)
            
            if not validated_market_data:
                raise ValueError("Invalid market data provided")
            
            if not filtered_traders_data:
                logger.warning(f"No traders found after filtering for market {market_data.get('id')}")
                return self._format_no_alpha_result(validated_market_data, "No qualifying traders found")
            
            logger.info(f"Analysis data prepared: {len(filtered_traders_data)} traders after filtering")
            
            # Prepare data package for agents
            agent_data = {
                "market": validated_market_data,
                "traders": filtered_traders_data,
                "filters": filters or {},
                "analysis_id": analysis_id
            }
            
            # Conduct voting process with all agents
            voting_result = await self.voting_system.conduct_vote(agent_data)
            
            # Format final analysis result
            analysis_result = self.format_analysis_result(
                validated_market_data, 
                filtered_traders_data, 
                voting_result, 
                filters
            )
            
            # Update performance metrics
            duration = time.time() - start_time
            self._update_performance_metrics(duration, True)
            
            logger.info(f"Alpha analysis {analysis_id} completed in {duration:.2f}s - "
                       f"Alpha: {voting_result.has_alpha}, Confidence: {voting_result.confidence_score}")
            
            return analysis_result
            
        except Exception as e:
            duration = time.time() - start_time
            self._update_performance_metrics(duration, False)
            logger.error(f"Alpha analysis {analysis_id} failed after {duration:.2f}s: {e}")
            
            # Return error response in API format
            return self._format_error_result(market_data, str(e))
    
    def prepare_market_data(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean market data for agent consumption.
        
        Args:
            market_data: Raw market data
            
        Returns:
            Validated and cleaned market data
        """
        if not market_data:
            return {}
        
        # Required fields validation
        required_fields = ["id", "title", "status"]
        for field in required_fields:
            if field not in market_data:
                logger.error(f"Missing required market field: {field}")
                return {}
        
        # Clean and validate market data
        cleaned_data = {
            "id": str(market_data.get("id", "")),
            "title": str(market_data.get("title", "")),
            "description": str(market_data.get("description", "")),
            "category": market_data.get("category"),
            "subcategory": market_data.get("subcategory"),
            "end_date": market_data.get("end_date"),
            "resolution_criteria": str(market_data.get("resolution_criteria", "")),
            "status": str(market_data.get("status", "unknown")),
            "creator": str(market_data.get("creator", "")),
            "total_volume": max(0, float(market_data.get("total_volume", 0))),
            "total_liquidity": max(0, float(market_data.get("total_liquidity", 0))),
            "outcomes": market_data.get("outcomes", [])
        }
        
        # Add current prices if available
        if "current_prices" in market_data:
            cleaned_data["current_prices"] = market_data["current_prices"]
        
        # Add trading activity if available
        if "trading_activity" in market_data:
            cleaned_data["trading_activity"] = market_data["trading_activity"]
        
        return cleaned_data
    
    def filter_traders(self, 
                      traders_data: List[Dict[str, Any]], 
                      filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Apply filtering criteria to trader data.
        
        Args:
            traders_data: List of trader data
            filters: Filtering criteria
            
        Returns:
            Filtered list of trader data
        """
        if not traders_data:
            return []
        
        # Default filter values
        min_portfolio_ratio = filters.get("min_portfolio_ratio", settings.min_portfolio_ratio) if filters else settings.min_portfolio_ratio
        min_success_rate = filters.get("min_success_rate", settings.min_success_rate) if filters else settings.min_success_rate
        min_trade_history = filters.get("min_trade_history", settings.min_trade_history) if filters else settings.min_trade_history
        min_portfolio_value = filters.get("min_portfolio_value", 1000) if filters else 1000  # $1000 minimum
        
        filtered_traders = []
        
        for trader in traders_data:
            try:
                # Basic validation
                if not trader.get("address"):
                    continue
                
                # Portfolio value filter
                portfolio_value = float(trader.get("total_portfolio_value_usd", 0))
                if portfolio_value < min_portfolio_value:
                    continue
                
                # Performance metrics validation
                performance = trader.get("performance_metrics", {})
                success_rate = float(performance.get("overall_success_rate", 0))
                markets_resolved = int(performance.get("markets_resolved", 0))
                
                # Apply filters
                if success_rate < min_success_rate and markets_resolved >= min_trade_history:
                    continue
                
                if markets_resolved < min_trade_history:
                    # Allow traders with less history but very high success rates
                    if success_rate < 0.8 or markets_resolved < 3:
                        continue
                
                # Portfolio allocation filter (check if trader has any significant positions)
                positions = trader.get("positions", [])
                has_significant_position = False
                
                for position in positions:
                    allocation_pct = float(position.get("portfolio_allocation_pct", 0))
                    if allocation_pct >= min_portfolio_ratio:
                        has_significant_position = True
                        break
                
                # Include trader if they pass filters
                filtered_traders.append(trader)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Error processing trader {trader.get('address', 'unknown')}: {e}")
                continue
        
        logger.info(f"Filtered traders: {len(filtered_traders)} from {len(traders_data)} original traders")
        return filtered_traders
    
    def format_analysis_result(self, 
                             market_data: Dict[str, Any], 
                             traders_data: List[Dict[str, Any]], 
                             voting_result: VotingResult, 
                             filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Format the analysis result according to CLAUDE.md API specification.
        
        Args:
            market_data: Validated market data
            traders_data: Filtered trader data
            voting_result: Results from agent voting
            filters: Applied filtering criteria
            
        Returns:
            API-compliant alpha analysis response
        """
        # Determine recommended side and strength
        recommended_side = self._determine_recommended_side(traders_data, voting_result)
        strength = self._calculate_strength(voting_result.confidence_score, voting_result.votes_for_alpha)
        
        # Extract key traders (top performers with significant positions)
        key_traders = self._extract_key_traders(traders_data, market_data, voting_result)
        
        # Generate risk factors
        risk_factors = self._generate_risk_factors(market_data, traders_data, voting_result)
        
        # Format agent analyses for API response
        agent_analyses = self._format_agent_analyses(voting_result.agent_results)
        
        return {
            "market": {
                "id": market_data["id"],
                "title": market_data["title"],
                "description": market_data["description"],
                "end_date": market_data.get("end_date"),
                "status": market_data["status"],
                "current_prices": market_data.get("current_prices", {}),
                "total_volume_24h": market_data.get("total_volume", 0),
                "total_liquidity": market_data.get("total_liquidity", 0)
            },
            "alpha_analysis": {
                "has_alpha": voting_result.has_alpha,
                "confidence_score": round(voting_result.confidence_score, 3),
                "recommended_side": recommended_side,
                "strength": strength,
                "agent_consensus": {
                    "votes_for_alpha": voting_result.votes_for_alpha,
                    "votes_against_alpha": voting_result.votes_against_alpha,
                    "abstentions": voting_result.abstentions
                }
            },
            "key_traders": key_traders,
            "agent_analyses": agent_analyses,
            "risk_factors": risk_factors,
            "metadata": {
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "data_freshness": "real-time",
                "trader_sample_size": len(traders_data),
                "min_portfolio_ratio_filter": filters.get("min_portfolio_ratio", settings.min_portfolio_ratio) if filters else settings.min_portfolio_ratio,
                "min_success_rate_filter": filters.get("min_success_rate", settings.min_success_rate) if filters else settings.min_success_rate,
                "consensus_reached": voting_result.consensus_reached,
                "voting_duration_seconds": round(voting_result.voting_duration, 3)
            }
        }
    
    def _determine_recommended_side(self, 
                                  traders_data: List[Dict[str, Any]], 
                                  voting_result: VotingResult) -> Optional[str]:
        """Determine the recommended market side based on trader positions."""
        if not voting_result.has_alpha:
            return None
        
        # Analyze trader positions to determine side bias
        yes_weight = 0.0
        no_weight = 0.0
        
        for trader in traders_data:
            positions = trader.get("positions", [])
            portfolio_value = float(trader.get("total_portfolio_value_usd", 0))
            
            for position in positions:
                position_size = float(position.get("position_size_usd", 0))
                outcome_id = position.get("outcome_id", "").lower()
                
                # Weight by position size
                weight = position_size / max(portfolio_value, 1)
                
                if "yes" in outcome_id or outcome_id == "1":
                    yes_weight += weight
                elif "no" in outcome_id or outcome_id == "0":
                    no_weight += weight
        
        if yes_weight > no_weight * 1.2:  # 20% threshold for clear bias
            return "Yes"
        elif no_weight > yes_weight * 1.2:
            return "No"
        
        return None  # No clear side preference
    
    def _calculate_strength(self, confidence_score: float, votes_for_alpha: int) -> str:
        """Calculate alpha signal strength."""
        if confidence_score >= 0.8 and votes_for_alpha >= 3:
            return "strong"
        elif confidence_score >= 0.6 and votes_for_alpha >= 2:
            return "moderate"
        else:
            return "weak"
    
    def _extract_key_traders(self, 
                           traders_data: List[Dict[str, Any]], 
                           market_data: Dict[str, Any], 
                           voting_result: VotingResult) -> List[Dict[str, Any]]:
        """Extract and format key traders for API response."""
        key_traders = []
        
        # Sort traders by combination of position size and success rate
        sorted_traders = sorted(
            traders_data,
            key=lambda t: (
                float(t.get("performance_metrics", {}).get("overall_success_rate", 0)) *
                float(t.get("total_portfolio_value_usd", 0))
            ),
            reverse=True
        )
        
        market_id = market_data["id"]
        
        for trader in sorted_traders[:10]:  # Top 10 traders
            performance = trader.get("performance_metrics", {})
            positions = trader.get("positions", [])
            
            # Find market-specific positions
            market_positions = [
                pos for pos in positions 
                if pos.get("market_id") == market_id
            ]
            
            if not market_positions:
                continue
            
            # Calculate total position in this market
            total_position_size = sum(
                float(pos.get("position_size_usd", 0)) 
                for pos in market_positions
            )
            
            portfolio_value = float(trader.get("total_portfolio_value_usd", 0))
            allocation_pct = (total_position_size / portfolio_value * 100) if portfolio_value > 0 else 0
            
            # Get primary position side
            largest_position = max(market_positions, key=lambda p: float(p.get("position_size_usd", 0)))
            position_side = largest_position.get("outcome_id", "Unknown")
            entry_price = float(largest_position.get("entry_price", 0))
            
            # Generate confidence indicators
            confidence_indicators = {
                "large_position": total_position_size >= 10000,
                "high_allocation": allocation_pct >= settings.min_portfolio_ratio * 100,
                "proven_track_record": float(performance.get("overall_success_rate", 0)) >= settings.min_success_rate,
                "early_entry": entry_price <= 0.6  # Assume early entry if price was low
            }
            
            key_traders.append({
                "address": trader["address"],
                "position_size_usd": round(total_position_size, 2),
                "portfolio_allocation_pct": round(allocation_pct, 1),
                "historical_success_rate": round(float(performance.get("overall_success_rate", 0)), 3),
                "position_side": position_side,
                "entry_price": round(entry_price, 3),
                "confidence_indicators": confidence_indicators
            })
        
        return key_traders
    
    def _generate_risk_factors(self, 
                             market_data: Dict[str, Any], 
                             traders_data: List[Dict[str, Any]], 
                             voting_result: VotingResult) -> List[str]:
        """Generate risk factors for the alpha analysis."""
        risk_factors = []
        
        # Market-specific risks
        if market_data.get("category", "").lower() in ["politics", "elections"]:
            risk_factors.append("Market highly politicized - emotion may override analysis")
        
        # Time to resolution risk
        end_date = market_data.get("end_date")
        if end_date:
            try:
                # Add basic time risk assessment
                risk_factors.append("Time to resolution risk - events may change market dynamics")
            except:
                pass
        
        # Liquidity risk
        total_liquidity = float(market_data.get("total_liquidity", 0))
        if total_liquidity < 100000:
            risk_factors.append("Low liquidity market - price impact and execution risk")
        
        # Trader concentration risk
        if len(traders_data) < 5:
            risk_factors.append("Limited trader sample - analysis based on few participants")
        
        # Voting consensus risk
        if not voting_result.consensus_reached:
            risk_factors.append("Agent consensus not reached - mixed signals from analysis")
        
        if voting_result.abstentions > voting_result.votes_for_alpha:
            risk_factors.append("High agent abstention rate - uncertain analysis environment")
        
        # Success rate variance risk
        success_rates = [
            float(t.get("performance_metrics", {}).get("overall_success_rate", 0))
            for t in traders_data
        ]
        if success_rates and (max(success_rates) - min(success_rates)) > 0.4:
            risk_factors.append("High variance in trader performance - mixed track records")
        
        return risk_factors
    
    def _format_agent_analyses(self, agent_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format agent analysis results for API response."""
        formatted_analyses = []
        
        for result in agent_results:
            # Extract key findings from analysis
            analysis = result.get("analysis", {})
            key_findings = []
            
            # Format findings based on agent type
            agent_name = result["agent_name"]
            
            if "Portfolio" in agent_name:
                high_conviction_count = analysis.get("high_conviction_count", 0)
                avg_allocation = analysis.get("average_allocation", 0)
                if high_conviction_count > 0:
                    key_findings.append(f"{high_conviction_count} traders with high portfolio allocation")
                    key_findings.append(f"Average allocation: {avg_allocation:.1%}")
            
            elif "Success Rate" in agent_name:
                high_performers = analysis.get("high_performers_count", 0)
                avg_success_rate = analysis.get("avg_success_rate", 0)
                if high_performers > 0:
                    key_findings.append(f"{high_performers} high-performing traders identified")
                    key_findings.append(f"Average success rate: {avg_success_rate:.1%}")
            
            # Add generic findings if no specific ones
            if not key_findings:
                key_findings.append("Analysis completed with available data")
            
            formatted_analyses.append({
                "agent_name": agent_name,
                "vote": result["vote"],
                "confidence": round(result["confidence"], 3),
                "reasoning": result["reasoning"],
                "key_findings": key_findings
            })
        
        return formatted_analyses
    
    def _format_no_alpha_result(self, market_data: Dict[str, Any], reason: str) -> Dict[str, Any]:
        """Format a no-alpha result when insufficient data is available."""
        return {
            "market": {
                "id": market_data.get("id", "unknown"),
                "title": market_data.get("title", "Unknown Market"),
                "description": market_data.get("description", ""),
                "status": market_data.get("status", "unknown")
            },
            "alpha_analysis": {
                "has_alpha": False,
                "confidence_score": 0.0,
                "recommended_side": None,
                "strength": "none",
                "agent_consensus": {
                    "votes_for_alpha": 0,
                    "votes_against_alpha": 0,
                    "abstentions": 0
                }
            },
            "key_traders": [],
            "agent_analyses": [],
            "risk_factors": [reason],
            "metadata": {
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "data_freshness": "real-time",
                "trader_sample_size": 0,
                "error": reason
            }
        }
    
    def _format_error_result(self, market_data: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """Format an error result when analysis fails."""
        return {
            "market": {
                "id": market_data.get("id", "unknown"),
                "title": market_data.get("title", "Unknown Market"),
                "description": market_data.get("description", ""),
                "status": "error"
            },
            "alpha_analysis": {
                "has_alpha": False,
                "confidence_score": 0.0,
                "recommended_side": None,
                "strength": "none",
                "agent_consensus": {
                    "votes_for_alpha": 0,
                    "votes_against_alpha": 0,
                    "abstentions": 0
                }
            },
            "key_traders": [],
            "agent_analyses": [],
            "risk_factors": [f"Analysis failed: {error_message}"],
            "metadata": {
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "error": error_message,
                "status": "failed"
            }
        }
    
    def _update_performance_metrics(self, duration: float, success: bool) -> None:
        """Update performance tracking metrics."""
        if success:
            self.performance_metrics["successful_analyses"] += 1
        
        # Update average duration
        total_analyses = self.performance_metrics["total_analyses"]
        current_avg = self.performance_metrics["avg_analysis_duration"]
        self.performance_metrics["avg_analysis_duration"] = (
            (current_avg * (total_analyses - 1) + duration) / total_analyses
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance monitoring data for the coordinator.
        
        Returns:
            Dictionary containing performance metrics and agent health status
        """
        # Calculate success rate
        total = self.performance_metrics["total_analyses"]
        successful = self.performance_metrics["successful_analyses"]
        success_rate = (successful / total) if total > 0 else 0.0
        
        # Get agent health status
        agent_health = {}
        for agent_name, agent in self.voting_system.agents.items():
            agent_health[agent_name] = {
                "weight": agent.weight,
                "confidence": float(agent.get_confidence()),
                "status": "healthy"  # Could be enhanced with actual health checks
            }
        
        # Get voting system summary
        voting_summary = self.voting_system.get_voting_summary()
        
        return {
            "coordinator_performance": {
                "total_analyses": total,
                "successful_analyses": successful,
                "success_rate": round(success_rate, 3),
                "avg_analysis_duration": round(self.performance_metrics["avg_analysis_duration"], 3)
            },
            "agent_health": agent_health,
            "voting_system": voting_summary,
            "system_status": "operational" if success_rate > 0.8 else "degraded"
        }
    
    def update_agent_performance(self, performance_data: Dict[str, float]) -> None:
        """
        Update agent weights based on historical performance data.
        
        Args:
            performance_data: Dict mapping agent names to accuracy scores (0.0 to 1.0)
        """
        self.voting_system.update_agent_weights(performance_data)
        logger.info(f"Updated agent weights: {performance_data}")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get detailed status of all registered agents."""
        return {
            "registered_agents": self.voting_system.get_registered_agents(),
            "voting_config": {
                "threshold": self.voting_system.vote_threshold,
                "min_participation": self.voting_system.min_participation_ratio
            },
            "agent_details": {
                name: {
                    "type": type(agent).__name__,
                    "weight": agent.weight,
                    "last_confidence": float(agent.get_confidence())
                }
                for name, agent in self.voting_system.agents.items()
            }
        }