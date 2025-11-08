# Documentation Index

This directory contains all project documentation files.

## 📚 Documentation Files

### Core Documentation
- **README.md** (in root) - Main project documentation and setup guide

### Submission Documents
- **SHL_two_page_report.md** - Technical report for SHL submission
- **SUBMISSION_CHECKLIST.md** - Checklist for submission requirements
- **SUBMISSION_VERIFICATION.md** - Verification report and compliance check

### Guides
- **DEPLOYMENT_GUIDE.md** - Comprehensive deployment instructions (Render, Heroku, Streamlit Cloud)
- **GITHUB_SUBMISSION_GUIDE.md** - Guide for GitHub repository setup and submission

### Development & Analysis
- **IMPROVEMENTS.md** - List of improvements and their status
- **IMPROVEMENTS_PRIORITY.md** - Prioritized improvements list
- **FINAL_AUDIT_REPORT.md** - Complete audit report and compliance analysis
- **FINALIZATION_SUMMARY.md** - Summary of finalization changes
- **TERMINAL_ANALYSIS.md** - Analysis of terminal output and system status
- **DATA_FILES_EXPLANATION.md** - Explanation of data files and structure

### Setup & Configuration
- **LOGO_INSTRUCTIONS.md** - Instructions for adding SHL logo
- **README_SUBMISSION.md** - Submission-specific README

---

## 🗂️ Repository Structure

```
shl2/
├── README.md                 # Main documentation
├── requirements.txt          # Dependencies
├── .env.example             # Environment variables template
├── pytest.ini               # Test configuration
│
├── api.py                   # FastAPI backend
├── app.py                   # Streamlit frontend
├── recommender.py           # Core recommendation logic
├── embedder.py              # Embedding generation
├── data_loader.py           # Data cleaning
├── generate_predictions.py  # Batch prediction generator
├── evaluate.py              # Evaluation script
│
├── docs/                    # All documentation (this folder)
├── data/                    # Data files (catalogs, indexes, queries)
├── assets/                  # Static assets (logos, images)
├── tests/                   # Unit tests
└── predictions.csv          # Generated predictions (output)
```

---

## 📖 Quick Links

- [Main README](../README.md) - Start here for setup and usage
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Deploy to production
- [Technical Report](SHL_two_page_report.md) - System architecture and evaluation
- [Submission Checklist](SUBMISSION_CHECKLIST.md) - Verify submission readiness

