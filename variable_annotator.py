import ast
import os
import runpy
import csv

def analyze_python_file(file_path):
    class VariableTypeExtractor(ast.NodeVisitor):
        def __init__(self):
            self.function_variables = {}

        def visit_FunctionDef(self, node):
            func_name = node.name
            self.function_variables[func_name] = {}
            
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            var_type = self.infer_type(stmt.value)
                            self.function_variables[func_name][var_name] = var_type
            
            self.generic_visit(node)
        
        def infer_type(self, node):
            if isinstance(node, ast.Constant):
                return type(node.value).__name__
            elif isinstance(node, ast.List):
                return "list"
            elif isinstance(node, ast.Dict):
                return "dict"
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id == "input":
                        return "str"
                    elif node.func.id == "int":
                        return "int"
            return "Unknown"
    
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    
    extractor = VariableTypeExtractor()
    extractor.visit(tree)
    return extractor.function_variables

def generate_variable_report(files):
    variable_data = []
    for file in files:
        module_name = os.path.basename(file).replace(".py", "")
        function_vars = analyze_python_file(file)
        
        for func, vars in function_vars.items():
            for var_name, var_type in vars.items():
                variable_data.append([module_name, func, var_name, var_type])
    
    return variable_data
