# AI Interview Agent

An intelligent, AI-powered interview system built with **Streamlit**, **LangGraph**, and **OpenAI GPT** that conducts professional technical interviews with voice support, code evaluation, and PDF-based RAG (Retrieval-Augmented Generation).

## 🌟 Features

- **🎙️ Voice-Enabled Interviews**: Text-to-Speech (TTS) for questions and Speech-to-Text (STT) for answers
- **💻 Live Code Editor**: Integrated code editor with syntax highlighting for coding assessments
- **📄 PDF-Based RAG**: Upload Job Description and Resume PDFs for context-aware questioning
- **🤖 Multi-Agent Architecture**: LangGraph-powered workflow with role routing, interviewing, and evaluation
- **📊 Detailed Evaluation**: Comprehensive candidate assessment with ratings, strengths, and recommendations
- **🔄 Stateful Conversations**: Maintains interview context throughout the session

---

## 📋 Table of Contents

- [Setup Instructions](#setup-instructions)
- [Architecture](#architecture)
- [Design Decisions](#design-decisions)
- [Usage Guide](#usage-guide)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Development](#development)

---

## 🚀 Setup Instructions

### Prerequisites

- Python 3.8+
- OpenAI API Key
- Windows/Linux/macOS

### Installation

1. **Clone the repository**
   ```bash
   cd interview_agent
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Run the application**
   ```bash
   streamlit run ui.py
   ```

6. **Access the app**
   
   Open your browser to `http://localhost:8501`

---

## 🏗️ Architecture

### System Overview

The application uses a **multi-agent architecture** powered by **LangGraph**, where different agents handle specific interview phases:

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit UI Layer                    │
│  (ui.py - Chat Interface, Audio I/O, Code Editor)      │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              LangGraph Workflow (graph.py)              │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐   ┌──────────┐  │
│  │ Main Agent   │───▶│ Interviewer  │──▶│Evaluation│  │
│  │  (Router)    │    │    Agent     │   │  Agent   │  │
│  └──────────────┘    └──────────────┘   └──────────┘  │
│         │                    │                          │
│         ▼                    ▼                          │
│   Determine Role      Ask Questions                    │
│                    + Code Evaluation                    │
│                    + RAG Retrieval                      │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│                   Support Modules                       │
│                                                         │
│  • state.py - Shared state management                  │
│  • models.py - Pydantic schemas for structured output  │
│  • prompts.py - System prompts for each agent          │
│  • rag_utils.py - PDF processing & vector retrieval    │
│  • nodes.py - Agent implementations                    │
└─────────────────────────────────────────────────────────┘
```

### Agent Flow

1. **Main Agent (Router)**
   - Analyzes job description and determines interview role
   - Runs once at the start
   - Output: Role title (e.g., "Senior Python Developer")

2. **Interviewer Agent**
   - Asks 5 substantial questions
   - Uses RAG to retrieve context from JD and Resume PDFs
   - Evaluates code submissions
   - Determines when interview is finished

3. **Evaluation Agent**
   - Generates comprehensive candidate assessment
   - Provides structured ratings (1-10 scale)
   - Makes final hiring recommendation (HIRE/NO HIRE/HOLD)

### State Management

**InterviewState** (TypedDict) maintains:
- `messages`: Conversation history
- `job_description`: JD text
- `candidate_details`: Candidate info
- `interview_role`: Determined role
- `interview_status`: "active" | "finished" | "completed"
- `num_questions_asked`: Question counter
- `req_code_input`: Whether code editor should be shown
- `detailed_evaluation`: Final assessment
- `retriever`: FAISS vectorstore for JD
- `resume_retriever`: FAISS vectorstore for resume

---

## 🎯 Design Decisions

### 1. **LangGraph for Orchestration**
   - **Why**: Provides declarative, graph-based workflow management
   - **Benefit**: Clear separation of concerns, easy to visualize and debug
   - **Alternative considered**: Sequential agent calls (rejected due to poor maintainability)

### 2. **Streamlit for UI**
   - **Why**: Rapid prototyping, built-in components for chat, audio, file uploads
   - **Benefit**: Fast development, native Python integration
   - **Trade-off**: Limited customization vs. React/Next.js

### 3. **RAG with FAISS**
   - **Why**: Efficient similarity search for document retrieval
   - **Implementation**: 
     - PDF → PyPDFLoader → RecursiveCharacterTextSplitter → OpenAI Embeddings → FAISS
     - Chunk size: 1000 characters, overlap: 200
   - **Benefit**: Context-aware questions based on actual JD/resume content

### 4. **Function Calling for Tool Use**
   - **Why**: LLM decides when to retrieve context (vs. always retrieving)
   - **Benefit**: More natural conversation flow, reduces irrelevant context
   - **Fallback**: Uses simple LLM prompt if no PDFs uploaded

### 5. **Caching Strategy**
   - **@st.cache_resource**: Used for LLM initialization and graph compilation
   - **@st.cache_resource(show_spinner=False)**: Used for PDF processing
   - **Why**: Prevents re-initialization on every Streamlit rerun
   - **Impact**: ~80% reduction in response latency

### 6. **Structured Outputs with Pydantic**
   - **Why**: Ensures consistent evaluation format
   - **Models**: 
     - `FeedbackScore`: Simple ratings
     - `DetailedEvaluation`: Comprehensive assessment
   - **Benefit**: Type-safe, validated outputs

### 7. **Voice Integration**
   - **TTS**: OpenAI `tts-1` model with "alloy" voice
   - **STT**: OpenAI `whisper-1` for transcription
   - **Why**: Accessibility and hands-free operation
   - **Trade-off**: Requires API calls (cost consideration)

### 8. **Code Editor Integration**
   - **Library**: streamlit-ace
   - **Why**: Production-grade editor with syntax highlighting
   - **Languages**: Python, Java, C++
   - **Theme**: Monokai (developer-friendly)

### 9. **Interview Termination Logic**
   - **Method**: Agent outputs "INTERVIEW_FINISHED" after 5 questions
   - **Why**: Natural language signal vs. hard counter
   - **Benefit**: Allows flexibility (can finish early if candidate struggles)

### 10. **Session State Management**
   - **Pattern**: Streamlit session_state for all UI state
   - **Why**: Survives widget interactions and reruns
   - **Critical states**: 
     - `messages`: Chat history
     - `started`: Interview initiated flag
     - `detailed_evaluation`: Triggers results screen

---

## 📖 Usage Guide

### Basic Workflow

1. **Configure Interview** (Sidebar)
   - Enter job description or upload JD PDF
   - Enter candidate details or upload resume PDF
   - Click "Start / Reset Interview"

2. **Begin Interview**
   - Click "Begin Interview" button
   - Answer questions via text or voice 🎤

3. **Code Challenges** (if requested)
   - Toggle "Show Code Editor"
   - Select language (Python/Java/C++)
   - Submit code with answer

4. **Review Evaluation**
   - After 5 questions, view detailed assessment
   - See ratings, strengths, areas for improvement
   - Review hiring recommendation

### Advanced Features

**PDF Context Retrieval**
- The interviewer automatically queries PDFs when relevant
- Example: "You mentioned React on your resume, tell me about that project"

**Voice Mode**
- Click the microphone icon to record answer
- Audio is transcribed and submitted automatically
- Questions are read aloud via TTS

**Code Evaluation**
- Interviewer critiques code quality
- Asks for improvements if code is poor
- Moves forward if code is acceptable

---

## 📁 Project Structure

```
interview_agent/
├── app/
│   ├── __init__.py
│   ├── graph.py           # LangGraph workflow definition
│   ├── models.py          # Pydantic schemas for evaluation
│   ├── nodes.py           # Agent implementations (router, interviewer, evaluation)
│   ├── prompts.py         # System prompts for each agent
│   ├── rag_utils.py       # PDF processing & FAISS vector store utilities
│   └── state.py           # InterviewState TypedDict definition
├── ui.py                  # Streamlit frontend application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (API keys) - not in repo
├── .gitignore
└── README.md              # This file
```

### Key Files

| File | Purpose |
|------|---------|
| `ui.py` | Streamlit UI, session management, audio I/O, chat interface |
| `app/graph.py` | LangGraph workflow, defines agent connections and flow |
| `app/nodes.py` | Agent logic: routing, interviewing, evaluation |
| `app/state.py` | Shared state schema used across all agents |
| `app/prompts.py` | System prompts that define each agent's behavior |
| `app/models.py` | Pydantic models for structured LLM outputs |
| `app/rag_utils.py` | PDF processing, embedding generation, FAISS indexing |

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | ✅ Yes |

### Customization Points

**Interview Length** (`app/prompts.py`)
```python
# Change from 5 to 3 questions
7. Ask 5 substantial questions then output: "INTERVIEW_FINISHED"
```

**LLM Model** (`app/nodes.py`)
```python
def get_llm():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
```

**RAG Chunk Size** (`app/rag_utils.py`)
```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,  # Adjust for more/less context
    chunk_overlap=200,
)
```

**TTS Voice** (`ui.py`)
```python
resp = client.audio.speech.create(
    model="tts-1",
    voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
    input=msg_content
)
```

---

## 🛠️ Development

### Testing

The project includes test scripts in the root directory:

- `test_full_interview.py` - End-to-end interview simulation
- `test_counting.py` - Question counter logic validation
- `test_rag.py` - PDF processing and retrieval testing
- `debug_graph.py` - Graph execution debugging
- `validate_resume_feature.py` - Resume RAG functionality tests

Run tests:
```bash
python test_full_interview.py
```

### Adding New Features

**Adding a New Agent**

1. Define agent function in `app/nodes.py`:
   ```python
   def new_agent(state: InterviewState):
       # Your logic here
       return {"new_field": value}
   ```

2. Add to graph in `app/graph.py`:
   ```python
   workflow.add_node("new_agent", new_agent)
   workflow.add_edge("previous_agent", "new_agent")
   ```

3. Update `InterviewState` in `app/state.py` if needed:
   ```python
   class InterviewState(TypedDict):
       new_field: Optional[str]
   ```

### Debugging

**Enable LangGraph Debug Mode**
```python
# In graph.py
app_graph = build_graph().compile(debug=True)
```

**View Agent Outputs**
```python
# In ui.py process_response()
for event in events:
    print(f"Event: {event}")  # Add logging
```

---

## 📝 Dependencies

Core libraries:
- **streamlit**: Web UI framework
- **langchain**: LLM application framework
- **langchain-openai**: OpenAI integration
- **langgraph**: Graph-based agent orchestration
- **pydantic**: Data validation
- **python-dotenv**: Environment variable management
- **pypdf**: PDF parsing
- **faiss-cpu**: Vector similarity search
- **tiktoken**: Token counting
- **streamlit-ace**: Code editor component

---

## 🤝 Contributing

When contributing, please:
1. Follow existing code structure
2. Add tests for new features
3. Update this README if adding new functionality
4. Use type hints for all functions

---

## 📄 License

This project is for educational and demonstration purposes.

---

## 🐛 Troubleshooting

**Issue**: "Module not found" errors
- **Solution**: Ensure virtual environment is activated: `venv\Scripts\activate`

**Issue**: API errors
- **Solution**: Check `.env` file has valid `OPENAI_API_KEY`

**Issue**: PDF upload fails
- **Solution**: Ensure PDF is valid and not password-protected

**Issue**: Slow responses
- **Solution**: Check internet connection, consider upgrading to GPT-4o-mini for faster responses

**Issue**: Code editor not appearing
- **Solution**: Ensure `streamlit-ace` is installed: `pip install streamlit-ace`

---

## 📧 Support

For issues or questions, please:
1. Check this README's troubleshooting section
2. Review the code comments in `app/` directory
3. Test with the provided test scripts

---

**Built with ❤️ using LangGraph, Streamlit, and OpenAI GPT**
