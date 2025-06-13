# NewMindAI-FinalCase

# 🤖 AI/ML Research Assistant

**An Intelligent Assistant for Understanding AI Research**

## 📌 Project Overview

This project aims to tackle the increasing difficulty of staying up-to-date with the ever-growing body of knowledge in the field of Artificial Intelligence. Traditional search engines often fall short when it comes to deep, contextual queries. The AI/ML Research Assistant addresses this gap by offering an intelligent search interface that understands natural language and retrieves contextually relevant results from a graph-based database.

---


https://github.com/user-attachments/assets/57ada060-a195-43fc-84e8-2eff40122ccc



## 🚀 Features

- 📄 Web scraping of AI research papers from PapersWithCode
- 📘 PDF parsing and semantic chunking
- 🔍 Semantic vector-based search (embeddings)
- 🕸️ Neo4j Graph Database integration
- 💬 Natural language query processing using LLMs (OpenAI & Groq)
- 🔗 LangChain-powered multi-chain logic (Cypher QA, Vector Search, Reasoning, Question Rewriting)
- 🌐 Interactive user interface built with Streamlit
- 🧪 Auto-generated Cypher queries and summarized responses in Turkish

---

## 🛠️ Technologies Used

| Technology / Library | Description |
|----------------------|-------------|
| **Streamlit** | Web interface for user interaction |
| **LangChain** | Chain-of-thought logic, memory, prompt templates |
| **Neo4j + LangChain Integration** | Converts natural language to Cypher queries |
| **OpenAI / Groq** | LLM providers for smart responses |
| **HuggingFace Embeddings** | Semantic similarity via vector space |
| **PyMuPDF (fitz)** | PDF text extraction |
| **BeautifulSoup** | HTML scraping |
| **PyTorch** | Embedding model backend |

---

## 🧩 Application Flow

1. User types a natural language question via Streamlit UI.
2. User selects a search type and preferred model.
3. `AIMLChatbot` selects the appropriate LangChain based on query type.
4. Cypher query is generated and executed on Neo4j.
5. Retrieved data is summarized and translated into Turkish using LLM.
6. Chat history is stored for conversational continuity.

---

## 🔍 Search Types & LangChains

| Search Type        | Description |
|--------------------|-------------|
| **Normal Search**  | Metadata-based Cypher querying |
| **Vector Search**  | Embedding-based semantic similarity search |
| **Reasoning**      | Chain with rationale cleaning for step-by-step reasoning |
| **Question Rewriter** | Maintains conversational flow by rewriting follow-up questions |

---

## 📊 Example Scenario

**Question:** “Which papers address the Large Language Model task?”

- Search Type: Reasoning
- Model: `deepseek-r1-distill-llama-70b`
- Result: The system generates a Cypher query based on the input and retrieves relevant papers from Neo4j. These are then presented to the user in a natural-language response in Turkish.
---
