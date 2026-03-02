import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import fitz  # PyMuPDF
from docx import Document
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from langchain.vectorstores import FAISS as LangchainFAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter

class DocumentChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Document Chat Assistant with Llama 3.2")
        self.root.geometry("800x700")
        self.root.configure(bg='#f0f0f0')
       
        # Initialize variables
        self.qa_system = None
        self.documents_loaded = False
        self.embed_model = None
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Document Chat Assistant", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Document loading section
        doc_frame = ttk.LabelFrame(main_frame, text="Document Management", padding="10")
        doc_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        doc_frame.columnconfigure(1, weight=1)
        
        # Folder selection
        ttk.Label(doc_frame, text="Documents Folder:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.folder_var = tk.StringVar()
        self.folder_entry = ttk.Entry(doc_frame, textvariable=self.folder_var, state='readonly')
        self.folder_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.browse_btn = ttk.Button(doc_frame, text="Browse", command=self.browse_folder)
        self.browse_btn.grid(row=0, column=2)
        
        # Load documents button
        self.load_btn = ttk.Button(doc_frame, text="Load Documents", 
                                  command=self.load_documents_thread, state='disabled')
        self.load_btn.grid(row=1, column=0, columnspan=3, pady=(10, 0))
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="Ready - Please select a documents folder")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Progress bar
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Chat section
        chat_frame = ttk.LabelFrame(main_frame, text="Chat", padding="10")
        chat_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(chat_frame, height=15, state='disabled',
                                                     wrap=tk.WORD, font=('Arial', 10))
        self.chat_display.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Query input
        ttk.Label(chat_frame, text="Ask a question:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.query_var = tk.StringVar()
        self.query_entry = ttk.Entry(chat_frame, textvariable=self.query_var, state='disabled')
        self.query_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.query_entry.bind('<Return>', self.ask_question_event)
        
        self.ask_btn = ttk.Button(chat_frame, text="Ask", command=self.ask_question_thread, state='disabled')
        self.ask_btn.grid(row=1, column=2)
        
        # Clear chat button
        self.clear_btn = ttk.Button(chat_frame, text="Clear Chat", command=self.clear_chat)
        self.clear_btn.grid(row=2, column=2, pady=(10, 0))
        
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Documents Folder")
        if folder:
            self.folder_var.set(folder)
            self.load_btn.config(state='normal')
            self.status_var.set(f"Folder selected: {folder}")
            
    def load_documents_thread(self):
        # Run document loading in a separate thread to prevent GUI freezing
        thread = threading.Thread(target=self.load_documents)
        thread.daemon = True
        thread.start()
        
    def load_documents(self):
        try:
            folder = self.folder_var.get()
            if not folder or not os.path.exists(folder):
                messagebox.showerror("Error", "Please select a valid documents folder")
                return
                
            # Update UI
            self.root.after(0, lambda: self.progress.start())
            self.root.after(0, lambda: self.load_btn.config(state='disabled'))
            self.root.after(0, lambda: self.status_var.set("Loading documents..."))
            
            # Load documents
            texts = self.read_documents_from_folder(folder)
            if not texts:
                self.root.after(0, lambda: messagebox.showwarning("Warning", "No PDF or DOCX files found in the selected folder"))
                return
                
            self.root.after(0, lambda: self.status_var.set(f"Loaded {len(texts)} documents. Creating embeddings..."))
            
            # Split texts into chunks for better retrieval
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            
            all_chunks = []
            for text in texts:
                chunks = text_splitter.split_text(text)
                all_chunks.extend(chunks)
                
            self.root.after(0, lambda: self.status_var.set(f"Split into {len(all_chunks)} chunks. Building QA system..."))
            
            # Create QA system
            self.create_qa_system(all_chunks)
            
            # Update UI
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.status_var.set(f"Ready! Loaded {len(texts)} documents with {len(all_chunks)} chunks."))
            self.root.after(0, lambda: self.query_entry.config(state='normal'))
            self.root.after(0, lambda: self.ask_btn.config(state='normal'))
            self.root.after(0, lambda: self.load_btn.config(state='normal'))
            self.root.after(0, lambda: self.add_to_chat("System", "Documents loaded successfully! You can now ask questions."))
            
            self.documents_loaded = True
            
        except Exception as e:
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.load_btn.config(state='normal'))
            self.root.after(0, lambda: self.status_var.set("Error loading documents"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load documents: {str(e)}"))
            
    def read_documents_from_folder(self, folder):
        texts = []
        supported_files = []
        
        for file in os.listdir(folder):
            if file.endswith(('.pdf', '.docx')):
                supported_files.append(file)
                
        for i, file in enumerate(supported_files):
            full_path = os.path.join(folder, file)
            self.root.after(0, lambda f=file, idx=i+1, total=len(supported_files): 
                          self.status_var.set(f"Reading {f} ({idx}/{total})..."))
            
            try:
                if file.endswith(".pdf"):
                    text = self.read_pdf(full_path)
                elif file.endswith(".docx"):
                    text = self.read_word(full_path)
                    
                if text.strip():  # Only add non-empty texts
                    texts.append(text)
            except Exception as e:
                print(f"Error reading {file}: {str(e)}")
                continue
                
        return texts
        
    def read_pdf(self, path):
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
        
    def read_word(self, path):
        doc = Document(path)
        return "\n".join([p.text for p in doc.paragraphs])
        
    def create_qa_system(self, texts):
        # Initialize embedding model if not already done
        if self.embed_model is None:
            self.embed_model = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
            
        # Create FAISS vector store
        faiss_store = LangchainFAISS.from_texts(texts, self.embed_model)
        
        # Initialize Llama 3.2 model
        llm = Ollama(model="llama3.2")  # Updated to use Llama 3.2
        
        # Create QA chain
        self.qa_system = RetrievalQA.from_chain_type(
            llm=llm, 
            chain_type="stuff",
            retriever=faiss_store.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=False
        )
        
    def ask_question_event(self, event):
        self.ask_question_thread()
        
    def ask_question_thread(self):
        # Run question answering in a separate thread
        thread = threading.Thread(target=self.ask_question)
        thread.daemon = True
        thread.start()
        
    def ask_question(self):
        if not self.documents_loaded or not self.qa_system:
            self.root.after(0, lambda: messagebox.showwarning("Warning", "Please load documents first"))
            return
            
        query = self.query_var.get().strip()
        if not query:
            return
            
        try:
            # Update UI
            self.root.after(0, lambda: self.ask_btn.config(state='disabled'))
            self.root.after(0, lambda: self.status_var.set("Processing question..."))
            self.root.after(0, lambda: self.add_to_chat("You", query))
            self.root.after(0, lambda: self.query_var.set(""))
            
            # Get answer
            answer = self.qa_system.run(query)
            
            # Update UI with answer
            self.root.after(0, lambda: self.add_to_chat("Assistant", answer))
            self.root.after(0, lambda: self.status_var.set("Ready"))
            self.root.after(0, lambda: self.ask_btn.config(state='normal'))
            
        except Exception as e:
            self.root.after(0, lambda: self.add_to_chat("System", f"Error: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Error processing question"))
            self.root.after(0, lambda: self.ask_btn.config(state='normal'))
            
    def add_to_chat(self, sender, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"\n{sender}: {message}\n")
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
        
    def clear_chat(self):
        self.chat_display.config(state='normal')
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state='disabled')

def main():
    # Check if Ollama is available
    try:
        # Test Ollama connection
        test_llm = Ollama(model="llama3.2")
        print("Ollama connection successful")
    except Exception as e:
        print(f"Warning: Could not connect to Ollama: {e}")
        print("Make sure Ollama is installed and running with llama3.2 model")
        print("Install: curl -fsSL https://ollama.ai/install.sh | sh")
        print("Pull model: ollama pull llama3.2")
        
    root = tk.Tk()
    app = DocumentChatGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()