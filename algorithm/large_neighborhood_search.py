"""
Large Neighborhood Search (LNS) for PDPTW
Destroy-Repair based metaheuristic with LAHC acceptance and strict feasibility
"""

import random
import math
import time
from typing import List, Tuple, Set, Optional
from data_loader import Instance, Solution
from solution_encoder import SolutionEncoder
from construction_heuristic import GreedyInsertion
from feasibility_validator import validate_solution
from lahc_acceptance import LAHCAcceptance
from route_improvement import RouteImprovement


class LargeNeighborhoodSearch:
    """Large Neighborhood Search metaheuristic for PDPTW with strict feasibility"""
    
    def __init__(self, instance: Instance,
                 max_iterations: int = 1000,
                 max_time: int = 300,
                 min_destroy_size: int = 10,
                 max_destroy_size: int = 60,
                 lahc_history: int = 1000):
        self.instance = instance
        self.max_iterations = max_iterations
        self.max_time = max_time
        self.min_destroy_size = min_destroy_size
        self.max_destroy_size = max_destroy_size
        
        # Initialize with greedy solution
        greedy = GreedyInsertion(instance)
        routes = greedy.solve()
        self.current_solution = SolutionEncoder.create_solution_from_routes(routes, instance.name, "Initial")
        self.best_solution = self._copy_solution(self.current_solution)
        
        # ENHANCED operator set with Worst Removal
        self.destroy_operators = [
            ('random', self._random_pair_removal),
            ('shaw', self._shaw_removal),
            ('worst', self._worst_removal)  # NEW!
        ]
        
        self.repair_operators = [
            ('greedy', self._greedy_pair_insertion),
            ('regret_k', self._regret_k_insertion)  # Variable k (2-5)
        ]
        
        # LAHC acceptance (instead of simple improvement)
        self.lahc = LAHCAcceptance(history_length=lahc_history)
        
        # Route improvement (local search)
        self.route_improver = RouteImprovement(instance)
        
        # Statistics
        self.iterations = 0
        self.improvements = 0
        self.accepted_worse = 0
        self.rejected_infeasible = 0
        self.rejected_by_lahc = 0
        self.repair_failures = 0
        
    def solve(self) -> Solution:
        """
        Run Large Neighborhood Search with strict feasibility and LAHC acceptance
        
        CRITICAL GUARDRAILS:
        - Validator is the single source of truth
        - LAHC is applied ONLY after feasibility passes
        - Never accept infeasible solutions, even temporarily
        """
        print(f"Starting LNS with strict feasibility...")
        print(f"Initial solution: {self.current_solution.get_num_vehicles()} vehicles, "
              f"cost = {self.current_solution.get_cost(self.instance)}")
        
        # Validate initial solution
        is_feasible, violations = validate_solution(self.current_solution, self.instance)
        if not is_feasible:
            print(f"WARNING: Initial solution is INFEASIBLE!")
            print(f"Violations: {violations}")
            print(f"Will try to find feasible solution during search...")
        
        # Initialize LAHC with initial solution
        self.lahc.initialize(self.current_solution, self.instance)
        
        start_time = time.time()
        last_progress_time = start_time
        
        while (self.iterations < self.max_iterations and
               time.time() - start_time < self.max_time):
            
            self.iterations += 1
            
            # Select destroy and repair operators (round-robin for simplicity)
            destroy_idx = (self.iterations - 1) % len(self.destroy_operators)
            repair_idx = (self.iterations - 1) % len(self.repair_operators)
            
            destroy_op = self.destroy_operators[destroy_idx][0]
            repair_op = self.repair_operators[repair_idx][0]
            
            # Determine destroy size (number of PAIRS to remove)
            destroy_size = random.randint(self.min_destroy_size, self.max_destroy_size)
            
            # Create neighbor solution
            neighbor = self._create_neighbor(destroy_op, repair_op, destroy_size)
            
            if neighbor is None:
                self.repair_failures += 1
                continue
            
            # Apply route improvement every 20 iterations (to save time)
            if self.iterations % 20 == 0:
                neighbor = self.route_improver.improve_solution(neighbor, max_time=2.0)
            
            # === GATE 1: FEASIBILITY CHECK (MANDATORY) ===
            is_feasible, violations = validate_solution(neighbor, self.instance)
            
            if not is_feasible:
                self.rejected_infeasible += 1
                # Log violations periodically
                if self.iterations % 100 == 0:
                    print(f"  [Infeasible at iter {self.iterations}] Example: {violations[0] if violations else 'unknown'}")
                continue  # REJECT immediately, no further consideration
            
            # === GATE 2: LAHC ACCEPTANCE (only for feasible solutions) ===
            should_accept, reason = self.lahc.should_accept(
                neighbor, self.current_solution, self.instance
            )
            
            if should_accept:
                # Accept neighbor as new current solution
                self.current_solution = self._copy_solution(neighbor)
                
                if reason == "better_than_current":
                    self.improvements += 1
                elif reason == "better_than_history":
                    self.accepted_worse += 1
                
                # Update global best if better
                if self._is_better_solution(neighbor, self.best_solution):
                    self.best_solution = self._copy_solution(neighbor)
                    print(f"[{self.iterations}] NEW BEST: {self.best_solution.get_num_vehicles()} veh, "
                          f"cost {self.best_solution.get_cost(self.instance)}")
            else:
                self.rejected_by_lahc += 1
            
            # Progress update every 10 seconds
            current_time = time.time()
            if current_time - last_progress_time >= 10:
                elapsed = current_time - start_time
                print(f"[{self.iterations}] Current: {self.current_solution.get_num_vehicles()} veh, "
                      f"cost {self.current_solution.get_cost(self.instance)} | "
                      f"Best: {self.best_solution.get_num_vehicles()} veh, "
                      f"cost {self.best_solution.get_cost(self.instance)} | "
                      f"Time: {elapsed:.1f}s")
                last_progress_time = current_time
        
        elapsed = time.time() - start_time
        
        # Final validation
        is_final_feasible, final_violations = validate_solution(self.best_solution, self.instance)
        
        print(f"\n{'='*70}")
        print(f"LNS COMPLETED")
        print(f"{'='*70}")
        print(f"Iterations: {self.iterations}")
        print(f"Improvements: {self.improvements}")
        print(f"Accepted worse: {self.accepted_worse}")
        print(f"Rejected (infeasible): {self.rejected_infeasible}")
        print(f"Rejected (LAHC): {self.rejected_by_lahc}")
        print(f"Repair failures: {self.repair_failures}")
        print(f"Time: {elapsed:.2f}s")
        print(f"Best solution: {self.best_solution.get_num_vehicles()} vehicles, "
              f"cost = {self.best_solution.get_cost(self.instance)}")
        print(f"Final feasibility: {'YES' if is_final_feasible else 'NO'}")
        
        if not is_final_feasible:
            print(f"WARNING: Final solution is INFEASIBLE!")
            print(f"Violations: {final_violations[:3]}...")  # Show first 3
        
        lahc_stats = self.lahc.get_statistics()
        print(f"LAHC acceptance rate: {lahc_stats['acceptance_rate']:.1f}%")
        print(f"{'='*70}")
        
        return self.best_solution
    
    def _is_better_solution(self, sol1: Solution, sol2: Solution) -> bool:
        """Compare two solutions (lexicographic: vehicles first, then cost)"""
        vehicles1 = sol1.get_num_vehicles()
        vehicles2 = sol2.get_num_vehicles()
        
        if vehicles1 != vehicles2:
            return vehicles1 < vehicles2
        
        return sol1.get_cost(self.instance) < sol2.get_cost(self.instance)
    
    def _create_neighbor(self, destroy_op: str, repair_op: str, destroy_size: int) -> Optional[Solution]:
        """
        Create neighbor solution using destroy-repair on PICKUP-DELIVERY PAIRS
        
        Returns None if repair fails
        """
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
            
            # Destroy phase - removes PAIRS
            removed_pairs = destroy_func(neighbor, destroy_size)
            
            if not removed_pairs:
                return None
            
            # Repair phase - inserts PAIRS back
            success = repair_func(neighbor, removed_pairs)
            
            if not success:
                return None
            
            return neighbor
            
        except Exception as e:
            # Log error but don't crash
            if self.iterations % 100 == 0:
                print(f"Error in _create_neighbor: {e}")
            return None
    
    def _get_all_pairs(self) -> List[Tuple[int, int]]:
        """Get all pickup-delivery pairs from instance"""
        pairs = []
        for node in self.instance.nodes:
            if node.is_pickup():
                pairs.append((node.idx, node.pair))
        return pairs
    
    def _random_pair_removal(self, solution: Solution, k: int) -> List[Tuple[int, int]]:
        """
        Random removal: remove k random PICKUP-DELIVERY PAIRS
        Always removes both pickup and delivery together
        """
        # Collect all pairs present in solution
        pairs_in_solution = []
        for route in solution.routes:
            visited_pickups = set()
            for node_id in route:
                node = self.instance.nodes[node_id]
                if node.is_pickup():
                    if node.pair in route:
                        pairs_in_solution.append((node_id, node.pair))
                        visited_pickups.add(node_id)
        
        # Remove duplicates
        pairs_in_solution = list(set(pairs_in_solution))
        
        if not pairs_in_solution:
            return []
        
        # Limit k to available pairs
        k = min(k, len(pairs_in_solution))
        
        # Randomly select k pairs to remove
        pairs_to_remove = random.sample(pairs_in_solution, k)
        
        # Remove both pickup and delivery from solution
        for pickup, delivery in pairs_to_remove:
            self._remove_nodes_from_solution(solution, [pickup, delivery])
        
        return pairs_to_remove
    
    def _shaw_removal(self, solution: Solution, k: int) -> List[Tuple[int, int]]:
        """
        Shaw removal: remove k PAIRS that are related
        Relatedness based on: distance, time window overlap, same route
        """
        # Collect all pairs in solution
        pairs_in_solution = []
        pair_routes = {}  # Map pair to route index
        
        for route_idx, route in enumerate(solution.routes):
            for node_id in route:
                node = self.instance.nodes[node_id]
                if node.is_pickup() and node.pair in route:
                    pair = (node_id, node.pair)
                    if pair not in pairs_in_solution:
                        pairs_in_solution.append(pair)
                        pair_routes[pair] = route_idx
        
        if not pairs_in_solution:
            return []
        
        k = min(k, len(pairs_in_solution))
        
        # Start with random seed pair
        seed_pair = random.choice(pairs_in_solution)
        removed_pairs = [seed_pair]
        remaining_pairs = [p for p in pairs_in_solution if p != seed_pair]
        
        # Iteratively remove most related pairs
        while len(removed_pairs) < k and remaining_pairs:
            best_relatedness = -float('inf')
            best_pair = None
            
            for pair in remaining_pairs:
                relatedness = self._calculate_pair_relatedness(
                    pair, removed_pairs, pair_routes
                )
                if relatedness > best_relatedness:
                    best_relatedness = relatedness
                    best_pair = pair
            
            if best_pair:
                removed_pairs.append(best_pair)
                remaining_pairs.remove(best_pair)
            else:
                break
        
        # Remove pairs from solution
        for pickup, delivery in removed_pairs:
            self._remove_nodes_from_solution(solution, [pickup, delivery])
        
        return removed_pairs
    
    def _calculate_pair_relatedness(self, pair: Tuple[int, int], 
                                    removed_pairs: List[Tuple[int, int]],
                                    pair_routes: dict) -> float:
        """Calculate relatedness score between pair and already removed pairs"""
        pickup, delivery = pair
        pickup_node = self.instance.nodes[pickup]
        
        total_relatedness = 0.0
        
        for removed_pickup, removed_delivery in removed_pairs:
            removed_pickup_node = self.instance.nodes[removed_pickup]
            
            # Distance relatedness (closer = more related)
            distance = self.instance.get_travel_time(pickup, removed_pickup)
            max_distance = self.instance.nodes[0].ltw  # Use depot time window as scale
            distance_score = 1.0 - (distance / max(max_distance, 1))
            
            # Time window overlap
            tw_overlap = min(pickup_node.ltw, removed_pickup_node.ltw) - max(pickup_node.etw, removed_pickup_node.etw)
            tw_range = max(pickup_node.ltw - pickup_node.etw, removed_pickup_node.ltw - removed_pickup_node.etw, 1)
            tw_score = max(0, tw_overlap / tw_range)
            
            # Same route bonus
            same_route = 1.0 if pair_routes.get(pair) == pair_routes.get((removed_pickup, removed_delivery)) else 0.0
            
            # Weighted combination
            relatedness = 0.5 * distance_score + 0.3 * tw_score + 0.2 * same_route
            total_relatedness += relatedness
        
        return total_relatedness / len(removed_pairs)
    
    def _worst_removal(self, solution: Solution, k: int) -> List[Tuple[int, int]]:
        """
        Worst removal: remove k PAIRS that contribute most to total distance
        Removes pairs whose removal would save the most distance
        """
        # Collect all pairs with their removal savings
        pair_savings = []
        
        for route in solution.routes:
            if not route:
                continue
            
            visited_pickups = set()
            for node_id in route:
                node = self.instance.nodes[node_id]
                if node.is_pickup() and node.pair in route:
                    if node_id not in visited_pickups:
                        # Calculate cost saving if this pair is removed
                        saving = self._calculate_pair_removal_saving(route, node_id, node.pair)
                        pair_savings.append((saving, (node_id, node.pair)))
                        visited_pickups.add(node_id)
        
        if not pair_savings:
            return []
        
        # Sort by saving (highest first) - these are the "worst" pairs
        pair_savings.sort(reverse=True)
        
        # Take top k pairs
        k = min(k, len(pair_savings))
        removed_pairs = [pair for _, pair in pair_savings[:k]]
        
        # Remove from solution
        for pickup, delivery in removed_pairs:
            self._remove_nodes_from_solution(solution, [pickup, delivery])
        
        return removed_pairs
    
    def _calculate_pair_removal_saving(self, route: List[int], pickup: int, delivery: int) -> float:
        """
        Calculate distance saving if pickup-delivery pair is removed from route
        Saving = distance_with_pair - distance_without_pair
        """
        # Calculate current cost with pair
        cost_with = self._calculate_route_distance(route)
        
        # Calculate cost without pair
        route_without = [n for n in route if n != pickup and n != delivery]
        cost_without = self._calculate_route_distance(route_without)
        
        return cost_with - cost_without
    
    def _calculate_route_distance(self, route: List[int]) -> float:
        """Calculate total distance of a route"""
        if not route:
            return 0
        
        distance = 0
        current = 0  # Depot
        
        for node_id in route:
            distance += self.instance.get_travel_time(current, node_id)
            current = node_id
        
        distance += self.instance.get_travel_time(current, 0)  # Return to depot
        
        return distance
    
    
    def _greedy_pair_insertion(self, solution: Solution, removed_pairs: List[Tuple[int, int]]) -> bool:
        """
        Greedy insertion for PICKUP-DELIVERY PAIRS
        For each pair, find the cheapest feasible insertion position
        """
        for pickup, delivery in removed_pairs:
            best_cost = float('inf')
            best_route_idx = -1
            best_pickup_pos = -1
            best_delivery_pos = -1
            
            # Try inserting pair into existing routes
            for route_idx, route in enumerate(solution.routes):
                # Try all positions for pickup
                for pickup_pos in range(len(route) + 1):
                    # Try all positions for delivery (must be AFTER pickup)
                    for delivery_pos in range(pickup_pos + 1, len(route) + 2):
                        # Calculate cost and check feasibility
                        temp_route = route[:pickup_pos] + [pickup] + route[pickup_pos:delivery_pos] + [delivery] + route[delivery_pos:]
                        
                        # Quick feasibility check using local validator
                        if self._is_route_feasible(temp_route):
                            cost = self._calculate_pair_insertion_cost(route, pickup, delivery, pickup_pos, delivery_pos)
                            if cost < best_cost:
                                best_cost = cost
                                best_route_idx = route_idx
                                best_pickup_pos = pickup_pos
                                best_delivery_pos = delivery_pos
            
            # Try creating new route
            new_route_cost = self._calculate_new_pair_route_cost(pickup, delivery)
            
            if best_route_idx == -1 or new_route_cost < best_cost:
                # Create new route with pair
                solution.routes.append([pickup, delivery])
            else:
                # Insert into existing route (pickup first, then delivery)
                solution.routes[best_route_idx].insert(best_pickup_pos, pickup)
                # Adjust delivery position since we just inserted pickup
                adjusted_delivery_pos = best_delivery_pos if best_delivery_pos <= best_pickup_pos else best_delivery_pos
                solution.routes[best_route_idx].insert(adjusted_delivery_pos, delivery)
        
        return True
    
    def _regret_k_insertion(self, solution: Solution, removed_pairs: List[Tuple[int, int]]) -> bool:
        """
        Regret-k insertion for PICKUP-DELIVERY PAIRS with VARIABLE k (2-5)
        Prioritize pairs that have high regret (difference between best and k-th best insertion)
        k is randomly selected for each iteration for diversity
        """
        # Random k for diversity
        k = random.randint(2, 5)
        
        while removed_pairs:
            pair_regrets = []
            
            for pair in removed_pairs:
                pickup, delivery = pair
                costs = []
                
                # Find best and 2nd best insertion costs
                for route_idx, route in enumerate(solution.routes):
                    for pickup_pos in range(len(route) + 1):
                        for delivery_pos in range(pickup_pos + 1, len(route) + 2):
                            temp_route = route[:pickup_pos] + [pickup] + route[pickup_pos:delivery_pos] + [delivery] + route[delivery_pos:]
                            if self._is_route_feasible(temp_route):
                                cost = self._calculate_pair_insertion_cost(route, pickup, delivery, pickup_pos, delivery_pos)
                                costs.append(cost)
                
                # Cost of new route
                costs.append(self._calculate_new_pair_route_cost(pickup, delivery))
                
                # Calculate regret-k (difference between best and k-th best)
                costs.sort()
                if len(costs) >= k:
                    regret = costs[k-1] - costs[0]
                elif len(costs) >= 2:
                    regret = costs[-1] - costs[0]  # Use worst if less than k options
                else:
                    regret = costs[0] if costs else float('inf')
                
                pair_regrets.append((pair, regret))
            
            # Sort by regret (descending) - prioritize "difficult" pairs
            pair_regrets.sort(key=lambda x: x[1], reverse=True)
            
            # Insert pair with highest regret
            if not pair_regrets:
                break
            
            pair_to_insert, _ = pair_regrets[0]
            pickup, delivery = pair_to_insert
            
            # Find best position for this pair
            best_cost = float('inf')
            best_route_idx = -1
            best_pickup_pos = -1
            best_delivery_pos = -1
            
            for route_idx, route in enumerate(solution.routes):
                for pickup_pos in range(len(route) + 1):
                    for delivery_pos in range(pickup_pos + 1, len(route) + 2):
                        temp_route = route[:pickup_pos] + [pickup] + route[pickup_pos:delivery_pos] + [delivery] + route[delivery_pos:]
                        if self._is_route_feasible(temp_route):
                            cost = self._calculate_pair_insertion_cost(route, pickup, delivery, pickup_pos, delivery_pos)
                            if cost < best_cost:
                                best_cost = cost
                                best_route_idx = route_idx
                                best_pickup_pos = pickup_pos
                                best_delivery_pos = delivery_pos
            
            # Try new route
            new_route_cost = self._calculate_new_pair_route_cost(pickup, delivery)
            
            if best_route_idx == -1 or new_route_cost < best_cost:
                solution.routes.append([pickup, delivery])
            else:
                solution.routes[best_route_idx].insert(best_pickup_pos, pickup)
                adjusted_delivery_pos = best_delivery_pos if best_delivery_pos <= best_pickup_pos else best_delivery_pos
                solution.routes[best_route_idx].insert(adjusted_delivery_pos, delivery)
            
            # Remove inserted pair from list
            removed_pairs.remove(pair_to_insert)
        
        return True
    
    def _is_route_feasible(self, route: List[int]) -> bool:
        """Quick feasibility check for a single route"""
        if not route:
            return True
        
        time = 0
        load = 0
        visited_pickups = set()
        prev_node = 0
        
        for node_id in route:
            if node_id < 0 or node_id >= len(self.instance.nodes):
                return False
            
            node = self.instance.nodes[node_id]
            
            # Travel time
            time += self.instance.get_travel_time(prev_node, node_id)
            arrival_time = max(time, node.etw)
            
            # Time window check
            if arrival_time > node.ltw:
                return False
            
            # Precedence check
            if node.is_delivery():
                if node.pair not in visited_pickups:
                    return False
            
            # Capacity check
            load += node.dem
            if load > self.instance.capacity or load < 0:
                return False
            
            if node.is_pickup():
                visited_pickups.add(node_id)
            
            time = arrival_time + node.dur
            prev_node = node_id
        
        # Check return to depot
        return_time = time + self.instance.get_travel_time(prev_node, 0)
        return return_time <= self.instance.nodes[0].ltw
    
    def _calculate_pair_insertion_cost(self, route: List[int], pickup: int, delivery: int,
                                       pickup_pos: int, delivery_pos: int) -> float:
        """Calculate cost of inserting a pickup-delivery pair at given positions"""
        # Cost is the increase in route travel time
        original_cost = self._calculate_route_travel_cost(route)
        
        # Create temporary route with pair inserted
        temp_route = route[:pickup_pos] + [pickup] + route[pickup_pos:delivery_pos] + [delivery] + route[delivery_pos:]
        new_cost = self._calculate_route_travel_cost(temp_route)
        
        return new_cost - original_cost
    
    def _calculate_route_travel_cost(self, route: List[int]) -> float:
        """Calculate total travel cost for a route"""
        if not route:
            return 0.0
        
        cost = 0.0
        prev_node = 0
        
        for node_id in route:
            cost += self.instance.get_travel_time(prev_node, node_id)
            prev_node = node_id
        
        # Return to depot
        cost += self.instance.get_travel_time(prev_node, 0)
        return cost
    
    def _calculate_new_pair_route_cost(self, pickup: int, delivery: int) -> float:
        """Calculate cost of creating a new route with a single pair"""
        # Depot -> Pickup -> Delivery -> Depot
        cost = (self.instance.get_travel_time(0, pickup) +
                self.instance.get_travel_time(pickup, delivery) +
                self.instance.get_travel_time(delivery, 0))
        
        # Add penalty for creating new vehicle
        vehicle_penalty = 10000  # High penalty to discourage too many vehicles
        return cost + vehicle_penalty
    
    def _remove_nodes_from_solution(self, solution: Solution, nodes: List[int]):
        """Remove nodes from solution routes"""
        try:
            for node in nodes:
                for route in solution.routes[:]:
                    if node in route:
                        route.remove(node)
            
            # Remove empty routes
            solution.routes = [route for route in solution.routes if route and len(route) > 0]
        except Exception as e:
            print(f"Error in _remove_nodes_from_solution: {e}")
    
    
    def _copy_solution(self, solution: Solution) -> Solution:
        """Create a deep copy of solution"""
        copy_sol = Solution()
        copy_sol.inst_name = solution.inst_name
        copy_sol.authors = solution.authors
        copy_sol.date = solution.date
        copy_sol.reference = solution.reference
        copy_sol.routes = [route[:] for route in solution.routes]
        return copy_sol
