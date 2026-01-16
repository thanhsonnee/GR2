"""
Iterated Local Search (ILS) framework for PDPTW
Implements the research framework with:
- AGES: Vehicle reduction
- LNS: Cost optimization  
- SP: Set partitioning for best combination selection
- Perturbation: Escape local optima
"""

import random
import time
import copy
from typing import List, Dict, Tuple, Optional
from data_loader import Instance, Solution
from solution_encoder import SolutionEncoder
from construction_heuristic import GreedyInsertion
from clarke_wright_pdptw import ClarkeWrightPDPTW
from route_elimination import RouteElimination
from large_neighborhood_search import LargeNeighborhoodSearch
from local_search import LocalSearch
from feasibility_validator import validate_solution
from route_improvement import RouteImprovement


class AGES:
# Trong file thuật toán chính của bạn (ví dụ: iterated_local_search.py)

    def generate_initial_solution(self):
        """
        Tạo lời giải ban đầu bằng phương pháp Greedy Constructive Heuristic.
        Tự động thêm xe mới nếu xe hiện tại không chứa được nữa.
        """
        unassigned_requests = list(self.instance.pickup_delivery_pairs)
        # Sắp xếp request để dễ chèn hơn (ví dụ: theo thời gian sớm nhất e_i)
        unassigned_requests.sort(key=lambda x: self.instance.nodes[x[0]].early_time)
        
        routes = []
        
        while unassigned_requests:
            # Bắt đầu một xe mới (Route mới)
            current_route = [0, 0] # [Depot Start, ..., Depot End]
            route_load = 0
            route_time = 0
            
            # Biến lưu các request đã chèn được vào xe này
            inserted_in_this_route = []
            
            for req in unassigned_requests[:]: # Duyệt copy của danh sách
                pickup_node = req[0]
                delivery_node = req[1]
                
                # Thử chèn cặp (Pickup, Delivery) vào lộ trình hiện tại
                # Hàm này cần kiểm tra: Capacity, Time Window, Pairing
                best_pos = self.find_best_insertion(current_route, pickup_node, delivery_node)
                
                if best_pos is not None:
                    # Thực hiện chèn
                    self.apply_insertion(current_route, pickup_node, delivery_node, best_pos)
                    inserted_in_this_route.append(req)
            
            # Nếu tạo xe mới mà không nhét được ai -> Bế tắc (Lỗi dữ liệu hoặc logic chèn quá kém)
            if not inserted_in_this_route:
                print("CRITICAL: Cannot insert remaining requests even with empty vehicle!")
                return None 

            # Lưu lộ trình này và xóa các request đã phục vụ khỏi danh sách chờ
            routes.append(current_route)
            for req in inserted_in_this_route:
                unassigned_requests.remove(req)
                
        return routes
    
    """Automated Generation of Efficient Solutions - Vehicle reduction component"""
    
    def __init__(self, instance: Instance):
        self.instance = instance
    
    def reduce_vehicles(self, solution: Solution, max_iterations: int = 100) -> Solution:
        """
        Attempt to reduce number of vehicles while maintaining feasibility
        AGGRESSIVE: Try harder to merge routes
        """
        print(f"AGES: Starting vehicle reduction from {solution.get_num_vehicles()} vehicles")
        
        best_solution = self._copy_solution(solution)
        current_vehicles = solution.get_num_vehicles()
        attempts_without_improvement = 0
        max_attempts = 20
        
        for iteration in range(max_iterations):
            if len(solution.routes) <= 1:
                break
            
            # Early stop if too many failed attempts
            if attempts_without_improvement >= max_attempts:
                break
                
            # Try to merge two routes (AGGRESSIVE: try multiple combinations)
            merged_solution = self._try_merge_routes_aggressive(solution)
            
            if merged_solution and merged_solution.get_num_vehicles() < current_vehicles:
                if self._is_feasible(merged_solution):
                    solution = merged_solution
                    current_vehicles = solution.get_num_vehicles()
                    print(f"AGES: Reduced to {current_vehicles} vehicles (iteration {iteration+1})")
                    best_solution = self._copy_solution(solution)
                    attempts_without_improvement = 0
                else:
                    attempts_without_improvement += 1
            else:
                attempts_without_improvement += 1
                
        print(f"AGES: Final vehicles: {best_solution.get_num_vehicles()}")
        return best_solution
    
    def _try_merge_routes(self, solution: Solution) -> Optional[Solution]:
        """Try to merge two routes that can be combined feasibly"""
        if len(solution.routes) < 2:
            return None
            
        # Find two smallest routes to merge
        route_sizes = [(i, len(route)) for i, route in enumerate(solution.routes)]
        route_sizes.sort(key=lambda x: x[1])
        
        for i in range(len(route_sizes) - 1):
            for j in range(i + 1, len(route_sizes)):
                route1_idx = route_sizes[i][0]
                route2_idx = route_sizes[j][0]
                
                merged = self._merge_two_routes(solution, route1_idx, route2_idx)
                if merged:
                    return merged
        
        return None
    
    def _try_merge_routes_aggressive(self, solution: Solution) -> Optional[Solution]:
        """
        Aggressive route merging - try more combinations
        Priority: merge smallest routes first, but also try random pairs
        """
        if len(solution.routes) < 2:
            return None
        
        # Strategy 1: Try smallest routes first
        route_sizes = [(i, len(route)) for i, route in enumerate(solution.routes)]
        route_sizes.sort(key=lambda x: x[1])
        
        # Try top 5 smallest combinations
        attempts = 0
        for i in range(min(5, len(route_sizes) - 1)):
            for j in range(i + 1, min(i + 5, len(route_sizes))):
                route1_idx = route_sizes[i][0]
                route2_idx = route_sizes[j][0]
                
                merged = self._merge_two_routes(solution, route1_idx, route2_idx)
                if merged:
                    return merged
                
                attempts += 1
                if attempts > 10:
                    break
            if attempts > 10:
                break
        
        # Strategy 2: Try random pairs if smallest didn't work
        import random
        for _ in range(5):
            if len(solution.routes) < 2:
                break
            i, j = random.sample(range(len(solution.routes)), 2)
            merged = self._merge_two_routes(solution, i, j)
            if merged:
                return merged
        
        return None
    
    def _merge_two_routes(self, solution: Solution, route1_idx: int, route2_idx: int) -> Optional[Solution]:
        """Merge two specific routes"""
        new_solution = self._copy_solution(solution)
        
        route1 = new_solution.routes[route1_idx]
        route2 = new_solution.routes[route2_idx]
        
        # Try different merge strategies
        merge_strategies = [
            route1 + route2,  # Concatenate
            route2 + route1,  # Reverse concatenate
        ]
        
        for merged_route in merge_strategies:
            test_solution = self._copy_solution(new_solution)
            test_solution.routes[route1_idx] = merged_route
            test_solution.routes.pop(route2_idx)
            
            if self._is_feasible(test_solution):
                return test_solution
        
        return None
    
    def _is_feasible(self, solution: Solution) -> bool:
        """Check if solution is feasible"""
        validator = LocalSearch(self.instance)
        return validator._is_valid_solution(solution)
    
    def _copy_solution(self, solution: Solution) -> Solution:
        """Deep copy solution"""
        copy_sol = Solution()
        copy_sol.inst_name = solution.inst_name
        copy_sol.authors = solution.authors
        copy_sol.date = solution.date
        copy_sol.reference = solution.reference
        copy_sol.routes = [route[:] for route in solution.routes]
        return copy_sol


