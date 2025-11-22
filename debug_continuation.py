import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from app.graph import app_graph

# Load env vars
load_dotenv()

def run_debug():
    print("Starting debug run (Continuation Flow with Fix)...")
    
    # Mock continuation state (WITH FULL STATE now, mimicking ui.py fix)
    state_input = {
        "messages": [
            HumanMessage(content="Start"),
            AIMessage(content="Question 1"),
            HumanMessage(content="My answer is Python.")
        ],
        "job_description": "Senior Python Developer",
        "candidate_details": "5 years experience, strong SQL",
        "interview_role": "Technical Interviewer",
        "num_questions_asked": 1,
        "interview_status": "active"
    }
    
    print("Invoking graph with FULL state...")
    try:
        # Run the graph
        events = app_graph.stream(state_input)
        
        for event in events:
            print(f"Event received: {event.keys()}")
            for key, value in event.items():
                if key == "interviewer_agent":
                    print("Interviewer output:", value)
            
    except KeyError as e:
        print(f"CAUGHT KEYERROR: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"CAUGHT EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_debug()
