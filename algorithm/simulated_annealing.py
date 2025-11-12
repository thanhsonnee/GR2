"""
Simulated Annealing for PDPTW
Simple and effective metaheuristic implementation
"""

import random
import math
import time
from typing import List, Tuple
from data_loader import Instance, Solution
from solution_encoder import SolutionEncoder
from construction_heuristic import GreedyInsertion
from local_search import LocalSearch


class SimulatedAnnealing:
    """Simulated Annealing metaheuristic for PDPTW"""
    
    def __init__(self, instance: Instance, 
                 initial_temp: float = 1000.0,
                 final_temp: float = 0.1,
                 cooling_rate: float = 0.95,
                 max_iterations: int = 10000,
                 max_time: int = 300):
        self.instance = instance
        self.initial_temp = initial_temp
        self.final_temp = final_temp
        self.cooling_rate = cooling_rate
        self.max_iterations = max_iterations
        self.max_time = max_time
        
        # Initialize with greedy solution
        greedy = GreedyInsertion(instance)
        routes = greedy.solve()
        self.current_solution = SolutionEncoder.create_solution_from_routes(routes, instance.name, "Initial")
        
        # Create a copy for best solution
        self.best_solution = Solution()
        self.best_solution.inst_name = self.current_solution.inst_name
        self.best_solution.authors = self.current_solution.authors
        self.best_solution.date = self.current_solution.date
        self.best_solution.reference = self.current_solution.reference
        self.best_solution.routes = [route[:] for route in self.current_solution.routes]
        
        # Statistics
        self.iterations = 0
        self.accepted_moves = 0
        self.improved_moves = 0
        
    def solve(self) -> Solution:
        """Run Simulated Annealing algorithm"""
        print(f"Starting Simulated Annealing...")
        print(f"Initial solution: {self.current_solution.get_num_vehicles()} vehicles, "
              f"cost = {self.current_solution.get_cost(self.instance)}")
        
        start_time = time.time()
        temperature = self.initial_temp
        
        while (temperature > self.final_temp and 
               self.iterations < self.max_iterations and
               time.time() - start_time < self.max_time):
            
            # Generate neighbor solution
            neighbor = self._generate_neighbor()
            
            if neighbor is None:
                continue
                
            # Calculate cost difference
            current_cost = self.current_solution.get_cost(self.instance)
            neighbor_cost = neighbor.get_cost(self.instance)
            delta_cost = neighbor_cost - current_cost
            
            # Acceptance decision
            if delta_cost <= 0 or random.random() < math.exp(-delta_cost / temperature):
                self.current_solution = neighbor
                self.accepted_moves += 1
                
                if delta_cost < 0:
                    self.improved_moves += 1
                    
                # Update best solution
                if neighbor_cost < self.best_solution.get_cost(self.instance):
                    self.best_solution.inst_name = neighbor.inst_name
                    self.best_solution.authors = neighbor.authors
                    self.best_solution.date = neighbor.date
                    self.best_solution.reference = neighbor.reference
                    self.best_solution.routes = [route[:] for route in neighbor.routes]
                    print(f"Iteration {self.iterations}: New best! "
                          f"{self.best_solution.get_num_vehicles()} vehicles, "
                          f"cost = {neighbor_cost}")
            
            # Cool down
            temperature *= self.cooling_rate
            self.iterations += 1
            
            # Progress update
            if self.iterations % 1000 == 0:
                elapsed = time.time() - start_time
                print(f"Iteration {self.iterations}: T={temperature:.2f}, "
                      f"Current cost={current_cost}, "
                      f"Best cost={self.best_solution.get_cost(self.instance)}, "
                      f"Time={elapsed:.1f}s")
        
        elapsed = time.time() - start_time
        print(f"\nSimulated Annealing completed:")
        print(f"Iterations: {self.iterations}")
        print(f"Accepted moves: {self.accepted_moves}")
        print(f"Improved moves: {self.improved_moves}")
        print(f"Final temperature: {temperature:.4f}")
        print(f"Time: {elapsed:.2f}s")
        print(f"Best solution: {self.best_solution.get_num_vehicles()} vehicles, "
              f"cost = {self.best_solution.get_cost(self.instance)}")
        
        return self.best_solution
    
    def _generate_neighbor(self) -> Solution:
        """Generate a neighbor solution using random moves"""
        # Create a copy of current solution
        neighbor = Solution()
        neighbor.inst_name = self.current_solution.inst_name
        neighbor.authors = self.current_solution.authors
        neighbor.date = self.current_solution.date
        neighbor.reference = self.current_solution.reference
        neighbor.routes = [route[:] for route in self.current_solution.routes]
        
        # Randomly choose move type
        move_type = random.choice(['swap', 'relocate', '2opt'])
        
        try:
            if move_type == 'swap':
                self._swap_move(neighbor)
            elif move_type == 'relocate':
                self._relocate_move(neighbor)
            elif move_type == '2opt':
                self._two_opt_move(neighbor)
                
            return neighbor
        except:
            return None
    
    def _swap_move(self, solution: Solution):
        """Swap two nodes between routes"""
        if len(solution.routes) < 2:
            return
            
        # Choose two different routes
        route1_idx, route2_idx = random.sample(range(len(solution.routes)), 2)
        route1 = solution.routes[route1_idx]
        route2 = solution.routes[route2_idx]
        
        if len(route1) < 2 or len(route2) < 2:
            return
            
        # Choose positions to swap
        pos1 = random.randint(0, len(route1) - 1)
        pos2 = random.randint(0, len(route2) - 1)
        
        # Perform swap
        route1[pos1], route2[pos2] = route2[pos2], route1[pos1]
    
    def _relocate_move(self, solution: Solution):
        """Move a node from one route to another"""
        if len(solution.routes) < 2:
            return
            
        # Choose source route
        source_idx = random.randint(0, len(solution.routes) - 1)
        source_route = solution.routes[source_idx]
        
        if len(source_route) < 2:
            return
            
        # Choose node to move
        node_idx = random.randint(0, len(source_route) - 1)
        node = source_route[node_idx]
        
        # Remove from source
        source_route.pop(node_idx)
        
        # Choose destination route and position
        dest_idx = random.randint(0, len(solution.routes) - 1)
        dest_route = solution.routes[dest_idx]
        dest_pos = random.randint(0, len(dest_route))
        
        # Insert at destination
        dest_route.insert(dest_pos, node)
    
    def _two_opt_move(self, solution: Solution):
        """Apply 2-opt move within a route"""
        if not solution.routes:
            return
            
        # Choose a route
        route_idx = random.randint(0, len(solution.routes) - 1)
        route = solution.routes[route_idx]
        
        if len(route) < 4:
            return
            
        # Choose two positions
        i, j = random.sample(range(len(route)), 2)
        if i > j:
            i, j = j, i
            
        # Reverse segment between i and j
        route[i:j+1] = route[i:j+1][::-1]