class SetPartitioning:
    """Set Partitioning component to select best combination of routes"""
    
    def __init__(self, instance: Instance):
        self.instance = instance
    
    def select_best_combination(self, solutions: List[Solution]) -> Solution:
        """Select best combination from multiple solutions"""
        if not solutions:
            return None
            
        print(f"SP: Evaluating {len(solutions)} solutions")
        
        best_solution = None
        best_score = float('inf')
        
        for i, solution in enumerate(solutions):
            # Multi-criteria scoring: vehicles + cost
            vehicles = solution.get_num_vehicles()
            cost = solution.get_cost(self.instance)
            
            # Weighted score: prioritize fewer vehicles first, then cost
            score = vehicles * 10000 + cost
            
            print(f"SP: Solution {i+1}: {vehicles} vehicles, cost {cost}, score {score}")
            
            if score < best_score:
                best_score = score
                best_solution = solution
        
        print(f"SP: Selected solution with {best_solution.get_num_vehicles()} vehicles, cost {best_solution.get_cost(self.instance)}")
        return best_solution


class Perturbation:
    """Perturbation component to escape local optima"""
    
    def __init__(self, instance: Instance):
        self.instance = instance
    
    def perturb_solution(self, solution: Solution, intensity: int = 2) -> Solution:
        """
        Apply perturbation to solution to escape local optima
        
        CRITICAL: Perturbation must preserve feasibility!
        If perturbation creates infeasible solution, revert to original.
        """
        print(f"Perturbation: Applying intensity {intensity}")
        
        original = self._copy_solution(solution)
        perturbed = self._copy_solution(solution)
        
        for i in range(intensity):
            # Choose random perturbation type
            perturbation_type = random.choice([
                'relocate_customers',
                'swap_routes'
            ])
            
            if perturbation_type == 'relocate_customers':
                perturbed = self._relocate_random_customers(perturbed, 1)
            elif perturbation_type == 'swap_routes':
                perturbed = self._swap_route_segments(perturbed)
            
            # Validate after each perturbation step
            is_feasible, violations = validate_solution(perturbed, self.instance)
            if not is_feasible:
                print(f"  Perturbation step {i+1} created infeasibility, reverting...")
                return original  # Revert to original feasible solution
        
        # Final validation
        is_final_feasible, _ = validate_solution(perturbed, self.instance)
        if not is_final_feasible:
            print(f"  Perturbation failed feasibility check, returning original...")
            return original
        
        return perturbed
    
    def _relocate_random_customers(self, solution: Solution, num_pairs: int) -> Solution:
        """
        Relocate random PICKUP-DELIVERY PAIRS to different routes
        IMPORTANT: Always moves both pickup and delivery together
        """
        if not solution.routes:
            return solution
            
        # Collect all pickup-delivery pairs in solution
        pairs_in_solution = []
        for route_idx, route in enumerate(solution.routes):
            visited = set()
            for node_id in route:
                if node_id not in visited:
                    node = self.instance.nodes[node_id]
                    if node.is_pickup() and node.pair in route:
                        pairs_in_solution.append(((node_id, node.pair), route_idx))
                        visited.add(node_id)
                        visited.add(node.pair)
        
        if len(pairs_in_solution) < num_pairs:
            return solution
        
        # Select random pairs to relocate
        pairs_to_move = random.sample(pairs_in_solution, num_pairs)
        
        for (pickup, delivery), old_route_idx in pairs_to_move:
            # Remove BOTH pickup and delivery from old route
            if pickup in solution.routes[old_route_idx]:
                solution.routes[old_route_idx].remove(pickup)
            if delivery in solution.routes[old_route_idx]:
                solution.routes[old_route_idx].remove(delivery)
            
            # Add pair to a different random route
            if len(solution.routes) > 1:
                available_routes = [i for i in range(len(solution.routes)) if i != old_route_idx and solution.routes[i]]
                if available_routes:
                    new_route_idx = random.choice(available_routes)
                    # Insert pickup first, then delivery after
                    pickup_pos = random.randint(0, len(solution.routes[new_route_idx]))
                    solution.routes[new_route_idx].insert(pickup_pos, pickup)
                    delivery_pos = random.randint(pickup_pos + 1, len(solution.routes[new_route_idx]) + 1)
                    solution.routes[new_route_idx].insert(delivery_pos, delivery)
        
        # Remove empty routes
        solution.routes = [route for route in solution.routes if route]
        
        return solution
    
    def _swap_route_segments(self, solution: Solution) -> Solution:
        """
        Swap small segments between two routes
        Keep segments small to minimize breaking feasibility
        """
        if len(solution.routes) < 2:
            return solution
            
        # Select two random routes with customers
        routes_with_customers = [i for i, r in enumerate(solution.routes) if len(r) >= 2]
        if len(routes_with_customers) < 2:
            return solution
        
        route1_idx, route2_idx = random.sample(routes_with_customers, 2)
        route1 = solution.routes[route1_idx]
        route2 = solution.routes[route2_idx]
        
        # Keep segments small (max 2 nodes)
        max_seg_size = 2
        
        seg1_size = random.randint(1, min(max_seg_size, len(route1)))
        seg2_size = random.randint(1, min(max_seg_size, len(route2)))
        
        seg1_start = random.randint(0, len(route1) - seg1_size)
        seg2_start = random.randint(0, len(route2) - seg2_size)
        
        seg1_end = seg1_start + seg1_size
        seg2_end = seg2_start + seg2_size
        
        # Extract segments
        seg1 = route1[seg1_start:seg1_end]
        seg2 = route2[seg2_start:seg2_end]
        
        # Swap segments
        new_route1 = route1[:seg1_start] + seg2 + route1[seg1_end:]
        new_route2 = route2[:seg2_start] + seg1 + route2[seg2_end:]
        
        solution.routes[route1_idx] = new_route1
        solution.routes[route2_idx] = new_route2
        
        return solution
    
    def _copy_solution(self, solution: Solution) -> Solution:
        """Deep copy solution"""
        copy_sol = Solution()
        copy_sol.inst_name = solution.inst_name
        copy_sol.authors = solution.authors
        copy_sol.date = solution.date
        copy_sol.reference = solution.reference
        copy_sol.routes = [route[:] for route in solution.routes]
        return copy_sol


