import streamlit as st
import os
from langchain_core.messages import HumanMessage, AIMessage
from app.graph import app_graph
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Setup Page
st.set_page_config(page_title="AI Interviewer", layout="wide")
st.title("AI Interviewer (Streamlit + OpenAI)")

# Initialize OpenAI Client for Audio (TTS/STT)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- SESSION STATE SETUP ---
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

# --- SIDEBAR CONFIG ---
with st.sidebar:
    st.header("Interview Config")
    st.session_state.job_description = st.text_area("Job Description", st.session_state.job_description)
    st.session_state.candidate_details = st.text_area("Candidate Details", st.session_state.candidate_details)
    
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
        st.rerun()

# --- HELPER FUNCTIONS ---
def process_response(events):
    """Process LangGraph events and update UI"""
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
                        
                        # Check if code is required
                        st.session_state.req_code_input = value.get("req_code_input", False)
                        
                        # Update progress
                        if "num_questions_asked" in value:
                            st.session_state.num_questions_asked = value["num_questions_asked"]
                        if "interview_status" in value:
                            st.session_state.interview_status = value["interview_status"]
                        
                        # Generate Audio (TTS)
                        try:
                            response = client.audio.speech.create(
                                model="tts-1",
                                voice="alloy",
                                input=msg_content
                            )
                            # Save audio to session to play automatically
                            st.session_state["last_audio"] = response.content
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
        st.error(f"An error occurred during processing: {e}")
        import traceback
        st.text(traceback.format_exc())

def run_turn(user_text, code_snippet=None):
    """Run one turn of the conversation"""
    
    # 1. Construct Payload
    full_input = user_text
    if code_snippet:
        full_input += f"\n\n### CANDIDATE CODE SUBMISSION:\n```\n{code_snippet}\n```"
    
    st.session_state.messages.append({"role": "user", "content": full_input})

    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    
    # 2. Initialization vs Continuation Logic
    if not st.session_state.started:
        initial_state = {
            "messages": [HumanMessage(content="Start the interview.")],
            "job_description": st.session_state.job_description,
            "candidate_details": st.session_state.candidate_details,
            "interview_role": st.session_state.interview_role,
            "num_questions_asked": st.session_state.num_questions_asked,
            "interview_status": st.session_state.interview_status
        }
        st.session_state.started = True
        events = app_graph.stream(initial_state, config=config)
    else:
        # Convert session messages to LangChain messages
        # We need to pass the FULL history because the graph is stateless
        history = []
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                history.append(AIMessage(content=msg["content"]))
        
        events = app_graph.stream(
            {
                "messages": history,
                "job_description": st.session_state.job_description,
                "candidate_details": st.session_state.candidate_details,
                "interview_role": st.session_state.interview_role,
                "num_questions_asked": st.session_state.num_questions_asked,
                "interview_status": st.session_state.interview_status
            }, 
            config=config
        )
    
    process_response(events)
    st.rerun()

# --- UI LAYOUT ---

# Display Detailed Evaluation if available
if st.session_state.detailed_evaluation:
    st.success("🎉 Interview Completed!")
    
    eval_data = st.session_state.detailed_evaluation
    
    # Decision Banner
    decision = eval_data.get("decision", "PENDING")
    if decision == "HIRE":
        st.success(f"### ✅ Decision: {decision}")
    elif decision == "NO HIRE":
        st.error(f"### ❌ Decision: {decision}")
    else:
        st.warning(f"### ⏸️ Decision: {decision}")
    
    # Ratings Section
    st.divider()
    st.subheader("📊 Performance Ratings")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Overall", f"{eval_data.get('overall_rating', 0)}/10")
    with col2:
        st.metric("Technical", f"{eval_data.get('technical_rating', 0)}/10")
    with col3:
        st.metric("Communication", f"{eval_data.get('communication_rating', 0)}/10")
    with col4:
        st.metric("Problem Solving", f"{eval_data.get('problem_solving_rating', 0)}/10")
    
    # Strengths
    st.divider()
    st.subheader("💪 Strengths")
    for strength in eval_data.get("strengths", []):
        st.markdown(f"- {strength}")
    
    # Areas for Improvement
    st.divider()
    st.subheader("📈 Areas for Improvement")
    for area in eval_data.get("areas_for_improvement", []):
        st.markdown(f"- {area}")
    
    # Recommendations
    st.divider()
    st.subheader("💡 Recommendations")
    st.write(eval_data.get("recommendations", "No recommendations provided."))
    
    # Restart Button
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
        st.rerun()

else:
    # 1. Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Play Audio if fresh
    if "last_audio" in st.session_state:
        st.audio(st.session_state["last_audio"], format="audio/mp3", autoplay=True)
        del st.session_state["last_audio"] # Clear so it doesn't loop

    # 2. Input Area
    if st.session_state.interview_status == "completed":
        st.info("Interview Completed. Generating evaluation...")
    elif not st.session_state.started:
        if st.button("Begin Interview"):
            run_turn("Start")
    else:
        # Code Editor Toggle
        code_input = None
        if st.session_state.req_code_input or st.toggle("Show Code Editor"):
            code_input = st.text_area("Code Editor", height=150, placeholder="def solution():\n    pass")

        # Voice Input (Streamlit Audio Recorder) - use counter as key to reset widget
        audio_value = st.audio_input("Voice Mode 🎤", key=f"audio_{st.session_state.audio_counter}")
        
        if audio_value and audio_value != st.session_state.last_audio_processed:
            # Transcribe with OpenAI Whisper
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_value
            )
            # Mark this audio as processed
            st.session_state.last_audio_processed = audio_value
            # Increment counter to reset widget on next rerun
            st.session_state.audio_counter += 1
            # Only include code if it's not empty
            code_to_submit = code_input if (code_input and code_input.strip()) else None
            run_turn(transcription.text, code_snippet=code_to_submit)

        # Text Input
        user_input = st.chat_input("Type your answer...")
        if user_input:
            # Only include code if it's not empty
            code_to_submit = code_input if (code_input and code_input.strip()) else None
            run_turn(user_input, code_snippet=code_to_submit)