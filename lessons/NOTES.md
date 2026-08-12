# Lesson notes

Run: `python lessons/NN_….py`. This page is the **cheat sheet** for ideas that kept coming up.

---

## One-pager — how the pieces fit

```text
messages  ──chat()──►  model
                │
         tool_calls? ──► run_tool / MCP call_tool ──► append role=tool
                │
                └── no tools ──► final text

evals: score that text (10) or the trajectory (11)
```

| Idea | Takeaway |
|---|---|
| **API memory** | No server session. Whatever is in your `messages` list *is* the convo. Resend it every `chat()`. |
| **Roles** | `user` = human; `assistant` = model (text and/or `tool_calls`); `tool` = *your* function result (`tool_call_id` must match). |
| **Who runs tools?** | Never the model. It only *asks*. You run Python (`run_tool`) or MCP (`call_tool`). |
| **Batching** | One assistant message can request **many** tools. Your loop runs each locally — that is still **one** LLM round. |
| **`step_count` (agent)** | = number of **LLM** `chat()` calls, not number of tools. |
| **Tokens / $** | `prompt` ≈ input; `completion` ≈ output bill (often includes thinking); `reasoning_tokens` ⊆ completion when exposed. Short `content` ≠ cheap if the model reasoned hard. Use `print_usage()`. |
| **`max_tokens`** | Caps the output bucket. Reasoning models can burn it on thinking and leave `content: null` — keep evals ≥ ~200. |
| **Tools registry** | Function in `tools.py` + entry in `TOOL_SPECS` (menu for model) + `DISPATCH` (name → call). `run_tool` is the helper that uses `DISPATCH` — it is **not** itself a tool. |
| **MCP** | Stdio JSON-RPC **plugin process**, not a FastAPI URL. Client (`06`) spawns `mcp_server.py`. `@mcp.tool()` registers; FastMCP dispatches (no `run_tool`). Also: resources / prompts. |
| **05 vs 09** | Same loop. 05 teaches it inline; `agent.py` packages it + `on_step` hooks. |
| **Hooks** | You pass `on_step=fn`. Agent **labels** events (`type`: `llm` / `tool` / `messages` / `final`) at call sites — not magic from the API. Today = observe/log; guardrails need a `before_tool` style veto. |
| **Evals** | 10 = unit tests on **reply text**. 11 = checks on **agent behavior** (tools used, steps, success). |

### Message append order (tool calling / agent)

```text
[user]                         ← you write once (or each new human turn)
chat()
[assistant + tool_calls]       ← append API message as-is
[tool result]…                 ← you append after run_tool / call_tool
chat() again …
[assistant final text]         ← no tool_calls → done
```

### Free OpenRouter gotchas

- Daily free-model caps (`429` / `free-models-per-day`) — retries won’t invent quota.
- Prefer `openai/gpt-oss-20b:free` for chat/tools; free Nemotron often stalls.
- `common.chat`: timeouts, 3× backoff, then `OPENROUTER_MODEL_*_FALLBACKS`.

---

## Reliability (all API lessons)

`common.chat` handles flakes:

- timeouts `(connect=10s, read=60s)`
- up to **3** attempts with backoff `~1s → 2s → 4s`
- then **fallback models** from env
- does **not** retry `401`/`403` or most `400`s

Terminal: `[common.chat] retry…` / `fallback model → …`.

---

## Per lesson

### 00 — Mental model
Shape of one request/response. Start here for `usage` / `print_usage()`.

### 01 — Message
One user string → one assistant reply. Watch `finish_reason` (`stop` vs `length`).

### 02 — Multi-message
History is a **list**. Later turns see earlier ones (fake prior assistant = handwritten, not a previous API call).

### 03 — Chat
`system` / `user` / `assistant`; `temperature`, `max_tokens`, `stop`. Baseline vs constrained + token table. Notebook: `notebooks/03_chat_compare.ipynb`.

### 04 — Tool
A tool is a normal Python function. Call it yourself — no LLM.  
`list_tools()` reads the registry; defining a function ≠ registering it for the model.

### 05 — Tool calling
Model emits `tool_calls` → you `run_tool` → append `role: tool` → chat again (loop / `MAX_ROUNDS`).  
Client ↔ model only; tools run **beside** that, in your process. Banners + final convo memory.

### 06 — MCP
**Client** `06_mcp.py` starts **server** `mcp_server.py` as a subprocess (stdio pipes — **no URL**).  
`initialize` → `list_tools` / resources / prompts → `call_tool` / `read_resource`.  
Do **not** type into the server alone (`mcp dev` needs `pip install "mcp[cli]"`). No LLM in this lesson — protocol only.

### 07 — Structured data
Ask for JSON, **validate** (pydantic). Fail loud on bad shape.

### 08 — Responses
Anatomy: `content`, `finish_reason`, `usage`, `tool_calls`. Debug from the payload.

### 09 — Agent
`agent.py` = reusable 05 loop. `step_count` = LLM rounds.  
`on_step` events: `llm` (raw API), `tool` (args/result), `messages` (history), `final`.

### 10 — Gen evals
`evals/gen_cases.jsonl` → `chat` → score text with `contains` / `not_contains` / `max_chars`.  
All checks must pass. Banners: load → reply → checks → scoreboard.

### 11 — Agent evals
Score **behavior**: tools used, step budget (LLM rounds), optional answer substring.  
Cases: `evals/agent_cases.jsonl`. Each case = several API calls — heavy on free tier.  
Daily `429` / `free-models-per-day` fails fast now (no endless retries).

### 12 — Frameworks (optional)
Same task raw vs LangChain. Sugar on messages + tool_calls + the loop — learn 00–11 first.
Both halves follow `LLM_PROVIDER` (OpenRouter or Anthropic); LangChain is not OpenRouter-only.
