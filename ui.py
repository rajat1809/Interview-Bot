import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain_core.messages import HumanMessage, AIMessage
from app.graph import app_graph
from app.rag_utils import process_pdf

load_dotenv()

# Page configuration
st.set_page_config(page_title="AI Interviewer", layout="wide")
st.title("AI Interviewer (Streamlit + OpenAI)")

# OpenAI client for audio (TTS/STT)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Session state initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "session_1"
if "started" not in st.session_state:
    st.session_state.started = False
if "req_code_input" not in st.session_state:
    st.session_state.req_code_input = False
if "job_description" not in st.session_state:
    st.session_state.job_description = "Senior Python Developer"
if "candidate_details" not in st.session_state:
    st.session_state.candidate_details = "5 years experience, strong SQL"
if "interview_role" not in st.session_state:
    st.session_state.interview_role = None
if "num_questions_asked" not in st.session_state:
    st.session_state.num_questions_asked = 0
if "interview_status" not in st.session_state:
    st.session_state.interview_status = "active"
if "detailed_evaluation" not in st.session_state:
    st.session_state.detailed_evaluation = None
if "last_audio_processed" not in st.session_state:
    st.session_state.last_audio_processed = None
if "audio_counter" not in st.session_state:
    st.session_state.audio_counter = 0
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "code_editor_key" not in st.session_state:
    st.session_state.code_editor_key = 0
if "last_pdf_name" not in st.session_state:
    st.session_state.last_pdf_name = None

# --- Sidebar configuration ---
with st.sidebar:
    st.header("Interview Config")
    st.session_state.job_description = st.text_area("Job Description", st.session_state.job_description, height=100)
    st.session_state.candidate_details = st.text_area("Candidate Details", st.session_state.candidate_details, height=80)
    uploaded_pdf = st.file_uploader("Upload JD PDF", type=["pdf"], key="pdf_uploader")
    if uploaded_pdf:
        if st.session_state.last_pdf_name != uploaded_pdf.name:
            with st.spinner("Processing PDF..."):
                try:
                    vectorstore = process_pdf(uploaded_pdf)
                    st.session_state.vectorstore = vectorstore
                    st.session_state.last_pdf_name = uploaded_pdf.name
                    st.success(f"✅ Processed: {uploaded_pdf.name}")
                except Exception as e:
                    st.error(f"Error processing PDF: {e}")
                    st.session_state.vectorstore = None
        else:
            st.info(f"✅ Using cached PDF: {uploaded_pdf.name}")
    if st.button("Start / Reset Interview"):
        st.session_state.messages = []
        st.session_state.started = False
        st.session_state.req_code_input = False
        st.session_state.interview_role = None
        st.session_state.num_questions_asked = 0
        st.session_state.interview_status = "active"
        st.session_state.detailed_evaluation = None
        st.session_state.last_audio_processed = None
        st.session_state.audio_counter = 0
        st.session_state.vectorstore = None
        st.session_state.last_pdf_name = None
        st.rerun()

# --- Helper functions ---
def process_response(events):
    """Process LangGraph events and update session state/UI."""
    try:
        for event in events:
            for key, value in event.items():
                if value is None:
                    continue
                if key == "main_agent":
                    if "interview_role" in value:
                        st.session_state.interview_role = value["interview_role"]
                    if "interview_status" in value:
                        st.session_state.interview_status = value["interview_status"]
                elif key == "interviewer_agent":
                    if "messages" in value:
                        msg_content = value["messages"][-1].content
                        st.session_state.messages.append({"role": "assistant", "content": msg_content})
                        st.session_state.req_code_input = value.get("req_code_input", False)
                        if "num_questions_asked" in value:
                            st.session_state.num_questions_asked = value["num_questions_asked"]
                        if "interview_status" in value:
                            st.session_state.interview_status = value["interview_status"]
                        # TTS
                        try:
                            resp = client.audio.speech.create(model="tts-1", voice="alloy", input=msg_content)
                            st.session_state["last_audio"] = resp.content
                        except Exception as e:
                            st.error(f"TTS Error: {e}")
                elif key == "evaluation_agent":
                    st.session_state.messages.append({"role": "assistant", "content": "Interview Complete. Generating Detailed Evaluation..."})
                    if "detailed_evaluation" in value:
                        st.session_state.detailed_evaluation = value["detailed_evaluation"]
                        st.session_state.messages.append({"role": "assistant", "content": f"DECISION: {value['detailed_evaluation']['decision']}"})
                    if "interview_status" in value:
                        st.session_state.interview_status = value["interview_status"]
    except Exception as e:
        st.error(f"Processing error: {e}")
        import traceback
        st.text(traceback.format_exc())

