
# AutoDocGPT 

[![Python](https://img.shields.io/badge/python-3.11-blue?logo=python&logoColor=white)](https://www.python.org/)
[![OpenRouter API](https://img.shields.io/badge/OpenRouter-Enabled-brightgreen)](https://openrouter.ai/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Automated Project Documentation Agent** – an AI-powered tool that reads, analyzes, and documents your codebase automatically. AutoDocGPT integrates large language models (LLMs) with a modular, function-calling agent architecture to generate structured insights, summaries, and documentation for any Python project.

---

## 🌟 Key Features

- **AI-Powered Documentation**  
  Uses advanced LLMs (OpenRouter / GPT-4o) to read your project files and generate comprehensive README or technical summaries automatically.  

- **Modular Agent Architecture**  
  Separation of concerns with `Agent`, `Memory`, `Language`, `Environment`, and `Registry` components for easy extension and testing.  

- **Function-Calling Tools**  
  Dynamically register Python functions as tools, which the agent can call to perform actions like reading files, listing directories, or terminating execution.  

- **Memory-Enhanced Reasoning**  
  Maintains conversation and action history, allowing the agent to reason over past operations and produce context-aware documentation.  

- **Error-Resilient Execution**  
  Handles missing parameters and runtime errors gracefully with detailed logs.  

- **Easy Integration with OpenRouter API**  
  Supports reading API keys from `.env` or environment variables.

---

## 🏗 Architecture Overview

```

autodocgpt/
│
├── agent_core/
│   ├── base_agent.py      # Agent logic & OpenRouter integration
│   ├── memory.py          # Memory handling for conversation and action history
│   ├── language.py        # LLM language interface & function-calling parser
│   ├── environment.py     # Action execution environment
│   └── registry.py        # Tool & action registration
│
├── tools/
│   ├── file_tools.py      # File system operations
│   └── system_tools.py    # System-level utilities
│
├── main.py                # Entrypoint and agent loop
└── README.md

````

---

## ⚡ Installation

```bash
git clone https://github.com/yourusername/AutoDocGPT.git
cd AutoDocGPT
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
````

> Add your OpenRouter API key in `.env` or as environment variables:

```bash
OPENROUTER_API_KEY="sk-your-real-key"
OPENROUTER_API_BASE="https://openrouter.ai/api/v1"  # optional
```

---

## 📝 Usage

Run the agent to generate a README automatically:

```bash
python main.py --task "Write a professional README for this project."
```

Example output in memory:

```json
[
  {"role": "user", "content": "Write a professional README for this project."},
  {"role": "assistant", "content": "AutoDocGPT reads your codebase, extracts structure, and generates detailed documentation..."}
]
```
---

## 🔧 How It Works

1. **User Input / Goal** – Define what you want (e.g., “Generate README”).
2. **Agent Loop** – The agent constructs prompts using goals, available actions, and memory history.
3. **LLM Response** – The OpenRouter-powered LLM decides which tool to call next or provides direct content.
4. **Action Execution** – Environment executes the tool call, validates parameters, and stores results in memory.
5. **Memory Update** – The agent updates memory with results and continues reasoning until termination.
6. **Final Output** – Aggregates all insights into a structured README or summary.

---

## 💡 Example Tools

* `read_project_file(name: str) -> str` – Reads a file’s content.
* `list_project_files() -> List[str]` – Lists all Python files in the project.
* `terminate(message: str)` – Ends agent execution with a final message.

---

## 🚀 Skills Demonstrated

* Advanced Python development (OOP, dataclasses, decorators)
* LLM integration & prompt engineering
* Agent-based architecture for autonomous reasoning
* Dynamic tool registration and execution
* Robust error handling & memory management
* Modular, testable, and extensible code design

---

## 🔮 Future Improvements

* Add support for **vector databases** for long-term memory & scaling.
* Integrate **multi-agent collaboration** for cross-project analysis.
* Summarize **code metrics** and dependency graphs automatically.
* Enable **web UI** for interactive documentation generation.

---

## 🎯 Why AutoDocGPT?

> AutoDocGPT is not just a README generator; it’s a **showcase of AI-driven autonomous reasoning**. 
---

## 📄 License

MIT License © 2025 saman barahoie

