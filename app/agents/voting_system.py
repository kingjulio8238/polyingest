from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import asyncio
import logging
import time
from datetime import datetime, timezone

from app.agents.base_agent import BaseAgent
from app.config import settings

logger = logging.getLogger(__name__)

class VotingResult:
    """Represents the result of a voting process."""
    
    def __init__(self, 
                 has_alpha: bool, 
                 confidence_score: float, 
                 consensus_reached: bool,
                 votes_for_alpha: int,
                 votes_against_alpha: int,
                 abstentions: int,
                 total_weight: float,
                 weighted_alpha_score: float,
                 agent_results: List[Dict[str, Any]],
                 reasoning_summary: str,
                 voting_duration: float):
        self.has_alpha = has_alpha
        self.confidence_score = confidence_score
        self.consensus_reached = consensus_reached
        self.votes_for_alpha = votes_for_alpha
        self.votes_against_alpha = votes_against_alpha
        self.abstentions = abstentions
        self.total_weight = total_weight
        self.weighted_alpha_score = weighted_alpha_score
        self.agent_results = agent_results
        self.reasoning_summary = reasoning_summary
        self.voting_duration = voting_duration
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert voting result to dictionary format."""
        return {
            "has_alpha": self.has_alpha,
            "confidence_score": self.confidence_score,
            "consensus_reached": self.consensus_reached,
            "agent_consensus": {
                "votes_for_alpha": self.votes_for_alpha,
                "votes_against_alpha": self.votes_against_alpha,
                "abstentions": self.abstentions,
                "total_agents": len(self.agent_results)
            },
            "weighted_scores": {
                "total_weight": self.total_weight,
                "weighted_alpha_score": self.weighted_alpha_score,
                "threshold": settings.agent_vote_threshold
            },
            "agent_analyses": self.agent_results,
            "reasoning_summary": self.reasoning_summary,
            "metadata": {
                "voting_duration_seconds": self.voting_duration,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }


class VotingSystem:
    """Coordinates multiple analysis agents and builds consensus for alpha detection."""
    
    def __init__(self, vote_threshold: Optional[float] = None):
        """
        Initialize the voting system.
        
        Args:
            vote_threshold: Custom voting threshold (defaults to settings.agent_vote_threshold)
        """
        self.agents: Dict[str, BaseAgent] = {}
        self.vote_threshold = vote_threshold or settings.agent_vote_threshold
        self.min_participation_ratio = 0.5  # At least 50% of agents must not abstain
        
        logger.info(f"VotingSystem initialized with threshold: {self.vote_threshold}")
    
    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an analysis agent for participation in voting.
        
        Args:
            agent: The agent to register
        """
        if not isinstance(agent, BaseAgent):
            raise ValueError(f"Agent must be instance of BaseAgent, got {type(agent)}")
        
        if agent.name in self.agents:
            logger.warning(f"Agent '{agent.name}' already registered, replacing")
        
        self.agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name} (weight: {agent.weight})")
    
    def unregister_agent(self, agent_name: str) -> bool:
        """
        Remove an agent from the voting system.
        
        Args:
            agent_name: Name of the agent to remove
            
        Returns:
            True if agent was removed, False if not found
        """
        if agent_name in self.agents:
            del self.agents[agent_name]
            logger.info(f"Unregistered agent: {agent_name}")
            return True
        return False
    
    def get_registered_agents(self) -> List[str]:
        """Get list of registered agent names."""
        return list(self.agents.keys())
    
    async def conduct_vote(self, data: Dict[str, Any]) -> VotingResult:
        """
        Conduct a full voting process with all registered agents.
        
        Args:
            data: Market and trader data for analysis
            
        Returns:
            VotingResult containing comprehensive voting outcome
        """
        start_time = time.time()
        
        if not self.agents:
            logger.warning("No agents registered for voting")
            return VotingResult(
                has_alpha=False,
                confidence_score=0.0,
                consensus_reached=False,
                votes_for_alpha=0,
                votes_against_alpha=0,
                abstentions=0,
                total_weight=0.0,
                weighted_alpha_score=0.0,
                agent_results=[],
                reasoning_summary="No agents available for voting",
                voting_duration=time.time() - start_time
            )
        
        logger.info(f"Starting voting process with {len(self.agents)} agents")
        
        # Collect analyses from all agents concurrently
        agent_votes = await self._collect_agent_votes(data)
        
        # Calculate consensus
        voting_result = self._calculate_consensus(agent_votes)
        voting_result.voting_duration = time.time() - start_time
        
        logger.info(f"Voting completed in {voting_result.voting_duration:.2f}s - "
                   f"Alpha: {voting_result.has_alpha}, "
                   f"Confidence: {voting_result.confidence_score:.2f}, "
                   f"Consensus: {voting_result.consensus_reached}")
        
        return voting_result
    
    async def _collect_agent_votes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Collect votes from all registered agents concurrently.
        
        Args:
            data: Market and trader data for analysis
            
        Returns:
            List of agent vote results
        """
        async def analyze_and_vote(agent_name: str, agent: BaseAgent) -> Dict[str, Any]:
            """Analyze data and cast vote for a single agent."""
            try:
                logger.debug(f"Starting analysis for agent: {agent_name}")
                
                # Perform analysis
                analysis = await agent.analyze(data)
                
                # Cast vote based on analysis
                vote = agent.vote(analysis)
                
                # Get confidence and reasoning
                confidence = float(agent.get_confidence())
                reasoning = ""
                
                # Try to get reasoning if agent supports it
                if hasattr(agent, 'get_reasoning'):
                    try:
                        reasoning = agent.get_reasoning()
                    except Exception as e:
                        logger.warning(f"Failed to get reasoning from {agent_name}: {e}")
                        reasoning = f"Analysis completed (reasoning unavailable)"
                
                # Calculate effective vote weight
                vote_weight = agent.weight * confidence
                
                result = {
                    "agent_name": agent_name,
                    "vote": vote,
                    "confidence": confidence,
                    "agent_weight": agent.weight,
                    "effective_weight": vote_weight,
                    "reasoning": reasoning,
                    "analysis": analysis,
                    "success": True,
                    "error": None
                }
                
                logger.debug(f"Agent {agent_name} voted '{vote}' with confidence {confidence:.2f}")
                return result
                
            except Exception as e:
                logger.error(f"Agent {agent_name} failed: {e}")
                return {
                    "agent_name": agent_name,
                    "vote": "abstain",
                    "confidence": 0.0,
                    "agent_weight": agent.weight,
                    "effective_weight": 0.0,
                    "reasoning": f"Analysis failed: {str(e)}",
                    "analysis": {"error": str(e)},
                    "success": False,
                    "error": str(e)
                }
        
        # Execute all agent analyses concurrently
        tasks = [
            analyze_and_vote(name, agent) 
            for name, agent in self.agents.items()
        ]
        
        agent_votes = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions from gather
        processed_votes = []
        for i, result in enumerate(agent_votes):
            if isinstance(result, Exception):
                agent_name = list(self.agents.keys())[i]
                logger.error(f"Exception in agent {agent_name}: {result}")
                processed_votes.append({
                    "agent_name": agent_name,
                    "vote": "abstain",
                    "confidence": 0.0,
                    "agent_weight": self.agents[agent_name].weight,
                    "effective_weight": 0.0,
                    "reasoning": f"Exception occurred: {str(result)}",
                    "analysis": {"error": str(result)},
                    "success": False,
                    "error": str(result)
                })
            else:
                processed_votes.append(result)
        
        return processed_votes
    
    def _calculate_consensus(self, agent_votes: List[Dict[str, Any]]) -> VotingResult:
        """
        Calculate consensus from agent votes using weighted voting algorithm.
        
        Args:
            agent_votes: List of agent vote results
            
        Returns:
            VotingResult with consensus decision
        """
        # Initialize counters
        votes_for_alpha = 0
        votes_against_alpha = 0
        abstentions = 0
        
        # Initialize weighted scores
        weighted_alpha_score = 0.0
        weighted_no_alpha_score = 0.0
        total_weight = 0.0
        participating_weight = 0.0  # Weight of non-abstaining agents
        
        # Collect reasoning from all agents
        reasoning_parts = []
        successful_agents = 0
        
        for vote_result in agent_votes:
            vote = vote_result["vote"]
            effective_weight = vote_result["effective_weight"]
            agent_name = vote_result["agent_name"]
            reasoning = vote_result["reasoning"]
            
            # Count votes
            if vote == "alpha":
                votes_for_alpha += 1
                weighted_alpha_score += effective_weight
                participating_weight += effective_weight
                reasoning_parts.append(f"{agent_name}: {reasoning}")
            elif vote == "no_alpha":
                votes_against_alpha += 1
                weighted_no_alpha_score += effective_weight
                participating_weight += effective_weight
                reasoning_parts.append(f"{agent_name}: {reasoning}")
            else:  # abstain
                abstentions += 1
                reasoning_parts.append(f"{agent_name} (abstained): {reasoning}")
            
            total_weight += vote_result["agent_weight"]  # Use base weight for total
            
            if vote_result["success"]:
                successful_agents += 1
        
        # Check minimum participation
        total_agents = len(agent_votes)
        participation_ratio = (total_agents - abstentions) / max(total_agents, 1)
        min_participation_met = participation_ratio >= self.min_participation_ratio
        
        # Calculate final scores
        if participating_weight > 0:
            # Normalize weighted scores by participating weight
            alpha_ratio = weighted_alpha_score / participating_weight
            no_alpha_ratio = weighted_no_alpha_score / participating_weight
        else:
            # No participation - conservative approach
            alpha_ratio = 0.0
            no_alpha_ratio = 1.0
        
        # Determine consensus
        consensus_reached = (
            min_participation_met and
            participating_weight > 0 and
            successful_agents >= max(1, len(self.agents) // 2)  # At least half succeeded
        )
        
        # Apply voting threshold
        has_alpha = consensus_reached and alpha_ratio >= self.vote_threshold
        
        # Calculate confidence score
        if consensus_reached:
            if has_alpha:
                # Confidence based on how strongly agents voted for alpha
                confidence_score = min(1.0, alpha_ratio * 1.2)  # Slight boost for decisive votes
            else:
                # Confidence in no-alpha decision
                confidence_score = min(1.0, max(no_alpha_ratio, 1.0 - alpha_ratio) * 0.8)
        else:
            confidence_score = 0.2  # Low confidence if no consensus
        
        # Conservative adjustments
        if abstentions > votes_for_alpha + votes_against_alpha:
            confidence_score *= 0.7  # Reduce confidence if too many abstentions
        
        if successful_agents < len(self.agents):
            confidence_score *= (successful_agents / len(self.agents))  # Reduce for failed agents
        
        # Build reasoning summary
        reasoning_summary = self._build_reasoning_summary(
            agent_votes, has_alpha, votes_for_alpha, votes_against_alpha, abstentions
        )
        
        logger.debug(f"Consensus calculation: alpha_ratio={alpha_ratio:.3f}, "
                    f"threshold={self.vote_threshold}, has_alpha={has_alpha}, "
                    f"confidence={confidence_score:.3f}")
        
        return VotingResult(
            has_alpha=has_alpha,
            confidence_score=round(confidence_score, 3),
            consensus_reached=consensus_reached,
            votes_for_alpha=votes_for_alpha,
            votes_against_alpha=votes_against_alpha,
            abstentions=abstentions,
            total_weight=round(total_weight, 3),
            weighted_alpha_score=round(weighted_alpha_score, 3),
            agent_results=agent_votes,
            reasoning_summary=reasoning_summary,
            voting_duration=0.0  # Will be set by caller
        )
    
    def _build_reasoning_summary(self, 
                                agent_votes: List[Dict[str, Any]], 
                                has_alpha: bool,
                                votes_for: int, 
                                votes_against: int, 
                                abstentions: int) -> str:
        """Build a human-readable reasoning summary."""
        total_agents = len(agent_votes)
        
        # Overall decision summary
        if has_alpha:
            summary = f"ALPHA DETECTED: {votes_for}/{total_agents} agents voted for alpha"
        else:
            summary = f"NO ALPHA: {votes_against}/{total_agents} voted against, {abstentions} abstained"
        
        # Add key agent reasoning
        key_reasons = []
        for vote_result in agent_votes:
            if vote_result["vote"] == "alpha" and vote_result["effective_weight"] > 0.5:
                key_reasons.append(f"• {vote_result['agent_name']}: {vote_result['reasoning']}")
        
        if key_reasons:
            summary += "\n\nKey supporting evidence:\n" + "\n".join(key_reasons[:3])  # Top 3
        
        # Add failure warnings if any
        failed_agents = [v["agent_name"] for v in agent_votes if not v["success"]]
        if failed_agents:
            summary += f"\n\nNote: {len(failed_agents)} agents failed analysis: {', '.join(failed_agents)}"
        
        return summary
    
    def get_voting_summary(self) -> Dict[str, Any]:
        """Get summary information about the voting system configuration."""
        return {
            "registered_agents": [
                {
                    "name": name,
                    "weight": agent.weight,
                    "type": type(agent).__name__
                }
                for name, agent in self.agents.items()
            ],
            "total_agents": len(self.agents),
            "vote_threshold": self.vote_threshold,
            "min_participation_ratio": self.min_participation_ratio,
            "total_weight": sum(agent.weight for agent in self.agents.values())
        }
    
    def update_agent_weights(self, performance_data: Dict[str, float]) -> None:
        """
        Update agent weights based on historical performance.
        
        Args:
            performance_data: Dict mapping agent names to accuracy scores (0.0 to 1.0)
        """
        for agent_name, accuracy in performance_data.items():
            if agent_name in self.agents:
                self.agents[agent_name].update_weight(accuracy)
                logger.info(f"Updated weight for {agent_name}: {self.agents[agent_name].weight}")
    
    def reset_agent_weights(self) -> None:
        """Reset all agent weights to 1.0."""
        for agent in self.agents.values():
            agent.weight = 1.0
        logger.info("Reset all agent weights to 1.0")