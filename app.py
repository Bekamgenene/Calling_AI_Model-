import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
from PyPDF2 import PdfReader
from docx import Document
import io

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stTextInput > div > div > input {
        background-color: #f0f2f6;
    }
    .success-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
    .response-box {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #ffffff;
        border: 2px solid #4CAF50;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'document_text' not in st.session_state:
    st.session_state.document_text = ""

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    try:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"

def extract_text_from_docx(docx_file):
    """Extract text from DOCX file"""
    try:
        doc = Document(docx_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        return f"Error extracting DOCX: {str(e)}"

def extract_text_from_txt(txt_file):
    """Extract text from TXT file"""
    try:
        return txt_file.read().decode('utf-8')
    except Exception as e:
        return f"Error extracting TXT: {str(e)}"

def call_llm(prompt, document_context, model_choice, api_key):
    """Call the LLM with the prompt and document context"""
    try:
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Initialize model
        model = genai.GenerativeModel(model_choice)
        
        # Prepare the message
        if document_context:
            full_prompt = f"""Document Content:
{document_context}

User Question: {prompt}

Please answer the question based on the document content provided above."""
        else:
            full_prompt = prompt
        
        # Call Gemini API
        response = model.generate_content(full_prompt)
        
        return response.text
    
    except Exception as e:
        return f"Error calling LLM: {str(e)}"

# Main App
def main():
    # Header
    st.title("🤖 AI Document Assistant")
    st.markdown("### Connect to powerful AI models and analyze your documents")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Model selection
        st.subheader("✨ Google Gemini AI")
        
        model_choice = st.selectbox(
            "Select Model",
            [
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-1.0-pro"
            ],
            help="Choose the Gemini model to use"
        )
        
        # API Key input
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            value=os.getenv("GEMINI_API_KEY", ""),
            help="Enter your Gemini API key"
        )
        
        if api_key:
            st.markdown('<div class="success-message">✅ API Key configured</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-message">⚠️ Please enter your API key</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Information
        st.header("ℹ️ About")
        st.markdown("""
        This app allows you to:
        - 📤 Upload documents (PDF, DOCX, TXT)
        - 💬 Ask questions about your documents
        - 🤖 Get AI-powered responses
        - 📊 View conversation history
        """)
        
        # Clear conversation button
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.document_text = ""
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📄 Document Upload")
        uploaded_file = st.file_uploader(
            "Upload a document",
            type=['pdf', 'docx', 'txt'],
            help="Upload a PDF, DOCX, or TXT file"
        )
        
        if uploaded_file is not None:
            with st.spinner("Processing document..."):
                # Extract text based on file type
                if uploaded_file.type == "application/pdf":
                    document_text = extract_text_from_pdf(uploaded_file)
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    document_text = extract_text_from_docx(uploaded_file)
                else:
                    document_text = extract_text_from_txt(uploaded_file)
                
                st.session_state.document_text = document_text
                
                # Show document preview
                st.success(f"✅ Document loaded: {uploaded_file.name}")
                with st.expander("📖 View Document Content"):
                    st.text_area(
                        "Document Text",
                        value=document_text[:1000] + "..." if len(document_text) > 1000 else document_text,
                        height=200,
                        disabled=True
                    )
                    st.caption(f"Total characters: {len(document_text)}")
    
    with col2:
        st.header("💬 Ask Questions")
        
        # User input
        user_prompt = st.text_area(
            "Enter your question or prompt",
            height=100,
            placeholder="Ask a question about the document or have a general conversation..."
        )
        
        # Send button
        if st.button("🚀 Send to AI", type="primary", use_container_width=True):
            if not api_key:
                st.error("❌ Please configure your API key in the sidebar!")
            elif not user_prompt:
                st.error("❌ Please enter a prompt!")
            else:
                # Add user message to history
                st.session_state.messages.append({
                    "role": "user",
                    "content": user_prompt
                })
                
                # Show processing animation
                with st.spinner("🤔 AI is thinking..."):
                    # Call LLM
                    response = call_llm(
                        user_prompt,
                        st.session_state.document_text,
                        model_choice,
                        api_key
                    )
                    
                    # Add AI response to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                
                st.rerun()
    
    # Response area
    st.divider()
    st.header("💡 AI Responses")
    
    if st.session_state.messages:
        for idx, message in enumerate(st.session_state.messages):
            if message["role"] == "user":
                with st.container():
                    st.markdown("**👤 You:**")
                    st.info(message["content"])
            else:
                with st.container():
                    st.markdown("**🤖 AI Assistant:**")
                    st.markdown(f'<div class="response-box">{message["content"]}</div>', unsafe_allow_html=True)
            
            if idx < len(st.session_state.messages) - 1:
                st.divider()
    else:
        st.markdown('<div class="info-box">👋 No messages yet. Upload a document and start asking questions!</div>', unsafe_allow_html=True)
    
    # Footer
    st.divider()
    st.caption("🔒 Your API keys and documents are processed securely and are not stored.")

if __name__ == "__main__":
    main()
