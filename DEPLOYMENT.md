# Render Deployment Guide

## Prerequisites

1. **FRED API Key**: Get your free API key from [FRED API](https://fred.stlouisfed.org/docs/api/api_key.html)
2. **GitHub Account**: For repository hosting
3. **Render Account**: Sign up at [render.com](https://render.com)

## Step-by-Step Deployment

### 1. Fork and Clone Repository

1. Fork this repository to your GitHub account
2. Clone your fork locally:
```bash
git clone https://github.com/YOUR_USERNAME/mcp-fredapi-render.git
cd mcp-fredapi-render
```

### 2. Deploy on Render

#### Option A: Using Render Dashboard (Recommended)

1. **Connect GitHub**: 
   - Log into your Render account
   - Go to Dashboard and click "New +"
   - Select "Web Service"
   - Connect your GitHub account if not already connected

2. **Select Repository**:
   - Choose your forked `mcp-fredapi-render` repository
   - Click "Connect"

3. **Configure Service**:
   - **Name**: `mcp-fredapi` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Plan**: Free (or upgrade as needed)

4. **Set Environment Variables**:
   - Click "Advanced" 
   - Add environment variable:
     - **Key**: `FRED_API_KEY`
     - **Value**: Your FRED API key

5. **Deploy**:
   - Click "Create Web Service"
   - Wait for deployment to complete (usually 2-3 minutes)

#### Option B: Using render.yaml (Infrastructure as Code)

1. **Push to GitHub** (if you made local changes):
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Deploy from render.yaml**:
   - In Render dashboard, click "New +"
   - Select "Blueprint"
   - Connect your repository
   - Render will automatically detect the `render.yaml` file
   - Set the `FRED_API_KEY` environment variable when prompted
   - Click "Apply"

### 3. Verify Deployment

Once deployed, you'll get a URL like: `https://your-app-name.onrender.com`

Test the endpoints:

1. **Health Check**:
```bash
curl https://your-app-name.onrender.com/health
```

2. **API Documentation**:
   Visit: `https://your-app-name.onrender.com/docs`

3. **Test API**:
```bash
curl -X POST "https://your-app-name.onrender.com/fred/series/observations" \
     -H "Content-Type: application/json" \
     -d '{"series_id": "GDP", "limit": 5}'
```

## Configuration Options

### Environment Variables

- `FRED_API_KEY` (Required): Your FRED API key
- `PORT` (Auto-set): Port number (Render sets this automatically)

### Scaling

- **Free Plan**: 750 hours/month, sleeps after 15 minutes of inactivity
- **Starter Plan**: $7/month, no sleeping, more resources
- **Standard+**: Higher performance and availability

### Custom Domain

1. Go to your service in Render dashboard
2. Click "Settings" tab
3. Scroll to "Custom Domains"
4. Add your domain and configure DNS

## Monitoring and Logs

### View Logs

1. Go to your service in Render dashboard
2. Click "Logs" tab
3. View real-time logs and errors

### Monitoring

- **Health Check**: Service automatically monitors `/health` endpoint
- **Metrics**: Available in dashboard (CPU, memory, response times)
- **Alerts**: Configure email alerts for downtime

## Troubleshooting

### Common Issues

1. **Build Failed**:
   - Check that `requirements.txt` is properly formatted
   - Ensure Python version compatibility (3.9+)

2. **Service Won't Start**:
   - Verify `FRED_API_KEY` environment variable is set
   - Check logs for specific error messages

3. **API Key Issues**:
   - Ensure your FRED API key is valid and active
   - Check for any usage limits or restrictions

4. **Timeout Issues**:
   - FRED API calls may be slow; consider implementing caching
   - Free tier has resource limitations

### Getting Help

1. **Render Support**: [render.com/docs](https://render.com/docs)
2. **FRED API Docs**: [fred.stlouisfed.org/docs/api](https://fred.stlouisfed.org/docs/api)
3. **GitHub Issues**: Report issues in this repository

## Local Testing

Before deploying, test locally:

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set Environment Variable**:
```bash
export FRED_API_KEY=your_api_key_here
```

3. **Run Server**:
```bash
python app.py
```

4. **Test API**:
```bash
python test_api.py
```

## Updating Your Deployment

1. **Make Changes**: Edit code locally
2. **Commit and Push**:
```bash
git add .
git commit -m "Your changes"
git push origin main
```
3. **Auto-Deploy**: Render will automatically redeploy when you push to main branch

## Security Notes

- Never commit your FRED API key to version control
- Use Render's environment variables for sensitive data
- Consider implementing rate limiting for production use
- Monitor API usage to avoid exceeding FRED API limits
