import csv
from pathlib import Path
import pandas as pd

# Input file paths
ast_files = [
    "cli_AST_report.txt",
    "task_manager_AST_report.txt"
]

conditional_files = [
    "cli_conditional_runtime_annotation_report.txt",
    "task_manager_conditional_runtime_annotation_report.txt"
]

variable_file = "variable_annotation_report.txt"
righttyper_path = "/home/training/Final_Annotator/RightTyper/righttyper.out"
output_csv = "final_annotation_report.csv"

# Prepare data container and serial number
final_data = []
sl_no = 1

# Helper to extract clean module name
def get_module_name(file, suffix):
    return Path(file).name.replace(suffix, ".py")

# ------------------ AST ------------------
for file in ast_files:
    module = get_module_name(file, "_AST_report.txt")
    with open(file) as f:
        for line in f:
            line = line.strip()
            if line:
                final_data.append([
                    sl_no, module, line, "Unknown", "", "", "AST", "", ""
                ])
                sl_no += 1

# ------------------ Conditional ------------------
for file in conditional_files:
    module = get_module_name(file, "_conditional_runtime_annotation_report.txt")
    with open(file) as f:
        for line in f:
            line = line.strip()
            if line:
                final_data.append([
                    sl_no, module, line, "Unknown", "", "", "Conditional", "", ""
                ])
                sl_no += 1

# ------------------ Variable Annotator ------------------
if Path(variable_file).exists():
    with open(variable_file) as f:
        current_func = ""
        module = ""
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.endswith(".py:"):
                module = Path(line[:-1]).name
            elif line.startswith("Function:"):
                current_func = line.split("Function:")[1].strip()
            elif ":" in line:
                var_name, var_type = map(str.strip, line.split(":", 1))
                final_data.append([
                    sl_no, module, current_func, "", "", "", "var_annotator", var_name, var_type
                ])
                sl_no += 1

# ------------------ RightTyper ------------------
if Path(righttyper_path).exists():
    with open(righttyper_path) as f:
        lines = f.readlines()

    current_module = ""
    for line in lines:
        line = line.strip()
        if line.endswith(".py:"):
            current_module = Path(line[:-1]).name
        elif line.startswith("+ def "):
            func_sig = line[6:]
            if "->" in func_sig:
                func_part, return_type = func_sig.split("->")
                func_name = func_part.split("(")[0].strip()
                args_str = func_part.split("(", 1)[1].rstrip(")")
                args = [arg.strip() for arg in args_str.split(",") if arg.strip()]
                return_type = return_type.strip()

                for arg in args:
                    if ":" in arg:
                        arg_name, arg_type = map(str.strip, arg.split(":", 1))
                        final_data.append([
                            sl_no, current_module, func_name, return_type,
                            arg_name, arg_type, "RightTyper", "", ""
                        ])
                        sl_no += 1

# ------------------ Final CSV Output ------------------
df = pd.DataFrame(final_data, columns=[
    "SL_No", "Module", "Function", "Function_Return_Type",
    "Function_Arguments", "Function_Argument_Type", "Annotator_Type",
    "Variable_Name", "Variable_Type"
])
df.to_csv(output_csv, index=False)
print(f"✅ Final annotation report generated at: {output_csv}")
