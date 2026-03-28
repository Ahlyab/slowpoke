# slowpoke

**Install Linux packages with plain English — powered by LLMs, gated by you.**

> 🚧 *Active development: commands and behavior may change between releases.*

---

## What it does

**slowpoke** is a Linux-first CLI that turns “I want this app” into a **reviewed, structured install plan**. It figures out your distro and package manager, asks an LLM to resolve the right package names, optionally falls back to web docs when search comes up empty, shows a **dry-run** of exactly what would run, and **only executes after you confirm**. No arbitrary shell strings — plans are validated and executed with `shell=False`.

---

## Why this exists

Installing software on Linux still means remembering package names, meta-packages, and manager-specific flags. Docs are scattered, and copy-pasting random `curl | bash` snippets is risky.

slowpoke meets you in natural language, keeps the risky parts **out of the shell** until you’ve seen the plan, and makes the happy path: **detect → resolve → preview → confirm → run**.

---

## Features

- **Distro & package manager detection** — adapts to what your system actually uses
- **LLM-assisted package resolution** — maps “what I want” to concrete package names
- **Multiple LLM backends** — OpenAI, Gemini, xAI (Grok-compatible API)
- **Optional web search** — when local search isn’t enough, use docs-backed planning (e.g. Tavily)
- **Structured command plans** — validated steps, not raw shell; execution uses `shell=False`
- **Dry-run first** — you see every command before anything runs
- **Explicit confirmation** — installs only after you approve (with an opt-in non-interactive flag for automation)

---

## Demo

Typical interactive session:

```bash
$ slowpoke neovim
Loading configuration done.
Detecting Linux system done.
Initializing providers done.
Building install plan for 'neovim' done.
Detected distro: Fedora Linux 40 (Workstation Edition)
Detected package manager: dnf

Dry-run plan:
1. sudo dnf install -y neovim
   reason: Neovim editor from official repositories

Execute these commands? [y/N]: y
Executing plan done.
Installation workflow completed successfully.
```

Prompt for the package interactively:

```bash
$ slowpoke
Which package/app do you want to install? ripgrep
# ... same flow: dry-run, then confirmation ...
```

---

## Supported package managers

| Manager   | Status              |
| --------- | ------------------- |
| **DNF**   | Fully supported     |
| **APT**   | Planned / in progress |
| **Pacman** | Planned / in progress |
| **Zypper** | Planned / in progress |
| **APK**   | Planned / in progress |
| **Flatpak** | Planned / in progress |

Detection may still recognize these tools when present; **only DNF is fully implemented** today.

---

## Installation

From a clone of this repository:

```bash
python -m pip install -e .
```

**Development** (tests + tooling):

```bash
python -m pip install -e .[dev]
# or
python -m pip install -r requirements-dev.txt
```

**Platform:** Linux is supported. Windows (`winget`) and macOS (`brew`) are not targeted yet.

---

## Configuration

Copy `.env.example` to `.env` and set the variables you need.

| Variable | Purpose |
| -------- | ------- |
| `LLM_PROVIDER` | `gemini`, `openai`, or `grok` |
| `LLM_MODEL` | Model name for your provider |
| `OPENAI_API_KEY` | OpenAI API key |
| `GEMINI_API_KEY` | Google Gemini API key |
| `XAI_API_KEY` | xAI (Grok) API key |
| `WEB_SEARCH_PROVIDER` | `tavily` or `none` |
| `TAVILY_API_KEY` | Required if using Tavily search |
| `AUTO_SUDO` | `true` or `false` — prefix `sudo` when appropriate |
| `DEV_MODE` | `true` logs raw LLM/web payloads (debugging) |
| `LOG_LEVEL` | e.g. `INFO`, `DEBUG` |
| `SLOWPOKE_LOG_FILE` | Log file path (default `.slowpoke.log`) |

---

## Usage

| Command | Description |
| ------- | ----------- |
| `slowpoke` | Prompts: “Which package/app do you want to install?” |
| `slowpoke <name>` | Builds a plan for `<name>` (e.g. `slowpoke neovim`) |
| `slowpoke --yes` | Skips the confirmation prompt after the dry-run (use with care) |

**Flow:**

1. Detect Linux distro and package manager  
2. Search for package candidates where applicable  
3. Use the configured LLM to resolve names / plan steps  
4. Optionally use web search for a docs-based plan if search fails  
5. Print a **dry-run** list of commands (with short reasons when available)  
6. **Execute only if you confirm** (unless `--yes`)

---

## Project structure

```text
slowpoke/
├── src/slowpoke/
│   ├── cli.py                 # CLI entry
│   ├── core/                  # config, logging, orchestration
│   ├── system/                # distro detection + package_managers/
│   ├── llm/                   # providers + prompts
│   ├── execution/             # command model, safety, executor
│   └── web/                   # optional search clients
├── tests/
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

Architecture is **modular**: new LLM providers and package manager backends plug in without bolting on raw shell.

---

## Roadmap

Ideas contributors often care about:

- **First-class support** for APT, Pacman, Zypper, APK, and Flatpak (stubs exist; DNF is the reference implementation)
- **Broader distros** and edge cases in detection
- **Safer defaults** and clearer UX around `sudo` and confirmation
- **Tests and docs** as behaviors stabilize

If you want to help, pick an item, open an issue to avoid duplicate work, and send a focused PR.

---

## Contributing

We welcome issues and pull requests from Linux users, developers, and anyone who cares about **safe**, **boring** installs.

**Please read [CONTRIBUTING.md](CONTRIBUTING.md)** for branch workflow, coding expectations, and how to run tests locally.

Quick check before you open a PR:

```bash
python -m pytest -q
```

---

## Vision

**Package management should be predictable.** slowpoke uses LLMs as a **translator and planner**, not as a blind shell — so you stay in control, see every step, and only run what you approve. The goal is a small, trustworthy tool that feels natural to use and **straightforward to extend**.

---

<p align="center">
  <sub>Built for people who love Linux and dislike surprises in their terminal.</sub>
</p>
