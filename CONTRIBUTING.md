# Contributing to slowpoke

Welcome! **slowpoke** is a Python CLI that uses LLMs to suggest **safe**, **structured** install commands on Linux. Whether you are fixing a bug, improving docs, or extending a backend, we are glad you are here.

---

## Types of contributions

We appreciate:

- **Features** — new package managers, LLM providers, or UX improvements (discuss larger changes in an issue first).
- **Bugs** — reproducible reports with OS, distro, and relevant config (redact API keys).
- **Documentation** — README, CONTRIBUTING, code comments where behavior is non-obvious.
- **Tests** — especially around **safety**, execution, and package manager behavior.

---

## Getting started

**Requirements:** Python 3 with `pip` (see `pyproject.toml` for the supported range).

Clone the repo and install in editable mode with dev dependencies:

```bash
git clone https://github.com/Ahlyab/slowpoke.git
cd slowpoke
python -m pip install -e .[dev]
```

Alternative:

```bash
python -m pip install -r requirements-dev.txt
```

Copy `.env.example` to `.env` and set at least one LLM provider’s API key before exercising the full CLI.

---

## Project structure overview

| Area | Path | Role |
| ---- | ---- | ---- |
| CLI | `src/slowpoke/cli.py` | Arguments, prompts, dry-run display, confirmation |
| Config | `src/slowpoke/core/config.py` | Environment-based settings |
| Orchestration | `src/slowpoke/core/orchestrator.py` | Plan building, LLM/search wiring |
| Package managers | `src/slowpoke/system/package_managers/` | One module per manager; `base.py` defines the interface |
| System detection | `src/slowpoke/system/system_info.py` | Distro / manager detection and `create_package_manager()` |
| LLM | `src/slowpoke/llm/` | `LLMClient` contract, prompts, provider implementations |
| Execution | `src/slowpoke/execution/` | `CommandPlan` / steps, **safety** validation, `subprocess` runner |
| Web | `src/slowpoke/web/` | Optional search (e.g. Tavily) |
| Tests | `tests/` | Pytest suite |

Architecture goal: **package managers** and **LLM providers** stay pluggable and small.

---

## How to contribute

1. **Search existing issues** to avoid duplicate work.
2. **Open an issue** for non-trivial features or design questions; summarize the problem and your proposed direction.
3. **Fork → branch → PR.** Use a clear branch name (e.g. `fix/apt-search`, `docs/contributing`).
4. **Link the issue** in the PR when it closes or relates to one.

Feature requests are welcome; we prioritize **safety**, **clarity**, and **maintainability** over raw feature count.

---

## Coding guidelines

- **Match the surrounding style** — imports, typing, logging, and module layout consistent with neighboring files.
- **Prefer small PRs** — one logical change per request when possible.
- **Readability over cleverness** — explicit names, early returns, shallow nesting.
- **Types** — use annotations where the rest of the module does; keep public surfaces clear.
- **No drive-by refactors** — unrelated formatting or renames make review harder.

---

## Safety rules (read this before changing execution)

Unsafe behavior is a **security** issue, not a style issue.

1. **Never execute arbitrary shell strings.** The executor runs `subprocess.run(..., shell=False)` with a fixed executable and argument list (`src/slowpoke/execution/executor.py`).
2. **Plans must pass `validate_plan()`** (`src/slowpoke/execution/safety.py`) before execution. Do not bypass it without maintainer review and strong justification.
3. **Allowlisted executables only** — new commands may require extending `ALLOWED_EXECUTABLES` deliberately; justify each addition.
4. **No shell injection** — argument tokens must not introduce `|`, `` ` ``, `;`, `&&`, etc.; validation enforces this.
5. **Package manager code** should build `CommandPlan` / `CommandStep` with **structured** `executable` + `args` (see `PackageManager.plan()` in `base.py`), not concatenated user input into one string.
6. **LLM output** is untrusted: parsing and validation belong in code, not in “run whatever the model said.”

If you are unsure, **open an issue** before merging behavior that runs or validates commands.

---

## Adding a new package manager

1. Implement a class that subclasses `PackageManager` in `src/slowpoke/system/package_managers/base.py`.
2. Implement **`search(query) -> list[PackageCandidate]`** and **`build_install_plan(package_name) -> CommandPlan`** using structured steps (see `dnf.py` as a reference).
3. Register the class in **`create_package_manager()`** in `src/slowpoke/system/system_info.py` (the mapping from manager name → class).
4. Ensure **`detect_package_manager_name()`** and its mapping stay consistent with supported tools (`shutil.which` / priority order).
5. Add or extend **tests** (e.g. parsing, plan shape, interaction with `validate_plan()` where applicable).

Until a manager is fully implemented, keep behavior honest (clear errors or “not implemented”) rather than half-running dangerous paths.

---

## Adding a new LLM provider

1. Implement **`LLMClient`** (`src/slowpoke/llm/base.py`) — at minimum **`complete_json(...)`** returning structured data the orchestrator expects (follow existing providers).
2. Add a module under `src/slowpoke/llm/providers/` (see `gemini.py`, `chatgpt.py`, `grok.py`).
3. Wire it in **`build_llm_client()`** in `src/slowpoke/core/orchestrator.py`.
4. Extend **`Settings`** and **`load_settings()`** in `src/slowpoke/core/config.py`: provider name literal, env vars for keys, validation messages.
5. Document new env vars in **`.env.example`** and the **README**.

Reuse shared patterns (e.g. OpenAI-compatible HTTP) when it reduces duplication.

---

## Running tests

```bash
python -m pytest -q
```

Run the full suite before opening a PR. Add tests for new behavior, especially anything touching **plans**, **validation**, or **subprocess** execution.

---

## Pull request guidelines

- **Describe what changed and why** — link issues when relevant.
- **Call out user-visible changes** — CLI flags, config keys, default behavior, or safety rules.
- **Keep commits readable** — logical messages; squash if asked during review.
- **Ensure tests pass** and avoid introducing linter/type issues the project already enforces.

---

## Good first issues (examples)

Look for issues labeled **good first issue** (or similar). Typical starter tasks:

- Improve error messages when detection or API keys fail.
- Add or clarify tests for `validate_plan()` edge cases.
- Documentation fixes (README, env vars, supported distros).
- Small, isolated improvements in one package manager module with tests.

If no label exists yet, ask in an issue — maintainers can suggest a scoped task.

---

## Community guidelines

- **Be respectful and constructive** — assume good intent; disagree with ideas, not people.
- **Keep discussions on-topic** — security-sensitive details belong in private disclosure if they are exploitable (check project security policy if published).
- **Credit** — we value contributors; let us know if you want a particular name or handle in release notes.

Thank you for helping make installs on Linux a little safer and clearer.
