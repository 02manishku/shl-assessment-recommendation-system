"""
SHL Assessment Recommendation System - Streamlit UI
Web interface for the recommendation system.
"""

import streamlit as st
import requests
import logging
from typing import List, Dict, Optional
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import io
import time

from recommender import AssessmentRecommender

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="SHL Assessment Recommender",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# SHL color theme (purple/blue/white)
SHL_PRIMARY = "#6B46C1"  # Purple
SHL_SECONDARY = "#3B82F6"  # Blue
SHL_BACKGROUND = "#FFFFFF"  # White

# Custom CSS
st.markdown(f"""
    <style>
        .main {{
            background-color: {SHL_BACKGROUND};
        }}
        .stButton>button {{
            background-color: {SHL_PRIMARY};
            color: white;
            border-radius: 5px;
            border: none;
            padding: 0.5rem 2rem;
            font-weight: bold;
        }}
        .stButton>button:hover {{
            background-color: {SHL_SECONDARY};
        }}
        h1 {{
            color: {SHL_PRIMARY};
            margin-top: 0;
        }}
        h2 {{
            color: {SHL_SECONDARY};
        }}
        .recommendation-card {{
            background-color: #F3F4F6;
            padding: 1rem;
            border-radius: 5px;
            margin: 0.5rem 0;
            border-left: 4px solid {SHL_PRIMARY};
        }}
        .logo-container {{
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }}
        /* Hide Streamlit branding */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_recommender():
    """Get or initialize the recommender instance (cached)."""
    try:
        recommender = AssessmentRecommender()
        recommender.load_index()
        return recommender
    except Exception as e:
        st.error(f"Error initializing recommender: {e}")
        return None


def display_shl_logo(width=150, container=None):
    """
    Display SHL logo with fallback options.
    
    Args:
        width: Logo width in pixels
        container: Streamlit container (st, st.sidebar, etc.)
    """
    if container is None:
        container = st
    
    # Try multiple logo sources
    logo_sources = [
        ("assets/shl_logo.png", "local"),  # Assets folder (primary)
        ("shl_logo.png", "local"),  # Root (fallback)
        ("https://www.shl.com/wp-content/uploads/2020/06/SHL_Logo_RGB_2020.png", "url"),  # Official SHL logo URL
        ("https://www.shl.com/static/images/shl-logo.svg", "url"),  # Alternative SVG
    ]
    
    logo_displayed = False
    
    for logo_path, source_type in logo_sources:
        try:
            if source_type == "local":
                if os.path.exists(logo_path):
                    container.image(logo_path, width=width, use_container_width=False)
                    logo_displayed = True
                    break
            elif source_type == "url":
                # Try to load from URL
                container.image(logo_path, width=width, use_container_width=False)
                logo_displayed = True
                break
        except Exception:
            continue
    
    # Fallback: Display text logo if image fails
    if not logo_displayed:
        container.markdown(
            f"""
            <div style="text-align: center; padding: 0.5rem;">
                <h2 style="color: {SHL_PRIMARY}; margin: 0; font-weight: bold;">SHL</h2>
                <p style="color: {SHL_SECONDARY}; margin: 0; font-size: 0.8em;">Assessment Solutions</p>
            </div>
            """,
            unsafe_allow_html=True
        )


def fetch_jd_from_url(url: str) -> Optional[str]:
    """
    Fetch job description text from a URL.
    
    Args:
        url: URL to fetch from
        
    Returns:
        Job description text or None if failed
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        # Extract text from common job description containers
        text = soup.get_text(separator=' ', strip=True)
        return text[:5000]  # Limit to first 5000 characters
    
    except Exception as e:
        logger.error(f"Error fetching URL: {e}")
        return None


def main():
    """Main Streamlit application."""
    
    # Header with SHL Logo
    col_logo, col_title = st.columns([1, 4])
    
    with col_logo:
        display_shl_logo(width=150, container=st)
    
    with col_title:
        st.title("Assessment Recommendation System")
        st.markdown(
            "<p style='color: #6B7280; font-size: 1.1em;'>Enter a job description or natural language query to get personalized SHL assessment recommendations.</p>",
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        # SHL Logo in sidebar (smaller)
        display_shl_logo(width=120, container=st.sidebar)
        st.markdown("---")
        st.header("⚙️ Settings")
        
        # Initialize query history in session state
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        
        # Default to using API endpoint (recommended)
        use_api_default = os.getenv("USE_API_BY_DEFAULT", "true").lower() == "true"
        use_api = st.checkbox(
            "Use API endpoint (Recommended)", 
            value=use_api_default,
            help="Recommended: Use the FastAPI backend for better performance and reliability. Uncheck to use local recommender."
        )
        
        if use_api:
            api_url_input = st.text_input(
                "API URL",
                value=os.getenv("API_URL", "http://localhost:8000"),
                help="URL of the FastAPI backend. Make sure the API server is running."
            )
            # Store in session state to access later
            st.session_state['api_url'] = api_url_input
            st.success("✅ Using API endpoint (Recommended)")
            
            # Show API status
            try:
                import requests
                health_url = f"{api_url_input}/health"
                health_response = requests.get(health_url, timeout=2)
                if health_response.status_code == 200:
                    st.success("🟢 API is online and ready")
                else:
                    st.warning("🟡 API responded but may have issues")
            except Exception as e:
                st.warning(f"🟡 API connection check failed: {str(e)[:50]}...")
                st.info("💡 Tip: Start the API server with `python api.py`")
        else:
            st.warning("⚠️ Using local recommender (slower, requires local resources)")
            st.info("💡 For better performance, use the API endpoint")
        
        st.markdown("---")
        
        # Query History Section
        if st.session_state.query_history:
            st.markdown("### 📜 Query History")
            for i, history_item in enumerate(reversed(st.session_state.query_history[-5:]), 1):
                query_text = history_item.get('query', '')[:50]
                if len(history_item.get('query', '')) > 50:
                    query_text += '...'
                timestamp = history_item.get('timestamp', '')
                if st.button(f"🔍 {query_text}", key=f"history_{i}", use_container_width=True):
                    st.session_state['selected_query'] = history_item.get('query', '')
                    st.rerun()
            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.query_history = []
                st.rerun()
            st.markdown("---")
        
        st.markdown("### About")
        st.markdown(
            "This system uses semantic search to recommend the most relevant "
            "SHL Individual Test Solutions based on your job description."
        )
        st.markdown("**Recommended:** Use API endpoint for optimal performance.")
    
    # Main content
    col1, col2 = st.columns([3, 1])
    
    with col1:
        input_method = st.radio(
            "Input Method",
            ["Text Input", "URL"],
            horizontal=True
        )
    
    # Input section
    query = ""
    
    if input_method == "Text Input":
        # Check if there's a selected query from history
        selected_query = st.session_state.get('selected_query', '')
        if selected_query:
            query = st.text_area(
                "Job Description or Query",
                height=150,
                value=selected_query,
                placeholder="Enter a job description or query. For example:\n"
                           "'I need to hire a Java developer who can collaborate with business teams.'"
            )
            # Clear selected query after use
            del st.session_state['selected_query']
        else:
            query = st.text_area(
                "Job Description or Query",
                height=150,
                placeholder="Enter a job description or query. For example:\n"
                           "'I need to hire a Java developer who can collaborate with business teams.'"
            )
    else:
        url_input = st.text_input(
            "Job Description URL",
            placeholder="https://example.com/job-posting"
        )
        
        if url_input:
            with st.spinner("Fetching job description..."):
                jd_text = fetch_jd_from_url(url_input)
                if jd_text:
                    query = st.text_area(
                        "Fetched Job Description",
                        value=jd_text,
                        height=200
                    )
                else:
                    st.error("Failed to fetch job description from URL. Please try again or use text input.")
    
    # Recommendation button
    if st.button("🔍 Get Recommendations", type="primary", use_container_width=True):
        if not query or not query.strip():
            st.warning("Please enter a job description or query.")
        else:
            recommendations = []  # Initialize recommendations list
            
            # Get API URL from session state or sidebar input
            if use_api:
                api_url = st.session_state.get('api_url', os.getenv("API_URL", "http://localhost:8000"))
            else:
                api_url = None
            
            # Prioritize API endpoint
            if use_api:
                if not api_url:
                    st.error("⚠️ Please provide an API URL in the settings.")
                    st.info("💡 Default: http://localhost:8000")
                    st.stop()
                
                # Progress indicator
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    status_text.text("🔍 Connecting to API...")
                    progress_bar.progress(10)
                    
                    # Use API endpoint (recommended)
                    response = requests.post(
                        f"{api_url}/recommend",
                        json={"query": query},
                        timeout=30
                    )
                    
                    progress_bar.progress(50)
                    status_text.text("🔍 Processing recommendations...")
                    
                    response.raise_for_status()
                    data = response.json()
                    recommendations = data.get("recommendations", [])
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Recommendations received!")
                    time.sleep(0.5)  # Brief delay to show completion
                    progress_bar.empty()
                    status_text.empty()
                
                except requests.exceptions.ConnectionError:
                    progress_bar.empty()
                    status_text.empty()
                    st.error("❌ Cannot connect to API server. Please ensure the API is running.")
                    st.info("💡 Start the API with: `python api.py`")
                    st.info("💡 Or uncheck 'Use API endpoint' to use local recommender.")
                    st.stop()
                
                except requests.exceptions.Timeout:
                    progress_bar.empty()
                    status_text.empty()
                    st.error("⏱️ API request timed out. The server may be slow or overloaded.")
                    st.info("💡 Try again or use local recommender as fallback.")
                    st.stop()
                
                except requests.exceptions.RequestException as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"❌ API request failed: {str(e)}")
                    st.info("💡 Check if the API server is running and accessible.")
                    st.info("💡 You can switch to local recommender in settings.")
                    st.stop()
                
                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"❌ Unexpected error with API: {str(e)}")
                    st.info("💡 Falling back to local recommender...")
                    recommendations = []  # Clear recommendations on error
            
            # Fallback to local recommender if API is not used or failed
            if not use_api or (use_api and not recommendations):
                with st.spinner("🔍 Finding the best assessments (using local recommender)..."):
                    try:
                        recommender = get_recommender()
                        if recommender is None:
                            st.error("Failed to initialize recommender. Please check your configuration.")
                            st.info("💡 Make sure you have run `python embedder.py` to create the index.")
                            st.stop()
                        
                        # Helper function to clean nan values
                        def clean_value(value):
                            """Convert pandas nan/None to empty string."""
                            if value is None:
                                return ''
                            if isinstance(value, float) and (value != value or value == float('nan')):
                                return ''
                            if isinstance(value, str) and (value.lower() == 'nan' or value.strip() == ''):
                                return ''
                            return str(value) if value else ''
                        
                        recs = recommender.recommend(query, top_k=10)
                        recommendations = []
                        for rec in recs:
                            recommendations.append({
                                "name": rec.get('Assessment Name', rec.get('name', 'Unknown')),
                                "url": rec.get('URL', rec.get('url', '')),
                                "type": clean_value(rec.get('Test Type', rec.get('type', ''))),
                                "similarity": rec.get('similarity', 0.0),
                                "description": clean_value(rec.get('Description', rec.get('description', ''))),
                                "duration": clean_value(rec.get('Duration', rec.get('duration', ''))),
                                "difficulty": clean_value(rec.get('Difficulty', rec.get('difficulty', ''))),
                                "skills": clean_value(rec.get('Skills', rec.get('skills', ''))),
                                "prerequisites": clean_value(rec.get('Prerequisites', rec.get('prerequisites', ''))),
                                "use_cases": clean_value(rec.get('Use Cases', rec.get('use_cases', ''))),
                                "industry": clean_value(rec.get('Industry', rec.get('industry', '')))
                            })
                    
                    except Exception as e:
                        st.error(f"Error with local recommender: {e}")
                        logger.error(f"Error: {e}", exc_info=True)
                        st.info("💡 Try using the API endpoint for better reliability")
                        recommendations = []
            
            # Display results (common for both API and local)
            if recommendations:
                st.success(f"✅ Found {len(recommendations)} recommendations!")
                if use_api:
                    st.info("💡 Results powered by API endpoint with Gemini re-ranking")
                
                # Add to query history
                st.session_state.query_history.append({
                    'query': query,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'results_count': len(recommendations)
                })
                
                # Export functionality
                st.markdown("---")
                col_export1, col_export2, col_export3 = st.columns(3)
                
                with col_export1:
                    # Export to CSV
                    df = pd.DataFrame([
                        {
                            'Name': rec['name'],
                            'URL': rec.get('url', ''),
                            'Type': rec.get('type', ''),
                            'Similarity': rec.get('similarity', 0.0),
                            'Description': rec.get('description', '')[:100] if rec.get('description') else '',
                            'Skills': rec.get('skills', '')[:100] if rec.get('skills') else ''
                        }
                        for rec in recommendations
                    ])
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"shl_recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col_export2:
                    # Copy to clipboard (simulated with text area)
                    recommendations_text = "\n".join([
                        f"{i+1}. {rec['name']} - {rec.get('url', '')}"
                        for i, rec in enumerate(recommendations)
                    ])
                    st.text_area(
                        "Copy to Clipboard",
                        value=recommendations_text,
                        height=100,
                        key="clipboard",
                        help="Select all (Ctrl+A) and copy (Ctrl+C) to copy to clipboard"
                    )
                
                with col_export3:
                    # Print view
                    if st.button("🖨️ Print View", use_container_width=True):
                        st.info("💡 Use your browser's print function (Ctrl+P)")
                
                st.markdown("---")
                
                # Results table
                st.subheader("📊 Recommended Assessments")
                
                for i, rec in enumerate(recommendations, 1):
                    with st.container():
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            st.markdown(f"### {i}. {rec['name']}")
                            
                            # Show description if available
                            description = rec.get('description', rec.get('Description', ''))
                            if description and description != 'nan' and description:
                                st.markdown(f"*{description[:200]}{'...' if len(description) > 200 else ''}*")
                            
                            # Show metadata
                            meta_parts = []
                            if rec.get('type'):
                                meta_parts.append(f"**Type:** {rec.get('type')}")
                            if rec.get('duration', rec.get('Duration')):
                                meta_parts.append(f"**Duration:** {rec.get('duration', rec.get('Duration'))}")
                            if rec.get('difficulty', rec.get('Difficulty')):
                                meta_parts.append(f"**Difficulty:** {rec.get('difficulty', rec.get('Difficulty'))}")
                            meta_parts.append(f"**Similarity:** {rec.get('similarity', 0.0):.4f}")
                            
                            st.markdown(" | ".join(meta_parts) if meta_parts else f"**Similarity:** {rec.get('similarity', 0.0):.4f}")
                            
                            # Show skills if available
                            skills = rec.get('skills', rec.get('Skills', ''))
                            if skills and skills != 'nan' and skills:
                                st.markdown(f"**Skills:** {skills[:150]}{'...' if len(str(skills)) > 150 else ''}")
                        
                        with col2:
                            if rec.get('url'):
                                st.markdown(f"[🔗 View Assessment]({rec['url']})")
                        
                        st.markdown("---")
                
                # Summary statistics
                st.markdown("### 📈 Summary")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Recommendations", len(recommendations))
                
                with col2:
                    k_count = sum(1 for r in recommendations if r.get('type', '').upper() in ['K', 'H'])
                    st.metric("Knowledge Tests (K)", k_count)
                
                with col3:
                    p_count = sum(1 for r in recommendations if r.get('type', '').upper() in ['P', 'H'])
                    st.metric("Personality Tests (P)", p_count)
            
            else:
                if not query or not query.strip():
                    pass  # Already warned above
                else:
                    st.warning("No recommendations found. Please try a different query.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #6B7280;'>"
        "SHL Assessment Recommendation System | Powered by Semantic Search"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

