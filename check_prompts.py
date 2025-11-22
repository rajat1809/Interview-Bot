try:
    from app.prompts import ROUTER_SYSTEM_PROMPT
    print("Successfully imported ROUTER_SYSTEM_PROMPT")
except SyntaxError as e:
    print(f"SyntaxError: {e}")
except Exception as e:
    print(f"Error: {e}")
