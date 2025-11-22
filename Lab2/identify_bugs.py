from pydriller import Repository
import pandas as pd
import os

# --- Configuration ---
REPO_PATH = "apprise"  # The folder where you cloned flask
KEYWORDS = ["fix", "bug", "issue", "resolve", "error", "patch"]
OUTPUT_FILE = "bug_fixing_commits.csv"

def is_bug_fix(message):
    """Check if the commit message contains any bug keywords."""
    msg_lower = message.lower()
    for word in KEYWORDS:
        if word in msg_lower:
            return True
    return False

def main():
    print(f"Scanning repository: {REPO_PATH}...")
    
    data = []
    
    # pydriller iterates through every commit in history
    # only_in_branch='main' ensures we look at the main history
    for commit in Repository(REPO_PATH).traverse_commits():
        
        # Check our criteria
        if is_bug_fix(commit.msg):
            
            # Get list of modified filenames
            file_list = [f.filename for f in commit.modified_files]
            
            # Store the info required by the assignment
            commit_info = {
                "Hash": commit.hash,
                "Message": commit.msg,
                "Parents": [p for p in commit.parents], # List of parent hashes
                "Is_Merge": commit.merge,
                "Modified_Files": file_list
            }
            data.append(commit_info)

    # Save to CSV using Pandas
    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"Success! Found {len(data)} bug-fixing commits.")
    print(f"Saved results to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

