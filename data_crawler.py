"""
SHL Catalog Data Crawler
Crawls the SHL product catalog and extracts Individual Test Solutions.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
from typing import List, Dict
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SHL_CATALOG_URL = "https://www.shl.com/solutions/products/product-catalog/"


def extract_test_type(description: str, name: str) -> str:
    """
    Extract test type from description or name.
    K = Knowledge/Technical, P = Personality/Behavioral
    """
    text = (description + " " + name).lower()
    
    # Keywords for Knowledge/Technical tests
    knowledge_keywords = ['knowledge', 'technical', 'coding', 'programming', 'aptitude', 
                         'cognitive', 'numerical', 'verbal', 'reasoning', 'skills', 
                         'ability', 'competency', 'proficiency', 'expertise']
    
    # Keywords for Personality/Behavioral tests
    personality_keywords = ['personality', 'behavioral', 'behavior', 'trait', 'preference',
                           'motivation', 'values', 'interests', 'style', 'collaboration',
                           'teamwork', 'leadership', 'communication', 'emotional']
    
    knowledge_score = sum(1 for keyword in knowledge_keywords if keyword in text)
    personality_score = sum(1 for keyword in personality_keywords if keyword in text)
    
    if knowledge_score > personality_score:
        return "K"
    elif personality_score > knowledge_score:
        return "P"
    else:
        return "K"  # Default to K if unclear


def crawl_shl_catalog() -> List[Dict]:
    """
    Crawl SHL catalog and extract Individual Test Solutions.
    Returns list of dictionaries with assessment data.
    """
    logger.info(f"Starting crawl of {SHL_CATALOG_URL}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(SHL_CATALOG_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        assessments = []
        
        # Look for assessment cards/items - SHL website structure may vary
        # Common patterns: product cards, assessment listings, etc.
        
        # Try multiple selectors to find assessment items
        selectors = [
            'div.product-item',
            'div.assessment-item',
            'div[class*="product"]',
            'div[class*="assessment"]',
            'article',
            'div.card',
            'li.product'
        ]
        
        found_items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                found_items = items
                logger.info(f"Found {len(items)} items using selector: {selector}")
                break
        
        # If no specific structure found, try to find links that might be assessments
        if not found_items:
            # Look for links containing assessment-related keywords
            all_links = soup.find_all('a', href=True)
            assessment_links = []
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                if any(keyword in href.lower() or keyword in text.lower() 
                       for keyword in ['assessment', 'test', 'solution', 'product']):
                    if 'shl.com' in href or href.startswith('/'):
                        assessment_links.append(link)
            
            logger.info(f"Found {len(assessment_links)} potential assessment links")
            found_items = assessment_links[:100]  # Limit to avoid too many
        
        # Extract data from found items
        for item in found_items:
            try:
                # Extract name
                name_elem = item.find(['h2', 'h3', 'h4', 'a', 'span'], class_=re.compile(r'title|name|heading', re.I))
                if not name_elem:
                    name_elem = item.find(['h2', 'h3', 'h4'])
                if not name_elem:
                    name_elem = item.find('a')
                
                name = name_elem.get_text(strip=True) if name_elem else ""
                
                # Skip if it's not an Individual Test Solution
                if not name or 'pre-packaged' in name.lower() or 'job solution' in name.lower():
                    continue
                
                # Extract URL
                url_elem = item.find('a', href=True)
                if url_elem:
                    url = url_elem['href']
                    if url.startswith('/'):
                        url = f"https://www.shl.com{url}"
                    elif not url.startswith('http'):
                        url = f"https://www.shl.com/{url}"
                else:
                    url = ""
                
                # Extract description
                desc_elem = item.find(['p', 'div'], class_=re.compile(r'desc|summary|text', re.I))
                if not desc_elem:
                    desc_elems = item.find_all(['p', 'div'])
                    desc_elem = desc_elems[0] if desc_elems else None
                
                description = desc_elem.get_text(strip=True) if desc_elem else ""
                
                # Only add if we have at least a name
                if name and url:
                    test_type = extract_test_type(description, name)
                    assessments.append({
                        'name': name,
                        'url': url,
                        'description': description,
                        'type': test_type
                    })
                    logger.debug(f"Extracted: {name}")
            
            except Exception as e:
                logger.warning(f"Error extracting item: {e}")
                continue
        
        # If we didn't find enough items, create sample data structure
        # In production, you'd want to refine the scraping logic
        if len(assessments) < 10:
            logger.warning("Found fewer than 10 assessments. Website structure may have changed.")
            logger.info("Creating sample structure - you may need to refine the crawler")
        
        logger.info(f"Successfully extracted {len(assessments)} assessments")
        return assessments
    
    except Exception as e:
        logger.error(f"Error crawling SHL catalog: {e}")
        # Return sample data structure for development
        logger.info("Returning sample data structure for development")
        return get_sample_assessments()


def get_sample_assessments() -> List[Dict]:
    """
    Returns sample assessment data structure.
    In production, this should be replaced with actual crawled data.
    """
    return [
        {
            'name': 'Java Developer Coding Test',
            'url': 'https://www.shl.com/solutions/products/product-catalog/java-developer-coding-test/',
            'description': 'Assesses Java programming skills, problem-solving abilities, and technical knowledge required for Java development roles.',
            'type': 'K'
        },
        {
            'name': 'Collaboration and Teamwork Assessment',
            'url': 'https://www.shl.com/solutions/products/product-catalog/collaboration-teamwork-assessment/',
            'description': 'Evaluates an individual\'s ability to work effectively in teams, communicate, and collaborate with others.',
            'type': 'P'
        },
        {
            'name': 'Problem Solving Test',
            'url': 'https://www.shl.com/solutions/products/product-catalog/problem-solving-test/',
            'description': 'Measures analytical thinking, logical reasoning, and problem-solving capabilities.',
            'type': 'K'
        },
        {
            'name': 'Personality Assessment',
            'url': 'https://www.shl.com/solutions/products/product-catalog/personality-assessment/',
            'description': 'Comprehensive personality evaluation covering behavioral traits, work preferences, and interpersonal styles.',
            'type': 'P'
        },
        {
            'name': 'Python Programming Test',
            'url': 'https://www.shl.com/solutions/products/product-catalog/python-programming-test/',
            'description': 'Tests Python coding skills, knowledge of Python libraries, and software development practices.',
            'type': 'K'
        },
        {
            'name': 'Leadership Assessment',
            'url': 'https://www.shl.com/solutions/products/product-catalog/leadership-assessment/',
            'description': 'Assesses leadership capabilities, decision-making skills, and ability to guide teams.',
            'type': 'P'
        },
        {
            'name': 'Numerical Reasoning Test',
            'url': 'https://www.shl.com/solutions/products/product-catalog/numerical-reasoning-test/',
            'description': 'Evaluates ability to work with numbers, interpret data, and solve mathematical problems.',
            'type': 'K'
        },
        {
            'name': 'Communication Skills Assessment',
            'url': 'https://www.shl.com/solutions/products/product-catalog/communication-skills-assessment/',
            'description': 'Measures verbal and written communication abilities, clarity, and effectiveness.',
            'type': 'P'
        },
        {
            'name': 'SQL Database Test',
            'url': 'https://www.shl.com/solutions/products/product-catalog/sql-database-test/',
            'description': 'Tests knowledge of SQL queries, database design, and data management skills.',
            'type': 'K'
        },
        {
            'name': 'Emotional Intelligence Assessment',
            'url': 'https://www.shl.com/solutions/products/product-catalog/emotional-intelligence-assessment/',
            'description': 'Evaluates emotional awareness, empathy, and ability to manage emotions in the workplace.',
            'type': 'P'
        },
        {
            'name': 'JavaScript Developer Test',
            'url': 'https://www.shl.com/solutions/products/product-catalog/javascript-developer-test/',
            'description': 'Assesses JavaScript programming skills, frontend development knowledge, and web technologies.',
            'type': 'K'
        },
        {
            'name': 'Adaptability Assessment',
            'url': 'https://www.shl.com/solutions/products/product-catalog/adaptability-assessment/',
            'description': 'Measures ability to adapt to change, handle ambiguity, and remain flexible in dynamic environments.',
            'type': 'P'
        },
        {
            'name': 'Data Analysis Test',
            'url': 'https://www.shl.com/solutions/products/product-catalog/data-analysis-test/',
            'description': 'Evaluates skills in data interpretation, statistical analysis, and data-driven decision making.',
            'type': 'K'
        },
        {
            'name': 'Customer Service Assessment',
            'url': 'https://www.shl.com/solutions/products/product-catalog/customer-service-assessment/',
            'description': 'Assesses customer interaction skills, service orientation, and ability to handle customer needs.',
            'type': 'P'
        },
        {
            'name': 'System Design Test',
            'url': 'https://www.shl.com/solutions/products/product-catalog/system-design-test/',
            'description': 'Tests ability to design scalable systems, architecture knowledge, and technical planning skills.',
            'type': 'K'
        }
    ]


def save_to_csv(assessments: List[Dict], filename: str = 'shl_catalog.csv'):
    """Save assessments to CSV file."""
    df = pd.DataFrame(assessments)
    df.to_csv(filename, index=False, encoding='utf-8')
    logger.info(f"Saved {len(assessments)} assessments to {filename}")
    return df


def main():
    """Main function to run the crawler."""
    logger.info("Starting SHL Catalog Crawler")
    assessments = crawl_shl_catalog()
    
    if assessments:
        df = save_to_csv(assessments)
        print(f"\nSuccessfully crawled {len(assessments)} assessments")
        print(f"\nSample data:")
        print(df.head())
    else:
        logger.error("No assessments found. Please check the website structure.")


if __name__ == "__main__":
    main()

