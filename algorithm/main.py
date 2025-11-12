#!/usr/bin/env python3
"""
Main script for PDPTW algorithm framework
Provides command-line interface to run different algorithms
"""

import argparse
import os
import sys
from data_loader import Instance
from solution_encoder import SolutionEncoder
from construction_heuristic import GreedyInsertion, NearestNeighbor
from local_search import LocalSearch
from simulated_annealing import SimulatedAnnealing
from large_neighborhood_search import LargeNeighborhoodSearch
from evaluator import PDPTWBenchmarkEvaluator


def validate_instance_file(filepath: str) -> bool:
    """Check if instance file exists and is valid"""
    if not os.path.exists(filepath):
        print(f"Error: Instance file '{filepath}' not found")
        return False
    
    if not filepath.endswith('.txt'):
        print("Warning: Instance file should have .txt extension")
    
    return True


def run_single_algorithm(instance_file: str, method: str, algorithm: str = None, 
                        output_dir: str = "output", timeout: int = 300):
    """Run single algorithm on single instance"""
    
    if not validate_instance_file(instance_file):
        return
    
    print(f"Running {method} on {os.path.basename(instance_file)}")
    print("="*50)
    
    # Load instance
    instance = Instance()
    try:
        instance.read_from_file(instance_file)
        print(f"Instance loaded: {instance.name}")
        print(f"Size: {instance.size-1} locations + depot")
        print(f"Capacity: {instance.capacity}")
        print()
    except Exception as e:
        print(f"Error loading instance: {e}")
        return
    
    # Select algorithm
    algorithm_instance = None
    solution_name = ""
    
    if method == "construction":
        if algorithm == "greedy":
            algorithm_instance = GreedyInsertion(instance)
            solution_name = "Greedy Insertion"
        elif algorithm == "nearest":
            algorithm_instance = NearestNeighbor(instance)
            solution_name = "Nearest Neighbor"
        else:
            print("Available construction algorithms: greedy, nearest")
            return
            
        routes = algorithm_instance.solve()
        solution = SolutionEncoder.create_solution_from_routes(routes, instance.name, solution_name)
        
    elif method == "local_search":
        # Start with greedy solution
        constructor = GreedyInsertion(instance)
        routes = constructor.solve()
        initial_solution = SolutionEncoder.create_solution_from_routes(routes, instance.name, "Initial")
        
        # Apply local search
        local_search = LocalSearch(instance)
        improved_solution = local_search.multi_route_improvement(initial_solution)
        solution = improved_solution or initial_solution
        solution_name = "Local Search"
        
    elif method == "metaheuristic":
        if algorithm == "sa":
            algorithm_instance = SimulatedAnnealing(instance)
            solution_name = "Simulated Annealing"
        elif algorithm == "lns":
            algorithm_instance = LargeNeighborhoodSearch(instance)
            solution_name = "Large Neighborhood Search"
        else:
            print("Available metaheuristic algorithms: sa, lns")
            return
            
        solution = algorithm_instance.solve()
        
    else:
        print("Available methods: construction, local_search, metaheuristic")
        return
    
    # Validate solution
    local_search = LocalSearch(instance)
    is_valid = local_search._is_valid_solution(solution)
    
    # Calculate metrics
    num_vehicles = solution.get_num_vehicles()
    cost = solution.get_cost(instance)
    
    print("Solution Results:")
    print(f"Valid: {'Yes' if is_valid else 'No'}")
    print(f"Cost: {cost}")
    print(f"Vehicles: {num_vehicles}")
    print(f"Algorithm: {solution_name}")
    
    # Save solution
    if os.path.exists(output_dir) is not True:
        os.makedirs(output_dir)
    
    output_file = SolutionEncoder.validate_and_save(
        solution, instance, output_dir, 
        authors=solution_name, 
        reference="PDPTW Solver"
    )
    
    # Validate using original validator if available
    validator_path = "../validator/validator.py"
    if os.path.exists(validator_path):
        os.system(f"python {validator_path} -i {instance_file} -s {output_file}")
    
    print(f"\nSolution saved: {output_file}")


