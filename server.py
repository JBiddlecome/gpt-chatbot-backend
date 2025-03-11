from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)

# Enable CORS for all origins and methods
CORS(app, resources={r"/chat": {"origins": "*"}})

# Set OpenAI API Key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/", methods=["GET"])
def home():
    """Debug route to check if backend is running and list available endpoints."""
    return jsonify({
        "message": "Backend is running",
        "available_routes": ["/chat"]
    })

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    """Handles incoming chat requests and forwards them to OpenAI."""
    if request.method == "OPTIONS":
        # Handle preflight request for CORS
        response = jsonify({"message": "CORS preflight successful"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response, 200

    data = request.json
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_message}]
        )

        result = response["choices"][0]["message"]["content"]
        return jsonify({"response": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
