import pandas as pd
import glob
import re

def standardize_columns(df, source):
    """Standardizes column names across different annotation reports."""
    column_mapping = {
        "File": "Module",
        "Variable/Function": "Function",
        "Type Hint": "Function_Return_Type",
        "Filename": "Function_Arguments",
        "Inferred Type": "Function_Argument_Type"
    }
    df = df.rename(columns=column_mapping)
    df["Annotator_Type"] = source
    return df

def parse_righttyper_output(file_path):
    """Parses RightTyper output file and extracts function annotations."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    modules = re.findall(r"(/home/training/RightTyper/[^:]+):", content)
    function_matches = re.findall(r"- def (\w+)\((.*?)\) -> (.+?):", content)
    
    data = []
    for match in function_matches:
        func, args, return_type = match
        module = modules[0] if modules else "Unknown"
        
        # Extract argument types properly
        arg_types = []
        for arg in args.split(','):
            arg_parts = arg.strip().split(':')
            if len(arg_parts) == 2:
                arg_types.append(arg_parts[1].strip())
        
        formatted_args = ", ".join(arg_types) if arg_types else "None"
        
        data.append({
            "Module": module,
            "Function": func,
            "Function_Arguments": args if args else "None",
            "Function_Argument_Type": formatted_args,
            "Function_Return_Type": return_type.strip(),
            "Annotator_Type": "RightTyper",
            "Variable Name": "",
            "Variable Type": ""
        })
    
    return pd.DataFrame(data)

def merge_reports():
    """Merges all annotation reports into final_annotation_report.csv with fixed formatting."""
    ast_files = glob.glob('*_AST_report.csv')
    variable_files = glob.glob('variable_annotation_report.csv')
    righttyper_file = '/home/training/Final_Annotator/RightTyper/righttyper.out'

    final_df = pd.DataFrame(columns=[
        "SL_No", "Module", "Function", "Function_Return_Type",
        "Function_Arguments", "Function_Argument_Type", "Annotator_Type",
        "Variable Name", "Variable Type"
    ])

    index = 1

    for file in ast_files:
        try:
            df = pd.read_csv(file)
            df = standardize_columns(df, "AST")
            df.insert(0, "SL_No", range(index, index + len(df)))
            final_df = pd.concat([final_df, df], ignore_index=True)
            index += len(df)
        except Exception as e:
            print(f"Error processing {file}: {e}")

    for file in variable_files:
        try:
            df = pd.read_csv(file)
            df = standardize_columns(df, "var_annotator")
            df.insert(0, "SL_No", range(index, index + len(df)))
            final_df = pd.concat([final_df, df], ignore_index=True)
            index += len(df)
        except Exception as e:
            print(f"Error processing {file}: {e}")

    try:
        df_righttyper = parse_righttyper_output(righttyper_file)
        df_righttyper.insert(0, "SL_No", range(index, index + len(df_righttyper)))
        final_df = pd.concat([final_df, df_righttyper], ignore_index=True)
        index += len(df_righttyper)
    except Exception as e:
        print(f"Error processing RightTyper output: {e}")

    final_df.to_csv("final_annotation_report.csv", index=False)
    print("✅ Final annotation report successfully updated!")

if __name__ == "__main__":
    merge_reports()
