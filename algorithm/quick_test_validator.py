"""Quick test to verify validator and LNS work correctly"""

from data_loader import Instance
from construction_heuristic import GreedyInsertion
from solution_encoder import SolutionEncoder
from feasibility_validator import validate_solution
from large_neighborhood_search import LargeNeighborhoodSearch

# Test on single instance
instance_file = "../instances/n100/n100/bar-n100-1.txt"

print("Loading instance...")
instance = Instance()
instance.read_from_file(instance_file)
print(f"Instance: {instance.name}, size: {instance.size}")

# Generate initial solution with Greedy
print("\nGenerating initial solution with Greedy...")
greedy = GreedyInsertion(instance)
initial_routes = greedy.solve()
initial_solution = SolutionEncoder.create_solution_from_routes(
    initial_routes, instance.name, "Greedy"
)

print(f"Initial solution: {initial_solution.get_num_vehicles()} vehicles, "
      f"cost {initial_solution.get_cost(instance)}")

# Validate initial solution
print("\nValidating initial solution...")
is_feasible, violations = validate_solution(initial_solution, instance)
print(f"Feasible: {is_feasible}")
if not is_feasible:
    print(f"Violations (first 5): {violations[:5]}")
else:
    print("SUCCESS: Initial solution is feasible!")

# Test LNS
print("\nTesting LNS with LAHC and strict feasibility...")
lns = LargeNeighborhoodSearch(
    instance,
    max_iterations=50,
    max_time=20,
    min_destroy_size=2,
    max_destroy_size=8
)
lns.current_solution = initial_solution
lns.best_solution = lns._copy_solution(initial_solution)

try:
    final_solution = lns.solve()
    
    # Validate final solution
    is_final_feasible, final_violations = validate_solution(final_solution, instance)
    
    print(f"\nFinal solution: {final_solution.get_num_vehicles()} vehicles, "
          f"cost {final_solution.get_cost(instance)}")
    print(f"Final feasibility: {is_final_feasible}")
    
    if not is_final_feasible:
        print(f"Violations: {final_violations[:5]}")
    else:
        print("SUCCESS: LNS produced feasible solution!")
        
except Exception as e:
    print(f"\nERROR during LNS: {e}")
    import traceback
    traceback.print_exc()
