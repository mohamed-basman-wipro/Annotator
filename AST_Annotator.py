import ast
import os
import sys
from typing import List, Dict

def infer_type(node):
    """Infers type based on AST nodes."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, int):
            return 'int'
        elif isinstance(node.value, float):
            return 'float'
        elif isinstance(node.value, str):
            return 'str'
        elif isinstance(node.value, bool):
            return 'bool'
        else:
            return 'Some type needed'
    elif isinstance(node, ast.List):
        element_types = set(infer_type(e) for e in node.elts)
        return f"List[{element_types.pop()}]" if len(element_types) == 1 else "List[Some type needed]"
    elif isinstance(node, ast.Dict):
        key_types = set(infer_type(k) for k in node.keys)
        value_types = set(infer_type(v) for v in node.values)
        key_type = key_types.pop() if len(key_types) == 1 else "Some type needed"
        value_type = value_types.pop() if len(value_types) == 1 else "Some type needed"
        return f"Dict[{key_type}, {value_type}]"
    return 'Some type needed'

def analyze_code_for_types(file_path):
    """Analyzes Python file for type hints."""
    try:
        with open(file_path, 'r') as file:
            code = file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

    tree = ast.parse(code)
    annotations = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    type_hint = infer_type(node.value)
                    annotations.append(f"Variable '{target.id}' should have a type hint: {type_hint}.")
        elif isinstance(node, ast.FunctionDef):
            for arg in node.args.args:
                if not arg.annotation:
                    annotations.append(f"Function parameter '{arg.arg}' in function '{node.name}' should have an explicit type hint.")
            if not node.returns:
                annotations.append(f"Function '{node.name}' should have a return type hint.")
        elif isinstance(node, ast.Call):
            for arg in node.args:
                if isinstance(arg, ast.Name):
                    annotations.append(f"Argument '{arg.id}' in function call should have an explicit type hint.")
    return annotations

def generate_report(file_path, annotations):
    """Generates a report from analysis."""
    report_file = file_path.replace('.py', '_AST_report.txt')
    try:
        with open(report_file, 'w') as report:
            for annotation in annotations:
                report.write(annotation + '\n')
        print(f"Annotation report generated at {report_file}")
    except Exception as e:
        print(f"Error generating report: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 AST_Annotator.py <file1.py> <file2.py> ...")
        sys.exit(1)

    for file_path in sys.argv[1:]:
        if os.path.exists(file_path):
            annotations = analyze_code_for_types(file_path)
            if annotations:
                generate_report(file_path, annotations)
            else:
                print(f"No issues found in {file_path}.")
        else:
            print(f"File not found: {file_path}")
