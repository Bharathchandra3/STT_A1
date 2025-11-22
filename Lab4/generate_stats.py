import pandas as pd
import matplotlib.pyplot as plt
import os

INPUT_CSV = "diff_discrepancy_analysis.csv"
OUTPUT_IMAGE = "discrepancy_stats.png"

def main():
    if not os.path.exists(INPUT_CSV):
        print("Error: Input CSV not found!")
        return

    # 1. Load Data
    df = pd.read_csv(INPUT_CSV)
    
    # 2. Filter for only Mismatches (Discrepancy == Yes)
    mismatches = df[df["Discrepancy"] == "Yes"]
    
    # 3. Calculate Counts for specific categories
    # We ensure these keys exist even if count is 0
    categories = ["Source Code", "Test Code", "README", "LICENSE"]
    stats = {cat: 0 for cat in categories}
    
    # Count them up
    for file_type in mismatches["File_Type"]:
        if file_type in stats:
            stats[file_type] += 1
        else:
            # Handle "Other" or unexpected types if necessary
            pass

    # Print Text Stats for your Report
    print("-" * 30)
    print("FINAL DATASET STATISTICS")
    print("-" * 30)
    print(f"Total Files Analyzed: {len(df)}")
    print(f"Total Discrepancies Found: {len(mismatches)}")
    print("-" * 30)
    print("Mismatches by File Type:")
    for cat, count in stats.items():
        print(f"  - {cat}: {count}")
    print("-" * 30)

    # 4. Generate Plot
    plt.figure(figsize=(10, 6))
    bars = plt.bar(stats.keys(), stats.values(), color=['blue', 'orange', 'green', 'red'])
    
    plt.title("Diff Algorithm Discrepancies (Myers vs Histogram)", fontsize=14)
    plt.xlabel("File Artifact Type", fontsize=12)
    plt.ylabel("Number of Mismatches", fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add numbers on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                 f'{int(height)}',
                 ha='center', va='bottom')

    # Save
    plt.savefig(OUTPUT_IMAGE)
    print(f"Plot saved to {OUTPUT_IMAGE}")

if __name__ == "__main__":
    main()
