import pandas as pd
from radon.metrics import mi_visit, h_visit
from radon.complexity import cc_visit
from radon.raw import analyze
import sys

# --- Configuration ---
INPUT_FILE = "lab2_dataset.csv"
OUTPUT_FILE = "lab3_structural_metrics.csv"

def get_metrics(code):
    """
    Calculates MI, CC, and LOC for a given code string.
    Returns tuple: (MI, CC, LOC)
    """
    if not isinstance(code, str) or not code.strip():
        return 0, 0, 0

    try:
        # 1. Maintainability Index (MI)
        mi = mi_visit(code, multi=True)
        
        # 2. Cyclomatic Complexity (CC)
        # cc_visit returns a list of blocks (functions/classes). 
        # We sum the complexity of all blocks + 1 for the file itself.
        blocks = cc_visit(code)
        cc = sum([block.complexity for block in blocks]) + 1
        
        # 3. Lines of Code (LOC) - distinct from SLOC or LLOC
        raw_metrics = analyze(code)
        loc = raw_metrics.loc
        
        return round(mi, 2), cc, loc
    except Exception as e:
        # If syntax error (e.g., partial code), return 0
        return 0, 0, 0

def main():
    print("Loading dataset...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found. Please complete Step 2.")
        return

    print(f"Calculating metrics for {len(df)} rows. This may take a moment...")

    # Lists to store new columns
    mi_changes = []
    cc_changes = []
    loc_changes = []

    for index, row in df.iterrows():
        # Get Source Code
        # Adjust these column names if they are different in your CSV
        code_before = row.get('Source_Code_Before', '')
        code_after = row.get('Source_Code_Current', '')

        # Calculate Metrics Before
        mi_b, cc_b, loc_b = get_metrics(code_before)

        # Calculate Metrics After
        mi_a, cc_a, loc_a = get_metrics(code_after)

        # Calculate Change (After - Before) or just the After value 
        # The assignment asks for "Change Magnitude", usually implies After - Before 
        # OR comparing Before vs After. 
        # Let's store the 'Change' (Delta) as requested in Lab Activity (f) headers
        
        mi_change = mi_a - mi_b
        cc_change = cc_a - cc_b
        loc_change = loc_a - loc_b

        mi_changes.append(round(mi_change, 2))
        cc_changes.append(cc_change)
        loc_changes.append(loc_change)

    # Add new columns to DataFrame
    df['MI_Change'] = mi_changes
    df['CC_Change'] = cc_changes
    df['LOC_Change'] = loc_changes

    # Save to new CSV
    df.to_csv(OUTPUT_FILE, index=False)
    print("-" * 30)
    print("SUCCESS!")
    print(f"Structural metrics calculated. Saved to: {OUTPUT_FILE}")
    print("-" * 30)

if __name__ == "__main__":
    main()
