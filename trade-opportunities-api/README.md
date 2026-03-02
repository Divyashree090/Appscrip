# 🏭 Trade Opportunities API

A FastAPI service that analyzes market data and provides AI-powered trade opportunity insights for Indian market sectors.

---

## 📋 Features

| Feature | Details |
|---|---|
| **AI Analysis** | Google Gemini 1.5 Flash for market insights |
| **Web Search** | DuckDuckGo search (no API key needed) |
| **Authentication** | JWT-based auth (register → login → use) |
| **Rate Limiting** | 10 requests/hour per authenticated user |
| **Caching** | 30-minute in-memory cache for reports |
| **Session Tracking** | Per-request session management |
| **Input Validation** | Pydantic validation on all inputs |
| **Docs** | Swagger UI + ReDoc auto-documentation |

---

## 🏗️ Project Structure

```
trade-opportunities-api/
├── app/
│   ├── main.py                 # FastAPI app, middleware registration
│   ├── config.py               # Settings from environment variables
│   ├── routers/
│   │   ├── auth.py             # /auth/register, /auth/login, /auth/logout
│   │   └── analyze.py          # GET /analyze/{sector}  ← core endpoint
│   ├── services/
│   │   ├── search_service.py   # DuckDuckGo web scraping
│   │   ├── gemini_service.py   # Gemini AI report generation
│   │   └── analysis_service.py # Orchestrates search + AI pipeline
│   ├── middleware/
│   │   ├── rate_limiter.py     # Request rate limiting
│   │   └── session.py          # Session tracking
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response models
│   └── utils/
│       ├── auth.py             # JWT helpers, password hashing
│       └── storage.py          # In-memory storage (users, sessions, cache)
├── requirements.txt
├── .env.example
├── run.py
└── README.md
```

---

## ⚡ Quick Start

### 1. Clone & Install

```bash
git clone <repo-url>
cd trade-opportunities-api
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your Gemini API key
```

Get a **free** Gemini API key: https://aistudio.google.com/app/apikey

```env
GEMINI_API_KEY=your_key_here
JWT_SECRET_KEY=your-random-secret-here
```

### 3. Run the Server

```bash
python run.py
# OR
uvicorn app.main:app --reload
```

Server starts at: **http://localhost:8000**

API Docs: **http://localhost:8000/docs**

---

## 🔌 API Usage

### Step 1: Register

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "trader1", "password": "mypassword123"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "username": "trader1"
}
```

### Step 2: Analyze a Sector

```bash
TOKEN="eyJhbGciOiJIUzI1NiJ9..."

curl http://localhost:8000/analyze/pharmaceuticals \
  -H "Authorization: Bearer $TOKEN"
```

### Step 3: Download as Markdown File

```bash
curl "http://localhost:8000/analyze/pharmaceuticals?format=markdown" \
  -H "Authorization: Bearer $TOKEN" \
  -o pharma-report.md
```

---

## 📝 Sample Report Structure

```markdown
# 🏭 Trade Opportunities Report: Pharmaceuticals Sector
**Analysis Date:** January 15, 2025
**Market:** India

## 📊 Executive Summary
...

## 🌍 Sector Overview
### Current Market Position
### Key Market Indicators

## 📈 Trade Opportunities
### 🟢 High-Priority Export Opportunities
### 🔵 Import Substitution Opportunities
### 🟡 Emerging Opportunities

## ⚠️ Challenges & Risk Factors

## 🏛️ Government Policies & Schemes

## 🏢 Key Players & Competitive Landscape

## 💡 Strategic Recommendations
### For Exporters
### For Importers/Buyers
### For Investors

## 📅 Outlook & Forecast

## 📚 Data Sources & References
```

---

## 🔒 Security Features

| Feature | Implementation |
|---|---|
| **Authentication** | JWT tokens (HS256, 24hr expiry) |
| **Password Storage** | SHA-256 hashed (never plain text) |
| **Input Validation** | Pydantic validators + regex patterns |
| **Rate Limiting** | 10 req/hour per user (configurable) |
| **CORS** | Configurable allowed origins |
| **Error Handling** | No stack traces exposed to clients |
| **Session Tracking** | UUID session IDs per request |

---

## 📊 All Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/` | ❌ | Health check |
| `GET` | `/health` | ❌ | Detailed health + stats |
| `POST` | `/auth/register` | ❌ | Register new user |
| `POST` | `/auth/login` | ❌ | Login, get JWT token |
| `POST` | `/auth/logout` | ✅ | Revoke token |
| `GET` | `/auth/me` | ✅ | Current user info |
| `GET` | `/analyze/` | ✅ | List example sectors |
| `GET` | `/analyze/{sector}` | ✅ | **Core: Generate report** |
| `GET` | `/docs` | ❌ | Swagger UI |
| `GET` | `/redoc` | ❌ | ReDoc documentation |

---

## ⚙️ Configuration

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(required)* | Google Gemini API key |
| `JWT_SECRET_KEY` | *(change this!)* | JWT signing secret |
| `RATE_LIMIT_REQUESTS` | `10` | Requests per window |
| `RATE_LIMIT_WINDOW` | `3600` | Window size in seconds |
| `CACHE_TTL` | `1800` | Report cache duration (seconds) |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## 🧪 Example Sectors

```
pharmaceuticals    technology         agriculture
automobile         textiles           fintech
renewable-energy   steel              chemicals
it-services        food-processing    defence
gems-and-jewellery electronics        logistics
```

---

## 🏗️ Architecture

```
Request
  │
  ▼
SessionMiddleware (assign/track session ID)
  │
  ▼
RateLimitMiddleware (check 10 req/hour limit)
  │
  ▼
JWT Authentication (verify Bearer token)
  │
  ▼
Input Validation (Pydantic + regex)
  │
  ▼
Cache Check (return if hit, 30min TTL)
  │
  ▼ (cache miss)
WebSearchService (DuckDuckGo, 4 parallel queries)
  │
  ▼
GeminiService (AI analysis with structured prompt)
  │
  ▼
Cache Store
  │
  ▼
JSON / Markdown Response
```

---

## 🚀 Production Notes

1. **Change `JWT_SECRET_KEY`** to a cryptographically random value:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Add HTTPS** via a reverse proxy (nginx, Caddy)

3. **Restrict CORS** in `app/main.py`:
   ```python
   allow_origins=["https://yourdomain.com"]
   ```

4. **Monitor** via the `/health` endpoint

---

## 📄 License

MIT License - Free to use and modify.
