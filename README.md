# LLM Cost & Latency Tracker

A local Python project that records LLM request metrics and displays them in a Streamlit dashboard. It uses Ollama to run Llama 3.2 locally, and SQLite to store each request.

## Features

- Records model, prompt and completion tokens, total tokens, latency, status, prompt, and response
- Stores request history in SQLite
- Displays request, token, latency, and cost metrics in a dashboard
- Filters by model and request status
- Shows latency and token usage charts, plus slowest and most expensive requests
- Runs locally with Ollama; no paid model API is required

## Requirements

- Python 3.12 or later
- [Ollama](https://ollama.com/download)
- The `llama3.2` model

## Setup

Pull the model:

```powershell
ollama pull llama3.2