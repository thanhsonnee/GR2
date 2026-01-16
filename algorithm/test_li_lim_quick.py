"""Quick test on 3 Li & Lim instances to verify everything works"""

import os
import time
from data_loader import Instance
from iterated_local_search import IteratedLocalSearch

# Test on 3 instances from different classes
TEST_INSTANCES = [
    "../instances/pdp_100/lc101.txt",
    "../instances/pdp_100/lr101.txt",
    "../instances/pdp_100/lrc101.txt"
]

print("="*80)
print("QUICK LI & LIM TEST (3 instances)")
print("="*80)

for i, instance_file in enumerate(TEST_INSTANCES, 1):
    instance_name = os.path.basename(instance_file).replace('.txt', '')
    print(f"\n[{i}/3] Testing {instance_name}...")
    
    try:
        instance = Instance()
        instance.read_from_file(instance_file)
        
        print(f"  Size: {instance.size} nodes, Capacity: {instance.capacity}")
        
        start = time.time()
        ils = IteratedLocalSearch(instance, max_iterations=100, max_time=10)
        result = ils.solve()
        runtime = time.time() - start
        
        if result:
            print(f"  Result: {result['vehicles']} veh, cost {result['cost']:.0f}, "
                  f"feasible={result['is_feasible']}, time={runtime:.1f}s")
        else:
            print(f"  FAILED to find solution")
            
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n" + "="*80)
print("Quick test complete!")
