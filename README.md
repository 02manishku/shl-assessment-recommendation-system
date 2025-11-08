# SHL Assessment Recommendation System

An intelligent web-based recommendation system that recommends the most relevant SHL Individual Test Solutions based on job descriptions or natural language queries using semantic search with vector embeddings.

## 🎯 Features

- **Semantic Search**: Uses Gemini embeddings and FAISS for efficient similarity search
- **REST API**: FastAPI backend with `/health` and `/recommend` endpoints
- **Web Interface**: Beautiful Streamlit UI with SHL color theme
- **Batch Processing**: Generate predictions for multiple queries at once
- **Type Balancing**: Automatically balances Knowledge (K) and Personality (P) test recommendations

## 🏗️ Architecture

```
┌─────────────────┐
│  data_loader.py │  → Clean and prepare catalog data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  embedder.py    │  → Generate embeddings and build FAISS index
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ recommender.py  │  → Core recommendation logic
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐  ┌────────┐
│ api.py │  │ app.py │  → API and UI interfaces
└────────┘  └────────┘
```

## 📋 Prerequisites

- Python 3.10 or higher
- Gemini API key (for embeddings)
- SHL catalog Excel file (`data/shl_catalogue.xlsx`)

## 📁 Repository Structure

```
shl2/
├── README.md                 # Main documentation
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
│
├── api.py                   # FastAPI backend
├── app.py                   # Streamlit frontend
├── recommender.py           # Core recommendation logic
├── embedder.py              # Embedding generation
├── data_loader.py           # Data cleaning
├── generate_predictions.py  # Batch prediction generator
├── evaluate.py              # Evaluation script
│
├── docs/                    # Documentation files
├── data/                    # Data files (catalogs, indexes)
├── assets/                  # Static assets (logos)
├── tests/                   # Unit tests
└── predictions.csv          # Generated predictions
```

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd shl2
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   API_HOST=0.0.0.0
   API_PORT=8000
   API_URL=http://localhost:8000
   USE_API_BY_DEFAULT=true
   ```

4. **Prepare the data**
   - Place `shl_catalogue.xlsx` in the project root
   - Run the data loader:
     ```bash
     python data_loader.py
     ```
   - This creates `shl_catalog_cleaned.csv`

5. **Generate embeddings**
   ```bash
   python embedder.py
   ```
   - This creates `shl_index.faiss` and `shl_index.pkl`

## 📖 Usage

### 1. Data Loading and Cleaning

```bash
python data_loader.py
```

This script:
- Loads `shl_catalogue.xlsx`
- Cleans and standardizes the data
- Saves to `shl_catalog_cleaned.csv`

### 2. Embedding Generation

```bash
python embedder.py
```

This script:
- Loads cleaned catalog
- Generates Gemini embeddings for each assessment
- Builds FAISS index
- Saves index and metadata

### 3. Run the API Server (Recommended - Required for App)

**Important:** The Streamlit app uses the API endpoint by default. You must start the API server first.

```bash
python api.py
```

Or using uvicorn directly:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

**Endpoints:**
- `GET /health` - Health check
- `POST /recommend` - Get recommendations
  ```json
  {
    "query": "I need to hire a Java developer who can collaborate with business teams."
  }
  ```

### 4. Run the Streamlit App

**Note:** The app defaults to using the API endpoint. Make sure the API server is running first.

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

**Using the App:**
- **Default:** Uses API endpoint (recommended for best performance)
- **Optional:** You can uncheck "Use API endpoint" in the sidebar to use local recommender as fallback
- The app will show API connection status in the sidebar

### 5. Generate Predictions

```bash
python generate_predictions.py
```

This script:
- Loads test queries from `test_queries.csv`
- Generates recommendations for each query
- Saves to `predictions.csv` with format: `Query, Assessment_url`

## 📁 Project Structure

```
shl2/
├── data_loader.py          # Load and clean catalog data
├── embedder.py             # Generate embeddings and build FAISS index
├── recommender.py          # Core recommendation logic
├── api.py                  # FastAPI backend
├── app.py                  # Streamlit UI
├── generate_predictions.py # Batch prediction generator
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── .env                    # Environment variables (create this)
├── .gitignore              # Git ignore rules
├── shl_catalogue.xlsx     # Input catalog file (provided)
├── shl_catalog_cleaned.csv # Cleaned catalog (generated)
├── shl_index.faiss         # FAISS index (generated)
├── shl_index.pkl           # Metadata (generated)
└── predictions.csv         # Output predictions (generated)
```

## 🔧 Configuration

### Environment Variables

- `GEMINI_API_KEY`: Required. Your Gemini API key for embeddings
- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 8000)
- `TEST_QUERIES_FILE`: Path to test queries CSV (default: test_queries.csv)
- `PREDICTIONS_OUTPUT`: Output file for predictions (default: predictions.csv)

### API Configuration

The API supports CORS and can be configured in `api.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure allowed origins
    ...
)
```

## 🧪 Testing

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Get recommendations
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "Java developer with teamwork skills"}'
```

