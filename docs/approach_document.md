# Design Approach: Conversational Assessment Recommender

This document outlines the design decisions, RAG implementation details, prompting strategies, and evaluation methodologies used to build the **Conversational Assessment Recommender**.

---

## 1. Architectural Design Choices
We adopted **Clean Architecture** and **Dependency Injection** principles to ensure decoupling and testability. The directory structure isolates concern layers:
* **API Route Layer** (`app/api/`): Handles HTTP routing. Utilizes FastAPI's dependency injection system to inject singletons (Retriever, Agent), minimizing context rebuild overhead.
* **Core Infrastructure** (`app/core/`): Handles type-safe configuration reading (`pydantic-settings` from `.env`) and unified logging.
* **Schema definitions** (`app/schemas/`): Restricts inputs/outputs strictly to the non-negotiable request/response schemas.
* **Service Interfaces** (`app/scraper.py`, `app/retriever.py`, `app/agent.py`): Encapsulates isolated chunks of business logic.

To satisfy the strict stateless requirement, no conversation history is persisted inside the service memory. Every `POST /chat` invocation carries the full conversation history, which the agent analyzes in real-time alongside retrieved context.

---

## 2. Retrieval-Augmented Generation (RAG) Setup
A pure prompt-based approach would fail due to context window limits, token cost, and hallucination risks. We built a structured RAG pipeline:
* **Data Scraper & Cleaning**: Parses the raw JSON database served on the host. To tolerate unescaped tabs and carriage returns, we used `strict=False` in JSON parsing.
* **Job Solutions Filter**: Automatically screens out pre-packaged job solutions by filtering out item names ending with the word "Solution" or "Solutions" (e.g., `Customer Service Phone Solution`), retaining only individual test components (e.g., `Customer Service Phone Simulation`).
* **Embeddings & Vector Database**: Uses **ChromaDB** as the persistent storage engine. Catalog records are embedded into dense 384-dimensional vectors using the local, lightweight **Sentence-Transformers** `all-MiniLM-L6-v2` model. This model runs completely offline with sub-100ms similarity query latency.
* **Document Chunking**: Each catalog entry is stored as a single document. This keeps description, job levels, and languages together, avoiding context fragmentation.

### Cold-Start Optimization
To respect the 2-minute cold-start window:
1. **Docker Caching**: We trigger `python -m scripts.build_vector_db` *during* the docker container build process. The vector database is pre-compiled inside the container image, reducing server boot-time to under 1 second.
2. **Self-Healing Hook**: If deployed outside Docker, the first API request checks the document count. If it is 0, it reads `data/shl_catalog_cleaned.json` and builds the index dynamically.

---

## 3. Prompt Engineering & Schema Conformance
The agent handles four distinct behaviors (Clarify, Recommend, Refine, Compare) and Refusal rules using a unified prompt strategy:
* **JSON Schema Enforcement**: We leverage Gemini's structured output generation by feeding the Pydantic schema model (`LLMAgentResponse`) directly to `response_schema` in the generative configuration. This ensures that the generated text is 100% compliant with the non-negotiable response schema.
* **Context Grounding**: The system instructions mandate that the agent only recommend items that exist inside the retrieved catalog context, preventing hallucinations.
* **Query Refinement**: The agent concatenates all user turns to build the search query. This preserves constraints across turns (e.g. Turn 1: "Java developer", Turn 2: "add personality tests"), ensuring the retriever pulls both Java coding and personality tests.

---

## 4. Evaluation Methodology (Testing Rigor)
To evaluate the agent before submission, we built a local simulation replay harness in `scripts/evaluate_agent.py`.
* **Markdown Parser**: Parses the 10 conversation traces, extracting the multi-turn user messages and final expected shortlists.
* **Simulation Loop**: Sequentially replays the stateless conversation history against the agent.
* **Metrics**: Computes the **Mean Recall@10** by calculating the overlap of matched URLs between the agent's recommended list and the trace's expected list:
  $$\text{Recall@10} = \frac{|\text{Recommended URLs} \cap \text{Expected URLs}|}{|\text{Expected URLs}|}$$
* **Probes**: Injects off-topic prompts and vague turn-1 queries to verify the pass rate of safety rules and clarification loops.

---

## 5. Lessons Learned & Iterative Refinements
* **Dirty Catalog Entries**: The raw catalog contains formatting anomalies (e.g., `Microsoft \n    365 (New)` with a missing product word and line breaks). We resolved this by cleaning strings and implementing URL-based normalizations during the scraping phase (e.g. mapping `microsoft-excel-365-new` link directly to `Microsoft Excel 365 (New)`).
* **Missing API Key Fallback**: We implemented an automatic fallback to rule-based mock logic in the agent when `GEMINI_API_KEY` is not present, allowing offline tests to pass without API costs.
