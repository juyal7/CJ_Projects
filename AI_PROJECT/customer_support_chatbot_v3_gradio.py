import os
import random
from datetime import datetime
import gradio as gr
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama.chat_models import ChatOllama
from langchain.schema import Document
from langchain.chains import RetrievalQA

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
# FAISS INDEX OPERATIONS
# -----------------------------------
def build_faiss_index(documents, persist=True):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(documents, embeddings)
    if persist:
        vectorstore.save_local("faiss_support_index")
    return vectorstore

def load_rag_chain():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.load_local("faiss_support_index", embeddings, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = ChatOllama(model="tinyllama")
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)
    return qa_chain

# -----------------------------------
# GRADIO CHAT HANDLER
# -----------------------------------
def respond_to_user(query, history):
    if "qa_chain" not in gradio_state:
        docs = generate_large_document_set()
        build_faiss_index(docs)
        gradio_state["qa_chain"] = load_rag_chain()
        gradio_state["chat_history"] = []

    chain = gradio_state["qa_chain"]
    result = chain(query)
    answer = result["result"]
    sources = result["source_documents"]

    # Append to history
    gradio_state["chat_history"].append((query, answer, sources))

    display = f"**Answer:** {answer}\n\n**Sources:**\n"
    for doc in sources:
        meta = doc.metadata
        display += f"- `{meta['category']}` ({meta['source']}) — *{doc.page_content}*\n"
    return display, gradio_state["chat_history"]

# -----------------------------------
# INITIALIZE GLOBAL STATE
# -----------------------------------
gradio_state = {}

with gr.Blocks() as demo:
    gr.Markdown("# 📦 Enterprise Customer Support Assistant (RAG)")
    gr.Markdown("Ask questions about Shipping, Returns, Account, etc. Powered by FAISS + HuggingFace + Ollama (Gemma3).")

    with gr.Row():
        query_input = gr.Textbox(label="Enter your question", placeholder="E.g. What’s the return policy?")
        submit_btn = gr.Button("Get Answer")

    output_display = gr.Markdown()
    chat_history_display = gr.Dataframe(headers=["Question", "Answer", "Sources"], interactive=False)

    state = gr.State([])

    def handle_submit(q):
        response, updated_history = respond_to_user(q, state.value)
        # Format for table
        formatted = [
            [h[0], h[1], "\n".join([f"{doc.metadata['category']} - {doc.page_content}" for doc in h[2]])]
            for h in updated_history[-5:]
        ]
        return response, formatted, updated_history

    submit_btn.click(handle_submit, inputs=[query_input], outputs=[output_display, chat_history_display, state])

if __name__ == "__main__":
    demo.launch()
