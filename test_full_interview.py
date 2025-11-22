import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from app.graph import app_graph

load_dotenv()

def test_full_interview():
    print("Testing Full Interview Flow...")
    
    messages = [HumanMessage(content="Start the interview.")]
    role = None
    q_count = 0
    status = "active"
    
    # Turn 1: Start
    print("\n--- Turn 1: Start ---")
    state = {
        "messages": messages,
        "job_description": "Python Dev",
        "candidate_details": "5 years exp",
        "interview_role": role,
        "num_questions_asked": q_count,
        "interview_status": status
    }
    
    events = list(app_graph.stream(state))
    
    for event in events:
        for key, value in event.items():
            if key == "main_agent" and "interview_role" in value:
                role = value["interview_role"]
            if key == "interviewer_agent":
                if "num_questions_asked" in value:
                    q_count = value["num_questions_asked"]
                if "messages" in value:
                    messages.append(value["messages"][-1])
                if "interview_status" in value:
                    status = value["interview_status"]
    
    print(f"Questions asked: {q_count}, Status: {status}")
    
    # Simulate 5 answers
    for i in range(2, 7):
        print(f"\n--- Turn {i}: User answers Q{i-1} ---")
        messages.append(HumanMessage(content=f"Answer {i-1}"))
        
        state = {
            "messages": messages,
            "job_description": "Python Dev",
            "candidate_details": "5 years exp",
            "interview_role": role,
            "num_questions_asked": q_count,
            "interview_status": status
        }
        
        events = list(app_graph.stream(state))
        
        for event in events:
            for key, value in event.items():
                if key == "interviewer_agent":
                    if "num_questions_asked" in value:
                        q_count = value["num_questions_asked"]
                    if "messages" in value:
                        messages.append(value["messages"][-1])
                    if "interview_status" in value:
                        status = value["interview_status"]
                elif key == "feedback_agent":
                    if "interview_status" in value:
                        status = value["interview_status"]
                    print("Feedback agent triggered!")
        
        print(f"Questions asked: {q_count}, Status: {status}")
        
        if status == "completed":
            print("\n✅ Interview completed after 5 questions!")
            break
    
    if status != "completed":
        print(f"\n❌ FAIL: Interview did not complete. Final count: {q_count}, Status: {status}")

if __name__ == "__main__":
    test_full_interview()
