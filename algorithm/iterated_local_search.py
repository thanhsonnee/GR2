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
from large_neighborhood_search import LargeNeighborhoodSearch
from local_search import LocalSearch


class AGES:
    """Automated Generation of Efficient Solutions - Vehicle reduction component"""
    
    def __init__(self, instance: Instance):
        self.instance = instance
    
    def reduce_vehicles(self, solution: Solution, max_iterations: int = 50) -> Solution:
        """Attempt to reduce number of vehicles while maintaining feasibility"""
        print(f"AGES: Starting vehicle reduction from {solution.get_num_vehicles()} vehicles")
        
        best_solution = self._copy_solution(solution)
        current_vehicles = solution.get_num_vehicles()
        
        for iteration in range(max_iterations):
            if len(solution.routes) <= 1:
                break
                
            # Try to merge two routes
            merged_solution = self._try_merge_routes(solution)
            
            if merged_solution and merged_solution.get_num_vehicles() < current_vehicles:
                if self._is_feasible(merged_solution):
                    solution = merged_solution
                    current_vehicles = solution.get_num_vehicles()
                    print(f"AGES: Reduced to {current_vehicles} vehicles (iteration {iteration+1})")
                    best_solution = self._copy_solution(solution)
                
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
    
    def perturb_solution(self, solution: Solution, intensity: int = 3) -> Solution:
        """Apply perturbation to solution to escape local optima"""
        print(f"Perturbation: Applying intensity {intensity}")
        
        perturbed = self._copy_solution(solution)
        
        for _ in range(intensity):
            # Choose random perturbation type
            perturbation_type = random.choice([
                'relocate_customers',
                'swap_routes', 
                'remove_random'
            ])
            
            if perturbation_type == 'relocate_customers':
                perturbed = self._relocate_random_customers(perturbed, 2)
            elif perturbation_type == 'swap_routes':
                perturbed = self._swap_route_segments(perturbed)
            elif perturbation_type == 'remove_random':
                perturbed = self._remove_and_reinsert(perturbed, 1)
        
        return perturbed
    
    def _relocate_random_customers(self, solution: Solution, num_customers: int) -> Solution:
        """Relocate random customers to different routes"""
        if not solution.routes:
            return solution
            
        all_customers = []
        for route_idx, route in enumerate(solution.routes):
            for customer in route:
                all_customers.append((customer, route_idx))
        
        if len(all_customers) < num_customers:
            return solution
        
        # Select random customers to relocate
        customers_to_move = random.sample(all_customers, num_customers)
        
        for customer, old_route_idx in customers_to_move:
            # Remove from old route
            if customer in solution.routes[old_route_idx]:
                solution.routes[old_route_idx].remove(customer)
            
            # Add to random route or create new route
            if solution.routes and random.random() > 0.3:
                new_route_idx = random.randint(0, len(solution.routes) - 1)
                if new_route_idx != old_route_idx and solution.routes[new_route_idx]:
                    pos = random.randint(0, len(solution.routes[new_route_idx]))
                    solution.routes[new_route_idx].insert(pos, customer)
                else:
                    # Add to end of old route if can't find good alternative
                    solution.routes[old_route_idx].append(customer)
            else:
                # Create new route
                solution.routes.append([customer])
        
        # Remove empty routes
        solution.routes = [route for route in solution.routes if route]
        
        return solution
    
    def _swap_route_segments(self, solution: Solution) -> Solution:
        """Swap segments between two routes"""
        if len(solution.routes) < 2:
            return solution
            
        # Select two random routes
        route1_idx, route2_idx = random.sample(range(len(solution.routes)), 2)
        route1 = solution.routes[route1_idx]
        route2 = solution.routes[route2_idx]
        
        if not route1 or not route2:
            return solution
        
        # Select random segments
        seg1_start = random.randint(0, max(0, len(route1) - 1))
        seg1_end = random.randint(seg1_start, len(route1))
        
        seg2_start = random.randint(0, max(0, len(route2) - 1))
        seg2_end = random.randint(seg2_start, len(route2))
        
        # Extract segments
        seg1 = route1[seg1_start:seg1_end]
        seg2 = route2[seg2_start:seg2_end]
        
        # Swap segments
        new_route1 = route1[:seg1_start] + seg2 + route1[seg1_end:]
        new_route2 = route2[:seg2_start] + seg1 + route2[seg2_end:]
        
        solution.routes[route1_idx] = new_route1
        solution.routes[route2_idx] = new_route2
        
        return solution
    
    def _remove_and_reinsert(self, solution: Solution, num_remove: int) -> Solution:
        """Remove random customers and reinsert them"""
        all_customers = []
        for route in solution.routes:
            all_customers.extend(route)
        
        if len(all_customers) < num_remove:
            return solution
        
        customers_to_remove = random.sample(all_customers, num_remove)
        
        # Remove customers
        for customer in customers_to_remove:
            for route in solution.routes:
                if customer in route:
                    route.remove(customer)
                    break
        
        # Remove empty routes
        solution.routes = [route for route in solution.routes if route]
        
        # Reinsert customers
        for customer in customers_to_remove:
            if solution.routes:
                route_idx = random.randint(0, len(solution.routes) - 1)
                pos = random.randint(0, len(solution.routes[route_idx]))
                solution.routes[route_idx].insert(pos, customer)
            else:
                solution.routes.append([customer])
        
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
    
    def __init__(self, instance: Instance, max_iterations: int = 10, max_time: int = 300):
        self.instance = instance
        self.max_iterations = max_iterations
        self.max_time = max_time
        
        # Components
        self.ages = AGES(instance)
        self.set_partitioning = SetPartitioning(instance)
        self.perturbation = Perturbation(instance)
        
        # Best known solutions for comparison
        self.best_known = self._load_best_known_solutions()
        
        # Statistics
        self.iteration_history = []
    
    def solve(self) -> Dict:
        """Run complete ILS framework"""
        print(f"Starting ILS for instance {self.instance.name}")
        print("="*60)
        
        start_time = time.time()
        
        # 1. Start with feasible solution
        print("Step 1: Generating initial feasible solution")
        greedy = GreedyInsertion(self.instance)
        initial_routes = greedy.solve()
        current_solution = SolutionEncoder.create_solution_from_routes(
            initial_routes, self.instance.name, "ILS-Initial"
        )
        
        # VALIDATE INITIAL SOLUTION
        validator = LocalSearch(self.instance)
        if not validator._is_valid_solution(current_solution):
            print("ERROR: Initial solution is not feasible!")
            return None
        
        print(f"Initial: {current_solution.get_num_vehicles()} vehicles, cost {current_solution.get_cost(self.instance)}")
        
        best_solution = self._copy_solution(current_solution)
        solutions_pool = []
        
        # ILS main loop
        for iteration in range(self.max_iterations):
            if time.time() - start_time > self.max_time:
                print(f"Time limit reached: {self.max_time}s")
                break
                
            print(f"\n--- ILS Iteration {iteration + 1} ---")
            
            # 2. AGES - Vehicle reduction
            print("Step 2: AGES - Vehicle reduction")
            reduced_solution = self.ages.reduce_vehicles(current_solution)
            
            # 3. LNS - Cost optimization  
            print("Step 3: LNS - Cost optimization")
            lns = LargeNeighborhoodSearch(
                self.instance, 
                max_iterations=100, 
                max_time=30  # Shorter time per LNS run
            )
            lns.current_solution = reduced_solution
            lns.best_solution = self._copy_solution(reduced_solution)
            optimized_solution = lns.solve()
            
            solutions_pool.append(optimized_solution)
            
            # 4. SP - Select best combination
            if len(solutions_pool) > 1:
                print("Step 4: SP - Set partitioning")
                current_solution = self.set_partitioning.select_best_combination(solutions_pool)
            else:
                current_solution = optimized_solution
            
            # VALIDATE SOLUTION BEFORE ACCEPTING 
            validator = LocalSearch(self.instance)
            if not validator._is_valid_solution(current_solution):
                print(f"WARNING: Solution at iteration {iteration+1} is not feasible! Skipping...")
                continue
            
            # Update best solution
            if self._is_better_solution(current_solution, best_solution):
                best_solution = self._copy_solution(current_solution)
                print(f"*** NEW BEST: {best_solution.get_num_vehicles()} vehicles, cost {best_solution.get_cost(self.instance)} ***")
            
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
        
        # FINAL VALIDATION
        validator = LocalSearch(self.instance)
        is_final_valid = validator._is_valid_solution(best_solution)
        
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
            print("⚠️  WARNING: Final solution is NOT feasible!")
        
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
    instance_file = "../instances/bar-n100-1.txt"
    
    try:
        # Load instance
        instance = Instance()
        instance.read_from_file(instance_file)
        
        # Run ILS
        ils = IteratedLocalSearch(instance, max_iterations=3, max_time=60)  # Shorter for testing
        results = ils.solve()
        
        # Add solution and instance to results for validation
        results['solution'] = ils.best_solution
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
