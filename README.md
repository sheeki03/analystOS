# analystOS

> **AI-powered research platform for crypto and traditional finance with Web UI + optional Notion automation**

A production-ready research and market intelligence platform powered by OpenRouter (50+ AI models). Analyze cryptocurrencies and stocks side-by-side, run comprehensive financial research, and automate due diligence workflows.

## Key Capabilities

| Crypto | Stocks | Cross-Asset |
|--------|--------|-------------|
| Real-time prices via CoinGecko | Fundamentals via OpenBB/FMP | Compare BTC vs VISA directly |
| Historical data & charts | SEC filings (10-K, 10-Q, 8-K) | Volatility normalization (24/7 vs market hours) |
| Top 250 coins by market cap | Income, balance sheet, cash flow | Sector-based analysis |
| AI-powered analysis | Analyst estimates & insider trades | Yield comparison (staking vs dividends) |

---

## Two Ways to Use

### Web UI (Interactive Research)
```
1. Open the Streamlit web interface
2. Upload documents, add URLs, or enter a research query
3. Use Financial Research for stocks or Crypto AI for crypto
4. Compare assets across markets with Market Intelligence
5. Get comprehensive research reports instantly
```

### Notion Automation (Zero-Touch Mode)
```
1. Connect your Notion database
2. Add a project to Notion
3. Agent automatically detects the new entry
4. AI researches, scores, and evaluates
5. Full report published back to Notion
```

---

## Features

### Financial Research (Stocks)
- **Price Data**: Real-time snapshots and historical prices via OpenBB
- **Fundamentals**: Income statements, balance sheets, cash flow statements
- **SEC Filings**: 10-K, 10-Q, 8-K with item-level extraction
- **Metrics**: Financial ratios, analyst estimates, insider trades
- **News**: Company news and market sentiment
- **AI Router**: Natural language queries routed to appropriate tools

### Crypto Intelligence
- **Live Market Data**: Real-time cryptocurrency prices via CoinGecko MCP
- **Historical Analysis**: Price history with customizable intervals
- **Top Coins**: Access to top 250 cryptocurrencies by market cap
- **AI Chat**: Interactive crypto analysis and insights
- **Portfolio Tracking**: Multi-coin comparisons and trends

### Market Intelligence (Cross-Asset)
- **Direct Comparison**: Compare crypto vs stocks (BTC vs V, ETH vs MA)
- **Volatility Analysis**: Normalized comparisons accounting for 24/7 vs market hours
- **Sector Views**: CMC-style sector categorization for tech stocks
- **Yield Comparison**: Staking APY vs dividend yields

### Research Suite
- **Multi-Format Documents**: PDF, DOCX, TXT, Markdown with OCR
- **DocSend Integration**: Automated presentation analysis
- **Web Scraping**: Firecrawl-powered sitemap discovery and extraction
- **Deep Research**: LangChain ODR framework for multi-agent research
- **RAG Chat**: Context-aware Q&A using FAISS vector search

### Entity Extraction (LangExtract)
- **Structured Extraction**: People, organizations, funding rounds, metrics
- **Source Grounding**: All entities linked to source documents
- **Smart Caching**: Results cached for unchanged content

### Notion Automation
- **Real-Time Monitoring**: Watches Notion database for new entries
- **Auto-Research**: Triggers deep research on new projects
- **AI Scoring**: Automated due diligence evaluation
- **Direct Publishing**: Reports published to Notion pages

---

## Architecture

```
├── main.py                          # Streamlit entry point
├── src/
│   ├── controllers/
│   │   └── app_controller.py        # Auth, routing, validation
│   ├── pages/
│   │   ├── interactive_research.py  # Document processing & AI analysis
│   │   ├── financial_research.py    # Stocks research UI
│   │   ├── market_intelligence.py   # Cross-asset comparison
│   │   ├── crypto_chatbot.py        # Crypto AI interface
│   │   └── notion_automation.py     # Notion CRM integration
│   ├── services/
│   │   ├── financial_tools/         # 19 financial data tools
│   │   │   ├── tools.py             # Tool implementations
│   │   │   ├── router.py            # OpenRouter-based routing
│   │   │   ├── schemas.py           # OpenAI function schemas
│   │   │   └── crypto_resolver.py   # Ticker format conversion
│   │   ├── market_intelligence/     # Cross-asset services
│   │   │   ├── cross_asset_service.py
│   │   │   ├── volatility_service.py
│   │   │   └── sector_service.py
│   │   ├── openbb/                  # OpenBB Platform client
│   │   │   └── client.py
│   │   └── mcp/                     # MCP integrations
│   │       └── coingecko_client.py  # CoinGecko data
│   ├── core/
│   │   ├── research_engine.py       # Research automation
│   │   ├── scanner_utils.py         # Web discovery (Firecrawl)
│   │   └── docsend_client.py        # DocSend processing
│   └── utils/
│       └── session_persistence.py   # Secure session management
├── config/
│   ├── users.yaml                   # User management
│   ├── mcp_config.json              # MCP integrations
│   └── sector_classifications.yaml  # Sector mappings
└── tests/
```

### Technology Stack
- **Backend**: Python 3.11+, Streamlit
- **Financial Data**: OpenBB Platform, CoinGecko, FMP
- **AI/ML**: OpenRouter, LangChain, FAISS
- **Browser Automation**: Selenium, Playwright
- **Document Processing**: PyMuPDF, Tesseract OCR
- **Visualization**: Plotly, Altair

---

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/sheeki03/analystOS.git
cd analystOS

# Install dependencies
pip install -r requirements.txt

# Install browser dependencies
playwright install

