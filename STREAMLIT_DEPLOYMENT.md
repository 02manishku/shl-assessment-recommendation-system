# Streamlit Cloud Deployment Guide

## Quick Steps (3 minutes)

1. **Go to Streamlit Cloud**
   - Visit: https://streamlit.io/cloud
   - Sign in with your GitHub account

2. **Create New App**
   - Click "New app" button
   - Select repository: `02manishku/shl-assessment-recommendation-system`
   - Set main file: `app.py`
   - Branch: `main`

3. **Configure Secrets**
   - Click "Advanced settings"
   - Under "Secrets", add:
   ```toml
   GEMINI_API_KEY="your_gemini_api_key_here"
   API_URL="https://shl-assessment-recommendation-system-rkiz.onrender.com"
   USE_API_BY_DEFAULT="true"
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes for build
   - Your app will be live at: `https://yourapp.streamlit.app`

5. **Update Report**
   - After deployment, update `docs/SHL_two_page_report.md` with Streamlit URL
   - Commit and push to GitHub

## Troubleshooting

- **Build fails**: Check logs, ensure `requirements.txt` is correct
- **Can't connect to API**: Verify `API_URL` in secrets matches Render URL
- **Missing environment variables**: Double-check secrets configuration

## Done!

Once Streamlit is deployed, all deliverables are complete:
- ✅ GitHub Repository
- ✅ API Endpoint (Render)
- ✅ Streamlit App (Streamlit Cloud)
- ✅ predictions.csv
- ✅ Technical Report

