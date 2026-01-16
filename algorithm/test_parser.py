"""Quick test to verify Li & Lim parser works"""

from data_loader import Instance
from feasibility_validator import validate_solution
from construction_heuristic import GreedyInsertion
from solution_encoder import SolutionEncoder

# Test on a single Li & Lim instance
instance_file = "../instances/pdp_100/lc101.txt"

print("Testing Li & Lim parser...")
print(f"Instance: {instance_file}\n")

# Parse instance
instance = Instance()
instance.read_from_file(instance_file)

print(f"Successfully parsed!")
print(f"Name: {instance.name}")
print(f"Size: {instance.size} nodes")
print(f"Capacity: {instance.capacity}")
print(f"Number of pickup-delivery pairs: {(instance.size-1)//2}")

# Check some nodes
print(f"\nFirst few nodes:")
for i in range(min(5, len(instance.nodes))):
    node = instance.nodes[i]
    print(f"  Node {node.idx}: demand={node.dem}, tw=[{node.etw}, {node.ltw}], "
          f"service={node.dur}, pair={node.pair}")

# Check distance matrix
print(f"\nDistance matrix size: {len(instance.times)} x {len(instance.times[0])}")
print(f"Distance depot->node1: {instance.times[0][1]}")
print(f"Distance node1->node2: {instance.times[1][2]}")

# Try generating a solution
print(f"\nTesting construction heuristic...")
greedy = GreedyInsertion(instance)
routes = greedy.solve()
solution = SolutionEncoder.create_solution_from_routes(routes, instance.name, "Greedy")

print(f"Generated solution: {solution.get_num_vehicles()} vehicles, cost {solution.get_cost(instance)}")

# Validate
is_feasible, violations = validate_solution(solution, instance)
print(f"Feasible: {is_feasible}")
if not is_feasible:
    print(f"Violations (first 3): {violations[:3]}")
else:
    print("SUCCESS: Parser and validator work correctly!")
