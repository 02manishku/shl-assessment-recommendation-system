"""
SHL Catalog Data Loader
Loads and cleans the SHL catalogue Excel file.
"""

import pandas as pd
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_dataset(path: str = 'data/shl_catalogue.xlsx') -> pd.DataFrame:
    """
    Load the SHL catalogue dataset from Excel file.
    
    Args:
        path: Path to the Excel file
        
    Returns:
        DataFrame with the loaded data
    """
    logger.info(f"Loading dataset from {path}")
    
    try:
        # Read Excel file
        df = pd.read_excel(path)
        logger.info(f"Successfully loaded {len(df)} rows from {path}")
        logger.info(f"Columns found: {list(df.columns)}")
        
        return df
    
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        raise
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        raise


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the dataset by:
    - Keeping only required columns (Assessment Name, Description, Test Type, URL)
    - Renaming columns to standard names
    - Removing duplicates
    - Removing rows with missing essential fields
    
    Args:
        df: Raw DataFrame
        
    Returns:
        Cleaned DataFrame
    """
    logger.info("Starting dataset cleaning")
    logger.info(f"Initial shape: {df.shape}")
    
    # Create a copy to avoid modifying original
    df_clean = df.copy()
    
    # Map common column name variations to standard names
    column_mapping = {}
    
    # Find and map Assessment Name column
    name_cols = [col for col in df_clean.columns 
                 if 'name' in col.lower() or 'assessment' in col.lower()]
    if name_cols:
        column_mapping[name_cols[0]] = 'Assessment Name'
    else:
        logger.warning("Assessment Name column not found. Please check column names.")
    
    # Find and map Description column
    desc_cols = [col for col in df_clean.columns 
                 if 'description' in col.lower() or 'desc' in col.lower()]
    if desc_cols:
        column_mapping[desc_cols[0]] = 'Description'
    else:
        logger.warning("Description column not found. Please check column names.")
    
    # Find and map Test Type column
    type_cols = [col for col in df_clean.columns 
                 if 'type' in col.lower() or 'test type' in col.lower()]
    if type_cols:
        column_mapping[type_cols[0]] = 'Test Type'
    else:
        logger.warning("Test Type column not found. Please check column names.")
    
    # Find and map URL column
    url_cols = [col for col in df_clean.columns 
                if 'url' in col.lower() or 'link' in col.lower()]
    if url_cols:
        column_mapping[url_cols[0]] = 'URL'
    else:
        logger.warning("URL column not found. Please check column names.")
    
    # Rename columns
    df_clean = df_clean.rename(columns=column_mapping)
    
    # Keep only required columns (if they exist)
    required_columns = ['Assessment Name', 'Description', 'Test Type', 'URL']
    existing_columns = [col for col in required_columns if col in df_clean.columns]
    
    if len(existing_columns) < len(required_columns):
        missing = set(required_columns) - set(existing_columns)
        logger.warning(f"Missing columns: {missing}")
        logger.info(f"Keeping available columns: {existing_columns}")
    
    df_clean = df_clean[existing_columns]
    
    # Remove duplicates
    initial_count = len(df_clean)
    df_clean = df_clean.drop_duplicates()
    duplicates_removed = initial_count - len(df_clean)
    logger.info(f"Removed {duplicates_removed} duplicate rows")
    
    # Remove rows with missing essential fields
    # Assessment Name and URL are essential
    essential_cols = ['Assessment Name', 'URL']
    available_essential = [col for col in essential_cols if col in df_clean.columns]
    
    if available_essential:
        initial_count = len(df_clean)
        df_clean = df_clean.dropna(subset=available_essential)
        missing_removed = initial_count - len(df_clean)
        logger.info(f"Removed {missing_removed} rows with missing essential fields")
    
    # Filter out Pre-packaged Job Solutions (keep only Individual Test Solutions)
    logger.info("Filtering out Pre-packaged Job Solutions...")
    initial_count = len(df_clean)
    
    # Pattern to match pre-packaged job solutions
    exclude_pattern = r"pre[-\s]*packaged|prepackaged|pre packaged|job solution|job-solution"
    
    # Check both Assessment Name and Description columns
    mask_exclude = pd.Series(False, index=df_clean.index)
    if 'Assessment Name' in df_clean.columns:
        mask_exclude |= df_clean["Assessment Name"].str.contains(exclude_pattern, case=False, na=False, regex=True)
    if 'Description' in df_clean.columns:
        mask_exclude |= df_clean["Description"].str.contains(exclude_pattern, case=False, na=False, regex=True)
    
    df_clean = df_clean[~mask_exclude].copy()
    df_clean.reset_index(drop=True, inplace=True)
    
    filtered_count = initial_count - len(df_clean)
    logger.info(f"Removed {filtered_count} Pre-packaged Job Solutions")
    logger.info(f"Remaining Individual Test Solutions: {len(df_clean)}")
    
    # Clean data types and strip whitespace
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object':
            df_clean[col] = df_clean[col].astype(str).str.strip()
            # Replace 'nan' strings with empty string
            df_clean[col] = df_clean[col].replace('nan', '')
    
    logger.info(f"Final shape after cleaning: {df_clean.shape}")
    
    return df_clean


def save_cleaned_data(df: pd.DataFrame, output_path: str = 'data/shl_catalog_cleaned.csv'):
    """
    Save cleaned dataset to CSV file.
    
    Args:
        df: Cleaned DataFrame
        output_path: Path to save the CSV file
    """
    logger.info(f"Saving cleaned data to {output_path}")
    
    try:
        df.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"Successfully saved {len(df)} rows to {output_path}")
    
    except Exception as e:
        logger.error(f"Error saving cleaned data: {e}")
        raise


def main():
    """Main function to execute the data loading and cleaning process."""
    try:
        # Load dataset
        df = load_dataset('shl_catalogue.xlsx')
        
        # Display initial info
        print(f"\n{'='*60}")
        print(f"Dataset loaded: {len(df)} rows, {len(df.columns)} columns")
        print(f"{'='*60}")
        print("\nFirst 5 rows of original data:")
        print(df.head())
        print(f"\nColumn names: {list(df.columns)}")
        
        # Clean dataset
        df_cleaned = clean_dataset(df)
        
        # Save cleaned data
        save_cleaned_data(df_cleaned)
        
        # Display final info
        print(f"\n{'='*60}")
        print(f"Cleaned dataset: {len(df_cleaned)} rows")
        print(f"{'='*60}")
        print("\nFirst 5 rows of cleaned data:")
        print(df_cleaned.head())
        print(f"\nColumn names: {list(df_cleaned.columns)}")
        print(f"\nData types:")
        print(df_cleaned.dtypes)
        print(f"\nMissing values per column:")
        print(df_cleaned.isnull().sum())
        
        logger.info("Data loading and cleaning completed successfully")
    
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"\nError: File 'data/shl_catalogue.xlsx' not found.")
        print("Please ensure the file exists in the data/ directory.")
    
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        raise


if __name__ == "__main__":
    main()