def run_benchmark(test_size: str = "small", max_instances: int = 5, output_file: str = "benchmark_results.json"):
    """Run benchmark comparison on multiple algorithms"""
    
    print("Running PDPTW Algorithm Benchmark")
    print("="*50)
    
    # Find instances
    instances_dir = "../instances"
    if not os.path.exists(instances_dir):
        print("Error: Instances directory not found")
        print("Please ensure instance files are in ../instances/")
        return
    
    available_instances = []
    for filename in os.listdir(instances_dir):
        if filename.endswith('.txt') and filename not in ['README.txt', 'how_to_read.txt', 'configurations.txt']:
            available_instances.append(os.path.join(instances_dir, filename))
    
    if not available_instances:
        print("Error: No instance files found")
        print("Please download instances from: https://data.mendeley.com/datasets/wr2ct4r22f/2")
        return
    
    # Select test instances based on size
    test_instances = []
    for filename in available_instances:
        basename = os.path.basename(filename)
        
        # Size-based filtering
        if test_size == "small":
            if any(size in basename for size in ["n100", "n200"]):
                test_instances.append(filename)
        elif test_size == "medium":
            if any(size in basename for size in ["n400", "n600", "n800"]):
                test_instances.append(filename)
        elif test_size == "large":
            if any(size in basename for size in ["n1000", "n1500", "n2000"]):
                test_instances.append(filename)
        elif test_size == "all":
            test_instances.append(filename)
        
        if len(test_instances) >= max_instances:
            break
    
    if not test_instances:
        print(f"No instances found for test size '{test_size}'")
        return
    
    print(f"Testing on {len(test_instances)} instances:")
    for inst in test_instances:
        print(f"  - {os.path.basename(inst)}")
    
    # Define algorithms
    algorithms = [
        ("Greedy", GreedyInsertion),
        ("NearestNeighbor", NearestNeighbor)
    ]
    
    # Run evaluation
    evaluator = PDPTWBenchmarkEvaluator()
    results = evaluator.compare_algorithms(algorithms, test_instances)
    
    # Save results
    evaluator.save_results(results, output_file)
    
    # Print summary
    report = evaluator.create_summary_report(results)
    print("\n" + report)


def main():
    parser = argparse.ArgumentParser(description='PDPTW Algorithm Framework')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Single algorithm command
    single_parser = subparsers.add_parser('single', help='Run single algorithm on single instance')
    single_parser.add_argument('--instance', required=True, help='Path to instance file')
    single_parser.add_argument('--method', required=True, choices=['construction', 'local_search', 'metaheuristic'],
                               help='Algorithm method to use')
    single_parser.add_argument('--algorithm', help='Specific algorithm (greedy, nearest, sa, lns)')
    single_parser.add_argument('--output-dir', default='output', help='Output directory')
    single_parser.add_argument('--timeout', type=int, default=300, help='Timeout in seconds')
    
    # Benchmark command
    benchmark_parser = subparsers.add_parser('benchmark', help='Run benchmark comparison')
    benchmark_parser.add_argument('--test-size', choices=['small', 'medium', 'large', 'all'], 
                                default='small', help='Test instance sizes')
    benchmark_parser.add_argument('--max-instances', type=int, default=5, 
                                help='Maximum number of instances to test')
    benchmark_parser.add_argument('--output', default='benchmark_results.json', 
                                 help='Output file for results')
    
    args = parser.parse_args()
    
    if args.command == 'single':
        run_single_algorithm(
            args.instance, args.method, args.algorithm, 
            args.output_dir, args.timeout
        )
    elif args.command == 'benchmark':
        run_benchmark(args.test_size, args.max_instances, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    print("PDPTW Algorithm Framework")
    print("Citation: Carlo S. Sartori and Luciana S. Buriol (2020)")
    print('"A Study on the Pickup and Delivery Problem with Time Windows: Matheuristics and New Instances"')
    print("Computers & Operations Research")
    print()
    
    main()