### Test the Recommender

```bash
python recommender.py
```

This runs sample queries and displays recommendations.

## 📊 Output Format

### API Response

```json
{
  "query": "Java developer with teamwork skills",
  "recommendations": [
    {
      "name": "Java Developer Coding Test",
      "url": "https://www.shl.com/...",
      "type": "K",
      "similarity": 0.8542
    },
    ...
  ]
}
```

### Predictions CSV

```csv
Query,Assessment_url
"I need a Java developer","https://www.shl.com/..."
"Looking for a data analyst","https://www.shl.com/..."
```

## 🚀 Deployment

See `DEPLOYMENT_GUIDE.md` for comprehensive deployment instructions.

### Quick Deployment Steps

#### Deploy API to Render (Recommended - 5 minutes)

1. **Create Render Account:** Sign up at [render.com](https://render.com) with GitHub
2. **Create Web Service:** New → Web Service → Connect repository
3. **Configure Service:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn api:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables:** Add `GEMINI_API_KEY`
4. **Deploy:** Click "Create Web Service" and wait ~5 minutes
5. **Copy API URL:** Use for Streamlit app (e.g., `https://shl-api.onrender.com`)

#### Deploy Streamlit App to Streamlit Cloud (3 minutes)

1. **Sign up:** Go to [streamlit.io/cloud](https://streamlit.io/cloud) with GitHub
2. **New App:** Click "New app" → Select repository → Set `app.py` as main file
3. **Secrets:** Add in Advanced Settings:
   ```toml
   GEMINI_API_KEY="your_api_key_here"
   API_URL="https://your-render-api-url.onrender.com"
   USE_API_BY_DEFAULT="true"
   ```
4. **Deploy:** Click "Deploy" and wait ~2 minutes
5. **Access:** Your app is live at `https://yourapp.streamlit.app`

#### Test Your Deployed API

```bash
# Health check
curl https://your-api-url.onrender.com/health

# Get recommendations
curl -X POST https://your-api-url.onrender.com/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "Java developer with teamwork skills", "top_k": 10}'

# Expected response
{"query": "Java developer...", "recommendations": [...]}
```

#### Troubleshooting

- **API not responding:** Check Render logs, verify GEMINI_API_KEY is set
- **Streamlit can't connect:** Update API_URL in secrets to match Render URL
- **Index files missing:** Upload to cloud storage or generate on startup

## 📈 Evaluation

The system uses semantic search with cosine similarity. To evaluate:

1. Prepare labeled test data
2. Run `generate_predictions.py`
3. Calculate metrics:
   - **Recall@10**: Percentage of relevant assessments found in top 10
   - **Mean Reciprocal Rank (MRR)**: Average rank of first relevant result
   - **Precision@K**: Percentage of relevant results in top K

## 🔍 How It Works

1. **Data Preparation**: Catalog is cleaned and standardized
2. **Embedding Generation**: Each assessment description is converted to a vector embedding using Gemini
3. **Index Building**: Embeddings are stored in a FAISS index for fast similarity search
4. **Query Processing**: User queries are embedded and compared against catalog embeddings
5. **Recommendation**: Top-K most similar assessments are returned using cosine similarity

## 🛠️ Troubleshooting

### Common Issues

1. **"Index file not found"**
   - Run `embedder.py` first to generate the index

2. **"Gemini API key not found"**
   - Ensure `.env` file exists with `GEMINI_API_KEY` set

3. **"Catalog file not found"**
   - Ensure `shl_catalogue.xlsx` exists and run `data_loader.py`

4. **API connection errors**
   - Check that API server is running
   - Verify API_URL in Streamlit app matches server address

## 📝 License

This project is part of an assignment for building an SHL Assessment Recommendation System.

## 👥 Author

Built as part of the SHL Assessment Recommendation System assignment.

## 🙏 Acknowledgments

- SHL for the assessment catalog
- Google Gemini for embedding capabilities
- FAISS for efficient vector search

