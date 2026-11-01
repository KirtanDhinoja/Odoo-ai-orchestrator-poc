# Reelo AI Candidate Practical Test - Odoo Orchestrator

## How to Run
1. `pip install -r requirements.txt`
2. Add your Groq API key to `.env`
3. `python main.py`

## Architecture Overview
This PoC implements a **Router-Executor pattern** using LangGraph to ensure tool-first correctness over ERP data.
* **Routing (`graph.py`):** Uses an LLM with structured output strictly to classify intent and extract arguments (bounded context).
* **Tools (`tools.py`):** 100% deterministic Python functions. The LLM is isolated from making compliance or stock decisions to prevent hallucinations.
* **State (`graph.py`):** LangGraph `SessionState` maintains minimal memory (`last_intent`, `last_product_ids`) for follow-up context.
* **Observability (`logger.py`):** Structured JSON traces log intent, latencies, and tool arguments per request.