"""
Simulated Annealing Acceptance Criterion - Vehicles-First
==========================================================
Based on Ropke & Pisinger, adapted for lexicographic (vehicles, distance)
"""

import math
import random
from typing import Tuple
from data_loader import Instance, Solution


class SimulatedAnnealingVehiclesFirst:
    """
    Simulated Annealing with vehicles-first lexicographic ordering
    
    Key features:
    - If vehicles decrease → always accept
    - If vehicles increase → reject (or tiny probability)
    - If vehicles same → SA on distance with temperature
    - Temperature decreases linearly over time
    """
    
    def __init__(self, initial_solution: Solution, instance: Instance,
                 time_limit: float = 300.0, t0_factor: float = 0.01):
        """
        Args:
            initial_solution: Starting solution for calibration
            instance: Problem instance
            time_limit: Total time budget for cooling schedule
            t0_factor: Initial temperature as fraction of initial distance
        """
        self.instance = instance
        self.time_limit = time_limit
        
        # Calibrate initial temperature based on initial solution
        initial_distance = initial_solution.get_cost(instance)
        self.T0 = t0_factor * initial_distance
        self.Tmin = 1e-4
        
        # Track time for cooling schedule
        import time
        self.start_time = time.time()
        
        # Statistics
        self.total_evaluations = 0
        self.accepted_better = 0
        self.accepted_worse = 0
        self.rejected = 0
        
    def should_accept(self, candidate_solution: Solution, 
                     current_solution: Solution, 
                     instance: Instance) -> Tuple[bool, str]:
        """
        Determine if candidate should be accepted using SA vehicles-first
        
        IMPORTANT: Assumes candidate has passed feasibility check!
        
        Args:
            candidate_solution: New solution to evaluate
            current_solution: Current solution
            instance: Problem instance
            
        Returns:
            (should_accept, reason)
        """
        self.total_evaluations += 1
        
        # Get scores (lexicographic: vehicles first, then distance)
        v_candidate = candidate_solution.get_num_vehicles()
        d_candidate = candidate_solution.get_cost(instance)
        
        v_current = current_solution.get_num_vehicles()
        d_current = current_solution.get_cost(instance)
        
        # Update temperature
        T = self._get_temperature()
        
        # VEHICLES-FIRST LOGIC
        
        # 1. If vehicles decrease → ALWAYS ACCEPT
        if v_candidate < v_current:
            self.accepted_better += 1
            return True, "vehicles_decreased"
        
        # 2. If vehicles increase → REJECT (or very tiny probability)
        if v_candidate > v_current:
            # Optional: allow tiny probability to escape (usually not needed)
            if random.random() < 1e-6:
                self.accepted_worse += 1
                return True, "vehicles_increased_lucky"
            else:
                self.rejected += 1
                return False, "vehicles_increased"
        
        # 3. Same vehicles → SA on distance
        delta_distance = d_candidate - d_current
        
        # If distance improves → accept
        if delta_distance <= 0:
            self.accepted_better += 1
            return True, "distance_improved"
        
        # If distance worsens → accept with probability exp(-delta/T)
        acceptance_prob = math.exp(-delta_distance / max(T, 1e-10))
        
        if random.random() < acceptance_prob:
            self.accepted_worse += 1
            return True, f"sa_accepted_T={T:.2f}"
        else:
            self.rejected += 1
            return False, f"sa_rejected_T={T:.2f}"
    
    def _get_temperature(self) -> float:
        """
        Calculate current temperature using linear cooling schedule
        
        T = T0 * (Tmin / T0) ^ (elapsed / time_limit)
        """
        import time
        elapsed = time.time() - self.start_time
        
        if elapsed >= self.time_limit:
            return self.Tmin
        
        # Linear interpolation in log space
        progress = elapsed / self.time_limit
        T = self.T0 * (self.Tmin / self.T0) ** progress
        
        return max(T, self.Tmin)
    
    def get_statistics(self) -> dict:
        """Get acceptance statistics"""
        total = self.total_evaluations
        if total == 0:
            return {
                'total_evaluations': 0,
                'accepted_better': 0,
                'accepted_worse': 0,
                'rejected': 0,
                'acceptance_rate': 0.0,
                'current_temperature': self.Tmin
            }
        
        return {
            'total_evaluations': total,
            'accepted_better': self.accepted_better,
            'accepted_worse': self.accepted_worse,
            'rejected': self.rejected,
            'acceptance_rate': (self.accepted_better + self.accepted_worse) / total * 100,
            'better_rate': self.accepted_better / total * 100,
            'worse_rate': self.accepted_worse / total * 100,
            'rejection_rate': self.rejected / total * 100,
            'current_temperature': self._get_temperature()
        }
    
    def reset_statistics(self):
        """Reset statistics (keep temperature schedule)"""
        self.total_evaluations = 0
        self.accepted_better = 0
        self.accepted_worse = 0
        self.rejected = 0


if __name__ == "__main__":
    # Quick test
    from data_loader import Instance, Solution
    
    instance = Instance()
    instance.read_from_file("../instances/pdp_100/lc101.txt")
    
    # Create dummy solution
    solution = Solution()
    solution.routes = [[1, 2, 3], [4, 5, 6]]
    
    sa = SimulatedAnnealingVehiclesFirst(solution, instance, time_limit=60.0)
    
    print("SA Vehicles-First initialized")
    print(f"T0 = {sa.T0:.2f}")
    print(f"Tmin = {sa.Tmin}")
    print(f"Time limit = {sa.time_limit}s")
    print("\nReady to use!")
