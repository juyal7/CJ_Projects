# enhanced_customer_support_rag.py

import streamlit as st
import os
import random
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama.chat_models import ChatOllama
from langchain.schema import Document
from langchain.chains import RetrievalQA
from datetime import datetime
import time

# -----------------------------------
# SIMULATED REAL-WORLD KNOWLEDGE BASE
# -----------------------------------
def generate_large_document_set():
    categories = ["Returns", "Shipping", "Payments", "Account", "Product", "Membership"]
    template_knowledge = {
        "Returns": [
            "Returns must be initiated within 30 days of purchase.",
            "Refunds are processed within 5-7 business days after the return is approved.",
            "Items marked 'non-returnable' cannot be refunded.",
        ],
        "Shipping": [
            "Standard shipping takes 5-7 days.",
            "Express shipping is available at extra cost.",
            "We ship to over 100 countries globally.",
        ],
        "Payments": [
            "We support credit cards, UPI, PayPal, and EMI options.",
            "You can save your preferred payment method for faster checkout.",
        ],
        "Account": [
            "Reset your password by clicking 'Forgot Password'.",
            "Your account can be locked after 5 failed login attempts.",
        ],
        "Product": [
            "All electronics come with 1-year warranty.",
            "Check product specifications before purchase.",
        ],
        "Membership": [
            "Premium members get free express shipping.",
            "Membership is billed annually and renews automatically.",
        ]
    }

    documents = []
    for category, facts in template_knowledge.items():
        for i in range(10):
            content = random.choice(facts)
            documents.append(Document(
                page_content=content,
                metadata={
                    "category": category,
                    "source": f"{category}_policy_v{random.randint(1,3)}.md",
                    "last_updated": str(datetime(2024, random.randint(1, 12), random.randint(1, 28)))
                }
            ))
    return documents

# -----------------------------------
# CREATE AND SAVE FAISS INDEX LOCALLY
# -----------------------------------
def build_faiss_index(documents, persist=True):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(documents, embeddings)
    if persist:
        vectorstore.save_local("faiss_support_index")
    return vectorstore

# -----------------------------------
# LOAD RAG PIPELINE FROM SAVED INDEX
# -----------------------------------
def load_rag_chain():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.load_local("faiss_support_index", embeddings, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = ChatOllama(model="tinyllama")
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)
    return qa_chain

# -----------------------------------
# STREAMLIT FRONTEND
# -----------------------------------
def run_streamlit():
    st.set_page_config(page_title="Enterprise RAG Assistant", layout="centered")
    st.title("Enterprise Customer Support Assistant (RAG)")
    st.caption("Ask questions about shipping, returns, accounts, etc. Powered by Gemma3 (Ollama) + FAISS + HuggingFace.")

    if "qa_chain" not in st.session_state:
        with st.spinner("Preparing knowledge base..."):
            docs = generate_large_document_set()
            build_faiss_index(docs)
            st.session_state.qa_chain = load_rag_chain()
            st.session_state.chat_history = []

    query = st.text_input("Enter your question about policies, delivery, etc:")
    if st.button("Get Answer") and query.strip():
        with st.spinner("Thinking..."):
            response = st.session_state.qa_chain(query)
            answer = response["result"]
            sources = response["source_documents"]

            # Save to chat history
            st.session_state.chat_history.append({
                "question": query,
                "answer": answer,
                "sources": sources
            })

    # ----------------------
    # Show Chat History
    # ----------------------
    for idx, chat in enumerate(reversed(st.session_state.chat_history[-5:]), 1):
        st.markdown(f"### Q{idx}: {chat['question']}")
        st.success(chat["answer"])
        with st.expander("Sources used"):
            for doc in chat["sources"]:
                st.markdown(f"- **{doc.metadata['category']}** ({doc.metadata['source']}) — *{doc.page_content}*")

if __name__ == "__main__":
    run_streamlit()