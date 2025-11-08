"""
SHL Assessment Recommender
Core recommendation logic using semantic search with FAISS.
"""

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
EMBEDDING_DIMENSION = 768


class AssessmentRecommender:
    """Handles recommendation logic using FAISS semantic search."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the recommender.
        
        Args:
            api_key: Gemini API key (if None, uses GEMINI_API_KEY env var)
        """
        api_key = api_key or GEMINI_API_KEY
        
        if not api_key:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY environment variable."
            )
        
        # Configure Gemini API
        genai.configure(api_key=api_key)
        self.api_key = api_key
        
        self.index = None
        self.metadata = []
        self.dimension = EMBEDDING_DIMENSION
    
    def load_index(self, index_file: str = FAISS_INDEX_FILE,
                   metadata_file: str = METADATA_FILE):
        """
        Load FAISS index and metadata from disk.
        
        Args:
            index_file: Path to FAISS index file
            metadata_file: Path to metadata file
        """
        if not os.path.exists(index_file):
            raise FileNotFoundError(
                f"Index file not found: {index_file}. "
                "Please run embedder.py first to create the index."
            )
        
        if not os.path.exists(metadata_file):
            raise FileNotFoundError(
                f"Metadata file not found: {metadata_file}. "
                "Please run embedder.py first to create the metadata."
            )
        
        logger.info(f"Loading index from {index_file}")
        self.index = faiss.read_index(index_file)
        
        logger.info(f"Loading metadata from {metadata_file}")
        with open(metadata_file, 'rb') as f:
            self.metadata = pickle.load(f)
        
        # Clean NaN values in metadata (convert pandas nan to None or empty string)
        import pandas as pd
        import numpy as np
        for item in self.metadata:
            for key, value in item.items():
                if isinstance(value, float) and (np.isnan(value) or value != value):
                    item[key] = None
                elif isinstance(value, str) and value.lower() == 'nan':
                    item[key] = None
        
        logger.info(f"Loaded index with {self.index.ntotal} vectors")
    
    def generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding for a query text.
        
        Args:
            query: Query text to embed
            
        Returns:
            numpy array of embedding vector
        """
        try:
            query = query.strip()
            if not query:
                query = "assessment"
            
            # Generate embedding using Gemini API
            # Try different API methods based on available SDK version
            try:
                # Method 1: Using genai.embed_content (newer API)
                result = genai.embed_content(
                    model='models/text-embedding-004',
                    content=query,
                    task_type='RETRIEVAL_QUERY'
                )
                embedding = np.array(result['embedding'], dtype=np.float32)
            except (KeyError, TypeError, AttributeError):
                try:
                    # Method 2: Using GenerativeModel
                    model = genai.GenerativeModel('models/text-embedding-004')
                    result = model.embed_content(query)
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
                        params={'key': self.api_key},
                        json={'content': {'parts': [{'text': query}]}}
                    )
                    response.raise_for_status()
                    embedding = np.array(response.json()['embedding']['values'], dtype=np.float32)
            
            return embedding
        
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            return np.zeros(self.dimension, dtype=np.float32)
    
    def recommend(self, query: str, top_k: int = 10, 
                  balance_types: bool = True, use_reranking: bool = True) -> List[Dict]:
        """
        Get recommendations for a given query.
        
        Args:
            query: Natural language query or job description
            top_k: Number of recommendations to return
            balance_types: If True, tries to balance between K and P types
            use_reranking: If True, use Gemini to re-rank results for better relevance
            
        Returns:
            List of dictionaries with assessment recommendations
        """
        if self.index is None:
            raise ValueError("Index not loaded. Call load_index() first.")
        
        # Generate query embedding
        query_embedding = self.generate_query_embedding(query)
        
        # Normalize query embedding
        query_embedding = query_embedding.reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        # Search for more results to allow for reranking and type balancing
        # Get more candidates for better reranking
        search_k = top_k * 5 if use_reranking else (top_k * 3 if balance_types else top_k)
        similarities, indices = self.index.search(query_embedding, search_k)
        
        # Format results - keep ALL candidates first
        all_candidates = []
        seen_urls = set()
        
        for similarity, idx in zip(similarities[0], indices[0]):
            if idx >= len(self.metadata):
                continue
            
            result = self.metadata[idx].copy()
            result['similarity'] = float(similarity)
            
            # Skip duplicates by URL
            url = result.get('URL', '') or result.get('url', '')
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            all_candidates.append(result)
        
        # Take top candidates for reranking (more than top_k to allow filtering)
        candidates_for_reranking = all_candidates[:min(top_k * 2, len(all_candidates))]
        
        # Use Gemini to re-rank results by relevance
        if use_reranking and len(candidates_for_reranking) > 0:
            logger.info("Re-ranking results using Gemini for better relevance...")
            reranked_results = self._rerank_with_gemini(query, candidates_for_reranking, top_k)
            # IMPORTANT: Do NOT re-sort reranked results - they're already in the correct order from Gemini
            # Only apply light type balancing if needed, but preserve rerank order
        else:
            # Fallback: sort by similarity
            candidates_for_reranking.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            reranked_results = candidates_for_reranking[:top_k]
        
        # Balance types if requested, but don't override reranking order
        if balance_types and len(all_candidates) > len(reranked_results):
            balanced_results = self._balance_types_light(reranked_results, all_candidates, query, top_k)
            # IMPORTANT: Preserve rerank order - only sort if no rerank_score exists
            # If rerank_score exists, maintain the order (already sorted by Gemini)
            has_rerank_scores = any(r.get('rerank_score', 0) > 0 for r in balanced_results)
            if not has_rerank_scores:
                # No reranking was done, sort by similarity
                balanced_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            # If rerank scores exist, keep the order as-is (Gemini already sorted it)
            return balanced_results[:top_k]
        
        # Return reranked results in the order Gemini specified (don't re-sort)
        return reranked_results[:top_k]
    
    def _balance_types_light(self, reranked_results: List[Dict], all_candidates: List[Dict],
                            query: str, top_k: int) -> List[Dict]:
        """
        Light type balancing that doesn't override reranking too much.
        Only adds behavioral assessments if they're missing and reasonably relevant.
        """
        query_lower = query.lower()
        
        # Check what types we have in reranked results
        types_in_results = set()
        for r in reranked_results:
            test_type = r.get('Test Type', r.get('type', '')).upper()
            if test_type:
                types_in_results.add(test_type)
        
        # IMPORTANT: If reranking was done, preserve the rerank order
        # Don't add behavioral assessments if it would disrupt the reranking
        has_rerank_scores = any(r.get('rerank_score', 0) > 0 for r in reranked_results)
        
        if has_rerank_scores:
            # Reranking was done - preserve the order from Gemini
            # Only add behavioral if explicitly needed and at the very end
            return reranked_results
        
        # Only balance if reranking was NOT done (fallback mode)
        # If we already have both K and P types, return as-is
        if 'K' in types_in_results and 'P' in types_in_results:
            return reranked_results
        
        # Only add behavioral if it's a role query and we have no behavioral assessments
        role_keywords = ['engineer', 'developer', 'programmer', 'manager', 'lead', 'senior', 'analyst']
        is_role_query = any(keyword in query_lower for keyword in role_keywords)
        
        if is_role_query and 'P' not in types_in_results:
            # Find behavioral assessments from all candidates
            p_candidates = [r for r in all_candidates 
                          if r.get('Test Type', '').upper() in ['P', 'H']
                          and r not in reranked_results]
            
            # Only add if we have at least 8 technical assessments
            if len(reranked_results) >= 8 and p_candidates:
                # Take top 1-2 behavioral assessments
                num_to_add = min(2, len(p_candidates))
                # Sort by similarity (since no rerank scores)
                p_sorted = sorted(p_candidates, 
                                key=lambda x: x.get('similarity', 0), 
                                reverse=True)
                # Add at the end to not override reranking
                result = reranked_results[:top_k - num_to_add] + p_sorted[:num_to_add]
                return result
        
        return reranked_results
    
    def _balance_types(self, primary_results: List[Dict], all_candidates: List[Dict], 
                      query: str, top_k: int) -> List[Dict]:
        """
        Balance results between Knowledge (K) and Personality (P) types,
        while prioritizing the most relevant assessments first.
        
        Args:
            primary_results: Top results sorted by similarity
            all_candidates: All candidate results from search
            query: Original query text
            top_k: Number of results to return
            
        Returns:
            Balanced list of results, still sorted by relevance
        """
        query_lower = query.lower()
        
        # Check if query mentions both technical and behavioral aspects
        technical_keywords = ['developer', 'coding', 'programming', 'technical', 
                            'skill', 'knowledge', 'aptitude', 'ability', 'engineer',
                            'software', 'programmer', 'coder']
        behavioral_keywords = ['personality', 'behavior', 'teamwork', 'collaboration',
                            'communication', 'leadership', 'soft skill', 'interpersonal',
                            'team', 'collaborate', 'communicate']
        
        has_technical = any(keyword in query_lower for keyword in technical_keywords)
        has_behavioral = any(keyword in query_lower for keyword in behavioral_keywords)
        
        # Separate primary results by type
        k_primary = [r for r in primary_results if r.get('Test Type', '').upper() in ['K', 'H']]
        p_primary = [r for r in primary_results if r.get('Test Type', '').upper() in ['P', 'H']]
        
        # If primary results already have both types, return as-is (already sorted by relevance)
        if len(k_primary) > 0 and len(p_primary) > 0:
            return primary_results  # Already balanced and sorted by relevance
        
        # For role queries, consider adding behavioral assessments if missing
        role_keywords = ['engineer', 'developer', 'programmer', 'manager', 'lead', 'senior', 'analyst']
        is_role_query = any(keyword in query_lower for keyword in role_keywords)
        
        # If it's a role query and we only have technical assessments, 
        # try to find relevant behavioral assessments from all candidates
        if is_role_query and len(p_primary) == 0 and len(k_primary) >= 5:
            # Get behavioral assessments from all candidates (sorted by similarity)
            p_candidates = [r for r in all_candidates 
                          if r.get('Test Type', '').upper() in ['P', 'H'] 
                          and r not in primary_results]
            
            # Only add behavioral assessments if they have reasonable similarity
            # (at least 80% of the lowest similarity in primary results)
            if p_candidates and len(primary_results) > 0:
                min_similarity = min(r.get('similarity', 0) for r in primary_results)
                threshold = min_similarity * 0.8  # 80% threshold
                
                relevant_p = [r for r in p_candidates if r.get('similarity', 0) >= threshold]
                
                if relevant_p:
                    # Take top 2-3 behavioral assessments
                    num_to_add = min(2, len(relevant_p), top_k - len(primary_results))
                    if num_to_add > 0:
                        # Replace last 2-3 technical results with behavioral ones
                        balanced = k_primary[:max(0, len(k_primary) - num_to_add)]
                        balanced.extend(relevant_p[:num_to_add])
                        # Sort by similarity to maintain relevance order
                        balanced.sort(key=lambda x: x.get('similarity', 0), reverse=True)
                        return balanced[:top_k]
        
        # If query explicitly mentions behavioral aspects but we only have technical
        if has_behavioral and len(p_primary) == 0:
            p_candidates = [r for r in all_candidates 
                          if r.get('Test Type', '').upper() in ['P', 'H']
                          and r not in primary_results]
            if p_candidates:
                # Add top behavioral assessments, replacing some technical ones
                num_to_replace = min(3, len(p_candidates), len(k_primary) // 2)
                if num_to_replace > 0:
                    balanced = k_primary[:len(k_primary) - num_to_replace]
                    balanced.extend(p_candidates[:num_to_replace])
                    balanced.sort(key=lambda x: x.get('similarity', 0), reverse=True)
                    return balanced[:top_k]
        
        # Default: return primary results (most relevant first)
        return primary_results
    
    def _rerank_with_gemini(self, query: str, candidates: List[Dict], top_k: int) -> List[Dict]:
        """
        Use Gemini to re-rank assessment recommendations by relevance to the query.
        
        Args:
            query: Original query or job description
            candidates: List of candidate assessments from FAISS search
            top_k: Number of top results to return
            
        Returns:
            Re-ranked list of assessments sorted by relevance
        """
        try:
            # Use gemini-1.5-flash (faster, recommended) or fallback to gemini-1.5-pro
            # gemini-pro is deprecated, so try newer models first
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception:
                # Fallback to gemini-1.5-pro if flash not available
                try:
                    model = genai.GenerativeModel('gemini-1.5-pro')
                except Exception:
                    # Last resort: try old model name (may not work)
                    logger.warning("Using deprecated gemini-pro model. Consider updating API key.")
                    model = genai.GenerativeModel('gemini-pro')
            
            # Prepare candidate information for Gemini
            # Optimize: Limit description/skills length to keep prompt size manageable
            candidate_info = []
            for i, candidate in enumerate(candidates):
                name = candidate.get('Assessment Name', candidate.get('name', 'Unknown'))
                description = candidate.get('Description', candidate.get('description', ''))
                test_type = candidate.get('Test Type', candidate.get('type', ''))
                skills = candidate.get('Skills', candidate.get('skills', ''))
                similarity = candidate.get('similarity', 0.0)
                
                info = f"Assessment {i+1}: {name}"
                if description and description != 'nan' and description:
                    # Truncate description to 200 chars to optimize prompt size
                    desc = description[:200] + '...' if len(description) > 200 else description
                    info += f"\n   Description: {desc}"
                if test_type:
                    info += f"\n   Type: {test_type}"
                if skills and skills != 'nan' and skills:
                    # Truncate skills to 100 chars
                    skills_text = skills[:100] + '...' if len(skills) > 100 else skills
                    info += f"\n   Skills: {skills_text}"
                # Include similarity for context
                info += f"\n   (Similarity: {similarity:.3f})"
                
                candidate_info.append(info)
            
            candidates_text = "\n\n".join(candidate_info)
            
            # Detect if this is a software/technical role query
            query_lower = query.lower()
            is_technical_role = any(kw in query_lower for kw in ['software', 'engineer', 'developer', 'programmer', 'coding', 'technical'])
            
            role_context = ""
            if is_technical_role:
                role_context = """
