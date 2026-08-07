# llm-api-compare

OpenRouter notebook that compares **baseline** chat vs **constrained** generation (system prompt + strict user instruction + stop sequences).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add OPENROUTER_API_KEY
```

Get a key at [openrouter.ai/keys](https://openrouter.ai/keys).

## Run

```bash
jupyter notebook compare_apis.ipynb
```

Or open the notebook in Cursor and select the `llm-api-compare` / `.venv` kernel.

## What it shows

| Run | Messages | Stop | Typical result |
|---|---|---|---|
| Baseline | user only | none | prose + code + extras |
| Constrained | system + strict user | postamble phrases | mostly just the code |

Default model: `nvidia/nemotron-3-ultra-550b-a55b:free` (change `MODEL` in the notebook if needed).

## Notes

- Put secrets in `.env` only — never commit them. Cursor’s notebook kernel does not inherit shell `export`s.
- OpenRouter free tiers can return HTTP 200 with an `error` body when capacity is exhausted; wait and retry.
- Prefer stop phrases like `**Output` / `Sure,` — avoid `\n\n`, which can truncate multi-line code.
