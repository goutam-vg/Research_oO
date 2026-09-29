# 🔎 ResearchAgentPy

A **local AI research agent** built with Python and Ollama.

Give it a topic, and the agent searches **Wikipedia** and **DuckDuckGo**, generates a research summary with **inline citations and references**, streams the response live, and saves the result as a `.txt` or `.md` file.

Everything runs locally using **Ollama**, so no paid API is required.

---

## 🚀 Features

* 🔍 **Web Research** — Searches Wikipedia and DuckDuckGo
* 📚 **Real Citations** — Generates `[1]`-style citations from retrieved sources
* 📑 **References** — Automatically creates a numbered references list
* ⚡ **Live Streaming** — Displays research progress and generated content in real time
* 🤖 **Local AI** — Runs using Ollama and locally installed models
* 🛡️ **Safety Net** — Performs direct searches if the model fails to use its research tools
* 🌐 **Multiple Languages** — Generate summaries in different languages
* 📏 **Length Control** — `short`, `medium`, or `long`
* 📦 **Batch Mode** — Research multiple topics from a text file
* 💻 **CLI Interface** — Use the agent directly from the terminal
* 🌐 **Streamlit Web App** — Interactive browser-based interface
* 📥 **Export** — Save results as `.txt` or `.md`
* 🕘 **History** — Access previously generated research
* 🩺 **Health Checks** — Detects Ollama/model availability
* 🧪 **Testing & CI** — Unit tests and GitHub Actions CI

---

## 🛠️ Tech Stack

* **Python 3.10+**
* **Ollama**
* **LangChain**
* **Streamlit**
* **Wikipedia**
* **DuckDuckGo**
* **Pytest**
* **GitHub Actions**

---

## 🧠 How It Works

```text
                    Research Topic
                          │
                          ▼
              ┌─────────────────────┐
              │   Research Agent    │
              │    CLI / Web App    │
              └──────────┬──────────┘
                         │
                         ▼
                Check Ollama + Model
                         │
                         ▼
              ┌─────────────────────┐
              │   LangChain Agent   │
              │    Ollama LLM       │
              └──────────┬──────────┘
                         │
                ┌────────┴────────┐
                ▼                 ▼
          Wikipedia          DuckDuckGo
            Search              Search
                │                 │
                └────────┬────────┘
                         ▼
                  Retrieved Sources
                         │
                         ▼
                  Generate Summary
                         │
                         ▼
                 Clean Citations
                         │
                         ▼
                 Add References
                         │
                  ┌──────┴──────┐
                  ▼             ▼
                .txt           .md
```

### Citation System

Sources are recorded by the application itself.

```text
Quantum computing uses qubits [1].

References:

1. Quantum computing - Wikipedia
   https://en.wikipedia.org/wiki/Quantum_computing
```

The citation numbers come from the **actual pages retrieved by the tools**, rather than allowing the model to freely invent references.

> Citations indicate which sources the summary relied on; they do not guarantee that every generated claim is correct. Important information should still be verified against the original sources.

---

## 📂 Project Structure

```text
ResearchAgentPy/
│
├── research_agent/
│   ├── agent.py
│   ├── tools.py
│   ├── citations.py
│   ├── storage.py
│   ├── health.py
│   ├── config.py
│   ├── cli.py
│   └── web.py
│
├── tests/
│   ├── conftest.py
│   ├── test_agent_stream.py
│   ├── test_citations.py
│   ├── test_cli.py
│   ├── test_health.py
│   ├── test_storage.py
│   └── test_tools.py
│
├── outputs/
│   └── .gitkeep
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── app.py
├── main.py
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

---

## ⚙️ Requirements

Before running the project, install:

* Python **3.10+**
* [Ollama](https://ollama.com)
* An Ollama model with tool-calling support

---

## 📥 Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/ResearchAgentPy.git
cd ResearchAgentPy
```

### 2. Create a virtual environment

**Windows:**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

**Windows:**

```powershell
copy .env.example .env
```

**Linux / macOS:**

```bash
cp .env.example .env
```

### 5. Pull an Ollama model

```bash
ollama pull qwen3:8b
```

Make sure Ollama is running.

---

## 💻 CLI Usage

```bash
python -m research_agent "Quantum computing"
```

Or install the project:

```bash
pip install -e .
```

Then:

```bash
research-agent "Quantum computing"
```

### Examples

```bash
research-agent "Quantum computing"
```

```bash
research-agent "Black holes" --length long
```

```bash
research-agent "Black holes" --format md
```

```bash
research-agent "Climate change" --lang Spanish
```

```bash
research-agent --file topics.txt


---

## 🌐 Web App

Start the Streamlit application:

```bash
streamlit run app.py
```

The web application provides:

* Model selection
* Research length selection
* Language selection
* Topic input
* Live research output
* Research history
* `.txt` downloads
* `.md` downloads

---

## 📋 CLI Options

| Option               | Default        | Description                  |
| -------------------- | -------------- | ---------------------------- |
| `topic`              | Prompt         | Topic to research            |
| `-f`, `--file`       | —              | Text file containing topics  |
| `-m`, `--model`      | `OLLAMA_MODEL` | Ollama model                 |
| `-l`, `--length`     | `medium`       | `short`, `medium`, or `long` |
| `--lang`             | `English`      | Output language              |
| `--format`           | `txt`          | `txt` or `md`                |
| `-o`, `--output-dir` | `outputs`      | Output directory             |

---

## 🔧 Configuration

Create a `.env` file based on `.env.example`.

| Variable             | Default                  | Description               |
| -------------------- | ------------------------ | ------------------------- |
| `OLLAMA_MODEL`       | `qwen3:8b`               | Ollama model              |
| `OLLAMA_BASE_URL`    | `http://localhost:11434` | Ollama server             |
| `OLLAMA_KEEP_ALIVE`  | `30m`                    | Model keep-alive duration |
| `OLLAMA_REASONING`   | `false`                  | Enable model reasoning    |
| `OLLAMA_NUM_PREDICT` | Per length               | Maximum summary tokens    |

### Summary Token Limits

```text
short   → 500 tokens
medium  → 1000 tokens
long    → 1800 tokens
```

---

## 🧪 Testing

The project includes unit tests that do not require network access or a running Ollama server.

```bash
python -m pytest
```

CI runs the test suite using Python **3.10** and **3.12**.

---

## 🛠️ Troubleshooting

### Ollama cannot be reached

```bash
ollama serve
```

### Model is not installed

```bash
ollama pull qwen3:8b
```

### First response is slow

Ollama may be loading the model into memory. The `OLLAMA_KEEP_ALIVE` setting controls how long the model remains loaded.

### No references are generated

If both Wikipedia and DuckDuckGo are unreachable, the agent may not have sources available.

### Weak research results

Try a larger or more capable Ollama model.

---

## 🔮 Roadmap

* [ ] Follow-up questions about research results
* [ ] PDF export
* [ ] Deeper page-reading tool
* [ ] Docker support
* [ ] More research sources
* [ ] Improved multi-step research

---

## 🙏 Acknowledgements

This project was **inspired by and developed with reference to the work and tutorials of Tech With Tim**.

Special thanks to **Tim Ruscica (Tech With Tim)** for his educational content and practical guidance around Python, AI agents, and building AI-powered applications.

This repository contains my **own implementation, modifications, and extensions** built from that learning process.

You can find more of Tim's work on [Tech With Tim](https://www.youtube.com/@TechWithTim).

---

## 📄 License

This project is licensed under the **MIT License**.

See [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**Goutam VG**

Built as a local AI research agent using Python, LangChain, and Ollama.
