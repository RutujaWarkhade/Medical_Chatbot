import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# =========================
# LOAD ENV VARIABLES
# =========================
load_dotenv()

DB_FAISS_PATH = "vectorstore/db_faiss"

# =========================
# VECTOR DATABASE
# =========================
def get_vectorstore():
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    db = FAISS.load_local(
        DB_FAISS_PATH,
        embedding_model,
        allow_dangerous_deserialization=True
    )
    return db


# =========================
# LLM (GROQ - FIXED MODEL)
# =========================
def load_llm():
    llm = ChatGroq(
        model_name="llama-3.1-8b-instant",   # ✅ FIXED (working model)
        temperature=0.5,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    return llm


# =========================
# PROMPT TEMPLATE
# =========================
CUSTOM_PROMPT_TEMPLATE = """
Use the context below to answer the question.
If you don't know the answer, just say "I don't know".

Context:
{context}

Question:
{question}

Answer directly and clearly.
"""

def set_custom_prompt():
    return PromptTemplate(
        template=CUSTOM_PROMPT_TEMPLATE,
        input_variables=["context", "question"]
    )


# =========================
# MAIN FUNCTION
# =========================
def main():
    print("Loading vector database...")

    vectorstore = get_vectorstore()

    print("Loading LLM (Groq)...")

    qa_chain = RetrievalQA.from_chain_type(
        llm=load_llm(),
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True,
        chain_type_kwargs={"prompt": set_custom_prompt()}
    )

    while True:
        user_query = input("\nAsk Question (type 'exit' to stop): ")

        if user_query.lower() == "exit":
            break

        response = qa_chain.invoke({"query": user_query})

        print("\n====================")
        print("ANSWER:")
        print(response["result"])

        print("\nSOURCE DOCUMENTS:")
        for doc in response["source_documents"]:
            print("-", doc.page_content)

        print("====================")


if __name__ == "__main__":
    main()