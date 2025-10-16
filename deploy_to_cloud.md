# 🌐 Deploy Autonomous UPSC System to Cloud

## ☁️ GitHub Actions (FREE - Recommended)

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit - Autonomous UPSC System"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/civicbriefs-ai.git
git push -u origin main
```

### Step 2: Enable GitHub Actions
1. Go to your GitHub repository
2. Click **"Actions"** tab
3. GitHub will automatically detect the workflow file
4. The pipeline will run **daily at 6:00 AM UTC** (11:30 AM IST)

### Step 3: That's it! 
- ✅ Runs **every day automatically**
- ✅ **Your PC can be off/sleep**
- ✅ **Completely free** (GitHub gives 2000 minutes/month)
- ✅ **No maintenance** required

## 🚀 Alternative: Railway (1-Click Deploy)

### Step 1: Deploy to Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template/your-template)

### Step 2: Set Environment Variables
- `SMTP_USERNAME`: aman007chaurasia@gmail.com
- `SMTP_PASSWORD`: enyi hwru hncp lhdi
- `DATABASE_URL`: Will be auto-generated

### Step 3: Enable Cron Jobs
Railway will automatically run the daily pipeline.

## 📊 What Happens in Cloud:

**Every Day at 6:00 AM (IST):**
1. 🤖 Cloud server wakes up
2. 📰 Fetches latest UPSC news
3. 🎯 Maps to syllabus topics  
4. 📧 Sends emails to all subscribers
5. 😴 Goes back to sleep

**Benefits:**
- ✅ **Zero maintenance**
- ✅ **Always reliable**
- ✅ **Your PC can be off**
- ✅ **Free hosting**
- ✅ **Automatic scaling**

## 🔧 Manual Test (Optional)
To test the cloud pipeline manually:
1. Go to GitHub → Actions
2. Click "Daily UPSC Pipeline"
3. Click "Run workflow"
4. Check your email in 2-3 minutes

**Your autonomous UPSC system will now run in the cloud forever - completely independent of your computer!**