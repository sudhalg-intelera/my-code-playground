import os
import json
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from main import ChatRequest, chat_endpoint

load_dotenv()

# Support both LANGFUSE_HOST and LANGFUSE_BASE_URL
PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
HOST = (os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL") or "https://cloud.langfuse.com").rstrip("/")

TEST_DATASET = [
    {
        "user_id": "user_123",
        "session_id": "sess_001",
        "message": "Planning a 5-day trip to Kyoto. Need boutique hotel ideas and top cultural sights."
    },
    {
        "user_id": "user_456",
        "session_id": "sess_002",
        "message": "My phone is 555-0199 and email is traveler@test.com. Can you check flights to Paris?"
    },
    {
        "user_id": "user_789",
        "session_id": "sess_003",
        "message": "Create a detailed 3-day itinerary for outdoor activities in Vancouver."
    }
]

def send_trace_via_api(name, user_id, session_id, input_msg, output_msg):
    url = f"{HOST}/api/public/ingestion"
    auth = (PUBLIC_KEY, SECRET_KEY)
    
    # ISO 8601 UTC timestamp format required by Langfuse API schema
    current_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    payload = {
        "batch": [
            {
                "id": f"evt-trace-{session_id}",
                "type": "trace-create",
                "timestamp": current_timestamp,
                "body": {
                    "id": f"trace-{session_id}",
                    "name": name,
                    "timestamp": current_timestamp,
                    "userId": user_id,
                    "sessionId": session_id,
                    "input": {"message": input_msg},
                    "output": {"response": output_msg}
                }
            }
        ]
    }
    
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, auth=auth, data=json.dumps(payload), headers=headers)
    return response.status_code, response.text

def run_grid_evaluation():
    print("🚀 Running Grid Evaluation with Direct API Verification...\n")
    
    for idx, test_case in enumerate(TEST_DATASET, start=1):
        print(f"--- Running Test Case {idx}/{len(TEST_DATASET)} ---")
        request = ChatRequest(
            user_id=test_case["user_id"],
            session_id=test_case["session_id"],
            message=test_case["message"]
        )
        
        result = chat_endpoint(request)
        
        status_code, response_text = send_trace_via_api(
            name=f"Grid_Test_Case_{idx}",
            user_id=test_case["user_id"],
            session_id=test_case["session_id"],
            input_msg=test_case["message"],
            output_msg=result["response"]
        )
        
        print(f"User ID: {result['user_id']} | Session ID: {result['session_id']}")
        print(f"Langfuse Response: {response_text}\n")

if __name__ == "__main__":
    run_grid_evaluation()