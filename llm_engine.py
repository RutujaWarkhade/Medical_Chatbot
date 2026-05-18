import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

DB_FAISS_PATH = "vectorstore/db_faiss"


def get_vectorstore():
    embedding = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    return FAISS.load_local(DB_FAISS_PATH, embedding, allow_dangerous_deserialization=True)


def load_llm():
    return ChatGroq(
        model_name="llama-3.1-8b-instant",
        temperature=0.3,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )


def get_qa_chain():
    prompt = PromptTemplate(
        template="""You are a trusted medical information assistant. Your role is to provide
accurate, evidence-based health information strictly from the provided medical context.

IMPORTANT RULES:
- Answer ONLY from the context provided below. Do not use outside knowledge.
- If the context does not contain enough information, say: "I don't have enough verified information on this topic. Please consult a doctor."
- Always be clear, structured, and compassionate.
- Never diagnose. Never prescribe. Always recommend consulting a doctor.
- End every answer with: "⚠️ This information is for educational purposes only. Please consult a qualified healthcare professional for personal medical advice."

Context (from verified medical documents):
{context}

Patient Question:
{question}

Structured Answer:
""",
        input_variables=["context", "question"]
    )

    db = get_vectorstore()

    return RetrievalQA.from_chain_type(
        llm=load_llm(),
        chain_type="stuff",
        retriever=db.as_retriever(search_kwargs={"k": 4}),
        return_source_documents=True,       # ← returns cited source chunks
        chain_type_kwargs={"prompt": prompt}
    )