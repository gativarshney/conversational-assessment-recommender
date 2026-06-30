# Conversational Assessment Recommender

An AI conversational recommendation engine that understands hiring requirements, retrieves relevant assessments using a RAG pipeline, and provides schema-compliant recommendations. Built with FastAPI, Pydantic, ChromaDB, Sentence-Transformers, and the Gemini API.

## Project Structure

```
conversational-assessment-recommender/
│
├── app/                        # Main application package
│   ├── main.py                 # FastAPI application entrypoint
│   ├── scraper.py              # Catalog scraper and text cleaning logic
│   ├── retriever.py            # ChromaDB vector index and query retriever
│   ├── agent.py                # Gemini conversation agent & RAG orchestrator
│   ├── models.py               # Domain models placeholder
│   │
│   ├── api/                    # API endpoints and routers
│   │   ├── deps.py             # Singleton providers and cold-start self-healing
│   │   └── routes.py           # /health and /chat route handlers
│   │
│   ├── core/                   # Configurations and logging helpers
│   │   ├── config.py           # Configuration loader (Pydantic Settings)
│   │   └── logging.py          # Centralized logging setup
│   │
│   └── schemas/                # Request/Response Pydantic schemas (DTOs)
│       └── chat.py             # ChatRequest and ChatResponse specifications
│
├── data/                       # Scraped catalog JSON and Chroma DB storage
│   ├── shl_catalog_cleaned.json
│   └── chroma/                 # (Git ignored) persistent vector database
│
├── docs/                       # Project documentation
│   └── approach_document.md    # 2-page design approach document
│
├── scripts/                    # Command-line utility runners
│   ├── run_scraper.py          # Raw catalog scraper trigger
│   ├── build_vector_db.py      # Embedding generator and database builder
│   └── evaluate_agent.py       # Conversation trace evaluation replayer
│
├── tests/                      # Automated unit tests
│   ├── test_api.py             # Schema & endpoints validation tests
│   ├── test_retriever.py       # Chroma DB retrieval & deserialization tests
│   └── test_agent.py           # Agent behavior & fallback tests
│
├── .env                        # Local environment variables
├── .env.example                # Example environment variables template
├── .gitignore                  # Git exclusion rules
├── Dockerfile                  # Production container packaging configuration
└── requirements.txt            # Python dependencies list
```

---

## Getting Started

### 1. Installation

Clone this repository and create a Python virtual environment:
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example configuration to `.env` and set your Gemini API key:
```bash
cp .env.example .env
```
Open `.env` and configure:
```ini
GEMINI_API_KEY="your_gemini_api_key"
```

---

## Running the Pipeline

### Step 1: Scrape Catalog
Downloads the raw catalog database, filters pre-packaged Job Solutions, cleans formatting, and generates the structured dataset:
```bash
python -m scripts.run_scraper
```

### Step 2: Build Vector DB
Computes sentence embeddings using `all-MiniLM-L6-v2` locally and indexes the catalog items into persistent ChromaDB:
```bash
python -m scripts.build_vector_db
```
*(Note: If deploying to a server, this step is automatically triggered during the Docker build process or on the first API request via a self-healing hook).*

### Step 3: Start the API
Starts the local development server at `http://127.0.0.1:8000`:
```bash
python -m uvicorn app.main:app --reload
```

---

## Testing & Evaluation

### Running Unit Tests
Executes the test suite validating schemas, scraper filters, retriever counts, and agent fallback controls:
```bash
python -m pytest
```

### Running Automated Trace Evaluation Replayer
Simulates multi-turn conversation loops against the agent using the 10 public trace markdown files, calculating the Mean Recall@10 score and running safety behavior probes:
```bash
python -m scripts.evaluate_agent
```

---

## API Documentation

The server exposes the following endpoints (reachable at root context):

### 1. GET `/health`
Readiness check.
* **Response**: `{"status": "ok"}` with HTTP 200.

### 2. POST `/chat`
Stateless conversational recommendations.
* **Request Body**:
  ```json
  {
    "messages": [
      {"role": "user", "content": "I am hiring a Java developer"},
      {"role": "assistant", "content": "What is the seniority level?"},
      {"role": "user", "content": "Mid-level, around 4 years"}
    ]
  }
  ```
* **Response Body**:
  ```json
  {
    "reply": "Got it. Here are 2 assessments that fit your requirements.",
    "recommendations": [
      {
        "name": "Core Java (Advanced Level) (New)",
        "url": "https://www.shl.com/products/product-catalog/view/core-java-advanced-level-new/",
        "test_type": "K"
      },
      {
        "name": "Java Frameworks (New)",
        "url": "https://www.shl.com/products/product-catalog/view/java-frameworks-new/",
        "test_type": "K"
      }
    ],
    "end_of_conversation": false
  }
  ```
* *Note: The recommendations list is empty when the agent is clarifying vagueness, comparing tests, or refusing unrelated topics.*
