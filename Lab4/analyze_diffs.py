import pandas as pd
from pydriller import Repository
import subprocess
import os

# --- Configuration ---
REPOS = ["repositories/httpie", "repositories/rich", "repositories/tqdm"]
OUTPUT_CSV = "diff_discrepancy_analysis.csv"
COMMIT_LIMIT = 100  # Limit per repo to save time

def clean_diff(diff_text):
    """
    Removes whitespace and blank lines to ensure fair comparison
    as per assignment instructions.
    """
    if not diff_text:
        return ""
    lines = diff_text.split('\n')
    # Filter out blank lines and strip whitespace from remaining lines
    cleaned = [line.strip() for line in lines if line.strip()]
    return "\n".join(cleaned)

def get_raw_diff(repo_path, algorithm, parent_hash, commit_hash, file_path):
    """
    Runs git diff with a specific algorithm (myers or histogram).
    """
    cmd = [
        "git", "diff",
        f"--diff-algorithm={algorithm}",
        parent_hash,
        commit_hash,
        "--", file_path
    ]
    try:
        result = subprocess.run(
            cmd, cwd=repo_path, capture_output=True, text=True, errors="replace"
        )
        return result.stdout
    except Exception as e:
        return ""

def categorize_file(filepath):
    """Categorizes files for the final report stats."""
    fp = filepath.lower()
    if "test" in fp:
        return "Test Code"
    elif "readme" in fp:
        return "README"
    elif "license" in fp:
        return "LICENSE"
    elif fp.endswith(('.py', '.c', '.cpp', '.java', '.js', '.ts', '.go', '.rs')):
        return "Source Code"
    else:
        return "Other"

def main():
    data = []
    
    for repo_path in REPOS:
        print(f"Scanning {repo_path}...")
        
        # Traverse commits (reversed to get recent ones first if we wanted, 
        # but pydriller goes chronological by default. We limit to first 100 found).
        count = 0
        for commit in Repository(repo_path).traverse_commits():
            if count >= COMMIT_LIMIT:
                break
            
            # Skip the first commit as it has no parent
            if not commit.parents:
                continue
                
            parent_hash = commit.parents[0]
            
            for mod in commit.modified_files:
                # We only care about Modified files (not new/deleted) for diff comparison
                if mod.change_type.name != 'MODIFY':
                    continue
                
                # 1. Get Diff using Myers (Default)
                diff_myers = get_raw_diff(repo_path, "myers", parent_hash, commit.hash, mod.filename)
                
                # 2. Get Diff using Histogram
                diff_hist = get_raw_diff(repo_path, "histogram", parent_hash, commit.hash, mod.filename)
                
                # 3. Compare (Ignoring whitespace/blanks)
                clean_myers = clean_diff(diff_myers)
                clean_hist = clean_diff(diff_hist)
                
                is_discrepancy = "No" if clean_myers == clean_hist else "Yes"
                
                # Store data
                data.append({
                    "Repository": repo_path,
                    "File_Path": mod.new_path,
                    "File_Type": categorize_file(mod.new_path or mod.old_path),
                    "Commit_SHA": commit.hash,
                    "Parent_SHA": parent_hash,
                    "Message": commit.msg.split('\n')[0], # Just the title
                    "Diff_Myers": diff_myers[:500], # Store snippet to save space
                    "Diff_Hist": diff_hist[:500],
                    "Discrepancy": is_discrepancy
                })
            
            count += 1
            if count % 10 == 0:
                print(f"  Processed {count} commits...")

    # Save Results
    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_CSV, index=False)
    print("-" * 30)
    print("SUCCESS!")
    print(f"Analysis complete. Found {len(data)} file modifications.")
    print(f"Results saved to {OUTPUT_CSV}")
    print("-" * 30)

if __name__ == "__main__":
    main()
