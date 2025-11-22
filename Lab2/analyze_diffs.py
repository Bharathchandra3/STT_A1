import pandas as pd
from pydriller import Repository
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import os

# --- Configuration ---
REPO_PATH = "apprise"
INPUT_CSV = "bug_fixing_commits.csv"
OUTPUT_CSV = "diff_analysis.csv"
MODEL_NAME = "mamiksik/CommitPredictorT5" # The model specified in your assignment
LIMIT = 20  # Limit to 20 commits to save time on the VM

def main():
    # 1. Load the list of bug commits we found earlier
    if not os.path.exists(INPUT_CSV):
        print(f"Error: {INPUT_CSV} not found. Please run the previous step first.")
        return

    df = pd.read_csv(INPUT_CSV)
    # Get unique commit hashes
    all_hashes = df["Hash"].unique().tolist()
    
    # Limit the number of commits we process
    target_hashes = all_hashes[:LIMIT]
    print(f"Processing {len(target_hashes)} commits (Limit set to {LIMIT})...")

    # 2. Load the AI Model (LLM)
    print(f"Loading AI Model ({MODEL_NAME})... this may take a moment.")
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    results = []

    # 3. Mine the specific commits
    # pydriller can filter for specific commits using 'only_commits'
    for commit in Repository(REPO_PATH, only_commits=target_hashes).traverse_commits():
        
        print(f"Analyzing commit: {commit.hash[:7]}")
        
        for mod_file in commit.modified_files:
            # We mostly care about code files (e.g., Python), skip images/binaries
            if mod_file.filename.endswith('.py'):
                
                diff = mod_file.diff
                source_before = mod_file.source_code_before
                source_current = mod_file.source_code
                
                # 4. AI Inference: Generate message from Diff
                if diff:
                    # Prepare input for the AI
                    input_text = diff
                    inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
                    
                    # Generate output
                    with torch.no_grad():
                        outputs = model.generate(**inputs, max_length=50)
                    
                    rectified_msg = tokenizer.decode(outputs[0], skip_special_tokens=True)
                else:
                    rectified_msg = ""

                # Store data
                results.append({
                    "Hash": commit.hash,
                    "Original_Message": commit.msg,
                    "Filename": mod_file.filename,
                    "Source_Code_Before": source_before,
                    "Source_Code_Current": source_current,
                    "Diff": diff,
                    "LLM_Rectified_Message": rectified_msg
                })

    # 5. Save results
    output_df = pd.DataFrame(results)
    output_df.to_csv(OUTPUT_CSV, index=False)
    print(f"Done! Processed {len(output_df)} file changes.")
    print(f"Results saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
