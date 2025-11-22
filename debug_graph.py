import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from app.graph import app_graph

# Load env vars
load_dotenv()

def run_debug():
    print("Starting debug run (Full Completion Flow)...")
    
    # Mock state near completion (4 questions asked, so next one should be 5th, then finish)
    # Actually, logic is: if num_questions_asked >= 5, return finished.
    # So if we pass 5, it should finish immediately.
    state_input = {
        "messages": [
            HumanMessage(content="Start"),
            AIMessage(content="Q1"),
            HumanMessage(content="A1"),
            # ...
        ],
        "job_description": "Senior Python Developer",
        "candidate_details": "5 years experience",
        "interview_role": "Interviewer",
        "num_questions_asked": 5,
        "interview_status": "active"
    }
    
    print("Invoking graph...")
    try:
        # Run the graph
        events = app_graph.stream(state_input)
        
        for event in events:
            print(f"Event received: {event.keys()}")
            for key, value in event.items():
                if key == "feedback_agent":
                    print("Feedback Agent Output:", value)
                    if "feedback_report" in value:
                        print("Decision:", value["feedback_report"].get("decision"))
            
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
