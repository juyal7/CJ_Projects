# pdf_support_chatbot.py

import streamlit as st
import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama.chat_models import ChatOllama
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# -----------------------------------
# PDF PROCESSING
# -----------------------------------
def process_pdf(pdf_file):
    # Save uploaded file temporarily
    temp_pdf_path = f"temp_pdf_{pdf_file.name}"
    with open(temp_pdf_path, "wb") as f:
        f.write(pdf_file.getbuffer())
    
    # Load and split the PDF
    loader = PyPDFLoader(temp_pdf_path)
    documents = loader.load()
    
    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    split_docs = text_splitter.split_documents(documents)
    
    # Clean up temp file
    os.remove(temp_pdf_path)
    
    return split_docs

# -----------------------------------
# CREATE AND SAVE FAISS INDEX LOCALLY
# -----------------------------------
def build_faiss_index(documents, persist=True):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(documents, embeddings)
    if persist:
        vectorstore.save_local("faiss_pdf_index")
    return vectorstore

# -----------------------------------
# LOAD RAG PIPELINE FROM SAVED INDEX
# -----------------------------------
def load_rag_chain():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.load_local("faiss_pdf_index", embeddings, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = ChatOllama(model="tinyllama")
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)
    return qa_chain

# -----------------------------------
# STREAMLIT FRONTEND
# -----------------------------------
def run_streamlit():
    st.set_page_config(page_title="PDF Question Answering", layout="centered")
    st.title("PDF Question Answering Assistant")
    st.caption("Upload a PDF and ask questions about its content.")

    # File uploader
    pdf_file = st.file_uploader("Upload your PDF", type="pdf")
    
    if pdf_file is not None:
        if "pdf_processed" not in st.session_state or st.session_state.pdf_name != pdf_file.name:
            with st.spinner("Processing PDF..."):
                # Process the PDF
                documents = process_pdf(pdf_file)
                build_faiss_index(documents)
                st.session_state.qa_chain = load_rag_chain()
                st.session_state.chat_history = []
                st.session_state.pdf_processed = True
                st.session_state.pdf_name = pdf_file.name
                st.success(f"PDF processed: {pdf_file.name}")
        
        # Query input
        query = st.text_input("Ask a question about your PDF:")
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

        # Show chat history
        for idx, chat in enumerate(reversed(st.session_state.chat_history[-5:]), 1):
            st.markdown(f"### Q{idx}: {chat['question']}")
            st.success(chat["answer"])
            with st.expander("Sources used"):
                for doc in chat["sources"]:
                    page_num = doc.metadata.get("page", "Unknown page")
                    st.markdown(f"- **Page {page_num}** — *{doc.page_content[:200]}...*")

if __name__ == "__main__":
    run_streamlit()