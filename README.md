# Q&A Agent CLI

A stateless Q&A agent that answers questions about a given set of files, docs, and/or
notes. It is a simple one-shot agent: it doesn't store conversations and answers one
question at a time with no memory of previous questions.

Under the hood it parses your file(s) into chunks, retrieves the most relevant chunk
with BM25, and asks an LLM (via [OpenRouter](https://openrouter.ai)) to answer using
only that context — with automatic retry/fallback across models.

## Requirements

- Python >= 3.12
- An [OpenRouter API key](https://openrouter.ai/keys)

## Install

The project is distributed via this Git repository (not yet published to PyPI).

Install straight from GitHub with [uv](https://docs.astral.sh/uv/) (recommended) —
this exposes a global `qa-agent` command:

```bash
uv tool install "git+https://github.com/<owner>/qa-agent"
```

Or with pipx:

```bash
pipx install "git+https://github.com/<owner>/qa-agent"
```

From a local clone:

```bash
git clone https://github.com/<owner>/qa-agent
cd qa-agent
uv tool install .        # install the command
# or: uv sync            # dev setup (project + dev deps in a venv)
```

## Configure

The agent needs an OpenRouter API key. Either export it:

```bash
export OPENROUTER_API_KEY=sk-or-...
```

...or copy the template and fill it in (the CLI loads `.env` from the working directory):

```bash
cp .env.example .env
# then edit .env
```

## Usage

```bash
qa-agent <path> "<question>" [--model ALIAS] [--log-level LEVEL] [--log-file FILE]
```

- `path` — a file or a directory of files to search (`.txt`, `.md`, `.docx`, `.pdf`).
- `question` — the question to answer, in quotes.
- `--model` — optional model alias (see below). Defaults to `gemma-4-31b`.
- `--log-level` — `DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL` (default `INFO`); logs go to stderr.
- `--log-file` — also write logs to this file.

Example:

```bash
qa-agent ./docs "What is the deployment process?"
```

The answer is printed to stdout; diagnostics go to stderr, so you can safely pipe or
capture just the answer.

### Model aliases

`gemma-4-31b` (default), `gemma-4-26b`, `gpt-oss-120`, `gpt-oss-20b`,
`nemotron-3-ultra`, `nemotron-3-nano-omni`.

If the chosen model is rate-limited or unavailable, the agent automatically falls back
to the others and reports which model actually answered.

## Data & privacy

This tool is a client for a third-party LLM service. When you ask a question, the
**relevant chunk(s) of your file(s) and your question are sent to OpenRouter and the
selected model provider** to generate the answer. Do not point it at files you are not
comfortable sending to those services. Nothing is stored by this tool itself — it keeps
no history and writes nothing beyond the answer (and logs, if you enable a log file).

## Costs & rate limits

The default models are OpenRouter **free** tiers, which have per-day rate limits; when
one is exhausted the agent falls back to the others. Selecting a non-free model with
`--model` may incur charges on your OpenRouter account. See
[OpenRouter pricing](https://openrouter.ai/models) for details.

## Development

Run the test suite:

```bash
uv run pytest
```
