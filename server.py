from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
from openai import OpenAIError  # Corrected import
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app, resources={r"/chat": {"origins": "*"}})

# Ensure OpenAI API key is set
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.error("❌ ERROR: OpenAI API key is missing! Set OPENAI_API_KEY in Render.")
    exit(1)

# Create OpenAI client (New API format)
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
    """Handles incoming chat requests and forwards them to OpenAI."""
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

        # Corrected OpenAI API call
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_message}]
        )

        # Debug log for response
        logging.debug("🔍 OpenAI Raw Response: %s", response)

        if not response.choices or len(response.choices) == 0:
            logging.error("❌ ERROR: Unexpected OpenAI response format: %s", response)
            return jsonify({"error": "Invalid OpenAI response"}), 500

        # Extracting content safely from OpenAI response
        result = response.choices[0].message.content
        logging.debug("🤖 GPT Response: %s", result)

        return jsonify({"response": result})

    except OpenAIError as e:  # Ensure proper exception handling
        logging.error(f"❌ OpenAI API Error: {str(e)}")
        return jsonify({"error": "OpenAI API error", "details": str(e)}), 500

    except Exception as e:
        logging.error(f"❌ Internal Server Error: {str(e)}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
