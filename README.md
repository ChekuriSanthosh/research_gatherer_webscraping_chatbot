# Research Assistant Chat

A web-based chat interface powered by AI agents for comprehensive research on any topic. It scrapes the web, queries Wikipedia, summarizes findings, fact-checks across sources, and generates detailed reports—all in a conversational format.

## 🚀 Features

- **Multi-Source Research**: Gathers information from DuckDuckGo, Bing, and Wikipedia.
- **Web Scraping**: Extracts and cleans content from search results for deeper insights.
- **Intelligent Summarization**: Uses extractive summarization to condense information while preserving key facts.
- **Fact-Checking**: Cross-references facts across sources with confidence scoring based on reliability.
- **Report Generation**: Produces Markdown-formatted reports with verified facts, source analysis, and citations.
- **Chat Interface**: Built with Streamlit for an intuitive, real-time conversation experience.
- **Quick & Deep Modes**: Fast summaries for quick queries or asynchronous deep dives for thorough analysis.
- **Reliability Scoring**: Domains are scored for trustworthiness (e.g., .gov/edu = high).

## 🛠️ Tech Stack

- **Backend**: Python 3.x with asyncio for parallel processing.
- **Libraries**: Requests, BeautifulSoup4, Wikipedia API, ThreadPoolExecutor.
- **Frontend**: Streamlit for the chat UI.
- **Agents**: Modular classes for web research, Wikipedia, summarization, fact-checking, and report writing.

## 📦 Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/research-assistant-chat.git
   cd research-assistant-chat
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## 🚀 Quick Start

Run the Streamlit app:
```
streamlit run app.py
```

- Open your browser to `http://localhost:8501`.
- Type a research query in the chat (e.g., "Latest developments in quantum computing").
- Watch as the assistant researches, summarizes, and responds with a formatted report.

### Sidebar Options
- Toggle "Use deep async research" for more comprehensive (but slower) analysis.
- Clear chat history with the button.

## 📖 Usage

### Backend-Only (CLI Testing)
For testing without the UI, use the `main()` function in `research_network.py`:
```python
python research_network.py
```
This runs example queries and prints summaries.

### Custom Queries
- **Quick Research**: Fast, synchronous mode for simple topics.
- **Full Research**: Async mode with parallel agents for in-depth reports.

Example output snippet:
```
# Quick Research Summary: artificial intelligence latest developments 2024

**Overall Summary:**
Artificial Intelligence (AI) has seen rapid advancements in 2024, particularly in generative models and multimodal systems...

**Sources Found:** 11
**Average Reliability:** 0.75

**Key Sources:**
- OpenAI's GPT-5 (Web)
- Quantum Computing Breakthroughs (Wikipedia)
...
```


### requirements.txt
```
requests>=2.28.0
beautifulsoup4>=4.11.0
wikipedia>=1.4.0
lxml>=4.9.0
streamlit>=1.28.0
```

---
