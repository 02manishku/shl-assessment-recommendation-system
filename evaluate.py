"""
Evaluation Script for SHL Assessment Recommendation System
Calculates Mean Recall@10 on labeled test data.
"""

import pandas as pd
import logging
import argparse
from typing import List, Dict, Set
from dotenv import load_dotenv

from recommender import AssessmentRecommender

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_labeled_data(file_path: str) -> pd.DataFrame:
    """
    Load labeled test data from CSV file.
    
    Expected format:
    - Query: Job description or query text
    - Relevant_Assessment_URLs: Comma-separated list of relevant URLs
    
    Args:
        file_path: Path to labeled test data file
        
    Returns:
        DataFrame with queries and relevant URLs
    """
    logger.info(f"Loading labeled test data from {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} labeled test cases")
        
        # Find query column
        query_col = None
        for col in df.columns:
            if col.lower() in ['query', 'text', 'job_description', 'jd']:
                query_col = col
                break
        
        if query_col is None:
            query_col = df.columns[0]
            logger.warning(f"Query column not found, using first column: {query_col}")
        
        # Find relevant URLs column
        relevant_col = None
        for col in df.columns:
            if 'relevant' in col.lower() or 'gold' in col.lower() or 'url' in col.lower():
                relevant_col = col
                break
        
        if relevant_col is None:
            raise ValueError(
                "Relevant URLs column not found. Please ensure your CSV has a column "
                "named 'Relevant_Assessment_URLs' or similar."
            )
        
        # Standardize column names
        df = df.rename(columns={query_col: 'Query', relevant_col: 'Relevant_URLs'})
        
        return df[['Query', 'Relevant_URLs']]
    
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading labeled data: {e}")
        raise


def parse_relevant_urls(url_string: str) -> Set[str]:
    """
    Parse relevant URLs from string (comma-separated or space-separated).
    
    Args:
        url_string: String containing one or more URLs
        
    Returns:
        Set of URLs
    """
    if pd.isna(url_string) or not url_string:
        return set()
    
    # Split by common delimiters
    urls = []
    for delimiter in [',', ';', '|', '\n']:
        if delimiter in str(url_string):
            urls = [url.strip() for url in str(url_string).split(delimiter)]
            break
    
    if not urls:
        # Single URL
        urls = [str(url_string).strip()]
    
    # Clean URLs
    cleaned_urls = set()
    for url in urls:
        url = url.strip()
        if url and url.lower() not in ['nan', 'none', '']:
            cleaned_urls.add(url)
    
    return cleaned_urls


def calculate_recall_at_k(predicted_urls: List[str], relevant_urls: Set[str], k: int = 10) -> float:
    """
    Calculate Recall@K for a single query.
    
    Recall@K = (Number of relevant items in top K) / (Total relevant items)
    
    Args:
        predicted_urls: List of predicted URLs (in order)
        relevant_urls: Set of ground-truth relevant URLs
        k: Number of top results to consider
        
    Returns:
        Recall@K score (0.0 to 1.0)
    """
    if not relevant_urls:
        return 0.0
    
    # Get top K predictions
    top_k_predictions = set(predicted_urls[:k])
    
    # Count how many relevant URLs are in top K
    hits = len(top_k_predictions.intersection(relevant_urls))
    
    # Recall = hits / total relevant
    recall = hits / len(relevant_urls)
    
    return recall


def evaluate_system(labeled_data: pd.DataFrame, 
                    recommender: AssessmentRecommender,
                    k: int = 10) -> Dict:
    """
    Evaluate the recommendation system on labeled data.
    
    Args:
        labeled_data: DataFrame with queries and relevant URLs
        recommender: Initialized AssessmentRecommender instance
        k: Number of top results to evaluate (default: 10)
        
    Returns:
        Dictionary with evaluation metrics
    """
    logger.info(f"Starting evaluation on {len(labeled_data)} test cases with k={k}")
    
    recalls = []
    successful_queries = 0
    failed_queries = 0
    
    for idx, row in labeled_data.iterrows():
        query = str(row['Query'])
        relevant_urls = parse_relevant_urls(row['Relevant_URLs'])
        
        if not query or query == 'nan':
            logger.warning(f"Empty query at row {idx}, skipping")
            failed_queries += 1
            continue
        
        if not relevant_urls:
            logger.warning(f"No relevant URLs for query at row {idx}, skipping")
            failed_queries += 1
            continue
        
        try:
            # Get recommendations
            recommendations = recommender.recommend(query, top_k=k, use_reranking=True, balance_types=True)
            
            # Extract predicted URLs
            predicted_urls = [
                rec.get('URL', rec.get('url', ''))
                for rec in recommendations
            ]
            
            # Calculate recall@k
            recall = calculate_recall_at_k(predicted_urls, relevant_urls, k)
            recalls.append(recall)
            successful_queries += 1
            
            logger.debug(f"Query {idx+1}: Recall@{k} = {recall:.4f}")
            
        except Exception as e:
            logger.error(f"Error processing query {idx+1}: {e}")
            failed_queries += 1
            recalls.append(0.0)
    
    # Calculate mean recall
    mean_recall = sum(recalls) / len(recalls) if recalls else 0.0
    
    results = {
        'mean_recall_at_k': mean_recall,
        'k': k,
        'total_queries': len(labeled_data),
        'successful_queries': successful_queries,
        'failed_queries': failed_queries,
        'recalls': recalls
    }
    
    return results


def main():
    """Main evaluation function."""
    parser = argparse.ArgumentParser(description='Evaluate SHL Assessment Recommendation System')
    parser.add_argument('--gold', type=str, default='labeled_test.csv',
                       help='Path to labeled test data (CSV with Query and Relevant_URLs)')
    parser.add_argument('--k', type=int, default=10,
                       help='K value for Recall@K metric (default: 10)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("SHL Assessment Recommendation System - Evaluation")
    print("=" * 60)
    
    try:
        # Load labeled test data
        labeled_data = load_labeled_data(args.gold)
        
        # Initialize recommender
        logger.info("Initializing recommender...")
        recommender = AssessmentRecommender()
        recommender.load_index()
        
        # Run evaluation
        results = evaluate_system(labeled_data, recommender, k=args.k)
        
        # Print results
        print(f"\n{'='*60}")
        print("EVALUATION RESULTS")
        print(f"{'='*60}")
        print(f"Mean Recall@{results['k']}: {results['mean_recall_at_k']:.4f}")
        print(f"Total queries: {results['total_queries']}")
        print(f"Successful: {results['successful_queries']}")
        print(f"Failed: {results['failed_queries']}")
        print(f"{'='*60}\n")
        
        # Print detailed recalls
        if results['recalls']:
            print("Detailed Recalls:")
            for i, recall in enumerate(results['recalls'][:10], 1):
                print(f"  Query {i}: {recall:.4f}")
            if len(results['recalls']) > 10:
                print(f"  ... and {len(results['recalls']) - 10} more")
        
        logger.info("Evaluation completed successfully")
        
        return results['mean_recall_at_k']
    
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"\nError: {e}")
        print("\nPlease ensure:")
        print(f"1. Labeled test file exists: {args.gold}")
        print("2. FAISS index files exist (run embedder.py first)")
        print("3. GEMINI_API_KEY is set in .env file")
        return None
    
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        raise


if __name__ == "__main__":
    main()

