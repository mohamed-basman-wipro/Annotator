import csv
import os
import glob
import re

# Define CSV headers
CSV_HEADERS = ["SL_No", "Module", "Function", "Function_Return_Type", "Function_Arguments", "Function_Argument_Type", "Annotator_Type"]

def parse_report(report_path, annotator_type):
    """Parses an annotator report and extracts relevant details."""
    results = []
    module_name = os.path.basename(report_path).replace("_AST_report.txt", "").replace("_conditional_runtime_annotation_report.txt", "").replace("righttyper.out", "")

    with open(report_path, "r") as file:
        for line in file:
            # Parsing for AST and Conditional Annotator Reports
            match_var = re.match(r"Variable '(.*?)' should have a type hint: (.*)", line.strip())
            match_func = re.match(r"Function '(.*?)' should have a return type hint.", line.strip())

            if match_var:
                var_name, var_type = match_var.groups()
                results.append({
                    "SL_No": len(results) + 1,
                    "Module": module_name,
                    "Function": var_name,
                    "Function_Return_Type": "Unknown",
                    "Function_Arguments": "N/A",
                    "Function_Argument_Type": var_type,
                    "Annotator_Type": annotator_type
                })
            elif match_func:
                func_name = match_func.group(1)
                results.append({
                    "SL_No": len(results) + 1,
                    "Module": module_name,
                    "Function": func_name,
                    "Function_Return_Type": "Unknown",
                    "Function_Arguments": "N/A",
                    "Function_Argument_Type": "Missing",
                    "Annotator_Type": annotator_type
                })
            else:
                # Parsing RightTyper Output
                match_rt = re.match(r"- def (\w+)\((.*?)\) -> (.*?):", line.strip())
                if match_rt:
                    func_name, args, return_type = match_rt.groups()
                    args_cleaned = re.sub(r"\s+", " ", args)  # Remove extra spaces
                    results.append({
                        "SL_No": len(results) + 1,
                        "Module": "task_manager" if "task_manager.py" in report_path else "cli",  # Assign correct module
                        "Function": func_name,
                        "Function_Return_Type": return_type,
                        "Function_Arguments": args_cleaned,
                        "Function_Argument_Type": "Explicit",
                        "Annotator_Type": "RightTyper"
                    })

    return results

def generate_csv(annotator_name, report_pattern, annotator_type):
    """Generates a CSV for a specific annotator."""
    report_files = glob.glob(report_pattern)
    all_data = []

    for report in report_files:
        all_data.extend(parse_report(report, annotator_type))

    if not all_data:
        print(f"No valid data found in {annotator_name} reports.")
        return

    csv_filename = f"{annotator_name}_report.csv"
    with open(csv_filename, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(all_data)

    print(f"CSV generated: {csv_filename}")

def merge_csvs(output_filename, csv_files):
    """Merges multiple CSV files into one final CSV, preferring the most detailed type information."""
    all_data = {}
    
    for csv_file in csv_files:
        if not os.path.exists(csv_file):
            continue

        with open(csv_file, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                key = (row["Module"], row["Function"])
                
                if key not in all_data:
                    all_data[key] = row
                else:
                    existing_entry = all_data[key]

                    # Prioritize RightTyper > Conditional > AST
                    if existing_entry["Annotator_Type"] == "AST" and row["Annotator_Type"] in ["Conditional", "RightTyper"]:
                        all_data[key] = row
                    elif existing_entry["Annotator_Type"] == "Conditional" and row["Annotator_Type"] == "RightTyper":
                        all_data[key] = row

                    # If RightTyper provided argument types, update them
                    if row["Annotator_Type"] == "RightTyper" and row["Function_Arguments"] != "N/A":
                        all_data[key]["Function_Arguments"] = row["Function_Arguments"]
                        all_data[key]["Function_Argument_Type"] = "Explicit"

    with open(output_filename, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(all_data.values())
    
    print(f"Final merged CSV: {output_filename}")

if __name__ == "__main__":
    generate_csv("AST", "*_AST_report.txt", "AST")
    generate_csv("Conditional", "*_conditional_runtime_annotation_report.txt", "Conditional")
    generate_csv("RightTyper", "RightTyper/righttyper.out", "RightTyper")

    merge_csvs("final_annotation_report.csv", ["AST_report.csv", "Conditional_report.csv", "RightTyper_report.csv"])
