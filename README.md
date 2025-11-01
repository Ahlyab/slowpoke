# Slowpoke

**Slowpoke** is an **AI-powered Linux utility** that simplifies and automates the application installation process — powered by modern AI command interpretation and safety checks.

> ⚡ Built with [uv](https://github.com/astral-sh/uv) — a blazing-fast Python package manager.

---

## 📦 Requirements

* **Python 3.13+**
* **[uv](https://github.com/astral-sh/uv)** (handles virtual environments automatically)

To install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## ⚙️ Environment Variables

Create a `.env` file (or rename `.env.example`) in the project root:

```bash
# API Keys
GEMINI_API_KEY=

# Logging
LOG_LEVEL=INFO   # Options: NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
```

> ⚠️ **Do not commit** `.env` to version control.

---

## 🚀 Local Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/Ahlyab/slowpoke.git
   cd slowpoke
   ```

2. **Install dependencies**

   ```bash
   uv sync
   ```

3. **(Optional) Activate virtual environment**

   ```bash
   source .venv/bin/activate   # Linux / macOS
   .venv\Scripts\activate      # Windows
   ```

---

## ▶️ Running the App

```bash
uv run main.py
```

---

## 🧪 Running Tests

Run all tests with:

```bash
pytest
```

---

## 📁 Project Structure

```init
slowpoke/
├── app/
│   ├── __init__.py
│   ├── cli.py                # Command-line entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── ai_interface.py   # Interfaces with AI models (Gemini, etc.)
│   │   ├── command_builder.py# Converts natural language → shell commands
│   │   ├── executor.py       # Executes & monitors system commands
│   │   ├── safety.py         # Detects/prevents dangerous operations
│   │   └── logger.py         # Logging & output formatting
│   ├── utils/
│   │   ├── config.py         # Configs, constants, and API keys
│   │   └── helpers.py        # Shared helper functions
│   └── interface/
│       ├── ui.py             # Handles user interaction (Rich-based)
│       └── prompts.py        # Message templates and responses
│
├── tests/
│   ├── test_ai_interface.py
│   ├── test_command_builder.py
│   ├── test_executor.py
│   └── ...
│
├── myproject.toml
├── setup.py
├── README.md
└── LICENSE
```