def run_turn(user_text, code_snippet=None):
    """Run one turn of the interview, sending the payload to the LangGraph."""
    full_input = user_text
    if code_snippet:
        full_input += f"\n\n### CANDIDATE CODE SUBMISSION:\n```\n{code_snippet}\n```"
    st.session_state.messages.append({"role": "user", "content": full_input})
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    if not st.session_state.started:
        initial_state = {
            "messages": [HumanMessage(content="Start the interview.")],
            "job_description": st.session_state.job_description,
            "candidate_details": st.session_state.candidate_details,
            "interview_role": st.session_state.interview_role,
            "num_questions_asked": st.session_state.num_questions_asked,
            "interview_status": st.session_state.interview_status,
            "retriever": st.session_state.vectorstore,
        }
        st.session_state.started = True
        events = app_graph.stream(initial_state, config=config)
    else:
        # Build full history for stateless graph
        history = []
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                history.append(HumanMessage(content=msg["content"]))
            else:
                history.append(AIMessage(content=msg["content"]))
        events = app_graph.stream({
            "messages": history,
            "job_description": st.session_state.job_description,
            "candidate_details": st.session_state.candidate_details,
            "interview_role": st.session_state.interview_role,
            "num_questions_asked": st.session_state.num_questions_asked,
            "interview_status": st.session_state.interview_status,
            "retriever": st.session_state.vectorstore,
        }, config=config)
    process_response(events)
    st.rerun()

# --- UI Layout ---
if st.session_state.detailed_evaluation:
    # Evaluation screen
    st.success("🎉 Interview Completed!")
    eval_data = st.session_state.detailed_evaluation
    decision = eval_data.get("decision", "PENDING")
    if decision == "HIRE":
        st.success(f"### ✅ Decision: {decision}")
    elif decision == "NO HIRE":
        st.error(f"### ❌ Decision: {decision}")
    else:
        st.warning(f"### ⏸️ Decision: {decision}")
    st.divider()
    st.subheader("📊 Performance Ratings")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Overall", f"{eval_data.get('overall_rating',0)}/10")
    with col2:
        st.metric("Technical", f"{eval_data.get('technical_rating',0)}/10")
    with col3:
        st.metric("Communication", f"{eval_data.get('communication_rating',0)}/10")
    with col4:
        st.metric("Problem Solving", f"{eval_data.get('problem_solving_rating',0)}/10")
    st.divider()
    st.subheader("💪 Strengths")
    for s in eval_data.get('strengths', []):
        st.markdown(f"- {s}")
    st.divider()
    st.subheader("📈 Areas for Improvement")
    for a in eval_data.get('areas_for_improvement', []):
        st.markdown(f"- {a}")
    st.divider()
    st.subheader("💡 Recommendations")
    st.write(eval_data.get('recommendations', "No recommendations provided."))
    st.divider()
    if st.button("🔄 Start New Interview", type="primary"):
        st.session_state.messages = []
        st.session_state.started = False
        st.session_state.req_code_input = False
        st.session_state.interview_role = None
        st.session_state.num_questions_asked = 0
        st.session_state.interview_status = "active"
        st.session_state.detailed_evaluation = None
        st.session_state.last_audio_processed = None
        st.session_state.audio_counter = 0
        st.session_state.vectorstore = None
        st.session_state.last_pdf_name = None
        st.rerun()
else:
    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    # Audio playback
    if "last_audio" in st.session_state:
        st.audio(st.session_state["last_audio"], format="audio/mp3", autoplay=True)
        del st.session_state["last_audio"]
    # Input area
    if st.session_state.interview_status == "completed":
        st.info("Interview Completed. Generating evaluation...")
    elif not st.session_state.started:
        if st.button("Begin Interview"):
            run_turn("Start")
    else:
        # Code editor toggle
        code_input = None
        if st.session_state.req_code_input or st.toggle("Show Code Editor"):
            from streamlit_ace import st_ace
            col1, col2 = st.columns([3, 1])
            with col2:
                language = st.selectbox("Language", ["python", "java", "c_cpp"], index=0, key="code_language")
            with col1:
                st.caption("💻 Code Editor (Ctrl+Enter to submit)")
            code_input = st_ace(
                placeholder="Write your code here...",
                language=language,
                theme="monokai",
                keybinding="vscode",
                font_size=14,
                tab_size=4,
                show_gutter=True,
                wrap=True,
                auto_update=True,
                readonly=False,
                min_lines=10,
                max_lines=30,
                key=f"code_editor_{st.session_state.code_editor_key}"
            )
        # Voice input
        audio_value = st.audio_input("Voice Mode 🎤", key=f"audio_{st.session_state.audio_counter}")
        if audio_value and audio_value != st.session_state.last_audio_processed:
            transcription = client.audio.transcriptions.create(model="whisper-1", file=audio_value)
            st.session_state.last_audio_processed = audio_value
            st.session_state.audio_counter += 1
            code_to_submit = code_input if (code_input and code_input.strip()) else None
            run_turn(transcription.text, code_snippet=code_to_submit)
        # Text input
        user_input = st.chat_input("Type your answer...")
        if user_input:
            code_to_submit = code_input if (code_input and code_input.strip()) else None
            run_turn(user_input, code_snippet=code_to_submit)
            # Reset code editor after submission
            st.session_state.code_editor_key += 1