# Docker Deployment Guide

## Free Hosting Options for Docker

### 1. **Render** (Easiest - Recommended)
- Free tier: 750 hours/month
- Supports Docker
- Auto-deploy from GitHub
- Free MongoDB instance available

### 2. **Railway**
- $5 free credit/month
- Easy Docker deployment
- Auto-deploy from GitHub

### 3. **Fly.io**
- Free tier available
- Good for Docker
- Global deployment

## Local Docker Deployment

### Prerequisites
- Docker Desktop installed
- Docker Compose installed

### Steps

1. **Clone your repository**
```bash
git clone https://github.com/yourusername/ai-examiner.git
cd ai-examiner
```

2. **Create .env file**
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

3. **Build and run with Docker Compose**
```bash
docker-compose up --build
```

4. **Access the application**
- Frontend: http://localhost
- Backend: http://localhost:5000
- MongoDB: localhost:27017

5. **Stop the application**
```bash
docker-compose down
```

## Deploy to Render (Free)

### Backend Deployment

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: ai-examiner-backend
   - **Environment**: Docker
   - **Region**: Choose closest to you
   - **Branch**: main
   - **Dockerfile Path**: backend/Dockerfile
   - **Docker Build Context Directory**: backend
5. Add Environment Variables:
   - `GEMINI_API_KEY`: your-api-key
   - `MONGO_URI`: your-mongodb-atlas-uri (get from MongoDB Atlas)
   - `DATABASE_NAME`: ai_examiner
6. Click "Create Web Service"
7. Note your backend URL: `https://your-app.onrender.com`

### Frontend Deployment

1. In Render, click "New +" → "Static Site"
2. Connect your repository
3. Configure:
   - **Name**: ai-examiner-frontend
   - **Branch**: main
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: frontend/build
4. Click "Create Static Site"
5. Your frontend URL: `https://ai-examiner.onrender.com`

### Update Frontend API URL

Before deploying frontend, update the API URL:

1. Edit `frontend/src/services/api.js`:
```javascript
const API_BASE_URL = 'https://your-backend.onrender.com/api';
```

2. Commit and push changes

## Deploy to Railway

1. Go to [Railway](https://railway.app)
2. Click "Start a New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect Docker
5. Add environment variables
6. Deploy!

## Deploy to Fly.io

1. Install Fly CLI:
```bash
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex

# Linux/Mac
curl -L https://fly.io/install.sh | sh
```

2. Login to Fly:
```bash
fly auth login
```

3. Deploy Backend:
```bash
cd backend
fly launch --dockerfile Dockerfile
# Follow prompts
```

4. Deploy Frontend:
```bash
cd frontend
fly launch --dockerfile Dockerfile
```

## MongoDB Setup (Free)

### Option 1: MongoDB Atlas (Recommended)
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create free cluster
3. Create database user
4. Whitelist IP: 0.0.0.0/0 (for testing)
5. Get connection string
6. Use it in your environment variables

### Option 2: Use Docker MongoDB
- Already included in docker-compose.yml
- For local development only

## Troubleshooting

### Build fails due to missing dependencies
- Ensure all requirements are in requirement.txt
- Check Dockerfile has correct base image

### Frontend can't connect to backend
- Check CORS settings in Flask
- Verify API_BASE_URL in frontend
- Ensure backend is running

### MongoDB connection issues
- Check MONGO_URI format
- Verify network access in MongoDB Atlas
- Ensure database name is correct

## Cost Optimization

**Free tier limits:**
- Render: 750 hours/month (1 service always on)
- Railway: $5 credit/month
- Fly.io: 3 shared-cpu VMs
- MongoDB Atlas: 512MB free tier

**Tips:**
- Use MongoDB Atlas free tier
- Deploy backend on Render (always on)
- Use GitHub Pages for frontend (truly free)
- Or deploy everything on single service

## Monitoring

After deployment, monitor your services:
- Check logs in hosting platform dashboard
- Set up alerts for downtime
- Monitor MongoDB usage

## Updates

To update deployed app:
1. Push changes to GitHub
2. Auto-deploy will trigger (if enabled)
3. Or manually trigger deploy from dashboard

## Security Notes

- Never commit .env file
- Use environment variables for secrets
- Keep API keys secure
- Enable authentication if making public
- Regularly update dependencies
