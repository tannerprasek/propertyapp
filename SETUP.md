# Polymarket Transcript Scanner - Setup Instructions

## Running Locally on Your Machine

If you want to run this application on your local computer:

### Prerequisites
- Python 3.11+
- Node.js 16+
- Git

### Setup Steps

1. **Clone the repository** (if not already cloned):
```bash
git clone <your-repo-url>
cd propertyapp
```

2. **Backend Setup**:
```bash
cd backend
pip install -r requirements.txt
python main.py
```

The backend will start on `http://localhost:8000`

3. **Frontend Setup** (in a new terminal):
```bash
cd frontend
npm install
npm start
```

The frontend will start on `http://localhost:3000`

4. **Access the Application**:
Open your browser to: `http://localhost:3000`

---

## How to Use

1. **Enter a stock ticker** (e.g., AAPL, TSLA, NVDA)
2. **Click "Search Markets"** to find Polymarket betting markets
3. **Click "Analyze All Markets"** to:
   - Pull 2 years of earnings call transcripts
   - Scan for keyword mentions
   - Identify mispriced betting opportunities
4. **Review the analysis** showing opportunities with recommendations

---

## What It Does

This tool helps identify mispriced prediction market opportunities by:
- Fetching Polymarket "mentions" markets for earnings calls
- Analyzing 2 years of historical earnings transcripts
- Using statistical probability models to detect pricing inefficiencies
- Highlighting opportunities where historical data suggests better odds

---

## Current Status

✅ All code is committed and pushed to: `claude/stock-web-interface-011CV4dmRGbwfMCrppFCgo19`

The application includes:
- React frontend with stock search interface
- FastAPI backend with transcript analysis
- Polymarket API integration
- Earnings transcript scrapers (SeekingAlpha, Motley Fool)
- Probability model for mispricing detection
- Sentiment analysis and keyword matching
