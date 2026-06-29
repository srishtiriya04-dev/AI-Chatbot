from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"]
    mode = request.json.get("mode", "friendly")

    prompt = f"""
You are an AI chatbot.

Current style: {mode}

Rules:
- friendly → warm, simple, helpful
- funny → humorous, light jokes
- realistic → professional and factual

User: {user_message}

Assistant:
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma3:1b",
                "prompt": prompt,
                "stream": False
            }
        )

        bot_reply = response.json()["response"]

    except Exception as e:
        bot_reply = "Error: " + str(e)

    return jsonify({"reply": bot_reply})

if __name__ == "__main__":
    app.run(debug=True)