# Install Tesseract OCR (for document processing)
# macOS: brew install tesseract
# Ubuntu: sudo apt-get install tesseract-ocr
```

### 2. Configuration

Create a `.env` file:

```env
# Required: AI Model Access
OPENROUTER_API_KEY=your_openrouter_key

# Financial Data (Stocks)
FMP_API_KEY=your_fmp_key              # financialmodelingprep.com
OPENBB_PAT=your_openbb_token          # Optional, for higher limits

# Optional: Additional Providers
FINNHUB_API_KEY=your_finnhub_key      # For news
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Optional: Notion Integration
NOTION_TOKEN=your_notion_token

# Optional: Web Scraping
FIRECRAWL_API_KEY=your_firecrawl_key

# Optional: Deep Research
TAVILY_API_KEY=your_tavily_key

# Security
SESSION_SECRET_KEY=your_random_secret_key
```

### 3. Run Application

```bash
streamlit run main.py
```

Visit `http://localhost:8501` and login.

---

## Financial Tools Reference

### Price Tools
| Tool | Description | Source |
|------|-------------|--------|
| `get_price_snapshot` | Current stock price | OpenBB/FMP |
| `get_prices` | Historical stock prices | OpenBB/FMP |
| `get_crypto_price_snapshot` | Current crypto price | CoinGecko |
| `get_crypto_prices` | Historical crypto prices | CoinGecko |
| `get_available_crypto_tickers` | Top 250 crypto tickers | CoinGecko |

### Fundamentals
| Tool | Description | Source |
|------|-------------|--------|
| `get_income_statements` | Revenue, expenses, profit | OpenBB/FMP |
| `get_balance_sheets` | Assets, liabilities, equity | OpenBB/FMP |
| `get_cash_flow_statements` | Operating, investing, financing | OpenBB/FMP |
| `get_all_financial_statements` | Combined statements | OpenBB/FMP |
| `get_financial_metrics_snapshot` | Current ratios & metrics | OpenBB/FMP |
| `get_financial_metrics` | Historical metrics | OpenBB/FMP |

### Filings & Research
| Tool | Description | Source |
|------|-------------|--------|
| `get_filings` | SEC filing list | OpenBB/SEC |
| `get_10k_filing_items` | Annual report sections | OpenBB/SEC |
| `get_10q_filing_items` | Quarterly report sections | OpenBB/SEC |
| `get_8k_filing_items` | Current event reports | OpenBB/SEC |
| `get_news` | Company news | OpenBB/Finnhub |
| `get_analyst_estimates` | Earnings estimates | OpenBB/FMP |
| `get_insider_trades` | Insider transactions | OpenBB/SEC |
| `get_segmented_revenues` | Revenue by segment | OpenBB/FMP |

### Crypto Limitations
- **USD pairs only**: BTC-USD supported, BTC-ETH not supported
- **No minute interval**: Use day, week, month, or year
- **Max 365 days**: Historical data limited to 1 year from today
- **Close prices only**: Returns close + volume, not OHLC

---

## Default Watchlist

The platform comes with a default cross-asset watchlist:

**Crypto**: BTC, ETH, SOL
**Payments**: V (Visa), MA (Mastercard)
**Tech**: NVDA, INTC, MSFT, GOOGL
**Finance**: JPM, COIN, SOFI

---

## Usage Examples

### Financial Research
```
Query: "Show me AAPL revenue for the last 3 years"
→ Routes to get_income_statements(ticker="AAPL", period="annual", limit=3)

Query: "Compare NVDA and AMD financial metrics"
→ Routes to get_financial_metrics for both tickers
```

### Crypto Analysis
```
Query: "Bitcoin price last month"
→ Routes to get_crypto_prices(ticker="BTC-USD", interval="day", ...)

Query: "Top 10 cryptocurrencies"
→ Uses CoinGecko markets endpoint
```

### Cross-Asset Comparison
```
Query: "Compare BTC vs VISA market cap"
→ Uses Market Intelligence cross-asset service
```

---

## Security Features

- **HMAC-Signed Sessions**: URL session tokens are cryptographically signed
- **Input Validation**: Username/password validation with strength requirements
- **Subprocess Whitelist**: Only approved commands can execute
- **SSL Verification**: Never disabled, fails safely
- **Role-Based Access**: Admin vs researcher permissions
- **XSS Prevention**: Safe Streamlit rendering methods

---

## AI Models

Supported via OpenRouter:

| Provider | Models |
|----------|--------|
| OpenAI | GPT-5.2, GPT-5.2 Pro |
| Anthropic | Claude Sonnet 4, Claude Sonnet 4.5, Claude Opus 4.5 |
| Google | Gemini 3, Gemini 2.5 Pro, Gemini 2.5 Flash |
| Free Tier | Nemotron 3 Nano 30B, Qwen3 30B/235B, DeepSeek R1T Chimera, Molmo 2 8B Vision |
| Image Gen | Seedream 4.5 |

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific tests
pytest tests/integration/test_tool_schemas.py
pytest tests/services/test_crypto_resolver.py
```

---

## Version History

### v3.0.0 (Current)
- Added OpenBB integration for stocks/fundamentals
- Added 19 financial data tools
- Added Market Intelligence with cross-asset comparison
- Added Financial Research and Market Intelligence pages
- Enhanced CoinGecko client with markets endpoint
- Integrated Firecrawl for sitemap scanning
- Security hardening (SSL, HMAC sessions, input validation)

### v2.1.0
- Deep Research (ODR) integration
- Enhanced crypto intelligence
- Entity extraction (LangExtract)

### v2.0.0
- Notion automation
- Crypto chatbot

### v1.0.0
- Basic research and document processing

---

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/sheeki03/analystOS/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sheeki03/analystOS/discussions)

---

**Built for researchers, analysts, and investors who need comprehensive market intelligence across crypto and traditional finance.**
