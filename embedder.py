"""
SHL Assessment Embedder
Generates embeddings for assessment descriptions using Gemini and stores them in FAISS vector store.
"""

import pandas as pd
import numpy as np
import faiss
import pickle
import logging
import os
from typing import List, Dict, Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
FAISS_INDEX_FILE = 'data/shl_index.faiss'
METADATA_FILE = 'data/shl_index.pkl'
CATALOG_FILE = 'data/shl_catalog_enriched.csv'  # Use enriched catalog if available

# Gemini embedding model dimension
# text-embedding-004: 768 dimensions
# text-embedding-004 (newer): may vary, will be detected automatically
EMBEDDING_DIMENSION = 768


def load_data(csv_file: str = CATALOG_FILE) -> pd.DataFrame:
    """
    Load the cleaned SHL catalog data from CSV.
    Falls back to cleaned catalog if enriched doesn't exist.
    
    Args:
        csv_file: Path to the CSV file
        
    Returns:
        DataFrame with assessments
    """
    # Try enriched catalog first, fall back to cleaned
    if not os.path.exists(csv_file):
        fallback_file = 'data/shl_catalog_cleaned.csv'
        if os.path.exists(fallback_file):
            logger.info(f"Enriched catalog not found, using {fallback_file}")
            csv_file = fallback_file
        else:
            raise FileNotFoundError(
                f"Catalog file not found: {csv_file} or {fallback_file}. "
                "Please run data_loader.py first to create the cleaned catalog."
            )
    
    logger.info(f"Loading data from {csv_file}")
    df = pd.read_csv(csv_file)
    logger.info(f"Loaded {len(df)} assessments from {csv_file}")
    
    return df


def generate_embeddings(df: pd.DataFrame, api_key: Optional[str] = None) -> np.ndarray:
    """
    Generate embeddings for assessment descriptions using Gemini.
    
    Args:
        df: DataFrame with assessments
        api_key: Gemini API key (if None, uses GEMINI_API_KEY env var)
        
    Returns:
        numpy array of embeddings (n_samples, dimension)
    """
    api_key = api_key or GEMINI_API_KEY
    
    if not api_key:
        raise ValueError(
            "Gemini API key is required. Set GEMINI_API_KEY environment variable."
        )
    
    # Configure Gemini API
    genai.configure(api_key=api_key)
    
    logger.info("Generating embeddings using Gemini...")
    all_embeddings = []
    
    # Extract descriptions for embedding
    # Include name, description, skills, and use cases for better semantic matching
    descriptions = []
    for _, row in df.iterrows():
        name = str(row.get('Assessment Name', ''))
        description = str(row.get('Description', ''))
        skills = str(row.get('Skills', ''))
        use_cases = str(row.get('Use Cases', ''))
        test_type = str(row.get('Test Type', ''))
        
        # Combine all available information for richer embeddings
        parts = [name]
        if description and description != 'nan':
            parts.append(description)
        if skills and skills != 'nan':
            parts.append(f"Skills: {skills}")
        if use_cases and use_cases != 'nan':
            parts.append(f"Use cases: {use_cases}")
        if test_type:
            parts.append(f"Type: {test_type}")
        
        combined_description = '. '.join(filter(None, parts))
        if not combined_description or combined_description == 'nan':
            combined_description = name if name else 'assessment'
        
        descriptions.append(combined_description)
    
    # Generate embeddings in batches
    batch_size = 100
    total_batches = (len(descriptions) - 1) // batch_size + 1
    
    for i in range(0, len(descriptions), batch_size):
        batch = descriptions[i:i + batch_size]
        batch_num = i // batch_size + 1
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")
        
        batch_embeddings = []
        for text in batch:
            try:
                # Generate embedding using Gemini API
                # Try different API methods based on available SDK version
                try:
                    # Method 1: Using genai.embed_content (newer API)
                    result = genai.embed_content(
                        model='models/text-embedding-004',
                        content=text,
                        task_type='RETRIEVAL_DOCUMENT'
                    )
                    embedding = np.array(result['embedding'], dtype=np.float32)
                except (KeyError, TypeError, AttributeError):
                    try:
                        # Method 2: Using GenerativeModel
                        model = genai.GenerativeModel('models/text-embedding-004')
                        result = model.embed_content(text)
                        if hasattr(result, 'embedding'):
                            embedding = np.array(result.embedding, dtype=np.float32)
                        elif isinstance(result, dict) and 'embedding' in result:
                            embedding = np.array(result['embedding'], dtype=np.float32)
                        elif isinstance(result, list):
                            embedding = np.array(result, dtype=np.float32)
                        else:
                            raise ValueError("Unexpected embedding format")
                    except Exception:
                        # Method 3: Fallback to REST API
                        import requests
                        response = requests.post(
                            'https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent',
                            headers={'Content-Type': 'application/json'},
                            params={'key': api_key},
                            json={'content': {'parts': [{'text': text}]}}
                        )
                        response.raise_for_status()
                        embedding = np.array(response.json()['embedding']['values'], dtype=np.float32)
                
                batch_embeddings.append(embedding)
            
            except Exception as e:
                logger.error(f"Error generating embedding: {e}")
                # Return zero vector as fallback
                batch_embeddings.append(np.zeros(EMBEDDING_DIMENSION, dtype=np.float32))
        
        all_embeddings.extend(batch_embeddings)
    
    embeddings_array = np.array(all_embeddings)
    
    # Update dimension if it differs
    if len(embeddings_array) > 0:
        actual_dim = embeddings_array.shape[1]
        logger.info(f"Generated {len(embeddings_array)} embeddings with dimension {actual_dim}")
        if actual_dim != EMBEDDING_DIMENSION:
            logger.info(f"Note: Actual embedding dimension ({actual_dim}) differs from expected ({EMBEDDING_DIMENSION})")
    else:
        logger.warning("No embeddings generated!")
    
    return embeddings_array


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    """
    Build FAISS index from embeddings.
    
    Args:
        embeddings: numpy array of embeddings (n_samples, dimension)
        
    Returns:
        FAISS index
    """
    logger.info(f"Building FAISS index with {len(embeddings)} embeddings")
    
    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)
    
    # Create index (using Inner Product for cosine similarity after normalization)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    
    logger.info(f"Index created with {index.ntotal} vectors")
    logger.info(f"Index dimension: {index.d}")
    
    return index


