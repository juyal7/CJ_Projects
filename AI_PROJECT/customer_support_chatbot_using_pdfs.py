# enhanced_customer_support_rag_with_pdfs.py

import streamlit as st
import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama.chat_models import ChatOllama
from langchain.schema import Document
from langchain.chains import RetrievalQA

# -----------------------------------
# LOAD DOCUMENTS FROM PDF FILES
# -----------------------------------
def load_documents_from_pdfs(pdf_dir: str):
    """Load and split PDF documents into text chunks."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    documents = []
    for filename in os.listdir(pdf_dir):
        if filename.lower().endswith(".pdf"):
            path = os.path.join(pdf_dir, filename)
            loader = PyPDFLoader(path)
            # load_and_split returns a list of Document objects
            docs = loader.load_and_split(text_splitter=splitter)
            # add metadata for clarity (optional)
            for doc in docs:
                doc.metadata["source_file"] = filename
            documents.extend(docs)
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
    vectorstore = FAISS.load_local(
        "faiss_support_index",
        embeddings,
        allow_dangerous_deserialization=True
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = ChatOllama(model="tinyllama")
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )
    return qa_chain

# -----------------------------------
# STREAMLIT FRONTEND
# -----------------------------------
def run_streamlit():
    st.set_page_config(page_title="Enterprise RAG Assistant", layout="centered")
    st.title("Enterprise Customer Support Assistant (RAG)")
    st.caption("Ask questions. Powered by Gemma3 + FAISS + HuggingFace.")

    if "qa_chain" not in st.session_state:
        with st.spinner("Preparing knowledge base..."):
            # Load real PDF documents
            pdf_dir = "pdf_files"
            docs = load_documents_from_pdfs(pdf_dir)
            # Build and persist FAISS index
            build_faiss_index(docs)
            # Load RAG chain
            st.session_state.qa_chain = load_rag_chain()
            st.session_state.chat_history = []

    query = st.text_input("Enter your question :")
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

    # Show recent chat history
    for idx, chat in enumerate(reversed(st.session_state.chat_history[-5:]), 1):
        st.markdown(f"### Q{idx}: {chat['question']}")
        st.success(chat["answer"])
        with st.expander("Sources used"):
            for doc in chat["sources"]:
                fn = doc.metadata.get("source_file", "unknown.pdf")
                st.markdown(f"- **Source:** {fn} — *{doc.page_content}*")

if __name__ == "__main__":
    # Ensure you've placed the PDF files inside a 'pdfs/' folder next to this script
    run_streamlit()
