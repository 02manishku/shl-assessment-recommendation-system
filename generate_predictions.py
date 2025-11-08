"""
Generate Predictions for Test Queries
Loads unlabeled test queries and generates predictions CSV.
"""

import pandas as pd
import logging
import os
from typing import List, Dict
from dotenv import load_dotenv

from recommender import AssessmentRecommender

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_test_queries(file_path: str = 'data/test_queries.csv') -> pd.DataFrame:
    """
    Load test queries from CSV or Excel file.
    
    Expected format:
    - Column with queries (can be named 'Query', 'query', 'text', etc.)
    
    Args:
        file_path: Path to test queries file (CSV or Excel)
        
    Returns:
        DataFrame with test queries
    """
    logger.info(f"Loading test queries from {file_path}")
    
    # Try common file variations
    file_variations = [
        file_path,
        'data/test_queries.csv',
        'data/unlabeled_test_set.csv',
        'data/unlabeled_test_set.xlsx',
        'data/test_set.csv',
        'test_queries.csv',  # Fallback to root for backward compatibility
        'unlabeled_test_set.csv',
        'unlabeled_test_set.xlsx'
    ]
    
    df = None
    actual_file = None
    
    for file_variant in file_variations:
        if os.path.exists(file_variant):
            actual_file = file_variant
            try:
                if file_variant.endswith('.xlsx'):
                    df = pd.read_excel(file_variant)
                else:
                    df = pd.read_csv(file_variant)
                logger.info(f"Loaded {len(df)} test queries from {file_variant}")
                break
            except Exception as e:
                logger.warning(f"Failed to load {file_variant}: {e}")
                continue
    
    if df is None:
        raise FileNotFoundError(
            f"Test queries file not found. Tried: {', '.join(file_variations)}. "
            "Please provide a CSV or Excel file with test queries."
        )
    
    # Find query column
    query_col = None
    for col in df.columns:
        if col.lower() in ['query', 'text', 'job_description', 'jd', 'description']:
            query_col = col
            break
    
    if query_col is None:
        # Use first column as query
        query_col = df.columns[0]
        logger.warning(f"Query column not found, using first column: {query_col}")
    
    # Ensure we have a 'Query' column
    if query_col != 'Query':
        df['Query'] = df[query_col]
    
    return df


def generate_predictions(queries_df: pd.DataFrame, 
                        recommender: AssessmentRecommender,
                        top_k: int = 1) -> pd.DataFrame:
    """
    Generate predictions for test queries.
    
    Args:
        queries_df: DataFrame with test queries
        recommender: Initialized AssessmentRecommender instance
        top_k: Number of top recommendations to use (default: 1 for primary recommendation)
        
    Returns:
        DataFrame with predictions (Query, Assessment_url)
    """
    logger.info(f"Generating predictions for {len(queries_df)} queries")
    
    predictions = []
    
    for idx, row in queries_df.iterrows():
        query = str(row.get('Query', ''))
        
        if not query or query == 'nan':
            logger.warning(f"Empty query at row {idx}, skipping")
            continue
        
        try:
            # Get recommendations
            recommendations = recommender.recommend(query, top_k=top_k)
            
            if recommendations:
                # Use the top recommendation
                top_rec = recommendations[0]
                assessment_url = top_rec.get('URL', top_rec.get('url', ''))
                
                predictions.append({
                    'Query': query,
                    'Assessment_url': assessment_url
                })
                
                logger.debug(f"Query {idx+1}: Found recommendation - {assessment_url}")
            else:
                # No recommendations found
                predictions.append({
                    'Query': query,
                    'Assessment_url': ''
                })
                logger.warning(f"Query {idx+1}: No recommendations found")
        
        except Exception as e:
            logger.error(f"Error processing query {idx+1}: {e}")
            predictions.append({
                'Query': query,
                'Assessment_url': ''
            })
    
    predictions_df = pd.DataFrame(predictions)
    logger.info(f"Generated {len(predictions_df)} predictions")
    
    return predictions_df


def save_predictions(predictions_df: pd.DataFrame, 
                    output_path: str = 'predictions.csv'):
    """
    Save predictions to CSV file.
    
    Args:
        predictions_df: DataFrame with predictions
        output_path: Path to save predictions CSV
    """
    logger.info(f"Saving predictions to {output_path}")
    
    # Ensure columns are exactly: Query, Assessment_url
    output_df = pd.DataFrame({
        'Query': predictions_df['Query'],
        'Assessment_url': predictions_df['Assessment_url']
    })
    
    output_df.to_csv(output_path, index=False, encoding='utf-8')
    logger.info(f"Saved {len(output_df)} predictions to {output_path}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("✅ PREDICTIONS SAVED SUCCESSFULLY")
    print(f"{'='*60}")
    print(f"Total predictions: {len(output_df)}")
    print(f"Predictions with URLs: {len(output_df[output_df['Assessment_url'] != ''])}")
    print(f"Predictions without URLs: {len(output_df[output_df['Assessment_url'] == ''])}")
    print(f"Output file: {output_path}")
    print(f"{'='*60}")
    print(f"\n✅ File saved: {output_path}")
    print(f"Format: Query, Assessment_url")
    print(f"Ready for submission!\n")


def main():
    """Main function to generate predictions."""
    logger.info("Starting prediction generation")
    
    try:
        # Load test queries
        # You can specify a different file path if needed
        test_queries_file = os.getenv('TEST_QUERIES_FILE', 'test_queries.csv')
        queries_df = load_test_queries(test_queries_file)
        
        # Initialize recommender
        logger.info("Initializing recommender...")
        recommender = AssessmentRecommender()
        recommender.load_index()
        
        # Generate predictions
        predictions_df = generate_predictions(queries_df, recommender, top_k=1)
        
        # Save predictions
        output_file = os.getenv('PREDICTIONS_OUTPUT', 'predictions.csv')
        save_predictions(predictions_df, output_file)
        
        # Display sample predictions
        print("\nSample predictions (first 5):")
        print(predictions_df.head())
        
        logger.info("Prediction generation completed successfully")
    
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"\nError: {e}")
        print("\nPlease ensure:")
        print("1. Test queries file exists (default: test_queries.csv)")
        print("2. FAISS index files exist (run embedder.py first)")
        print("3. GEMINI_API_KEY is set in .env file")
    
    except Exception as e:
        logger.error(f"Error in prediction generation: {e}")
        raise


if __name__ == "__main__":
    main()

