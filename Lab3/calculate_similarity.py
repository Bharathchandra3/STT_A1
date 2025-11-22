import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
import sacrebleu
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# --- Configuration ---
INPUT_FILE = "lab3_structural_metrics.csv"
OUTPUT_FILE = "lab3_final_dataset.csv"
MODEL_NAME = "microsoft/codebert-base"

# Thresholds (from Lab Assignment PDF)
SEMANTIC_THRESHOLD = 0.80
TOKEN_THRESHOLD = 0.75

def get_semantic_similarity(code1, code2, tokenizer, model):
    """Calculates Cosine Similarity between CodeBERT embeddings."""
    if not isinstance(code1, str) or not isinstance(code2, str):
        return 0.0
    if not code1.strip() or not code2.strip():
        return 0.0

    # Tokenize and truncate to 512 tokens (model limit)
    inputs1 = tokenizer(code1, return_tensors="pt", truncation=True, max_length=512)
    inputs2 = tokenizer(code2, return_tensors="pt", truncation=True, max_length=512)

    with torch.no_grad():
        # Get embeddings (use the 'pooler_output' or mean of last hidden state)
        # Here we use the CLS token representation (first token)
        emb1 = model(**inputs1).last_hidden_state[:, 0, :]
        emb2 = model(**inputs2).last_hidden_state[:, 0, :]

    # Calculate Cosine Similarity
    similarity = cosine_similarity(emb1, emb2)[0][0]
    return float(similarity)

def get_token_similarity(code1, code2):
    """Calculates BLEU score (0 to 1 scale)."""
    if not isinstance(code1, str) or not isinstance(code2, str):
        return 0.0
    if not code1.strip() or not code2.strip():
        return 0.0

    # sacrebleu expects lists of strings
    # score returns 0-100, we normalize to 0-1
    score = sacrebleu.corpus_bleu([code1], [[code2]]).score
    return score / 100.0

def classify_fix(similarity, threshold):
    """Classifies as Minor Fix (High Sim) or Major Fix (Low Sim)."""
    if similarity >= threshold:
        return "Minor Fix"
    else:
        return "Major Fix"

def main():
    print("1. Loading dataset...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found. Did Step 4 finish?")
        return

    print(f"2. Loading CodeBERT model ({MODEL_NAME})...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModel.from_pretrained(MODEL_NAME)
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    print(f"3. Calculating similarities for {len(df)} rows...")
    
    sem_sims = []
    tok_sims = []
    
    # Limit rows if testing, remove slice [:5] to run full dataset
    # processing_df = df.head(5) if you want to test first
    
    count = 0
    for index, row in df.iterrows():
        code_b = row.get('Source_Code_Before', '')
        code_a = row.get('Source_Code_Current', '')

        # Semantic (CodeBERT)
        sem = get_semantic_similarity(code_b, code_a, tokenizer, model)
        sem_sims.append(sem)

        # Token (BLEU)
        tok = get_token_similarity(code_a, code_b) # BLEU compares 'hypothesis' against 'reference'
        tok_sims.append(tok)
        
        count += 1
        if count % 10 == 0:
            print(f"   Processed {count} / {len(df)} rows...")

    df['Semantic_Similarity'] = sem_sims
    df['Token_Similarity'] = tok_sims

    print("4. Classifying fixes...")
    # Apply Thresholds
    df['Semantic_Class'] = df['Semantic_Similarity'].apply(lambda x: classify_fix(x, SEMANTIC_THRESHOLD))
    df['Token_Class'] = df['Token_Similarity'].apply(lambda x: classify_fix(x, TOKEN_THRESHOLD))

    # Check Agreement
    df['Classes_Agree'] = np.where(df['Semantic_Class'] == df['Token_Class'], 'YES', 'NO')

    # Save Final
    df.to_csv(OUTPUT_FILE, index=False)
    print("-" * 30)
    print("SUCCESS!")
    print(f"Final dataset with Analysis saved to: {OUTPUT_FILE}")
    print("-" * 30)

if __name__ == "__main__":
    main()
