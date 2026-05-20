# 🩺 MediSense AI – Multilingual Medical Assistant using RAG and LLM

## 📌 Project Overview

MediSense AI is an AI-powered multilingual healthcare assistant built using Retrieval-Augmented Generation (RAG), Large Language Models (LLMs), and Streamlit.

The application helps users ask medical-related questions using text or voice input and provides AI-generated responses based on trusted medical documents.

The system also supports:

* Multilingual interaction (English, Hindi, Marathi)
* Voice input and audio responses
* Symptom extraction
* Nearby hospital finder with interactive maps
* User authentication
* Persistent chat history similar to ChatGPT

---

# 🚀 Features

## ✅ AI-Powered Medical Question Answering

* Uses RAG architecture for accurate responses
* Retrieves relevant information from medical documents
* Generates responses using GROQ LLM

## 🌍 Multilingual Support

Supports:

* English
* Hindi
* Marathi

The system:

1. Translates user input into English
2. Processes query using LLM
3. Translates response back to selected language

## 🎤 Voice Input

Users can speak instead of typing.

Workflow:

1. Record voice
2. Convert speech to text
3. Process medical query
4. Generate response

## 🔊 Text-to-Speech Output

AI responses are converted into audio.

Useful for:

* Elderly users
* Accessibility
* Non-technical users

## 🧠 Symptom Extraction

The system extracts symptoms from user queries using LLM.

Example:
Input:

> “I have fever, cough, and headache.”

Output:

* Fever
* Cough
* Headache

## 🏥 Hospital Finder

Users can search nearby hospitals by location.

Features:

* Interactive maps
* Nearby hospital listing
* OpenStreetMap integration
* Folium map visualization

## 🔐 Authentication System

Includes:

* User signup
* Login
* Password hashing
* Session management

## 💬 Persistent Chat History

* Multiple chat sessions
* ChatGPT-like history
* Continue previous conversations
* Chats stored locally using JSON

---

# 🏗️ System Architecture

## Step 1: User Input

Users interact using:

* Text input
* Voice input

## Step 2: Language Processing

If the selected language is Hindi or Marathi:

* Input is translated into English
* Query sent to LLM pipeline

## Step 3: RAG Pipeline

Workflow:

1. Medical PDFs/documents are chunked
2. Embeddings are generated
3. Stored in FAISS vector database
4. Similar document chunks retrieved
5. GROQ LLM generates final response

## Step 4: Response Generation

The generated response is:

* Translated back to selected language
* Converted into speech audio
* Displayed to user

## Step 5: Hospital Finder

* User enters location
* OpenStreetMap API retrieves nearby hospitals
* Folium displays hospitals on interactive map

---

# 🧰 Technologies Used

## Frontend

* Streamlit
* HTML
* CSS

## Backend

* Python

## AI & NLP

* LangChain
* GROQ LLM API
* FAISS Vector Database
* Sentence Transformers

## Speech Processing

* SpeechRecognition
* gTTS
* pydub

## Translation

* deep-translator

## Maps & Location

* Folium
* OpenStreetMap API

## Storage

* JSON

---

# 📂 Project Structure

```bash
Medical_Chatbot/
│
├── app.py
├── llm_engine.py
├── symptom_extractor.py
├── hospital_finder.py
├── users.json
├── chats/
├── medical_docs/
├── requirements.txt
├── .env
└── README.md
```

---

# ⚙️ Installation

## 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/MediSense-AI.git
cd MediSense-AI
```

---

## 2️⃣ Create Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux/Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Create .env File

Create a `.env` file in the root directory.

```env
GROQ_API_KEY=your_groq_api_key
```

---

## 5️⃣ Run Application

```bash
streamlit run app.py
```

---

# 🔒 Security

## Password Security

Passwords are stored using SHA-256 hashing.

## API Key Protection

* API keys stored using environment variables
* `.env` added to `.gitignore`
* Keys not exposed publicly

---

# 🧠 RAG Workflow

## What is RAG?

RAG stands for Retrieval-Augmented Generation.

Instead of generating answers directly:

1. Relevant medical information is retrieved
2. LLM uses retrieved context
3. Final accurate answer is generated

Benefits:

* Better accuracy
* Reduced hallucination
* Uses custom medical documents

---

# 📊 Key Functionalities

| Feature              | Description                  |
| -------------------- | ---------------------------- |
| RAG Chatbot          | AI-generated medical answers |
| Multilingual Support | English, Hindi, Marathi      |
| Voice Input          | Speech-to-text functionality |
| Voice Output         | Text-to-speech responses     |
| Hospital Finder      | Nearby hospital search       |
| Authentication       | Login/signup system          |
| Chat History         | Persistent conversations     |
| Symptom Extraction   | Extract symptoms using AI    |

---

# 📈 Future Improvements

* Database integration (PostgreSQL/MongoDB)
* Real-time doctor consultation
* Medical report upload and analysis
* AI-based disease prediction
* Mobile application version
* User profile and health history
* Cloud deployment

---

# 🎯 Learning Outcomes

Through this project, I learned:

* RAG architecture
* LangChain integration
* Vector databases and embeddings
* LLM application development
* Speech processing
* Authentication systems
* Streamlit UI development
* API integration
* Session management

---

# 👩‍💻 Author

Rutuja Shivaji Warkhade
B.Tech Computer Engineering Student
AI/ML & Data Science Enthusiast

---

# 📜 Disclaimer

This application is developed for educational and research purposes only.
It is not a substitute for professional medical a