class IteratedLocalSearch:
    """Main ILS framework implementing the research approach"""
    
    def __init__(self, instance: Instance, max_iterations: int = 10, max_time: int = 300, 
                 no_improvement_limit: int = 5):
        self.instance = instance
        self.max_iterations = max_iterations
        self.max_time = max_time
        self.no_improvement_limit = no_improvement_limit
        
        # Components
        self.ages = AGES(instance)
        self.route_eliminator = RouteElimination(instance)
        self.set_partitioning = SetPartitioning(instance)
        self.perturbation = Perturbation(instance)
        self.route_improver = RouteImprovement(instance)
        
        # Best known solutions for comparison
        self.best_known = self._load_best_known_solutions()
        
        # Statistics
        self.iteration_history = []
    
    def solve(self) -> Dict:
        """Run complete ILS framework"""
        print(f"Starting ILS for instance {self.instance.name}")
        print("="*60)
        
        start_time = time.time()
        
        # 1. Start with feasible solution using improved construction
        print("Step 1: Generating initial feasible solution")
        
        # Try Clarke-Wright first
        # Use Clarke-Wright for better initial solution
        print("Step 1: Constructing initial solution with Clarke-Wright...")
        cw = ClarkeWrightPDPTW(self.instance)
        initial_routes = cw.solve(max_time=60)
        
        if not initial_routes or len(initial_routes) == 0:
            print("Clarke-Wright failed, falling back to Greedy")
            greedy = GreedyInsertion(self.instance)
            initial_routes = greedy.solve()
        
        initial_solution = SolutionEncoder.create_solution_from_routes(
            initial_routes, self.instance.name, "ILS-Initial"
        )
        
        # Use LNS to fix infeasible initial solution
        print("Step 1.5: Using LNS to fix initial solution")
        # Reduce time to leave budget for main ILS iterations
        initial_fix_time = min(20, self.max_time * 0.15)  # 15% of total time, max 20s
        lns_fixer = LargeNeighborhoodSearch(self.instance, max_iterations=100, max_time=initial_fix_time)
        lns_fixer.current_solution = initial_solution
        lns_fixer.best_solution = self._copy_solution(initial_solution)
        current_solution = lns_fixer.solve()
        
        # VALIDATE INITIAL SOLUTION - STRICT CHECK
        is_feasible, violations = validate_solution(current_solution, self.instance)
        if not is_feasible:
            print("ERROR: Initial solution is INFEASIBLE!")
            print(f"Violations: {violations[:5]}")  # Show first 5 violations
            print("Cannot proceed with infeasible starting point.")
            print("This indicates a bug in construction heuristic or LNS repair.")
            return None
        
        print("SUCCESS: Initial solution is feasible!")
        print(f"Initial: {current_solution.get_num_vehicles()} vehicles, cost {current_solution.get_cost(self.instance)}")
        
        # Start with feasible solution
        best_solution = self._copy_solution(current_solution)
        solutions_pool = []
        
        # Early stopping: stop if no improvement for N iterations
        iterations_without_improvement = 0
        max_iterations_without_improvement = self.no_improvement_limit
        
        # ILS main loop
        for iteration in range(self.max_iterations):
            if time.time() - start_time > self.max_time:
                print(f"Time limit reached: {self.max_time}s")
                break
            
            # Early stopping check
            if iterations_without_improvement >= max_iterations_without_improvement:
                print(f"Early stopping: No improvement for {max_iterations_without_improvement} iterations")
                break
                
            print(f"\n--- ILS Iteration {iteration + 1} ---")
            
            # 2. AGES - Vehicle reduction
            print("Step 2: AGES - Vehicle reduction")
            reduced_solution = self.ages.reduce_vehicles(current_solution)
            
            # 2.5 Route Elimination - Direct vehicle minimization
            print("Step 2.5: Route Elimination - Direct vehicle minimization")
            reduced_solution, eliminated = self.route_eliminator.eliminate_routes(
                reduced_solution, max_iterations=50, max_time=20
            )
            # Clean up empty routes
            reduced_solution.routes = [r for r in reduced_solution.routes if r]
            if eliminated > 0:
                print(f"  Eliminated {eliminated} route(s), now {len(reduced_solution.routes)} vehicles")
            
            # 3. LNS - Cost optimization  
            print("Step 3: LNS - Cost optimization")
            # Use more aggressive LNS if max_time is large
            if self.max_time >= 150:  # Ultra aggressive (3 min)
                lns_iterations = 3000
                lns_time = 90
            elif self.max_time >= 100:  # Aggressive (2 min)
                lns_iterations = 2000
                lns_time = 60
            else:  # Normal
                lns_iterations = 500
                lns_time = 20
            
            lns = LargeNeighborhoodSearch(
                self.instance, 
                max_iterations=lns_iterations,
                max_time=lns_time
            )
            lns.current_solution = reduced_solution
            lns.best_solution = self._copy_solution(reduced_solution)
            optimized_solution = lns.solve()
            
            # Apply route improvement after LNS
            print("Step 3.5: Route improvement (local search)")
            optimized_solution = self.route_improver.improve_solution(optimized_solution, max_time=5.0)
            
            solutions_pool.append(optimized_solution)
            
            # 4. SP - Select best combination
            if len(solutions_pool) > 1:
                print("Step 4: SP - Set partitioning")
                current_solution = self.set_partitioning.select_best_combination(solutions_pool)
            else:
                current_solution = optimized_solution
            
            # VALIDATE SOLUTION BEFORE ACCEPTING - STRICT CHECK
            is_valid, violations = validate_solution(current_solution, self.instance)
            
            if not is_valid:
                print(f"WARNING: Solution at iteration {iteration+1} is INFEASIBLE!")
                print(f"  Example violation: {violations[0] if violations else 'unknown'}")
                # Revert to last good solution - DON'T accept infeasible!
                current_solution = self._copy_solution(best_solution)
                continue  # Skip to next iteration
            
            # Update best solution - ONLY IF FEASIBLE!
            if self._is_better_solution(current_solution, best_solution):
                best_solution = self._copy_solution(current_solution)
                iterations_without_improvement = 0  # Reset counter
                print(f"*** NEW BEST FEASIBLE: {best_solution.get_num_vehicles()} vehicles, cost {best_solution.get_cost(self.instance)} ***")
            else:
                iterations_without_improvement += 1
            
            # Record iteration
            self.iteration_history.append({
                'iteration': iteration + 1,
                'vehicles': current_solution.get_num_vehicles(),
                'cost': current_solution.get_cost(self.instance),
                'time': time.time() - start_time
            })
            
            # 5. Perturbation for next iteration
            if iteration < self.max_iterations - 1:
                print("Step 5: Perturbation")
                current_solution = self.perturbation.perturb_solution(current_solution, intensity=2)
        
        total_time = time.time() - start_time
        
        # FINAL VALIDATION - STRICT
        is_final_valid, final_violations = validate_solution(best_solution, self.instance)
        
        # Calculate final metrics
        results = self._calculate_final_metrics(best_solution, total_time)
        results['is_feasible'] = is_final_valid
        
        print("\n" + "="*60)
        print("ILS COMPLETED")
        print("="*60)
        print(f"Best solution: {results['vehicles']} vehicles, cost {results['cost']}")
        print(f"Feasible solution: {'YES' if is_final_valid else 'NO'}")
        print(f"Vehicle gap: {results['gap_vehicles']:.2f}%")
        print(f"Cost gap: {results['gap_cost']:.2f}%")
        print(f"Total time: {total_time:.2f}s")
        
        if not is_final_valid:
            print("[WARNING] Final solution is NOT feasible!")
            print(f"  Violations: {final_violations[:3]}")  # Show first 3
        
        return results
    
    def _is_better_solution(self, sol1: Solution, sol2: Solution) -> bool:
        """Compare two solutions (vehicles first, then cost)"""
        vehicles1 = sol1.get_num_vehicles()
        vehicles2 = sol2.get_num_vehicles()
        
        if vehicles1 != vehicles2:
            return vehicles1 < vehicles2
            
        return sol1.get_cost(self.instance) < sol2.get_cost(self.instance)
    
    def _calculate_final_metrics(self, solution: Solution, runtime: float) -> Dict:
        """Calculate evaluation metrics"""
        vehicles = solution.get_num_vehicles()
        cost = solution.get_cost(self.instance)
        
        # Get best known values
        best_known = self.best_known.get(self.instance.name, {})
        best_vehicles = best_known.get('vehicles', vehicles)
        best_cost = best_known.get('cost', cost)
        
        # Calculate gaps
        gap_vehicles = ((vehicles - best_vehicles) / best_vehicles) * 100 if best_vehicles > 0 else 0
        gap_cost = ((cost - best_cost) / best_cost) * 100 if best_cost > 0 else 0
        
        return {
            'instance': self.instance.name,
            'vehicles': vehicles,
            'cost': cost,
            'gap_vehicles': gap_vehicles,
            'gap_cost': gap_cost,
            'runtime': runtime,
            'best_vehicles': best_vehicles,
            'best_cost': best_cost,
            'iterations': len(self.iteration_history),
            'history': self.iteration_history
        }
    
    def _load_best_known_solutions(self) -> Dict:
        """Load best known solutions from bks.dat"""
        best_known = {}
        
        try:
            with open('../solutions/bks.dat', 'r') as f:
                lines = f.readlines()[1:]  # Skip header
                
                for line in lines:
                    parts = line.strip().split(';')
                    if len(parts) >= 4:
                        instance_name = parts[0]
                        vehicles = int(parts[2])
                        cost = int(parts[3])
                        
                        best_known[instance_name] = {
                            'vehicles': vehicles,
                            'cost': cost
                        }
        except FileNotFoundError:
            print("Warning: Best known solutions file not found")
        
        return best_known
    
    def _copy_solution(self, solution: Solution) -> Solution:
        """Deep copy solution"""
        copy_sol = Solution()
        copy_sol.inst_name = solution.inst_name
        copy_sol.authors = solution.authors
        copy_sol.date = solution.date
        copy_sol.reference = solution.reference
        copy_sol.routes = [route[:] for route in solution.routes]
        return copy_sol


