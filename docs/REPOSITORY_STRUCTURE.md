# 📁 Repository Structure

## Clean, Organized Repository Layout

```
shl2/
│
├── 📄 Core Application Files (Root)
│   ├── README.md                 # Main documentation - START HERE
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example             # Environment variables template
│   ├── .gitignore               # Git ignore rules
│   ├── pytest.ini               # Test configuration
│   │
│   ├── api.py                   # FastAPI backend
│   ├── app.py                   # Streamlit frontend
│   ├── recommender.py           # Core recommendation logic
│   ├── embedder.py              # Embedding generation
│   ├── data_loader.py           # Data cleaning
│   ├── data_crawler.py          # Web crawler (optional)
│   ├── generate_predictions.py  # Batch prediction generator
│   ├── evaluate.py              # Evaluation script
│   │
│   └── predictions.csv          # Generated predictions (output)
│
├── 📁 docs/                      # All Documentation
│   ├── README.md                # Documentation index
│   ├── DEPLOYMENT_GUIDE.md      # Deployment instructions
│   ├── SHL_two_page_report.md   # Technical report
│   ├── SUBMISSION_CHECKLIST.md  # Submission checklist
│   ├── SUBMISSION_VERIFICATION.md
│   ├── GITHUB_SUBMISSION_GUIDE.md
│   ├── FINAL_AUDIT_REPORT.md
│   ├── FINALIZATION_SUMMARY.md
│   ├── TERMINAL_ANALYSIS.md
│   ├── DATA_FILES_EXPLANATION.md
│   ├── IMPROVEMENTS.md
│   ├── IMPROVEMENTS_PRIORITY.md
│   ├── LOGO_INSTRUCTIONS.md
│   └── README_SUBMISSION.md
│
├── 📁 data/                      # Data Files
│   ├── shl_catalogue.xlsx       # Source catalog
│   ├── shl_catalog_cleaned.csv  # Cleaned catalog
│   ├── shl_catalog_enriched.csv # Enriched catalog
│   ├── shl_index.faiss          # FAISS vector index
│   ├── shl_index.pkl            # Metadata
│   └── test_queries.csv         # Test queries
│
├── 📁 assets/                    # Static Assets
│   └── shl_logo.png             # SHL logo
│
└── 📁 tests/                     # Unit Tests
    ├── __init__.py
    ├── test_api.py
    └── test_recommender.py
```

---

## 📂 Directory Purposes

### Root Directory (`/`)
**Purpose:** Core application files only
- Python source files (.py)
- Configuration files (.txt, .ini, .example)
- Main README.md
- Output files (predictions.csv)

### `docs/` Directory
**Purpose:** All documentation files
- Technical reports
- Deployment guides
- Submission documents
- Development notes
- Analysis reports

### `data/` Directory
**Purpose:** Data files and indexes
- Source catalogs
- Processed data
- Vector indexes
- Test queries
- **Note:** Most data files are gitignored (see .gitignore)

### `assets/` Directory
**Purpose:** Static assets
- Images
- Logos
- Icons
- Other static files

### `tests/` Directory
**Purpose:** Unit and integration tests
- Test files
- Test fixtures
- Test configuration

---

## 🎯 File Organization Principles

1. **Root Directory:** Only essential files that users interact with directly
2. **Documentation:** All .md files (except README.md) in `docs/`
3. **Data Files:** All data and indexes in `data/`
4. **Assets:** All static files in `assets/`
5. **Tests:** All test files in `tests/`

---

## 📝 Notes

- **predictions.csv** stays in root (it's a deliverable)
- **README.md** stays in root (GitHub displays it)
- Data files in `data/` are mostly gitignored (see .gitignore)
- Documentation in `docs/` is version controlled
- Assets in `assets/` are version controlled (logos, etc.)

---

## ✅ Benefits of This Structure

1. **Clean Root:** Easy to find main files
2. **Organized:** Related files grouped together
3. **Scalable:** Easy to add new files in appropriate directories
4. **Professional:** Standard project structure
5. **Maintainable:** Clear separation of concerns

---

**Last Updated:** November 8, 2025

