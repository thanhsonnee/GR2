"""
Late Acceptance Hill Climbing (LAHC) acceptance criterion
Non-parametric acceptance mechanism for metaheuristics
"""

from typing import Tuple
from data_loader import Instance, Solution


class LAHCAcceptance:
    """
    Late Acceptance Hill Climbing acceptance criterion
    
    Accepts a solution if it's better than the solution from L iterations ago.
    No temperature parameter needed (unlike Simulated Annealing).
    """
    
    def __init__(self, history_length: int = 1000):
        """
        Initialize LAHC acceptance
        
        Args:
            history_length: Number of past costs to remember (L parameter)
        """
        self.history_length = history_length
        self.cost_history = []
        self.history_index = 0
        self.initialized = False
        
        # Statistics
        self.total_evaluations = 0
        self.accepted_better = 0
        self.accepted_worse = 0
        self.rejected = 0
    
    def initialize(self, initial_solution: Solution, instance: Instance):
        """Initialize the cost history with the initial solution"""
        initial_vehicles = initial_solution.get_num_vehicles()
        initial_cost = initial_solution.get_cost(instance)
        initial_score = (initial_vehicles, initial_cost)
        
        # Fill history with initial cost
        self.cost_history = [initial_score] * self.history_length
        self.history_index = 0
        self.initialized = True
    
    def should_accept(self, candidate_solution: Solution, current_solution: Solution, 
                     instance: Instance) -> Tuple[bool, str]:
        """
        Determine if candidate solution should be accepted
        
        IMPORTANT: This assumes the candidate has already passed feasibility check!
        This method only decides acceptance among feasible solutions.
        
        Args:
            candidate_solution: New solution to evaluate
            current_solution: Current solution
            instance: Problem instance
            
        Returns:
            (should_accept, reason) where reason is a string explaining the decision
        """
        if not self.initialized:
            raise RuntimeError("LAHC not initialized. Call initialize() first.")
        
        self.total_evaluations += 1
        
        # Calculate scores (lexicographic: vehicles first, then cost)
        candidate_vehicles = candidate_solution.get_num_vehicles()
        candidate_cost = candidate_solution.get_cost(instance)
        candidate_score = (candidate_vehicles, candidate_cost)
        
        current_vehicles = current_solution.get_num_vehicles()
        current_cost = current_solution.get_cost(instance)
        current_score = (current_vehicles, current_cost)
        
        # Get comparison score from history
        comparison_score = self.cost_history[self.history_index]
        
        # Decide acceptance
        accept = False
        reason = ""
        
        if candidate_score < current_score:
            # Better than current - always accept
            accept = True
            reason = "better_than_current"
            self.accepted_better += 1
        elif candidate_score <= comparison_score:
            # Worse than current, but better than L-iterations-ago - accept
            accept = True
            reason = "better_than_history"
            self.accepted_worse += 1
        else:
            # Worse than both current and history - reject
            accept = False
            reason = "worse_than_history"
            self.rejected += 1
        
        # Update history (circular buffer) - update with CURRENT cost, not candidate
        # This is the key LAHC mechanism: we compare against past, but store current
        self.cost_history[self.history_index] = current_score
        self.history_index = (self.history_index + 1) % self.history_length
        
        return accept, reason
    
    def get_statistics(self) -> dict:
        """Get acceptance statistics"""
        total = self.total_evaluations
        if total == 0:
            return {
                'total_evaluations': 0,
                'accepted_better': 0,
                'accepted_worse': 0,
                'rejected': 0,
                'acceptance_rate': 0.0
            }
        
        return {
            'total_evaluations': total,
            'accepted_better': self.accepted_better,
            'accepted_worse': self.accepted_worse,
            'rejected': self.rejected,
            'acceptance_rate': (self.accepted_better + self.accepted_worse) / total * 100,
            'better_rate': self.accepted_better / total * 100,
            'worse_rate': self.accepted_worse / total * 100,
            'rejection_rate': self.rejected / total * 100
        }
    
    def reset_statistics(self):
        """Reset acceptance statistics (keep history)"""
        self.total_evaluations = 0
        self.accepted_better = 0
        self.accepted_worse = 0
        self.rejected = 0
