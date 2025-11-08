# 🚀 Deployment Guide

Complete guide for deploying the SHL Assessment Recommendation System to production.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [API Deployment (Render/Heroku/Cloud Run)](#api-deployment)
3. [Streamlit App Deployment (Streamlit Cloud)](#streamlit-deployment)
4. [Environment Variables](#environment-variables)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- GitHub repository with your code
- Gemini API key
- Account on hosting platform (Render/Heroku/Streamlit Cloud)
- Basic knowledge of environment variables

---

## API Deployment

### Option 1: Render (Recommended)

#### Step 1: Create Render Account
1. Go to [Render](https://render.com)
2. Sign up with GitHub

#### Step 2: Create New Web Service
1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Select the repository

#### Step 3: Configure Service
- **Name**: `shl-recommendation-api`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn api:app --host 0.0.0.0 --port $PORT`
- **Instance Type**: Free tier (or paid for better performance)

#### Step 4: Set Environment Variables
In Render dashboard, add these environment variables:

```
GEMINI_API_KEY=your_gemini_api_key_here
FAISS_INDEX_FILE=shl_index.faiss
METADATA_FILE=shl_index.pkl
RATE_LIMIT=60/minute
ALLOWED_ORIGINS=https://your-streamlit-app.streamlit.app
```

#### Step 5: Deploy
1. Click "Create Web Service"
2. Wait for deployment (first deployment takes ~5-10 minutes)
3. Copy the service URL (e.g., `https://shl-api.onrender.com`)

#### Step 6: Upload Index Files
Since Render's file system is ephemeral, you need to:
1. **Option A**: Include index files in repository (not recommended for large files)
2. **Option B**: Use cloud storage (S3, Google Cloud Storage)
3. **Option C**: Generate index files on first startup (slower)

**Recommended**: Use cloud storage or generate on startup.

---

### Option 2: Heroku

#### Step 1: Install Heroku CLI
```bash
# Download from https://devcenter.heroku.com/articles/heroku-cli
```

#### Step 2: Create Heroku App
```bash
heroku login
heroku create shl-recommendation-api
```

#### Step 3: Set Environment Variables
```bash
heroku config:set GEMINI_API_KEY=your_api_key
heroku config:set RATE_LIMIT=60/minute
heroku config:set ALLOWED_ORIGINS=https://your-app.streamlit.app
```

#### Step 4: Create Procfile
Create `Procfile` in project root:
```
web: uvicorn api:app --host 0.0.0.0 --port $PORT
```

#### Step 5: Deploy
```bash
git push heroku main
```

---

### Option 3: Google Cloud Run

#### Step 1: Install gcloud CLI
```bash
# Install from https://cloud.google.com/sdk/docs/install
```

#### Step 2: Create Dockerfile
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
```

#### Step 3: Build and Deploy
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/shl-api
gcloud run deploy shl-api \
  --image gcr.io/YOUR_PROJECT_ID/shl-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Step 4: Set Environment Variables
```bash
gcloud run services update shl-api \
  --set-env-vars GEMINI_API_KEY=your_key,RATE_LIMIT=60/minute
```

---

## Streamlit Deployment

### Streamlit Cloud (Recommended)

#### Step 1: Create Streamlit Cloud Account
1. Go to [Streamlit Cloud](https://streamlit.io/cloud)
2. Sign up with GitHub

#### Step 2: Deploy App
1. Click "New app"
2. Select your GitHub repository
3. Set main file path: `app.py`
4. Set branch: `main` (or your default branch)

#### Step 3: Configure App
- **App URL**: Auto-generated (e.g., `https://shl-app.streamlit.app`)
- **Python version**: 3.10+

#### Step 4: Set Environment Variables
In Streamlit Cloud dashboard, go to "Advanced settings" → "Secrets":

```toml
GEMINI_API_KEY="your_gemini_api_key_here"
API_URL="https://your-api-url.onrender.com"
USE_API_BY_DEFAULT="true"
```

#### Step 5: Deploy
1. Click "Deploy"
2. Wait for deployment (~2-5 minutes)
3. Access your app at the generated URL

---

### Alternative: Self-Hosted Streamlit

#### Step 1: Install Streamlit
```bash
pip install streamlit
```

#### Step 2: Run App
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

#### Step 3: Use Reverse Proxy (Nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Environment Variables

### API Server (.env)

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
API_HOST=0.0.0.0
API_PORT=8000
RATE_LIMIT=60/minute
ALLOWED_ORIGINS=https://your-app.streamlit.app
GEMINI_API_TIMEOUT=30
FAISS_INDEX_FILE=shl_index.faiss
METADATA_FILE=shl_index.pkl
LOG_LEVEL=INFO
```

### Streamlit App (Streamlit Cloud Secrets)

```toml
GEMINI_API_KEY="your_gemini_api_key_here"
API_URL="https://your-api-url.onrender.com"
USE_API_BY_DEFAULT="true"
```

---

## Post-Deployment Checklist

### API Server
- [ ] Health check endpoint works: `GET /health`
- [ ] Recommend endpoint works: `POST /recommend`
- [ ] Rate limiting is active
- [ ] CORS is configured correctly
- [ ] Logs are accessible
- [ ] Index files are loaded

### Streamlit App
- [ ] App loads without errors
- [ ] API connection works
- [ ] Recommendations are generated
- [ ] Export functionality works
- [ ] Query history works

---

## Troubleshooting

### API Issues

#### Issue: "Index file not found"
**Solution**: 
- Upload index files to cloud storage
- Or generate index files on startup
- Or include in repository (for small files)

#### Issue: "Rate limit exceeded"
**Solution**:
- Check `RATE_LIMIT` environment variable
- Increase limit if needed
- Implement caching (if not already done)

#### Issue: "CORS error"
**Solution**:
- Set `ALLOWED_ORIGINS` to your Streamlit app URL
- Don't use `*` in production
- Check API logs for CORS errors

#### Issue: "Gemini API timeout"
**Solution**:
- Increase `GEMINI_API_TIMEOUT` (default: 30s)
- Check Gemini API status
- Implement retry logic

### Streamlit Issues

#### Issue: "Cannot connect to API"
**Solution**:
- Check `API_URL` in secrets
- Verify API is running and accessible
- Check CORS configuration
- Test API endpoint manually

#### Issue: "No recommendations returned"
**Solution**:
- Check API logs
- Verify index files are loaded
- Test API endpoint directly
- Check Gemini API key

#### Issue: "App crashes on startup"
**Solution**:
- Check Streamlit Cloud logs
- Verify all dependencies in `requirements.txt`
- Check environment variables
- Test locally first

---

## Monitoring and Maintenance

### API Monitoring
- Monitor response times
- Check error rates
- Monitor rate limit hits
- Track API usage

### Streamlit Monitoring
- Monitor app usage
- Check for errors in logs
- Monitor API connection status
- Track user queries

### Maintenance Tasks
- Update dependencies regularly
- Monitor Gemini API usage
- Backup index files
- Review and update rate limits
- Monitor costs

---

## Cost Estimation

### Render (Free Tier)
- **API**: Free (with limitations)
- **Limitations**: 750 hours/month, sleeps after 15 min inactivity

### Heroku (Free Tier - Discontinued)
- Use paid tier or alternative platform

### Streamlit Cloud
- **Free**: Unlimited public apps
- **Team**: $20/user/month (private apps)

### Gemini API
- **Free tier**: 60 requests/minute
- **Paid**: Pay per use
- Check [Google AI pricing](https://ai.google.dev/pricing)

---

## Security Best Practices

1. **Never commit API keys** - Use environment variables
2. **Use HTTPS** - Always use SSL/TLS in production
3. **Set CORS properly** - Don't use `*` in production
4. **Rate limiting** - Prevent abuse
5. **Input validation** - Validate all user inputs
6. **Error handling** - Don't expose sensitive information
7. **Regular updates** - Keep dependencies updated
8. **Monitoring** - Monitor for suspicious activity

---

## Support

For issues or questions:
1. Check logs first
2. Review this guide
3. Check GitHub issues
4. Contact support

---

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Google Gemini API](https://ai.google.dev/docs)

---

**Last Updated**: 2024

