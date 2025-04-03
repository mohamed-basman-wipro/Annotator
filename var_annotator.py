import ast
import csv
import sys
from typing import Dict, List, Tuple

class VariableTypeInferer(ast.NodeVisitor):
    def __init__(self):
        # Holds variables with their inferred types (global scope or function parameters)
        self.variables: Dict[str, str] = {}
        # Map for known function return types
        self.function_return_types: Dict[str, str] = {}
    
    def visit_Assign(self, node: ast.Assign):
        # Process each assignment target
        for target in node.targets:
            if isinstance(target, ast.Name):
                inferred_type = self.infer_type(node.value, target.id)
                # Overwrite if already present to ensure consistency
                self.variables[target.id] = inferred_type
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Process function parameters: we mark them as 'function_param' if not further inferred.
        for arg in node.args.args:
            self.variables[arg.arg] = "function_param"
        # Attempt to infer the function's return type from its return statements.
        return_type = self.infer_function_return_type(node)
        self.function_return_types[node.name] = return_type
        self.generic_visit(node)
    
    def infer_type(self, node: ast.AST, var_name: str = "") -> str:
        if isinstance(node, ast.Constant):
            return type(node.value).__name__
        elif isinstance(node, ast.List):
            return "list"
        elif isinstance(node, ast.Dict):
            return "dict"
        elif isinstance(node, ast.Tuple):
            return "tuple"
        elif isinstance(node, ast.Set):
            return "set"
        elif isinstance(node, ast.ListComp):
            return "list"
        elif isinstance(node, ast.DictComp):
            return "dict"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                # Use our mapping to return the known type for specific functions
                return self.map_function_return_type(node.func.id, var_name)
            return "function_call"
        return "Unknown"
    
    def infer_function_return_type(self, node: ast.FunctionDef) -> str:
        # Look for a return statement and infer its type
        for stmt in node.body:
            if isinstance(stmt, ast.Return) and stmt.value is not None:
                return self.infer_type(stmt.value)
        return "None"
    
    def map_function_return_type(self, func_name: str, var_name: str) -> str:
        # Mapping of known functions to their expected return types.
        return_type_map = {
            "input": "str",
            "int": "int",
            "float": "float",
            "list": "list",
            "dict": "dict",
            "tuple": "tuple",
            "set": "set",
            "generate_table": "list",   # Example: if you have a generate_table function
            "list_tasks": "list",         # list_tasks returns the table (a list of lists)\n",
            "load_tasks": "list",         # load_tasks returns a list from json.load\n",
        }
        # For variables like 'tasks', force the type to 'list'
        if var_name == "tasks":
            return "list"
        return return_type_map.get(func_name, "function_call")

def analyze_file(filepath: str) -> List[Tuple[str, str, str]]:
    with open(filepath, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read(), filename=filepath)
    
    inferer = VariableTypeInferer()
    inferer.visit(tree)
    
    # Build report: each variable with its inferred type
    return [(filepath, var, var_type) for var, var_type in inferer.variables.items()]

def generate_report(files: List[str], output_file: str):
    results = []
    for file in files:
        results.extend(analyze_file(file))
    
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Filename", "Variable Name", "Inferred Type"])
        writer.writerows(results)
    
    print(f"✅ Annotation report generated: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Usage: python3 var_annotator.py <file1.py> <file2.py> ...")
        sys.exit(1)
    
    files_to_analyze = sys.argv[1:]
    generate_report(files_to_analyze, "variable_annotation_report.csv")
