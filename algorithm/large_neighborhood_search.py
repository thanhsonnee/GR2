"""
Large Neighborhood Search (LNS) for PDPTW
Destroy-Repair based metaheuristic with adaptive operator selection
"""

import random
import math
import time
from typing import List, Tuple, Set
from data_loader import Instance, Solution
from solution_encoder import SolutionEncoder
from construction_heuristic import GreedyInsertion


class LargeNeighborhoodSearch:
    """Large Neighborhood Search metaheuristic for PDPTW"""
    
    def __init__(self, instance: Instance,
                 max_iterations: int = 1000,
                 max_time: int = 300,
                 min_destroy_size: int = 5,
                 max_destroy_size: int = 20,
                 adaptive: bool = True):
        self.instance = instance
        self.max_iterations = max_iterations
        self.max_time = max_time
        self.min_destroy_size = min_destroy_size
        self.max_destroy_size = max_destroy_size
        self.adaptive = adaptive
        
        # Initialize with greedy solution
        greedy = GreedyInsertion(instance)
        routes = greedy.solve()
        self.current_solution = SolutionEncoder.create_solution_from_routes(routes, instance.name, "Initial")
        self.best_solution = self._copy_solution(self.current_solution)
        
        # Adaptive operator selection
        self.destroy_operators = [
            ('random', self._random_removal),
            ('worst', self._worst_removal),
            ('related', self._related_removal),
            ('route', self._route_removal),
            ('pair', self._pair_removal)
        ]
        
        self.repair_operators = [
            ('greedy', self._greedy_insertion),
            ('regret', self._regret_insertion),
            ('best_position', self._best_position_insertion)
        ]
        
        # Operator scores and usage counts
        self.destroy_scores = {op[0]: 1.0 for op in self.destroy_operators}
        self.destroy_counts = {op[0]: 0 for op in self.destroy_operators}
        self.repair_scores = {op[0]: 1.0 for op in self.repair_operators}
        self.repair_counts = {op[0]: 0 for op in self.repair_operators}
        
        # Statistics
        self.iterations = 0
        self.improvements = 0
        self.accepted_worse = 0
        
    def solve(self) -> Solution:
        """Run Large Neighborhood Search algorithm"""
        print(f"Starting Large Neighborhood Search...")
        print(f"Initial solution: {self.current_solution.get_num_vehicles()} vehicles, "
              f"cost = {self.current_solution.get_cost(self.instance)}")
        
        start_time = time.time()
        
        while (self.iterations < self.max_iterations and
               time.time() - start_time < self.max_time):
            
            # Select destroy and repair operators
            destroy_op = self._select_destroy_operator()
            repair_op = self._select_repair_operator()
            
            # Determine destroy size
            destroy_size = random.randint(self.min_destroy_size, self.max_destroy_size)
            
            # Create neighbor solution
            neighbor = self._create_neighbor(destroy_op, repair_op, destroy_size)
            
            if neighbor is None:
                continue
                
            # Evaluate neighbor
            current_cost = self.current_solution.get_cost(self.instance)
            neighbor_cost = neighbor.get_cost(self.instance)
            
            # Acceptance criterion (simplified: only accept improvements)
            if neighbor_cost < current_cost:
                self.current_solution = neighbor
                self.improvements += 1
                
                # Update best solution
                if neighbor_cost < self.best_solution.get_cost(self.instance):
                    self.best_solution = self._copy_solution(neighbor)
                    print(f"Iteration {self.iterations}: New best! "
                          f"{self.best_solution.get_num_vehicles()} vehicles, "
                          f"cost = {neighbor_cost}")
                
                # Update operator scores
                if self.adaptive:
                    self._update_operator_scores(destroy_op, repair_op, True)
            else:
                # Update operator scores for non-improving moves
                if self.adaptive:
                    self._update_operator_scores(destroy_op, repair_op, False)
            
            self.iterations += 1
            
            # Progress update
            if self.iterations % 100 == 0:
                elapsed = time.time() - start_time
                print(f"Iteration {self.iterations}: "
                      f"Current cost={current_cost}, "
                      f"Best cost={self.best_solution.get_cost(self.instance)}, "
                      f"Time={elapsed:.1f}s")
        
        elapsed = time.time() - start_time
        print(f"\nLarge Neighborhood Search completed:")
        print(f"Iterations: {self.iterations}")
        print(f"Improvements: {self.improvements}")
        print(f"Time: {elapsed:.2f}s")
        print(f"Best solution: {self.best_solution.get_num_vehicles()} vehicles, "
              f"cost = {self.best_solution.get_cost(self.instance)}")
        
        return self.best_solution
    
    def _select_destroy_operator(self) -> str:
        """Select destroy operator using adaptive selection"""
        if not self.adaptive:
            return random.choice(self.destroy_operators)[0]
        
        # Roulette wheel selection based on scores
        total_score = sum(self.destroy_scores.values())
        if total_score == 0:
            return random.choice(self.destroy_operators)[0]
        
        r = random.uniform(0, total_score)
        cumulative = 0
        
        for op_name, score in self.destroy_scores.items():
            cumulative += score
            if r <= cumulative:
                return op_name
        
        return random.choice(self.destroy_operators)[0]
    
    def _select_repair_operator(self) -> str:
        """Select repair operator using adaptive selection"""
        if not self.adaptive:
            return random.choice(self.repair_operators)[0]
        
        # Roulette wheel selection based on scores
        total_score = sum(self.repair_scores.values())
        if total_score == 0:
            return random.choice(self.repair_operators)[0]
        
        r = random.uniform(0, total_score)
        cumulative = 0
        
        for op_name, score in self.repair_scores.items():
            cumulative += score
            if r <= cumulative:
                return op_name
        
        return random.choice(self.repair_operators)[0]
    
    def _create_neighbor(self, destroy_op: str, repair_op: str, destroy_size: int) -> Solution:
        """Create neighbor solution using destroy-repair"""
        try:
            # Create copy of current solution
            neighbor = self._copy_solution(self.current_solution)
            
            # Find destroy operator function
            destroy_func = None
            for op_name, op_func in self.destroy_operators:
                if op_name == destroy_op:
                    destroy_func = op_func
                    break
            
            # Find repair operator function
            repair_func = None
            for op_name, op_func in self.repair_operators:
                if op_name == repair_op:
                    repair_func = op_func
                    break
            
            if destroy_func is None or repair_func is None:
                return None
            
            # Destroy phase
            removed_nodes = destroy_func(neighbor, destroy_size)
            
            if not removed_nodes:
                return None
            
            # Repair phase
            success = repair_func(neighbor, removed_nodes)
            
            if not success:
                return None
            
            return neighbor
            
        except Exception as e:
            print(f"Error in _create_neighbor: {e}")
            return None
    
    def _random_removal(self, solution: Solution, k: int) -> List[int]:
        """Random removal: remove k random nodes"""
        all_nodes = []
        for route in solution.routes:
            all_nodes.extend(route)
        
        if len(all_nodes) < k:
            k = len(all_nodes)
        
        removed = random.sample(all_nodes, k)
        self._remove_nodes_from_solution(solution, removed)
        return removed
    
    def _worst_removal(self, solution: Solution, k: int) -> List[int]:
        """Worst removal: remove k nodes with highest cost"""
        # Calculate cost for each node position
        node_costs = []
        
        for route_idx, route in enumerate(solution.routes):
            for pos, node in enumerate(route):
                # Simple cost estimation: distance to next node
                if pos < len(route) - 1:
                    next_node = route[pos + 1]
                    cost = self.instance.distance_matrix[node][next_node]
                else:
                    cost = self.instance.distance_matrix[node][0]  # back to depot
                
                node_costs.append((node, cost, route_idx, pos))
        
        # Sort by cost (descending) and select top k
        node_costs.sort(key=lambda x: x[1], reverse=True)
        
        removed = []
        for i in range(min(k, len(node_costs))):
            removed.append(node_costs[i][0])
        
        self._remove_nodes_from_solution(solution, removed)
        return removed
    
    def _related_removal(self, solution: Solution, k: int) -> List[int]:
        """Related removal: remove k nodes that are geographically close"""
        if not solution.routes:
            return []
        
        # Start with a random node
        all_nodes = []
        for route in solution.routes:
            all_nodes.extend(route)
        
        if not all_nodes:
            return []
        
        start_node = random.choice(all_nodes)
        removed = [start_node]
        
        # Remove remaining nodes based on distance to already removed nodes
        remaining_nodes = [n for n in all_nodes if n not in removed]
        
        while len(removed) < k and remaining_nodes:
            min_distance = float('inf')
            best_node = None
            
            for node in remaining_nodes:
                # Calculate minimum distance to any removed node
                min_dist_to_removed = min(
                    self.instance.distance_matrix[node][removed_node]
                    for removed_node in removed
                )
                
                if min_dist_to_removed < min_distance:
                    min_distance = min_dist_to_removed
                    best_node = node
            
            if best_node is not None:
                removed.append(best_node)
                remaining_nodes.remove(best_node)
            else:
                break
        
        self._remove_nodes_from_solution(solution, removed)
        return removed
    
    def _route_removal(self, solution: Solution, k: int) -> List[int]:
        """Route removal: remove entire routes"""
        if not solution.routes:
            return []
        
        # Select random routes to remove
        num_routes_to_remove = min(k // 5 + 1, len(solution.routes))  # Remove 1-2 routes
        routes_to_remove = random.sample(range(len(solution.routes)), num_routes_to_remove)
        
        removed = []
        # Remove routes in reverse order to maintain indices
        for route_idx in sorted(routes_to_remove, reverse=True):
            removed.extend(solution.routes[route_idx])
            solution.routes.pop(route_idx)
        
        return removed
    
    def _pair_removal(self, solution: Solution, k: int) -> List[int]:
        """Pair removal: remove pickup-delivery pairs"""
        # Find all pickup-delivery pairs
        pairs = []
        for route in solution.routes:
            for node in route:
                if node > 0:  # Not depot
                    # Find pair (simplified: assume pair is node + size//2)
                    pair_node = node + self.instance.size // 2
                    if pair_node <= self.instance.size:
                        pairs.append((node, pair_node))
        
        # Remove random pairs
        num_pairs_to_remove = min(k // 2, len(pairs))
        pairs_to_remove = random.sample(pairs, num_pairs_to_remove)
        
        removed = []
        for pickup, delivery in pairs_to_remove:
            removed.extend([pickup, delivery])
        
        self._remove_nodes_from_solution(solution, removed)
        return removed
    
    def _greedy_insertion(self, solution: Solution, removed_nodes: List[int]) -> bool:
        """Greedy insertion: insert nodes at best position"""
        for node in removed_nodes:
            best_cost = float('inf')
            best_route_idx = -1
            best_position = -1
            
            # Try inserting in existing routes
            for route_idx, route in enumerate(solution.routes):
                for pos in range(len(route) + 1):
                    # Calculate insertion cost
                    cost = self._calculate_insertion_cost(solution, node, route_idx, pos)
                    if cost < best_cost:
                        best_cost = cost
                        best_route_idx = route_idx
                        best_position = pos
            
            # Try creating new route
            new_route_cost = self._calculate_new_route_cost(node)
            if new_route_cost < best_cost:
                solution.routes.append([node])
            else:
                solution.routes[best_route_idx].insert(best_position, node)
        
        return True
    
    def _regret_insertion(self, solution: Solution, removed_nodes: List[int]) -> bool:
        """Regret insertion: prioritize nodes with high regret"""
        # Calculate regret for each node
        node_regrets = []
        
        for node in removed_nodes:
            costs = []
            
            # Calculate cost for each possible insertion
            for route_idx, route in enumerate(solution.routes):
                for pos in range(len(route) + 1):
                    cost = self._calculate_insertion_cost(solution, node, route_idx, pos)
                    costs.append(cost)
            
            # Add cost for new route
            costs.append(self._calculate_new_route_cost(node))
            
            # Calculate regret (difference between best and second best)
            costs.sort()
            regret = costs[1] - costs[0] if len(costs) > 1 else costs[0]
            node_regrets.append((node, regret))
        
        # Sort by regret (descending)
        node_regrets.sort(key=lambda x: x[1], reverse=True)
        
        # Insert nodes in regret order
        for node, _ in node_regrets:
            best_cost = float('inf')
            best_route_idx = -1
            best_position = -1
            
            for route_idx, route in enumerate(solution.routes):
                for pos in range(len(route) + 1):
                    cost = self._calculate_insertion_cost(solution, node, route_idx, pos)
                    if cost < best_cost:
                        best_cost = cost
                        best_route_idx = route_idx
                        best_position = pos
            
            new_route_cost = self._calculate_new_route_cost(node)
            if new_route_cost < best_cost:
                solution.routes.append([node])
            else:
                solution.routes[best_route_idx].insert(best_position, node)
        
        return True
    
    def _best_position_insertion(self, solution: Solution, removed_nodes: List[int]) -> bool:
        """Best position insertion: find globally best position for each node"""
        # This is similar to greedy but with more sophisticated cost calculation
        return self._greedy_insertion(solution, removed_nodes)
    
    def _remove_nodes_from_solution(self, solution: Solution, nodes: List[int]):
        """Remove nodes from solution routes"""
        for node in nodes:
            for route in solution.routes:
                if node in route:
                    route.remove(node)
                    break
        
        # Remove empty routes
        solution.routes = [route for route in solution.routes if route]
    
    def _calculate_insertion_cost(self, solution: Solution, node: int, route_idx: int, position: int) -> float:
        """Calculate cost of inserting node at given position"""
        if route_idx >= len(solution.routes):
            return float('inf')
        
        route = solution.routes[route_idx]
        
        if position == 0:
            # Insert at beginning
            if route:
                return self.instance.distance_matrix[0][node] + self.instance.distance_matrix[node][route[0]]
            else:
                return self.instance.distance_matrix[0][node] * 2
        elif position == len(route):
            # Insert at end
            return self.instance.distance_matrix[route[-1]][node] + self.instance.distance_matrix[node][0]
        else:
            # Insert in middle
            prev_node = route[position - 1]
            next_node = route[position]
            return (self.instance.distance_matrix[prev_node][node] + 
                   self.instance.distance_matrix[node][next_node] - 
                   self.instance.distance_matrix[prev_node][next_node])
    
    def _calculate_new_route_cost(self, node: int) -> float:
        """Calculate cost of creating new route with single node"""
        return self.instance.distance_matrix[0][node] * 2
    
    def _copy_solution(self, solution: Solution) -> Solution:
        """Create a deep copy of solution"""
        copy_sol = Solution()
        copy_sol.inst_name = solution.inst_name
        copy_sol.authors = solution.authors
        copy_sol.date = solution.date
        copy_sol.reference = solution.reference
        copy_sol.routes = [route[:] for route in solution.routes]
        return copy_sol
    
    def _update_operator_scores(self, destroy_op: str, repair_op: str, improved: bool):
        """Update operator scores based on performance"""
        if improved:
            self.destroy_scores[destroy_op] += 1.0
            self.repair_scores[repair_op] += 1.0
        else:
            self.destroy_scores[destroy_op] *= 0.9
            self.repair_scores[repair_op] *= 0.9
        
        self.destroy_counts[destroy_op] += 1
        self.repair_counts[repair_op] += 1
