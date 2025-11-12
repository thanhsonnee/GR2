"""
Evaluation script for PDPTW algorithms
Compares algorithm performance against benchmark solutions
"""

import os
import time
import json
from typing import Dict, List, Tuple, Any
from data_loader import Instance
from solution_encoder import SolutionEncoder
from construction_heuristic import GreedyInsertion, NearestNeighbor
from local_search import LocalSearch


class PDPTWBenchmarkEvaluator:
    """Evaluator for PDPTW algorithms against benchmark dataset"""
    
    def __init__(self, instances_dir: str = "../instances", solutions_dir: str = "../solutions/files"):
        self.instances_dir = instances_dir
        self.solutions_dir = solutions_dir
        self.benchmark_solutions = self._load_benchmark_solutions()
        
    def _load_benchmark_solutions(self) -> Dict[str, Dict[str, Any]]:
        """Load best known solutions from benchmark repository"""
        benchmark = {
            "n100": {}, "n200": {}, "n400": {}, "n600": {}, "n800": {},
            "n1000": {}, "n1500": {}, "n2000": {}, "n2500": {}, "n3000": {},
            "n4000": {}, "n5000": {}
        }
        
        if os.path.exists(self.solutions_dir):
            for filename in os.listdir(self.solutions_dir):
                if filename.endswith('.txt'):
                    parts = filename.split('.')
                    if len(parts) >= 3:
                        instance_name = parts[0]
                        vehicles_cost = parts[1].split('_')
                        if len(vehicles_cost) == 2:
                            num_vehicles = int(vehicles_cost[0])
                            cost = int(vehicles_cost[1])
                            
                            # Determine size category
                            size_category = self._get_size_category(instance_name)
                            if size_category:
                                benchmark[size_category][instance_name] = {
                                    'vehicles': num_vehicles,
                                    'cost': cost,
                                    'filename': filename
                                }
        
        return benchmark
    
    def _get_size_category(self, instance_name: str) -> str:
        """Determine size category from instance name"""
        for size in ["n100", "n200", "n400", "n600", "n800", "n1000", 
                     "n1500", "n2000", "n2500", "n3000", "n4000", "n5000"]:
            if size in instance_name:
                return size
        return None
    
    def evaluate_algorithm(self, algorithm_class, algorithm_name: str, 
                          instance_files: List[str], max_runtime: int = 300) -> Dict[str, Any]:
        """
        Evaluate algorithm on given instance files
        
        Args:
            algorithm_class: Algorithm class to evaluate
            algorithm_name: Name of algorithm for reporting
            instance_files: List of instance file paths
            max_runtime: Maximum runtime per instance in seconds
        """
        results = {
            'algorithm': algorithm_name,
            'total_instances': len(instance_files),
            'solved_instances': 0,
            'total_time': 0.0,
            'instances': {}
        }
        
        for instance_file in instance_files:
            if not os.path.exists(instance_file):
                print(f"Warning: Instance file {instance_file} not found")
                continue
                
            instance_name = os.path.basename(instance_file).replace('.txt', '')
            print(f"Evaluating {algorithm_name} on {instance_name}...")
            
            try:
                # Load instance
                instance = Instance()
                instance.read_from_file(instance_file)
                
                # Run algorithm with timeout
                start_time = time.time()
                
                algorithm = algorithm_class(instance)
                solution = algorithm.solve()
                # Some construction algorithms may return raw routes (list of lists)
                if isinstance(solution, list):
                    solution = SolutionEncoder.create_solution_from_routes(
                        solution, instance.name, algorithm_name
                    )
                
                runtime = time.time() - start_time
                results['total_time'] += runtime
                results['solved_instances'] += 1
                
                # Calculate solution metrics
                num_vehicles = solution.get_num_vehicles()
                cost = solution.get_cost(instance)
                
                # Get benchmark solution for comparison
                size_category = self._get_size_category(instance_name)
                benchmark_cost = None
                benchmark_vehicles = None
                
                if size_category and instance_name in self.benchmark_solutions[size_category]:
                    benchmark_data = self.benchmark_solutions[size_category][instance_name]
                    benchmark_cost = benchmark_data['cost']
                    benchmark_vehicles = benchmark_data['vehicles']
                
                # Calculate gaps
                cost_gap = None
                vehicle_gap = None
                
                if benchmark_cost:
                    cost_gap = ((cost - benchmark_cost) / benchmark_cost) * 100
                if benchmark_vehicles:
                    vehicle_gap = num_vehicles - benchmark_vehicles
                
                # Store results
                results['instances'][instance_name] = {
                    'cost': cost,
                    'vehicles': num_vehicles,
                    'runtime': runtime,
                    'benchmark_cost': benchmark_cost,
                    'benchmark_vehicles': benchmark_vehicles,
                    'cost_gap_percent': cost_gap,
                    'vehicle_gap': vehicle_gap,
                    'timeout': runtime > max_runtime
                }
                
                # Validate solution
                validator = LocalSearch(instance)
                is_valid = validator._is_valid_solution(solution)
                results['instances'][instance_name]['valid'] = is_valid
                
                if not is_valid:
                    print(f"  Warning: Invalid solution for {instance_name}")
                
                print(f"  Cost: {cost}, Vehicles: {num_vehicles}, Runtime: {runtime:.2f}s")
                if cost_gap is not None:
                    print(f"  Gap: {cost_gap:.2f}%")
                    
            except Exception as e:
                print(f"Error evaluating {instance_name}: {str(e)}")
                results['instances'][instance_name] = {
                    'error': str(e),
                    'solved': False
                }
        
        # Calculate summary metrics
        if results['solved_instances'] > 0:
            valid_results = [inst for inst in results['instances'].values() 
                           if 'error' not in inst and inst['valid']]
            
            if valid_results:
                results['avg_cost_gap'] = sum(
                    inst.get('cost_gap_percent', 0) for inst in valid_results 
                    if inst.get('cost_gap_percent') is not None
                ) / len([inst for inst in valid_results if inst.get('cost_gap_percent') is not None])
                
                results['avg_vehicle_gap'] = sum(
                    inst.get('vehicle_gap', 0) for inst in valid_results 
                    if inst.get('vehicle_gap') is not None
                ) / len([inst for inst in valid_results if inst.get('vehicle_gap') is not None])
                
                results['avg_runtime'] = sum(inst['runtime'] for inst in valid_results) / len(valid_results)
        
        return results
    
    def compare_algorithms(self, algorithm_configs: List[Tuple[str, Any]], 
                          instance_files: List[str]) -> Dict[str, Any]:
        """
        Compare multiple algorithms on same instance set
        
        Args:
            algorithm_configs: List of (algorithm_name, algorithm_class) tuples
            instance_files: List of instance files to test
        """
        comparison_results = {
            'test_set': len(instance_files),
            'algorithms': {},
            'summary': {}
        }
        
        for algorithm_name, algorithm_class in algorithm_configs:
            print(f"\n=== Evaluating {algorithm_name} ===")
            results = self.evaluate_algorithm(algorithm_class, algorithm_name, instance_files)
            comparison_results['algorithms'][algorithm_name] = results
        
        # Create summary comparison
        summary = comparison_results['summary']
        for alg_name, results in comparison_results['algorithms'].items():
            summary[alg_name] = {
                'solved_instances': results['solved_instances'],
                'solve_rate': results['solved_instances'] / results['total_instances'],
                'total_runtime': results['total_time'],
                'avg_cost_gap': results.get('avg_cost_gap', None),
                'avg_vehicle_gap': results.get('avg_vehicle_gap', None),
                'avg_runtime': results.get('avg_runtime', None)
            }
        
        return comparison_results
    
    def save_results(self, results: Dict[str, Any], output_file: str):
        """Save evaluation results to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {output_file}")
    
    def create_summary_report(self, comparison_results: Dict[str, Any]) -> str:
        """Create human-readable summary report"""
        report = []
        report.append("="*60)
        report.append("PDPTW Algorithm Benchmark Comparison Report")
        report.append("="*60)
        
        report.append(f"Test set size: {comparison_results['test_set']} instances")
        report.append("")
        
        # Algorithm comparison table
        report.append("Algorithm Comparison:")
        report.append("-" * 60)
        report.append(f"{'Algorithm':<20} {'Solved':<8} {'Rate':<8} {'Avg Cost Gap':<15} {'Avg Runtime':<12}")
        report.append("-" * 60)
        
        for alg_name, summary in comparison_results['summary'].items():
            solved = summary['solved_instances']
            rate = summary.get('solve_rate', 0) * 100
            cost_gap_val = summary.get('avg_cost_gap', None)
            runtime_val = summary.get('avg_runtime', None)
            cost_gap_str = f"{cost_gap_val:.2f}%" if isinstance(cost_gap_val, (int, float)) else "N/A"
            runtime_str = f"{runtime_val:.2f}s" if isinstance(runtime_val, (int, float)) else "N/A"
            
            report.append(f"{alg_name:<20} {solved:<8} {rate:.1f}%{'':<3} {cost_gap_str:<15} {runtime_str:<12}")
        
        report.append("-" * 60)
        
        # Best performing algorithm
        # Best algorithm by lowest avg_cost_gap among those that have it
        candidates = [(name, s) for name, s in comparison_results['summary'].items() if isinstance(s.get('avg_cost_gap'), (int, float))]
        if candidates:
            best_alg = min(candidates, key=lambda x: x[1]['avg_cost_gap'])
            report.append(f"\nBest Algorithm: {best_alg[0]}")
            report.append(f"Average Cost Gap: {best_alg[1]['avg_cost_gap']:.2f}%")
        else:
            report.append("\nBest Algorithm: N/A")
            report.append("Average Cost Gap: N/A")
        
        report.append("")
        report.append("NOTE: This evaluation uses the PDPTW dataset from:")
        report.append("Carlo S. Sartori and Luciana S. Buriol (2020)")
        report.append("\"A Study on the Pickup and Delivery Problem with Time Windows:")
        report.append("Matheuristics and New Instances\", Computers & Operations Research")
        
        return "\n".join(report)


def run_benchmark_evaluation():
    """Run benchmark evaluation on sample instances"""
    
    # Find available instance files (you need to download them first)
    instances_dir = "../instances"
    available_instances = []
    
    if os.path.exists(instances_dir):
        for filename in os.listdir(instances_dir):
            if filename.endswith('.txt') and filename != 'README.txt' and filename != 'how_to_read.txt':
                available_instances.append(os.path.join(instances_dir, filename))
    
    if not available_instances:
        print("Warning: No instance files found in ../instances/")
        print("Please download the instance files from Mendeley Data first:")
        print("https://data.mendeley.com/datasets/wr2ct4r22f/2")
        return
    
    # Select a small subset for demonstration
    test_instances = available_instances[:5]  # Test on first 5 instances
    
    # Define algorithms to test
    algorithms = [
        ("Greedy", GreedyInsertion),
        ("NearestNeighbor", NearestNeighbor)
    ]
    
    # Run evaluation
    evaluator = PDPTWBenchmarkEvaluator()
    results = evaluator.compare_algorithms(algorithms, test_instances)
    
    # Save and display results
    evaluator.save_results(results, "benchmark_results.json")
    
    report = evaluator.create_summary_report(results)
    print("\n" + report)
    
    # Save report
    with open("benchmark_report.txt", 'w') as f:
        f.write(report)


if __name__ == "__main__":
    run_benchmark_evaluation()
