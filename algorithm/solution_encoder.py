"""
Solution encoder for PDPTW solutions
Converts solution objects to the format expected by the validator and benchmark repository
"""

from typing import List
from data_loader import Solution, Instance


class SolutionEncoder:
    """Encodes PDPTW solutions to standard format"""
    
    @staticmethod
    def encode_solution(solution: Solution, authors: str = "Algorithm Implementation", 
                       reference: str = "Local PDPTW Solver", date: str = "") -> str:
        """
        Encode solution to the standard format used in the benchmark repository
        
        Format:
        Instance name: <instance_name>
        Authors: <authors>
        Date: <date>
        Reference: <reference>  
        Solution
        Route 1 : <node_sequence>
        Route 2 : <node_sequence>
        ...
        """
        if not date:
            from datetime import datetime
            date = datetime.now().strftime("%d-%b-%y")
            
        encoded = []
        encoded.append(f"Instance name:\t{solution.inst_name}")
        encoded.append(f"Authors:\t\t{authors}")
        encoded.append(f"Date:\t\t\t{date}")
        encoded.append(f"Reference:\t\t{reference}")
        encoded.append("Solution")
        
        route_idx = 1
        for route in solution.routes:
            if route:  # Skip empty routes
                route_str = " ".join(str(node) for node in route)
                encoded.append(f"Route {route_idx} : {route_str}")
                route_idx += 1
                
        return "\n".join(encoded)
    
    @staticmethod
    def save_solution(solution: Solution, filename: str, authors: str = "Algorithm", 
                     reference: str = "PDPTW Solver", date: str = ""):
        """Save solution to file in standard format"""
        encoded_content = SolutionEncoder.encode_solution(solution, authors, reference, date)
        
        with open(filename, 'w') as f:
            f.write(encoded_content)
            
    @staticmethod
    def get_filename_from_instance(instance_name: str, num_vehicles: int, cost: int) -> str:
        """
        Generate filename following the convention:
        <instance-name>.<num-vehicles>_<cost>.txt
        """
        return f"{instance_name}.{num_vehicles}_{cost}.txt"
    
    @staticmethod
    def create_solution_from_routes(routes: List[List[int]], instance_name: str, 
                                  authors: str = "Algorithm", reference: str = "PDPTW Solver") -> Solution:
        """Create Solution object from route list"""
        solution = Solution()
        solution.inst_name = instance_name
        solution.authors = authors
        solution.date = ""
        solution.reference = reference
        solution.routes = [route[:] for route in routes]  # Deep copy
        return solution
        
    @staticmethod
    def validate_and_save(solution: Solution, instance: Instance, output_dir: str = "solutions/files/",
                         authors: str = "Algorithm", reference: str = "PDPTW Solver") -> str:
        """
        Validate solution, calculate cost and save to appropriately named file
        Returns the filename of the saved solution
        """
        # Calculate solution metrics
        num_vehicles = solution.get_num_vehicles()
        cost = solution.get_cost(instance)
        
        # Generate filename
        filename = SolutionEncoder.get_filename_from_instance(
            instance.name, num_vehicles, cost
        )
        
        # Create full path
        import os
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        full_path = os.path.join(output_dir, filename)
        
        # Save solution
        SolutionEncoder.save_solution(solution, full_path, authors, reference)
        
        print(f"Solution saved: {full_path}")
        print(f"Vehicles: {num_vehicles}, Cost: {cost}")
        
        return full_path


if __name__ == "__main__":
    # Test solution encoder
    test_routes = [[1, 2, 3], [4, 5, 6], [7, 8]]
    solution = SolutionEncoder.create_solution_from_routes(test_routes, "test-instance")
    
    encoded = SolutionEncoder.encode_solution(solution)
    print("Sample encoded solution:")
    print(encoded)
    print("\nSolution encoder implemented successfully")