CRITICAL: This is a TECHNICAL/SOFTWARE role query. You MUST:
- Rank programming/technical assessments (Java, Python, JavaScript, SQL, Selenium, etc.) HIGHEST
- Rank sales, entry-level, or non-technical assessments LOWEST or exclude them
- Prioritize assessments that test coding, programming, software development skills
- DO NOT rank "Sales", "Entry Level", or "General" assessments highly for technical roles"""
            
            prompt = f"""You are an expert assessment recommendation system. Re-rank assessments by relevance to this job query.

JOB QUERY: "{query}"
{role_context}

CANDIDATE ASSESSMENTS (currently ranked by similarity, but you need to re-rank by actual job relevance):
{candidates_text}

YOUR TASK:
Re-rank these {len(candidates)} assessments from MOST RELEVANT to LEAST RELEVANT for the job query.

CRITICAL RANKING RULES:
1. For "software engineer" / "developer" / technical roles:
   - MUST rank programming/technical assessments HIGHEST (Java, Python, JavaScript, SQL, Selenium, Automata, etc.)
   - MUST rank sales, entry-level sales, or non-technical assessments LOWEST
   - Focus on coding, programming, software development skills

2. Match assessments to the actual job requirements - ignore FAISS similarity scores if they don't match job relevance

3. Return ONLY the assessment numbers in your new ranking order (comma-separated)

