from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import openai
import os
import logging
import json
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app, resources={r"/chat": {"origins": "*"}})

# Ensure OpenAI API key is set
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")  # Default assistant

if not OPENAI_API_KEY:
    logging.error("❌ ERROR: OpenAI API key is missing! Set OPENAI_API_KEY in Render.")
    exit(1)

# Create OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    """Handles chat requests with real-time streaming responses."""
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
        assistant_id = data.get("assistant_id", DEFAULT_ASSISTANT_ID)

        # Ensure the assistant_id is valid
        VALID_ASSISTANTS = [
            "asst_ZyXJMQwA8MulRePeac9yxyJf",
            "asst_HwvvKaHr2KK96OG4yrEQODAr",
            "asst_1tMmOiBVSiXfWVZzH0jEVVM6",
            "asst_Vwwf9mz2Dgp7Ronqoo4Vr3iW",
            "asst_myeXUDSjkOVYOD49KywewOql",
            "asst_6eb0i7fRkgfe0YSnHNxHberr",
            "asst_7lyLvPhSSTRpBracIVDMQtCX",
            "asst_VgoKfFR5tyuzfsKIsdExS5jm",
            "asst_ioLttRdyfMxlFAuwkAcxImsm"
        ]
        if assistant_id not in VALID_ASSISTANTS:
            logging.error(f"❌ ERROR: Invalid Assistant ID {assistant_id}")
            return jsonify({"error": "Invalid Assistant ID"}), 400

        logging.debug(f"💬 User message: {user_message}")
        logging.debug(f"🤖 Using Assistant ID: {assistant_id}")

        # Create a new thread
        thread = client.beta.threads.create()

        # Add user message to thread
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_message
        )

        # Start the assistant run
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )

        # Wait for the assistant to start streaming
        def stream_response():
            """Generator function to stream OpenAI's response in real-time."""
            try:
                # Poll until the run completes
                while True:
                    time.sleep(1)  # Prevents overloading OpenAI with requests
                    run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                    
                    if run_status.status == "completed":
                        break
                    elif run_status.status == "failed":
                        yield json.dumps({"error": "Assistant API run failed"}) + "\n"
                        return

                # Retrieve the messages from OpenAI
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                response_text = messages.data[0].content[0].text.value

                # Stream response word by word
                for word in response_text.split():
                    yield json.dumps({"response": word + " "}) + "\n"
                    time.sleep(0.05)  # Simulate natural typing delay

            except Exception as e:
                logging.error(f"❌ Streaming Error: {str(e)}")
                yield json.dumps({"error": "Streaming failed"}) + "\n"

        return Response(stream_response(), content_type="text/event-stream")

    except openai.OpenAIError as e:
        logging.error(f"❌ OpenAI API Error: {str(e)}")
        return jsonify({"error": "OpenAI API error", "details": str(e)}), 500

    except Exception as e:
        logging.error(f"❌ Internal Server Error: {str(e)}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
