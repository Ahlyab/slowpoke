# slowpoke
AI powered utility that helps in application installation process for linux


## File Structure
slowpoke/
├── slowpoke/
│   ├── __init__.py
│   ├── cli.py                # Entry point for command-line interface
│   ├── core/
│   │   ├── __init__.py
│   │   ├── ai_interface.py   # Interacts with OpenAI/Anthropic/Gemini APIs
│   │   ├── command_builder.py# Translates natural language → shell commands
│   │   ├── executor.py       # Executes and monitors system commands
│   │   ├── safety.py         # Detects and prevents dangerous operations
│   │   └── logger.py         # Handles logs, output formatting
│   ├── utils/
│   │   ├── config.py         # API keys, constants, settings
│   │   └── helpers.py        # Shared helper functions
│   └── interface/
│       ├── ui.py             # Manages user input/output (Rich-based)
│       └── prompts.py        # Defines message templates
│
├── tests/
│   ├── test_ai_interface.py
│   ├── test_command_builder.py
│   ├── test_executor.py
│   └── ...
│
├── requirements.txt
├── setup.py                  # Packaging config for pip
├── README.md
└── LICENSE

