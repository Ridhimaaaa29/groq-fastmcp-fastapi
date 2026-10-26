# Groq + FastMCP + FastAPI with Langfuse Tracing & Monitoring

A FastAPI backend powered by Groq LLM inference, FastMCP tools, and complete observability with **Langfuse**.

---

## Features
- **FastMCP Tools**: Exposed in-memory and via HTTP sub-app at `/mcp-server/mcp`.
  - `add`: Sum two numbers.
  - `get_weather`: Simulated weather lookup.
- **Groq LLM Integration**: Multi-turn tool calling and reasoning with `openai/gpt-oss-120b` or custom Groq models.
- **Langfuse Tracing & Latency Monitoring**:
  - **MCP Tool Monitoring**: Traces tool calls as `tool` observations with execution duration (`duration_ms`), input parameters, and output payloads.
  - **LLM Inference Monitoring**: Traces Groq chat completions as `generation` observations capturing model names, inference duration (`duration_ms` / `inference_time_s`), and prompt/completion token usage.
  - **Trace Hierarchy**: Organizes end-to-end request pipelines under root chains (`api:/ask/local`, `api:/ask/remote`, `ask_local`).

---

## Setup & Configuration

1. **Environment Variables**:
   Copy `.env.example` to `.env` and configure your keys:
   ```env
   GROQ_API_KEY=gsk_your_groq_api_key
   GROQ_MODEL=openai/gpt-oss-120b
   MCP_PUBLIC_URL=https://your-host.example.com/mcp-server/mcp

   # Langfuse Cloud or Self-Hosted
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Application

### 1. Start the FastAPI Server
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- API Base: `http://127.0.0.1:8000`
- Interactive API Docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`
- MCP Endpoint: `http://127.0.0.1:8000/mcp-server/mcp`

### 2. Test via CLI Agent
```bash
python scripts/run_local_agent.py "What is 15 + 27 and what is the weather in Paris?"
```

### 3. Test via cURL
```bash
curl -X POST http://127.0.0.1:8000/ask/local \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the weather in Tokyo and what is 50 + 25?"}'
```

---

## Monitoring on the Langfuse Dashboard

Once your `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are configured:
1. Open [Langfuse Cloud](https://cloud.langfuse.com) (or your self-hosted instance).
2. Go to **Traces**:
   - Inspect the request hierarchy (`api:/ask/local` -> `ask_local` -> `groq_chat_completion_iter_X` -> `mcp_tool:add` / `mcp_tool:get_weather`).
3. View **Latency & Inference Time**:
   - **Generation Spans**: Shows exact inference time, TTFT, token counts, and model parameters.
   - **Tool Spans**: Shows tool execution latency and input/output payloads.
4. Go to **Dashboard & Metrics**:
   - Monitor average latency, tool call frequency, error rates, and token consumption across time.