def test_ils_on_n100():
    """Test ILS on n100 instance"""
    instance_file = "../instances/n100/n100/bar-n100-1.txt"
    
    try:
        # Load instance
        instance = Instance()
        instance.read_from_file(instance_file)
        
        # Run ILS
        ils = IteratedLocalSearch(instance, max_iterations=3, max_time=60)  # Shorter for testing
        results = ils.solve()
        
        # Check if ILS succeeded
        if results is None:
            print("\n" + "="*60)
            print("FAILED TO GENERATE FEASIBLE SOLUTION")
            print("="*60)
            print("ILS could not create a feasible solution.")
            print("This is a known issue with the current construction heuristic.")
            print("\nRecommendations:")
            print("1. Implement Clarke-Wright Savings construction")
            print("2. Debug LNS stuck issue (0 iterations in 60s)")
            print("3. Add verbose validation to identify violated constraints")
            print("\nSee STATUS_REPORT.md for detailed analysis and action plan.")
            return None
        
        # Add solution and instance to results for validation  
        results['solution'] = results.get('solution', None)
        results['instance'] = instance
        
        # Print formatted results
        print("\n" + "="*60)
        print(f"RESULTS FOR {instance.name}")
        print("="*60)
        print(f"Instance: {results['instance'].name}")
        print(f"Vehicles: {results['vehicles']}")
        print(f"Cost: {results['cost']}")
        print(f"Feasible: {'YES' if results.get('is_feasible', True) else 'NO'}")
        print(f"Gap (vehicles): {results['gap_vehicles']:.2f}%")
        print(f"Gap (cost): {results['gap_cost']:.2f}%")
        print(f"Runtime: {results['runtime']:.2f}s")
        print(f"Best known vehicles: {results['best_vehicles']}")
        print(f"Best known cost: {results['best_cost']}")
        
        return results
        
    except FileNotFoundError:
        print(f"Instance file not found: {instance_file}")
        print("Please ensure the instance file exists")
        return None


if __name__ == "__main__":
    print("ILS Framework for PDPTW")
    print("Testing on n100 instance...")
    test_ils_on_n100()
