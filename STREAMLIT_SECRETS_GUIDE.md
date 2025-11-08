# Streamlit Cloud Secrets Configuration Guide

## 📍 Where to Add Environment Variables

1. **On the Streamlit Cloud deployment page**, click **"Advanced settings"** (blue link below the form fields)

2. **Look for "Secrets" section** - This will show a text area or code editor

3. **Paste the following TOML format secrets:**

## 🔐 Required Secrets (Copy & Paste This)

**Important:** Replace `your_gemini_api_key_here` with your actual Gemini API key!

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
API_URL = "https://shl-assessment-recommendation-system-rkiz.onrender.com"
USE_API_BY_DEFAULT = "true"
```

### Example (with actual values):
```toml
GEMINI_API_KEY = "AIzaSyC1234567890abcdefghijklmnopqrstuvwxyz"
API_URL = "https://shl-assessment-recommendation-system-rkiz.onrender.com"
USE_API_BY_DEFAULT = "true"
```

## 📝 Step-by-Step Instructions

### Step 1: Click "Advanced settings"
   - Located below the "App URL" field on the deployment page

### Step 2: Find "Secrets" section
   - You'll see a text area labeled "Secrets" or ".streamlit/secrets.toml"
   - This is where you paste the TOML format secrets

### Step 3: Paste the secrets
   Copy and paste this exact text (replace `your_gemini_api_key_here` with your actual API key):

```toml
GEMINI_API_KEY = "your_actual_gemini_api_key_here"
API_URL = "https://shl-assessment-recommendation-system-rkiz.onrender.com"
USE_API_BY_DEFAULT = "true"
```

### Step 4: Replace the API key
   - Replace `"your_actual_gemini_api_key_here"` with your real Gemini API key
   - Keep the quotes around the values
   - Don't add spaces around the `=` signs (or it's okay if you do, TOML is flexible)

### Step 5: Click "Deploy"
   - After adding secrets, go back and click the "Deploy" button
   - Streamlit will build and deploy your app

## 🔍 What Each Secret Does

| Secret | Purpose | Required |
|--------|---------|----------|
| `GEMINI_API_KEY` | Used by the recommender to generate embeddings | ✅ Yes |
| `API_URL` | Your Render API endpoint URL | ✅ Yes |
| `USE_API_BY_DEFAULT` | Sets the app to use API endpoint by default | ⚠️ Optional (default: "true") |

## ⚠️ Important Notes

1. **Format**: Use TOML format (key = "value")
2. **Quotes**: Keep quotes around string values
3. **No spaces**: Avoid extra spaces (though TOML is forgiving)
4. **API Key**: Make sure your Gemini API key is correct
5. **API URL**: Should match your Render deployment URL exactly

## 🎯 Example (What it should look like)

```
┌─────────────────────────────────────────┐
│ Advanced settings                       │
│                                         │
│ Secrets                                 │
│ ┌─────────────────────────────────────┐ │
│ │ GEMINI_API_KEY = "AIzaSy..."        │ │
│ │ API_URL = "https://shl-assessment..." │ │
│ │ USE_API_BY_DEFAULT = "true"         │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## ✅ After Adding Secrets

1. Click "Deploy" button
2. Wait 2-3 minutes for build
3. Your app will be live at: `https://shl-assessment-recommendation-system-manish.streamlit.app`
4. Test the app to make sure it connects to your API

## 🚨 Troubleshooting

### Issue: "GEMINI_API_KEY not found"
- **Fix**: Make sure you pasted the secret correctly in Advanced settings
- Check that the key is in quotes

### Issue: "Can't connect to API"
- **Fix**: Verify `API_URL` matches your Render URL exactly
- Make sure Render API is deployed and running

### Issue: Secrets not working
- **Fix**: In Streamlit Cloud, secrets are accessed via `st.secrets["GEMINI_API_KEY"]`
- Our code uses `os.getenv()` which should work, but if not, we may need to update the code

## 📚 Reference

- Streamlit Secrets Documentation: https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management

