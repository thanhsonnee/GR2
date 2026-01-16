"""
Quick test script để test ILS ngay trong folder algorithm
"""

import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loader import Instance
from iterated_local_search import IteratedLocalSearch

def test_ils():
    """Quick test ILS"""
    # Đường dẫn tuyệt đối
    instance_file = r"C:\Users\HP\pdptw-instances\instances\n100\n100\bar-n100-1.txt"
    
    if not os.path.exists(instance_file):
        print(f"[X] File not found: {instance_file}")
        # Try relative path
        instance_file = os.path.join(os.path.dirname(__file__), "..", "instances", "n100", "n100", "bar-n100-1.txt")
        instance_file = os.path.normpath(instance_file)
        print(f"Trying: {instance_file}")
        
    if not os.path.exists(instance_file):
        print(f"[X] Still not found!")
        return
    
    print(f"[OK] Found instance file: {instance_file}")
    print("="*60)
    
    try:
        # Load instance
        instance = Instance()
        instance.read_from_file(instance_file)
        print(f"[OK] Loaded instance: {instance.name}")
        print(f"  - Customers: {len(instance.nodes)-1}")
        print(f"  - Vehicle capacity: {instance.capacity}")
        print()
        
        # Run ILS (quick test)
        print("Running ILS (quick test: 2 iterations, 30s timeout)...")
        ils = IteratedLocalSearch(instance, max_iterations=2, max_time=30)
        results = ils.solve()
        
        if results:
            print("\n" + "="*60)
            print("[OK] TEST COMPLETED SUCCESSFULLY")
            print("="*60)
            print(f"Instance: {results['instance']}")
            print(f"Vehicles: {results['vehicles']}")
            print(f"Cost: {results['cost']}")
            print(f"Feasible: {'YES' if results.get('is_feasible', False) else 'NO'}")
            print(f"Gap (cost): {results['gap_cost']:.2f}%")
            print(f"Runtime: {results['runtime']:.2f}s")
        else:
            print("[X] No results returned")
            
    except Exception as e:
        print(f"[X] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ils()

