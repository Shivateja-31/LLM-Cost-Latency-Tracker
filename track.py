import sqlite3
import time
from datetime import datetime

import requests


DB_NAME = "llm_metrics.db"
OLLAMA_URL = "http://localhost:11434/api/generate"


# Database

def init_db():
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS llm_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            model TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            latency_ms REAL,
            cost REAL,
            prompt TEXT,
            response TEXT,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()


# Model Pricing

# Ollama runs locally, so there is no API cost.
# You can add pricing for other models later.

MODEL_RATES = {
    "llama3.2": {
        "input": 0.0,
        "output": 0.0
    }
}


def calculate_cost(model, prompt_tokens, completion_tokens):

    rates = MODEL_RATES.get(
        model,
        {
            "input": 0.0,
            "output": 0.0
        }
    )

    input_cost = (
        prompt_tokens / 1_000_000
    ) * rates["input"]

    output_cost = (
        completion_tokens / 1_000_000
    ) * rates["output"]

    return input_cost + output_cost


# Call Ollama

def call_llm(prompt, model="llama3.2"):

    start_time = time.perf_counter()

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        response.raise_for_status()

        data = response.json()

        return {
            "response": data.get("response", ""),
            "prompt_tokens": data.get(
                "prompt_eval_count",
                0
            ),
            "completion_tokens": data.get(
                "eval_count",
                0
            ),
            "latency_ms": latency_ms,
            "status": "success"
        }

    except requests.exceptions.RequestException as e:

        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        return {
            "response": str(e),
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "latency_ms": latency_ms,
            "status": "error"
        }


# Save Request

def log_request(model, prompt, result):

    total_tokens = (
        result["prompt_tokens"]
        + result["completion_tokens"]
    )

    cost = calculate_cost(
        model,
        result["prompt_tokens"],
        result["completion_tokens"]
    )

    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        INSERT INTO llm_requests (
            timestamp,
            model,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            latency_ms,
            cost,
            prompt,
            response,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        model,
        result["prompt_tokens"],
        result["completion_tokens"],
        total_tokens,
        result["latency_ms"],
        cost,
        prompt,
        result["response"],
        result["status"]
    ))

    conn.commit()
    conn.close()


# Run LLM Request

def run_request(
    prompt,
    model="llama3.2"
):

    result = call_llm(
        prompt,
        model
    )

    log_request(
        model,
        prompt,
        result
    )

    return result


# Load Metrics

def load_metrics():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name='llm_requests'
    """)

    table_exists = cursor.fetchone()

    if not table_exists:
        conn.close()
        return None

    import pandas as pd

    df = pd.read_sql_query(
        "SELECT * FROM llm_requests",
        conn
    )

    conn.close()

    return df


# Main

if __name__ == "__main__":

    # Create database and table
    init_db()

    print("LLM Cost & Latency Tracker")
    print("-" * 40)

    prompt = input(
        "\nEnter your prompt: "
    )

    print("\nCalling Ollama...")

    result = run_request(
        prompt=prompt,
        model="llama3.2"
    )

    print("\nResponse:")
    print(result["response"])

    print("\nMetrics:")
    print(
        f"Prompt tokens: "
        f"{result['prompt_tokens']}"
    )

    print(
        f"Completion tokens: "
        f"{result['completion_tokens']}"
    )

    total_tokens = (
        result["prompt_tokens"]
        + result["completion_tokens"]
    )

    print(
        f"Total tokens: "
        f"{total_tokens}"
    )

    print(
        f"Latency: "
        f"{result['latency_ms']:.2f} ms"
    )

    cost = calculate_cost(
        "llama3.2",
        result["prompt_tokens"],
        result["completion_tokens"]
    )

    print(
        f"Cost: ${cost:.6f}"
    )

    print(
        f"Status: {result['status']}"
    )