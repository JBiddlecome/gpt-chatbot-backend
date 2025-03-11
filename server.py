from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app, resources={r"/chat": {"origins": "*"}})

# Ensure OpenAI API key is set
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")  # Your Assistant ID
if not OPENAI_API_KEY or not ASSISTANT_ID:
    logging.error("❌ ERROR: Missing OpenAI API Key or Assistant ID. Set them in Render.")
    exit(1)

# Create OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

@app.route("/", methods=["GET"])
def home():
    """Debug route to check if backend is running."""
    return jsonify({
        "message": "Backend is running",
        "available_routes": ["/chat"]
    })

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    """Handles incoming chat requests and forwards them to OpenAI Assistant API."""
    if request.method == "OPTIONS":
        response = jsonify({"message": "CORS preflight successful"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response, 200

    try:
        logging.debug("📥 Incoming request: %s", request.json)

        data = request.get_json()
        if not data or "message" not in data:
            logging.error("❌ ERROR: Invalid JSON request received!")
            return jsonify({"error": "Invalid request format"}), 400

        user_message = data["message"]
        logging.debug("💬 User message: %s", user_message)

        # Use OpenAI Assistant linked to the Vector Store
        thread = client.beta.threads.create()
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_message
        )

        # Run assistant to retrieve responses from vector-embedded files
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        # Wait for the run to complete (Polling)
        import time
        while run.status not in ["completed", "failed"]:
            time.sleep(2)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run.status == "failed":
            logging.error("❌ ERROR: Assistant API run failed")
            return jsonify({"error": "Assistant API failed"}), 500

        # Get the Assistant's response
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        response_text = messages.data[0].content[0].text.value

        logging.debug("🤖 Assistant Response: %s", response_text)
        return jsonify({"response": response_text})

    except openai.OpenAIError as e:
        logging.error(f"❌ OpenAI API Error: {str(e)}")
        return jsonify({"error": "OpenAI API error", "details": str(e)}), 500

    except Exception as e:
        logging.error(f"❌ Internal Server Error: {str(e)}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