EXAMPLE OUTPUT FORMAT:
If you think Assessment 5 (Java) is most relevant, Assessment 7 (Python) is 2nd, etc.:
5,7,8,1,2,3,4,6,9,10

Return ONLY numbers, no explanations."""
            
            # Generate content with timeout handling
            # Set timeout for Gemini API call (default 30 seconds)
            timeout_seconds = int(os.getenv('GEMINI_API_TIMEOUT', '30'))
            
            try:
                # Use generate_content with timeout protection
                # Note: Gemini API doesn't have built-in timeout, so we use a timeout wrapper
                import concurrent.futures
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(model.generate_content, prompt)
                    response = future.result(timeout=timeout_seconds)
                    ranking_text = response.text.strip()
            except concurrent.futures.TimeoutError:
                logger.warning(f"Gemini API call timed out after {timeout_seconds} seconds, falling back to similarity sorting")
                candidates_sorted = sorted(candidates, key=lambda x: x.get('similarity', 0), reverse=True)
                return candidates_sorted[:top_k]
            except Exception as api_error:
                logger.error(f"Error calling Gemini API: {api_error}")
                logger.warning("Falling back to similarity-based sorting")
                candidates_sorted = sorted(candidates, key=lambda x: x.get('similarity', 0), reverse=True)
                return candidates_sorted[:top_k]
            
            # Extract ranking numbers with improved parsing
            import re
            logger.debug(f"Raw Gemini response: {ranking_text}")
            
            # Clean the response - remove brackets, extra whitespace, prefixes, etc.
            cleaned_text = ranking_text.strip()
            # Remove common prefixes
            cleaned_text = re.sub(r'^(ranking|order|result|output|assessment|recommendation):?\s*', '', cleaned_text, flags=re.IGNORECASE)
            # Remove brackets
            cleaned_text = re.sub(r'[\[\]()]', '', cleaned_text)
            # Remove text after numbers if there's explanatory text
            # Find the first sequence of numbers
            number_match = re.search(r'(\d+(?:\s*,\s*\d+)+)', cleaned_text)
            if number_match:
                cleaned_text = number_match.group(1)
            
            # Extract all numbers
            numbers = re.findall(r'\b\d+\b', cleaned_text)
            logger.info(f"Extracted {len(numbers)} ranking numbers from Gemini response")
            
            if numbers:
                # Convert to indices (1-based to 0-based) and filter valid indices
                ranking_indices = []
                seen_indices = set()
                for n in numbers:
                    idx = int(n) - 1
                    if 0 <= idx < len(candidates) and idx not in seen_indices:
                        ranking_indices.append(idx)
                        seen_indices.add(idx)
                
                # If we got valid rankings, use them
                if len(ranking_indices) >= min(top_k, len(candidates)):
                    # Create a mapping of original index to new rank position
                    rank_map = {ranking_indices[i]: i + 1 for i in range(len(ranking_indices))}
                    
                    # Re-order candidates based on Gemini's ranking (keep exact order)
                    reranked = []
                    for rank_pos, orig_idx in enumerate(ranking_indices, 1):
                        if 0 <= orig_idx < len(candidates):
                            candidate = candidates[orig_idx].copy()
                            candidate['rerank_score'] = len(ranking_indices) - rank_pos + 1  # Higher score = better rank
                            candidate['rerank_position'] = rank_pos
                            candidate['original_similarity'] = candidate.get('similarity', 0)
                            reranked.append(candidate)
                    
                    # Add any remaining candidates that weren't ranked (at the end)
                    for i, candidate in enumerate(candidates):
                        if i not in ranking_indices:
                            candidate_copy = candidate.copy()
                            candidate_copy['rerank_score'] = 0  # Lower priority for unranked
                            candidate_copy['rerank_position'] = len(ranking_indices) + 1
                            candidate_copy['original_similarity'] = candidate_copy.get('similarity', 0)
                            reranked.append(candidate_copy)
                    
                    logger.info(f"✅ Successfully re-ranked {len(ranking_indices)} assessments using Gemini")
                    logger.info(f"📊 Top 5 re-ranked assessments:")
                    for i, r in enumerate(reranked[:5], 1):
                        name = r.get('Assessment Name', r.get('name', 'Unknown'))
                        rerank_pos = r.get('rerank_position', 'N/A')
                        orig_sim = r.get('original_similarity', 0)
                        logger.info(f"   {i}. {name} (rerank_pos: {rerank_pos}, orig_sim: {orig_sim:.4f})")
                    
                    # Return in reranked order (already sorted by Gemini) - DO NOT re-sort
                    return reranked[:top_k]
            
            # If ranking extraction failed, fall back to similarity sorting
            logger.warning("Failed to parse Gemini ranking, falling back to similarity sorting")
            candidates_sorted = sorted(candidates, key=lambda x: x.get('similarity', 0), reverse=True)
            return candidates_sorted[:top_k]
        
        except Exception as e:
            logger.error(f"Error in Gemini re-ranking: {e}")
            # Fallback to similarity sorting
            candidates_sorted = sorted(candidates, key=lambda x: x.get('similarity', 0), reverse=True)
            return candidates_sorted[:top_k]


def main():
    """Test the recommender with sample queries."""
    logger.info("Testing Assessment Recommender")
    
    try:
        recommender = AssessmentRecommender()
        recommender.load_index()
        
        # Test queries
        test_queries = [
            "I need to hire a Java developer who can collaborate with business teams.",
            "Looking for a data analyst with strong problem-solving skills.",
            "Need someone with excellent communication and leadership abilities."
        ]
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print(f"{'='*60}")
            
            recommendations = recommender.recommend(query, top_k=5)
            
            for i, rec in enumerate(recommendations, 1):
                name = rec.get('Assessment Name', rec.get('name', 'N/A'))
                url = rec.get('URL', rec.get('url', 'N/A'))
                test_type = rec.get('Test Type', rec.get('type', 'N/A'))
                similarity = rec.get('similarity', 0.0)
                description = rec.get('Description', rec.get('description', ''))
                duration = rec.get('Duration', rec.get('duration', ''))
                
                print(f"\n{i}. {name}")
                if description and description != 'nan':
                    print(f"   Description: {description[:100]}...")
                print(f"   Type: {test_type}")
                if duration:
                    print(f"   Duration: {duration}")
                print(f"   Similarity: {similarity:.4f}")
                print(f"   URL: {url}")
        
        logger.info("Recommender test completed successfully")
    
    except Exception as e:
        logger.error(f"Error testing recommender: {e}")
        raise


if __name__ == "__main__":
    main()

