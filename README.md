# Polymarket Transcript Scanner

An intelligent application that scans company transcripts for mentions of prediction market opportunities on Polymarket, analyzes sentiment and context, and identifies mispriced positions using statistical probability modeling.

## Features

- **Polymarket Market Monitoring**: Automatically fetches available markets and keywords from Polymarket
- **Transcript Collection**: Pulls transcripts from SEC EDGAR, earnings call services, and company IR sites
- **Intelligent Keyword Matching**: Matches transcript content against Polymarket market keywords
- **Sentiment Analysis**: Analyzes the tone and context of mentions
- **Probability Modeling**: Calculates base probabilities from transcript analysis
- **Mispricing Detection**: Identifies discrepancies between model probability and market probability
- **Dashboard**: Visual interface for exploring results and opportunities

## Architecture

```
backend/          - FastAPI application
  app/
    api/         - REST API endpoints
    models.py    - SQLAlchemy database models
    integrations/ - External API integrations
    processing/   - Text processing and NLP
    analysis/     - Probability modeling

frontend/         - React dashboard
  src/
    components/
    pages/
    services/

docker-compose.yml - Multi-container setup
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+

### Development Setup

1. **Clone and setup environment**
```bash
git clone <repo>
cd propertyapp
cp .env.example .env
```

2. **Start with Docker**
```bash
make docker-up
```

Or run locally:
```bash
make install
make dev-backend  # Terminal 1
make dev-frontend # Terminal 2
```

### API Endpoints

**Markets**
- `GET /api/markets` - List all markets
- `GET /api/markets/{market_id}` - Get market details
- `POST /api/markets` - Create market record
- `GET /api/markets/sync/polymarket` - Sync with Polymarket API

**Transcripts**
- `GET /api/transcripts` - List transcripts
- `GET /api/transcripts/{transcript_id}` - Get transcript with mentions
- `POST /api/transcripts` - Add new transcript
- `POST /api/transcripts/fetch/{company_id}/all` - Fetch company transcripts
- `POST /api/transcripts/process/{transcript_id}` - Process transcript

**Companies**
- `GET /api/companies` - List companies
- `GET /api/companies/{company_id}` - Get company details
- `POST /api/companies` - Create company record

**Analysis**
- `POST /api/analysis/scan` - Run transcript scan
- `GET /api/analysis/results` - Get latest scan results
- `GET /api/analysis/mispriced` - Get mispriced opportunities
- `GET /api/analysis/market/{market_id}/analysis` - Market analysis

## Configuration

### Environment Variables

Create `.env` file:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/polymarket_scanner
POLYMARKET_API_KEY=your_key
SEC_EDGAR_API_KEY=your_key
DEBUG=True
```

### Database

PostgreSQL 15+ is required. Initialize with:
```bash
make db-migrate
make db-seed  # Optional: load sample data
```

## Data Model

### Key Tables
- **PolymarketMarkets**: Available markets and odds
- **Companies**: Tracked companies
- **Transcripts**: Collected earnings calls and events
- **Mentions**: Keyword mentions within transcripts
- **ProbabilityModels**: Model results and recommendations

## Analysis Pipeline

1. **Fetch Markets** → Get Polymarket markets and keywords
2. **Collect Transcripts** → Pull from SEC EDGAR, earnings services
3. **Process Text** → Clean and normalize
4. **Find Mentions** → Match keywords with confidence scoring
5. **Calculate Probability** → Sentiment-weighted probability model
6. **Detect Mispricing** → Compare vs. market odds
7. **Rank Opportunities** → Sort by potential and confidence

## Probability Model

Uses multi-factor approach:
- **Sentiment Analysis**: Positive/negative mention ratio
- **Confidence Scoring**: Keyword match strength and context relevance
- **Mention Frequency**: Number of supporting mentions
- **Recency Weighting**: Recent transcripts weighted higher
- **Bayesian Updates**: Prior odds updated with new evidence

## Performance Considerations

- Cached Polymarket market data (syncs every hour)
- Batch transcript processing
- Indexed transcript searches
- Connection pooling for database
- Frontend lazy loading for large datasets

## Contributing

1. Create feature branch: `git checkout -b feature/name`
2. Commit changes: `git commit -am "Add feature"`
3. Push branch: `git push origin feature/name`
4. Submit pull request

## Testing

```bash
# Run backend tests
make test

# Run with coverage
pytest --cov=app backend/
```

## Deployment

### Docker Production Build
```bash
make build
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Setup
- Configure PostgreSQL with backup
- Set up monitoring and alerting
- Configure API rate limiting
- Enable HTTPS/SSL

## Troubleshooting

**Database connection error**
```bash
docker-compose logs postgres
docker-compose exec postgres psql -U polymarket -d polymarket_scanner
```

**API not responding**
```bash
docker-compose logs backend
```

**Frontend build issues**
```bash
cd frontend
npm cache clean --force
npm install
```

## License

Proprietary - Tanner Prasek

## Support

For issues, check:
1. Environment variables configured in `.env`
2. Database is running and accessible
3. API keys are valid
4. Docker containers are healthy: `docker-compose ps`

## Roadmap

- [ ] Real-time market data streaming
- [ ] Advanced NLP entity recognition
- [ ] Machine learning model improvements
- [ ] Mobile app interface
- [ ] Email alerts for opportunities
- [ ] Historical performance tracking
- [ ] Integration with trading APIs
- [ ] Multi-language support
