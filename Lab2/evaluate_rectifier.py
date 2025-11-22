import pandas as pd
import re

# --- Configuration ---
INPUT_CSV = "diff_analysis.csv"
OUTPUT_CSV = "final_evaluation.csv"
SIMILARITY_THRESHOLD = 0.2  # If similarity is below 20%, we say the Dev message was bad.

def get_words(text):
    """Converts text to a set of lowercase words."""
    if not isinstance(text, str): return set()
    # Remove special characters and split
    text = re.sub(r'[^\w\s]', '', text) 
    return set(text.lower().split())

def jaccard_similarity(text1, text2):
    """Calculates word overlap between two texts (0.0 to 1.0)."""
    set1 = get_words(text1)
    set2 = get_words(text2)
    
    if len(set1) == 0 or len(set2) == 0:
        return 0.0
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union

def main():
    try:
        df = pd.read_csv(INPUT_CSV)
    except FileNotFoundError:
        print("Error: diff_analysis.csv not found!")
        return

    print(f"Evaluating {len(df)} changes...")

    results = []
    
    # Counters for RQs
    dev_precise_count = 0
    llm_precise_count = 0
    rectified_count = 0

    for index, row in df.iterrows():
        dev_msg = str(row['Original_Message'])
        llm_msg = str(row['LLM_Rectified_Message'])
        diff_code = str(row['Diff'])

        # 1. Calculate Similarity (Dev vs LLM)
        score = jaccard_similarity(dev_msg, llm_msg)
        
        # 2. Define "Precise" for Developer (RQ1)
        # If Dev message is similar to our 'Gold Standard' (LLM), it's precise.
        is_dev_precise = score >= SIMILARITY_THRESHOLD
        if is_dev_precise:
            dev_precise_count += 1

        # 3. Define "Precise" for LLM (RQ2)
        # Does the LLM message actually mention words found in the code diff?
        # (e.g. function names, variable names)
        diff_words = get_words(diff_code)
        llm_words = get_words(llm_msg)
        # If LLM shares at least 1 meaningful word with the Diff code, we count it as relevant/precise
        overlap = len(llm_words.intersection(diff_words))
        is_llm_precise = overlap > 0 
        if is_llm_precise:
            llm_precise_count += 1

        # 4. Rectifier Logic (Activity e & RQ3)
        # If Dev was NOT precise, we Rectify (swap the message)
        if not is_dev_precise:
            final_message = llm_msg
            rectified_count += 1
            action = "Rectified"
        else:
            final_message = dev_msg
            action = "Kept Original"

        results.append({
            "Original": dev_msg,
            "LLM": llm_msg,
            "Similarity_Score": round(score, 2),
            "Action_Taken": action,
            "Final_Message": final_message
        })

    # Save detailed results
    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)

    # --- PRINT RESULTS FOR YOUR REPORT ---
    total = len(df)
    if total == 0: total = 1 # Avoid division by zero

    print("\n" + "="*40)
    print("       EVALUATION RESULTS (For Report)")
    print("="*40)
    print(f"Total Files Analyzed: {total}")
    print("-" * 40)
    
    # RQ1
    rq1_rate = (dev_precise_count / total) * 100
    print(f"RQ1 (Developer Precision): {rq1_rate:.1f}%")
    print(f"   -> Developers wrote precise messages in {dev_precise_count} cases.")

    # RQ2
    rq2_rate = (llm_precise_count / total) * 100
    print(f"RQ2 (LLM Precision):       {rq2_rate:.1f}%")
    print(f"   -> LLM generated code-relevant messages in {llm_precise_count} cases.")

    # RQ3
    rq3_rate = (rectified_count / total) * 100
    print(f"RQ3 (Rectifier Rate):      {rq3_rate:.1f}%")
    print(f"   -> The Rectifier had to fix the message in {rectified_count} cases.")
    print("="*40)
    print(f"Detailed results saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()

