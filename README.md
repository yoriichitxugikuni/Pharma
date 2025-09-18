# 🚀 PharmaGPT - AI Pharmaceutical Inventory Management

**Live Demo**: [Deployed on Render](https://pharmagpt.onrender.com)

An AI-powered pharmaceutical inventory management system with advanced analytics, demand forecasting, and smart reordering capabilities.

## ✨ Key Features

- 📊 **Real-time Dashboard** - Live inventory metrics and smart analytics
- 🤖 **AI Assistant** - Intelligent chatbot for inventory queries
- 🔮 **Demand Forecasting** - ML-powered demand prediction (Linear Regression, Random Forest, ARIMA)
- 📦 **Smart Reordering** - Automated reorder suggestions with supplier optimization
- ⏰ **Expiry Management** - Proactive expiry tracking and wastage prevention
- 💊 **Drug Interactions** - Safety checks and substitute recommendations
- 📷 **Receipt Scanner** - OCR-based inventory updates
- 📈 **Advanced Analytics** - Comprehensive reports and insights
- 🎨 **Modern UI** - Clean, responsive design optimized for all devices

## 🚀 One-Click Startup (Windows)

### Option 1: Double-Click
1. Double-click `START_PROJECT.bat`
2. Setup runs automatically
3. Open `http://localhost:8080`

### Option 2: Command Line
```bash
cd MediManage/MediManage
python start_project.py
```
Then open `http://localhost:8080`.

## 🔧 Manual Setup

### Prerequisites
- Python 3.11 recommended (3.10–3.12 OK)
- Windows 10/11 or Linux/Mac

### Steps
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r package-requirements.txt
streamlit run app.py --server.port 8080 --server.address 0.0.0.0
```

## 📁 Project Structure
```
MediManage/
├── app.py                     # Streamlit app
├── start_project.py           # Auto startup
├── START_PROJECT.bat          # Windows launcher
├── ai_chatbot.py              # Chatbot
├── ai_models.py               # Forecasting & ML
├── database.py                # DB layer
├── drug_interactions.py       # Interactions
├── receipt_scanner.py         # OCR
├── utils.py                   # Helpers
├── package-requirements.txt   # Deps
└── .streamlit/config.toml     # Streamlit config
```

## ⚡ Performance Notes
- Light theme only, no external JS
- Cached DB/models using `st.cache_resource`
- Charts/tables rendered only when needed
- Dependencies tuned for small Render free VMs

## 🚀 Deploy to Render (Free Plan)

### Quick Deploy
1. **Fork this repository**
2. **Connect to Render**:
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Use these settings:
     ```
     Name: pharmagpt
     Runtime: Python 3
     Build Command: pip install -r requirements.txt
     Start Command: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
     ```
   - **Environment Variables**:
     ```
     PYTHON_VERSION=3.11.9
     ```
3. **Deploy** - Render will automatically build and deploy your app!

### Render Optimization
- ✅ **Memory Optimized** - Uses minimal RAM (512MB free tier)
- ✅ **Fast Startup** - Optimized dependencies and caching
- ✅ **Auto-scaling** - Handles traffic spikes automatically
- ✅ **Free SSL** - HTTPS enabled by default

## ⬆️ Publish to GitHub
From the repository root (`Pharma/`):
```bash
git init
git add .
git commit -m "feat: init PharmaGPT with Render config"
# Replace with your repo URL
git branch -M main
git remote add origin https://github.com/<your-username>/pharmagpt.git
git push -u origin main
```

## 🔍 Troubleshooting
- Port in use:
  ```
  taskkill /F /IM streamlit.exe   # Windows
  pkill -f streamlit              # Linux/Mac
  ```
- Reinstall deps:
  ```
  pip install -r MediManage/MediManage/package-requirements.txt --upgrade --no-cache-dir
  ```

---
Built with ❤️ using Streamlit and Python.
