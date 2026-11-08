# 🤖 AI English Teacher Agent

An automated AI-powered agent designed to generate high-quality, TBLT (Task-Based Language Teaching) based English lesson plans and student worksheets from local curriculum data (RAG) with professional editorial design fidelity.

---

## 🚀 Overview

Teaching materials often require hours of curation, formatting, and structural alignment to ensure communicative efficacy (CEFR A1–A2 standards). **AI English Teacher Agent** bridges the gap between local curriculum documents and professional publishing. 

By leveraging the **Gemini API** for pedagogical reasoning, structured **Pydantic schemas** for data validation, and **WeasyPrint** for CSS-driven PDF typesetting, this agent automatically parses textbook data and outputs pristine, ready-to-print lesson packs.

---

## 🛠️ Tech Stack & Architecture

* **Core Language:** Python 3.10+
* **LLM Engine:** Google Gemini API (`gemini-2.5-flash`, `gemini-2.0-flash`) with automatic exponential backoff & model fallback.
* **Data Validation:** Pydantic (strict JSON schema enforcement).
* **RAG Pipeline:** Recursive directory traversal over local curriculum directories (`Student Book`, `Workbook`, `Writing Practice`).
* **PDF Rendering Engine:** WeasyPrint (HTML5/CSS3 advanced typesetting with Google Fonts integration).
* **Environment:** Google Colab / Local Python execution with Google Drive integration.

---

## ✨ Key Features

1. **Intelligent RAG System:** Recursively scans local directory structures to extract contextual grammar points, lexical chunks, and exercise patterns.
2. **Resilient API Wrapper:** Built-in retry mechanisms and model rotation to gracefully handle high-demand server states (`503 UNAVAILABLE`, `429`).
3. **Strict JSON Checkpointing:** Saves raw pedagogical structures (`.json`) prior to rendering, preventing API quota waste if layout adjustments occur.
4. **Professional Editorial Design System:** Renders outputs adhering to strict design tokens (semantic color palettes, cover bands, teacher rails, and numbered badges).

---

## 📂 Project Structure

```text
AI_English_Teacher_Agent/
│
├── A1/                      # Curriculum text data (Student Book, Workbook, etc.)
├── A2/                      # Curriculum text data (Student Book, Workbook, etc.)
├── System/
│   ├── lesson_schema.py     # Pydantic data models
│   ├── lessonkit.py         # WeasyPrint rendering & design system engine
│   └── design_tokens.json   # UI/UX design tokens (colors, typography)
│
└── AI_English_Teacher.ipynb # Main execution notebook (Colab UI)

⚙️ Getting Started & Installation
Clone the repository:

git clone [https://github.com/YOUR_USERNAME/AI_English_Teacher_Agent.git](https://github.com/YOUR_USERNAME/AI_English_Teacher_Agent.git)
cd AI_English_Teacher_Agent

Install system dependencies (for WeasyPrint typesetting):
sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0

Install Python packages:
pip install google-genai pydantic weasyprint ipywidgets

Configure your API Key:
Store your Gemini API key securely in your environment variables or Google Colab Userdata as GEMINI_API_KEY.

📄 Example Output
The agent compiles comprehensive worksheets containing:
Cover Band & Metadata: Lesson title, CEFR level, and core focus.
Teacher Rail: Pedagogical notes and lead-in strategies in Portuguese.
Comprehensible Input ($i+1$): Contextualized dialogues and texts.
Lexical Word Bank: Key vocabulary and false-friend alerts.
Shadowing Guide: Sentence-level stress and intonation tips.
TBLT Mission: Real-world communicative task with step-by-step execution.

🛡️ License
Distributed under the MIT License. See LICENSE for more information.


