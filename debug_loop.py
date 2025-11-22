import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from app.graph import app_graph

load_dotenv()

def run_debug_loop():
    print("Starting Debug Loop...")
    
    # Mock Session State
    job_description = "Python Dev"
    candidate_details = "Exp"
    interview_role = "Interviewer"
    num_questions_asked = 0
    interview_status = "active"
    
    # Turn 1: Start
    print("\n--- Turn 1: Start ---")
    initial_state = {
        "messages": [HumanMessage(content="Start the interview.")],
        "job_description": job_description,
        "candidate_details": candidate_details,
        "interview_role": None, # Router will set this
        "num_questions_asked": 0,
        "interview_status": "active"
    }
    
    events = list(app_graph.stream(initial_state))
    
    # Process Turn 1 Output
    ai_response = ""
    for event in events:
        for key, value in event.items():
            if key == "main_agent":
                interview_role = value.get("interview_role")
                print(f"Role set to: {interview_role}")
            elif key == "interviewer_agent":
                if "messages" in value:
                    ai_response = value["messages"][-1].content
                    print(f"AI Question 1: {ai_response}")
                if "num_questions_asked" in value:
                    num_questions_asked = value["num_questions_asked"]
                    print(f"Num Questions: {num_questions_asked}")

    # Turn 2: User Answers
    print("\n--- Turn 2: User Answer ---")
    user_answer = "I have 5 years of experience in Python."
    
    # Construct History
    history = [
        HumanMessage(content="Start the interview."),
        AIMessage(content=ai_response),
        HumanMessage(content=user_answer)
    ]
    
    next_state = {
        "messages": history,
        "job_description": job_description,
        "candidate_details": candidate_details,
        "interview_role": interview_role,
        "num_questions_asked": num_questions_asked,
        "interview_status": "active"
    }
    
    events = list(app_graph.stream(next_state))
    
    # Process Turn 2 Output
    for event in events:
        for key, value in event.items():
            if key == "interviewer_agent":
                if "messages" in value:
                    ai_response_2 = value["messages"][-1].content
                    print(f"AI Question 2: {ai_response_2}")
                if "num_questions_asked" in value:
                    num_questions_asked = value["num_questions_asked"]
                    print(f"Num Questions: {num_questions_asked}")

    if ai_response == ai_response_2:
        print("\nFAIL: AI repeated the same question!")
    else:
        print("\nSUCCESS: AI generated a new question.")

if __name__ == "__main__":
    run_debug_loop()