def save_index(index: faiss.Index, metadata: List[Dict], 
               index_file: str = FAISS_INDEX_FILE,
               metadata_file: str = METADATA_FILE):
    """
    Save FAISS index and metadata to disk.
    
    Args:
        index: FAISS index to save
        metadata: List of dictionaries with assessment metadata
        index_file: Path to save FAISS index
        metadata_file: Path to save metadata
    """
    logger.info(f"Saving index to {index_file}")
    faiss.write_index(index, index_file)
    
    logger.info(f"Saving metadata to {metadata_file}")
    with open(metadata_file, 'wb') as f:
        pickle.dump(metadata, f)
    
    logger.info("Index and metadata saved successfully")
    
    # Print summary
    index_size_mb = os.path.getsize(index_file) / (1024 * 1024)
    metadata_size_kb = os.path.getsize(metadata_file) / 1024
    logger.info(f"Index file size: {index_size_mb:.2f} MB")
    logger.info(f"Metadata file size: {metadata_size_kb:.2f} KB")


def main():
    """Main function to build and save embeddings."""
    logger.info("Starting embedding generation with Gemini")
    
    try:
        # Load data
        df = load_data()
        
        # Generate embeddings
        embeddings = generate_embeddings(df)
        
        # Build FAISS index
        index = build_faiss_index(embeddings)
        
        # Prepare metadata
        metadata = df.to_dict('records')
        
        # Save index
        save_index(index, metadata)
        
        # Print summary
        print(f"\n{'='*60}")
        print("Embedding Generation Summary")
        print(f"{'='*60}")
        print(f"Total embeddings created: {len(embeddings)}")
        print(f"Embedding dimension: {embeddings.shape[1]}")
        print(f"Index size: {index.ntotal} vectors")
        print(f"Index dimension: {index.d}")
        print(f"Index file: {FAISS_INDEX_FILE}")
        print(f"Metadata file: {METADATA_FILE}")
        print(f"{'='*60}\n")
        
        logger.info("Embedding generation completed successfully")
    
    except Exception as e:
        logger.error(f"Error in embedding generation: {e}")
        raise


if __name__ == "__main__":
    main()
