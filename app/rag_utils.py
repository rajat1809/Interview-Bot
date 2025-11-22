"""
RAG Utilities for PDF-based Job Description Retrieval
"""
from typing import Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.tools import Tool
from langchain_core.documents import Document
import tempfile
import os


def process_pdf(pdf_file) -> FAISS:
    """
    Process uploaded PDF and create FAISS vector store
    
    Args:
        pdf_file: Streamlit UploadedFile object
        
    Returns:
        FAISS vector store
    """
    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(pdf_file.getvalue())
        tmp_path = tmp_file.name
    
    try:
        # Load PDF
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)
        
        # Create embeddings and vector store
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(chunks, embeddings)
        
        return vectorstore
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def create_retrieval_tool(vectorstore: FAISS) -> Tool:
    """
    Create a LangChain tool for retrieving job description context
    
    Args:
        vectorstore: FAISS vector store containing job description
        
    Returns:
        LangChain Tool for retrieval
    """
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )
    
    def retrieve_context(query: str) -> str:
        """Retrieve relevant context from the job description"""
        docs = retriever.invoke(query)  # Updated to use invoke instead of get_relevant_documents
        if not docs:
            return "No relevant information found in job description."
        
        # Combine retrieved documents
        context = "\n\n".join([doc.page_content for doc in docs])
        return f"Relevant Job Description Context:\n{context}"
    
    tool = Tool(
        name="job_description_retrieval",
        description=(
            "Retrieves relevant information from the job description PDF. "
            "Use this when you need specific details about job requirements, "
            "responsibilities, qualifications, or any other aspect of the role. "
            "Input should be a specific question or topic related to the job."
        ),
        func=retrieve_context
    )
    
    return tool


def create_resume_retrieval_tool(vectorstore: FAISS) -> Tool:
    """
    Create a LangChain tool for retrieving candidate resume/experience context
    
    Args:
        vectorstore: FAISS vector store containing candidate resume
        
    Returns:
        LangChain Tool for resume retrieval
    """
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )
    
    def retrieve_resume_context(query: str) -> str:
        """Retrieve relevant context from the candidate's resume"""
        docs = retriever.invoke(query)
        if not docs:
            return "No relevant information found in candidate resume."
        
        # Combine retrieved documents
        context = "\n\n".join([doc.page_content for doc in docs])
        return f"Relevant Candidate Resume Context:\n{context}"
    
    tool = Tool(
        name="candidate_resume_retrieval",
        description=(
            "Retrieves relevant information from the candidate's resume PDF. "
            "Use this when you need details about their projects, work experience, "
            "internships, skills, education, or any other background information. "
            "Input should be a specific question about their experience or qualifications."
        ),
        func=retrieve_resume_context
    )
    
    return tool



def create_simple_vectorstore(text: str) -> FAISS:
    """
    Create a simple vector store from plain text (fallback if no PDF)
    
    Args:
        text: Plain text job description
        
    Returns:
        FAISS vector store
    """
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = text_splitter.create_documents([text])
    
    # Create embeddings and vector store
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    return vectorstore
