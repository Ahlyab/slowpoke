> **Under Construction**
>
> This project is actively being developed and behaviors/commands may change.

# slowpoke

`slowpoke` is a Linux-first, LLM-assisted package installer CLI.

It detects the system package manager, asks for the app/package to install, resolves package names using LLMs, and executes a validated command plan only after dry-run confirmation.

## Features

- Linux distro and package manager detection (see **Package managers** below for support status)
- Pluggable LLM providers:
  - Gemini
  - OpenAI (ChatGPT API)
  - xAI (Grok API)
- Optional web-search fallback for installation docs when package-manager search fails
- Structured command plans with safety validation (no raw shell execution, `shell=False`)
- Dry-run first, explicit user confirmation before execution

## Package managers

| Package manager | Status |
| ---------------- | ------ |
| **DNF** | ✓ Supported |
| **APT** | Will be implemented soon |
| **Pacman** | Will be implemented soon |
| **Zypper** | Will be implemented soon |
| **APK** | Will be implemented soon |
| **Flatpak** | Will be implemented soon |

Detection may still pick any of these when their CLI is present on the system; behavior beyond **DNF** is not fully implemented yet.

## Current project structure

```text
slowpoke/
├── src/
│   └── slowpoke/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── core/
│       │   ├── config.py
│       │   ├── logging.py
│       │   └── orchestrator.py
│       ├── system/
│       │   ├── system_info.py
│       │   └── package_managers/
│       │       ├── base.py
│       │       ├── apt.py
│       │       ├── dnf.py
│       │       ├── pacman.py
│       │       ├── zypper.py
│       │       ├── apk.py
│       │       └── flatpak.py
│       ├── llm/
│       │   ├── base.py
│       │   ├── prompts/
│       │   │   ├── package_resolution.md
│       │   │   └── install_plan_from_docs.md
│       │   └── providers/
│       │       ├── openai_compatible.py
│       │       ├── gemini.py
│       │       ├── chatgpt.py
│       │       └── grok.py
│       ├── execution/
│       │   ├── command_model.py
│       │   ├── safety.py
│       │   └── executor.py
│       ├── web/
│       │   ├── search_client.py
│       │   └── tavily_client.py
│       └── utils/
│           └── shell.py
├── tests/
├── .env.example
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Setup

```bash
python -m pip install -e .
```

For development (tests + lint):

```bash
python -m pip install -e .[dev]
```

If you prefer requirements files:

```bash
python -m pip install -r requirements-dev.txt
```

## Configuration

Copy `.env.example` to `.env` and set values you need:

- `LLM_PROVIDER=gemini|openai|grok`
- `LLM_MODEL=<model-name>`
- `OPENAI_API_KEY=...`
- `GEMINI_API_KEY=...`
- `XAI_API_KEY=...`
- `WEB_SEARCH_PROVIDER=tavily|none`
- `TAVILY_API_KEY=...` (required if `WEB_SEARCH_PROVIDER=tavily`)
- `AUTO_SUDO=true|false`
- `DEV_MODE=true|false` (when `true`, logs raw LLM/web API request and response payloads for debugging)
- `LOG_LEVEL=INFO|DEBUG|...`
- `SLOWPOKE_LOG_FILE=.slowpoke.log`

## Usage

Run with prompt:

```bash
slowpoke
```

Run directly with package name:

```bash
slowpoke neovim
```

Behavior:

1. Detect Linux package manager.
2. Search package candidates.
3. Use configured LLM provider to resolve package/install plan.
4. Fallback to docs-based plan using web search (if enabled).
5. Show dry-run commands.
6. Execute only after user confirmation.

## Platform support

- Supported: Linux
- Not supported yet: Windows `winget`, macOS `brew`

## Testing

```bash
python -m pytest -q
```

