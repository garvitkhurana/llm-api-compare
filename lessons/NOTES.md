# Lesson notes

Short concepts for each script. Run with `python lessons/NN_….py`.

## Reliability (all API lessons)

Free OpenRouter flakes (timeouts, `429`, `502`, capacity). `common.chat` handles this:

- timeouts `(connect=10s, read=60s)`
- up to **3** attempts with backoff `~1s → 2s → 4s`
- then **fallback models** from env (`OPENROUTER_MODEL_*_FALLBACKS`)
- does **not** retry bad keys (`401`/`403`) or most `400`s

You'll see `[common.chat] retry…` or `fallback model → …` in the terminal.

## 00 — Mental model
API = send `{model, messages}`, get `{choices, finish_reason, usage}` back.

**Tokens / pricing (what matters):**
| field | means |
|---|---|
| `prompt_tokens` | **input** — messages you sent |
| `completion_tokens` | **output bill bucket** — usually visible reply + thinking |
| `completion_tokens_details.reasoning_tokens` | **thinking** (when the model exposes it) |
| `total_tokens` | usually prompt + completion |

`completion_tokens` does mean something: it's what most price sheets call **output**.  
It is **not** “length of the answer string alone” if the model reasons — thinking can inflate completion while `message.content` stays short.  
`print_usage()` in `common.py` shows input / output / thinking / visible estimate.

## 01 — Message
One user string → one assistant reply. Watch `finish_reason` (`stop` vs `length`) and the usage breakdown.

## 02 — Multi-message
Conversation is a **list** of turns. Later turns see earlier ones.

## 03 — Chat
Roles: `system` / `user` / `assistant`. Knobs: `temperature`, `max_tokens`, `stop`.  
Compares baseline vs constrained (strict system + stop phrases) **and** token breakdown (in/out/think).  
Optional table: `notebooks/03_chat_compare.ipynb`.

## 04 — Tool
A tool is a **Python function** you define. Call it yourself — no LLM yet.

## 05 — Tool calling
Model emits `tool_calls` → you `run_tool` locally → append `role: tool` → chat again.  
Prompt hits calculator / reverse_string / word_stats; loop until final text (`MAX_ROUNDS`).  
Banners per round; prints high-level **final convo memory** once at the end.

## 06 — MCP
**Client** = `06_mcp.py`. **Server** = `mcp_server.py` (stdio JSON-RPC, no URL).  
Client spawns the server, then `initialize` → `list_tools` → `call_tool`.  
Do **not** run the server alone. Run: `python lessons/06_mcp.py`.

## 07 — Structured data
Ask for JSON, then **validate** (pydantic). Fail loudly if the shape is wrong.

## 08 — Responses
Read the payload: `content`, `finish_reason`, `usage` (via `print_usage`), `tool_calls`. Debugging starts here.

## 09 — Agent
Loop: model → tool_calls? run tools & continue : return answer. Cap steps. No framework.

## 10 — Gen evals
Score **final text** against checks (`contains`, `max_chars`, …). Cases in `evals/gen_cases.jsonl`.

## 11 — Agent evals
Score **behavior**: task success, tools used, step budget. Cases in `evals/agent_cases.jsonl`.

## 12 — Frameworks (optional)
Same task as the agent lesson, twice: raw `agent.py` vs LangChain `AgentExecutor`.  
Frameworks are sugar on messages + tool_calls + the loop — learn 00–11 first.
