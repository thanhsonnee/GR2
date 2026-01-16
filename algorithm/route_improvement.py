"""
Route improvement operators for PDPTW
Includes: 2-opt, relocate, exchange
All operators preserve PDPTW feasibility (pickup before delivery)
"""

from typing import List, Tuple, Optional
from data_loader import Instance, Solution
from feasibility_validator import validate_solution


class RouteImprovement:
    """Local search operators for route improvement"""
    
    def __init__(self, instance: Instance):
        self.instance = instance
    
    def improve_solution(self, solution: Solution, max_time: float = 10.0) -> Solution:
        """Apply all improvement operators to solution"""
        import time
        start_time = time.time()
        
        improved = self._copy_solution(solution)
        iterations = 0
        
        while time.time() - start_time < max_time:
            improved_this_round = False
            
            # Try all operators on all routes
            for route_idx in range(len(improved.routes)):
                if time.time() - start_time >= max_time:
                    break
                
                # 2-opt within route
                if self._two_opt_route(improved, route_idx):
                    improved_this_round = True
                
                # Relocate within route
                if self._relocate_within_route(improved, route_idx):
                    improved_this_round = True
                
                # Exchange within route
                if self._exchange_within_route(improved, route_idx):
                    improved_this_round = True
            
            # Inter-route operators
            for i in range(len(improved.routes)):
                for j in range(i + 1, len(improved.routes)):
                    if time.time() - start_time >= max_time:
                        break
                    
                    # Relocate between routes
                    if self._relocate_between_routes(improved, i, j):
                        improved_this_round = True
                    
                    # Exchange between routes
                    if self._exchange_between_routes(improved, i, j):
                        improved_this_round = True
            
            iterations += 1
            
            # Stop if no improvement
            if not improved_this_round:
                break
        
        # Final validation
        is_valid, _ = validate_solution(improved, self.instance)
        if is_valid and improved.get_cost(self.instance) < solution.get_cost(self.instance):
            return improved
        else:
            return solution
    
    def _two_opt_route(self, solution: Solution, route_idx: int) -> bool:
        """2-opt improvement within a single route (PDPTW-aware)"""
        route = solution.routes[route_idx]
        if len(route) < 4:
            return False
        
        best_improvement = 0
        best_i = -1
        best_j = -1
        
        for i in range(len(route) - 1):
            for j in range(i + 2, len(route)):
                # Calculate current cost
                if i > 0:
                    cost_before = self.instance.get_travel_time(route[i-1], route[i])
                else:
                    cost_before = self.instance.get_travel_time(0, route[i])
                
                cost_before += self.instance.get_travel_time(route[j-1], route[j])
                
                # Calculate new cost after 2-opt
                if i > 0:
                    cost_after = self.instance.get_travel_time(route[i-1], route[j-1])
                else:
                    cost_after = self.instance.get_travel_time(0, route[j-1])
                
                cost_after += self.instance.get_travel_time(route[i], route[j])
                
                improvement = cost_before - cost_after
                
                if improvement > best_improvement:
                    # Check if this preserves PDPTW constraints
                    new_route = route[:i] + route[i:j][::-1] + route[j:]
                    if self._is_route_feasible(new_route):
                        best_improvement = improvement
                        best_i = i
                        best_j = j
        
        if best_improvement > 0:
            route = solution.routes[route_idx]
            solution.routes[route_idx] = route[:best_i] + route[best_i:best_j][::-1] + route[best_j:]
            return True
        
        return False
    
    def _relocate_within_route(self, solution: Solution, route_idx: int) -> bool:
        """Relocate a customer to a different position in the same route"""
        route = solution.routes[route_idx]
        if len(route) < 3:
            return False
        
        best_improvement = 0
        best_from = -1
        best_to = -1
        
        for from_pos in range(len(route)):
            for to_pos in range(len(route)):
                if from_pos == to_pos or abs(from_pos - to_pos) == 1:
                    continue
                
                # Calculate improvement
                new_route = route[:]
                customer = new_route.pop(from_pos)
                new_route.insert(to_pos, customer)
                
                if self._is_route_feasible(new_route):
                    old_cost = self._route_cost(route)
                    new_cost = self._route_cost(new_route)
                    improvement = old_cost - new_cost
                    
                    if improvement > best_improvement:
                        best_improvement = improvement
                        best_from = from_pos
                        best_to = to_pos
        
        if best_improvement > 0:
            route = solution.routes[route_idx]
            customer = route.pop(best_from)
            route.insert(best_to, customer)
            solution.routes[route_idx] = route
            return True
        
        return False
    
    def _exchange_within_route(self, solution: Solution, route_idx: int) -> bool:
        """Exchange two customers within the same route"""
        route = solution.routes[route_idx]
        if len(route) < 2:
            return False
        
        best_improvement = 0
        best_i = -1
        best_j = -1
        
        for i in range(len(route)):
            for j in range(i + 1, len(route)):
                new_route = route[:]
                new_route[i], new_route[j] = new_route[j], new_route[i]
                
                if self._is_route_feasible(new_route):
                    old_cost = self._route_cost(route)
                    new_cost = self._route_cost(new_route)
                    improvement = old_cost - new_cost
                    
                    if improvement > best_improvement:
                        best_improvement = improvement
                        best_i = i
                        best_j = j
        
        if best_improvement > 0:
            route = solution.routes[route_idx]
            route[best_i], route[best_j] = route[best_j], route[best_i]
            solution.routes[route_idx] = route
            return True
        
        return False
    
    def _relocate_between_routes(self, solution: Solution, route1_idx: int, route2_idx: int) -> bool:
        """Relocate a customer from one route to another"""
        route1 = solution.routes[route1_idx]
        route2 = solution.routes[route2_idx]
        
        if len(route1) == 0:
            return False
        
        best_improvement = 0
        best_from = -1
        best_to = -1
        
        for from_pos in range(len(route1)):
            customer = route1[from_pos]
            
            for to_pos in range(len(route2) + 1):
                new_route1 = route1[:from_pos] + route1[from_pos+1:]
                new_route2 = route2[:to_pos] + [customer] + route2[to_pos:]
                
                if self._is_route_feasible(new_route1) and self._is_route_feasible(new_route2):
                    old_cost = self._route_cost(route1) + self._route_cost(route2)
                    new_cost = self._route_cost(new_route1) + self._route_cost(new_route2)
                    improvement = old_cost - new_cost
                    
                    if improvement > best_improvement:
                        best_improvement = improvement
                        best_from = from_pos
                        best_to = to_pos
        
        if best_improvement > 0:
            customer = solution.routes[route1_idx].pop(best_from)
            solution.routes[route2_idx].insert(best_to, customer)
            # Remove empty routes
            solution.routes = [r for r in solution.routes if r]
            return True
        
        return False
    
    def _exchange_between_routes(self, solution: Solution, route1_idx: int, route2_idx: int) -> bool:
        """Exchange customers between two routes"""
        route1 = solution.routes[route1_idx]
        route2 = solution.routes[route2_idx]
        
        if len(route1) == 0 or len(route2) == 0:
            return False
        
        best_improvement = 0
        best_i = -1
        best_j = -1
        
        for i in range(len(route1)):
            for j in range(len(route2)):
                new_route1 = route1[:]
                new_route2 = route2[:]
                new_route1[i], new_route2[j] = new_route2[j], new_route1[i]
                
                if self._is_route_feasible(new_route1) and self._is_route_feasible(new_route2):
                    old_cost = self._route_cost(route1) + self._route_cost(route2)
                    new_cost = self._route_cost(new_route1) + self._route_cost(new_route2)
                    improvement = old_cost - new_cost
                    
                    if improvement > best_improvement:
                        best_improvement = improvement
                        best_i = i
                        best_j = j
        
        if best_improvement > 0:
            route1 = solution.routes[route1_idx]
            route2 = solution.routes[route2_idx]
            route1[best_i], route2[best_j] = route2[best_j], route1[best_i]
            solution.routes[route1_idx] = route1
            solution.routes[route2_idx] = route2
            return True
        
        return False
    
    def _is_route_feasible(self, route: List[int]) -> bool:
        """Quick feasibility check for a route"""
        if not route:
            return True
        
        time = 0
        load = 0
        visited = set()
        
        prev_node = 0
        for node_id in route:
            node = self.instance.nodes[node_id]
            
            # Travel time
            time += self.instance.get_travel_time(prev_node, node_id)
            time = max(time, node.etw)
            
            # Time window
            if time > node.ltw:
                return False
            
            # Pickup before delivery
            if node.is_delivery():
                if node.pair not in visited:
                    return False
            
            # Capacity
            load += node.dem
            if load > self.instance.capacity or load < 0:
                return False
            
            visited.add(node_id)
            time += node.dur
            prev_node = node_id
        
        return True
    
    def _route_cost(self, route: List[int]) -> float:
        """Calculate route cost (total travel time)"""
        if not route:
            return 0
        
        cost = self.instance.get_travel_time(0, route[0])
        for i in range(len(route) - 1):
            cost += self.instance.get_travel_time(route[i], route[i+1])
        cost += self.instance.get_travel_time(route[-1], 0)
        
        return cost
    
    def _copy_solution(self, solution: Solution) -> Solution:
        """Deep copy solution"""
        from data_loader import Solution as Sol
        copy_sol = Sol()
        copy_sol.inst_name = solution.inst_name
        copy_sol.authors = solution.authors
        copy_sol.date = solution.date
        copy_sol.reference = solution.reference
        copy_sol.routes = [route[:] for route in solution.routes]
        return copy_sol
