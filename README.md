# NexusFlow 🌊
**Autonomous Text-to-Dashboard Orchestration**

NexusFlow is an intelligent, agentic data analytics tool that eliminates the need for SQL or Python. Simply upload your `.csv` or `.parquet` file, and start exploring your data using plain English or voice commands. Powered by **Streamlit**, **DuckDB**, and the **Google Gemini 2.5 Flash API**, NexusFlow translates your intent into actionable insights, editable dataframes, and dynamic visualizations.

## ✨ Key Features

* 🗣️ **Natural Language to SQL:** Ask questions in plain English, and the integrated Gemini agent writes DuckDB-compatible SQL instantly.
* 🔄 **Agentic Auto-Healing:** If a generated SQL query fails, the system automatically catches the error, feeds it back to the LLM, and self-corrects in an iterative loop (up to 3 retries).
* 📊 **Dynamic Visualizations:** Automatically selects and renders the most appropriate Plotly Express chart based on your data's shape and your original intent via dynamic Python code execution.
* ✏️ **Editable Data Sandbox:** View raw data results, double-click to edit cells, and export the modified dataset directly to CSV.
* 🎙️ **Multimodal Voice Input:** Speak your queries directly into the app—NexusFlow transcribes and executes them automatically.
* ⚡ **Zero-Shot Caching:** Intelligently caches exact SQL and dataframes for identical queries, saving API calls and processing time.
* 🎨 **Modern UI/UX:** Features a sleek, responsive design with custom CSS, Lottie animations, and global keyboard shortcuts.

## 🛠️ Tech Stack

* **Frontend UI:** Streamlit (`app.py`, `.streamlit/config.toml`)
* **Database Engine:** DuckDB (In-memory, `database.py`)
* **AI / Agentic Logic:** Google Gemini API (`gemini-2.5-flash`, `agent.py`)
* **Visualizations:** Plotly Express
* **Data Handling:** Pandas

## 🚀 Getting Started

### 1. Prerequisites
Make sure you have Python 3.9+ installed. You will also need a Google Gemini API key.

### 2. Installation
Clone the repository and navigate into the project directory:
```bash
git clone [https://github.com/Zafar3712/NexusFlow.git](https://github.com/Zafar3712/NexusFlow.git)
cd NexusFlow
