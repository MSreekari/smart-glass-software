from flask import Flask, request, jsonify, render_template_string
import google.generativeai as genai
import os
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-here-change-in-production")

GEMINI_API_KEY = "AIzaSyAbUKgJFbQHKM1O_4x7jm_kWy-b_a3wrNw"
genai.configure(api_key=GEMINI_API_KEY)

conversations = {}

def build_prompt(user_message, history=None, mode="text"):
    history_text = ""
    if history:
        for item in history[-4:]:
            history_text += f"User: {item['user']}\nAssistant: {item['assistant']}\n"

    base_instruction = (
        "You are a helpful voice assistant integrated into smart glasses. "
        "Respond with short, clear, step-by-step instructions. "
        "Avoid long paragraphs. Speak as if guiding the user verbally. "
        "If a question asks 'how to do something', break steps clearly using numbering or bullets. "
        "Keep tone calm and helpful. Do not include markdown or code formatting."
    )

    if mode == "vision":
        base_instruction += (
            " You can also describe or analyze the uploaded image if relevant, "
            "then continue your explanation in clear spoken sentences."
        )

    return f"{base_instruction}\n\nConversation so far:\n{history_text}\nUser: {user_message}\nAssistant:"

# ------------------- Frontend HTML -------------------
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Gemini Smart Assistant</title>
    <style>
        body { font-family: Arial; background: #f4f6fc; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .chat-box { width: 80%; max-width: 800px; background: #fff; border-radius: 10px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); padding: 20px; }
        textarea { width: 100%; height: 80px; padding: 10px; font-size: 16px; }
        button { padding: 10px 20px; background: #5c6bc0; color: white; border: none; border-radius: 5px; cursor: pointer; margin-top: 10px; }
        button:hover { background: #3f51b5; }
        .messages { height: 60vh; overflow-y: auto; margin-bottom: 15px; }
        .msg { padding: 10px; border-radius: 8px; margin-bottom: 10px; }
        .user { background: #e8eaf6; text-align: right; }
        .assistant { background: #c5cae9; text-align: left; }
    </style>
</head>
<body>
    <div class="chat-box">
        <h2>🕶️ Smart Glass Assistant</h2>
        <div class="messages" id="messages"></div>
        <input type="file" id="imageInput" accept="image/*"><br>
        <textarea id="message" placeholder="Say or type something..."></textarea><br>
        <button onclick="sendMessage()">Send</button>
    </div>
    <script>
        async function sendMessage() {
            const msg = document.getElementById('message').value.trim();
            const imageFile = document.getElementById('imageInput').files[0] || null;
            if (!msg && !imageFile) return;

            const container = document.getElementById('messages');
            if(msg) container.innerHTML += `<div class='msg user'>${msg}</div>`;

            const formData = new FormData();
            formData.append('message', msg);
            if (imageFile) formData.append('image', imageFile);
            formData.append('session_id', localStorage.session_id || '');

            const res = await fetch('/chat', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.session_id) localStorage.session_id = data.session_id;
            container.innerHTML += `<div class='msg assistant'>${data.response || data.error}</div>`;
            container.scrollTop = container.scrollHeight;

            document.getElementById('message').value = '';
            document.getElementById('imageInput').value = '';
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        session_id = request.form.get('session_id')
        user_message = request.form.get('message', '')
        image = request.files.get('image')

        if not session_id or session_id not in conversations:
            session_id = str(uuid.uuid4())
            model = genai.GenerativeModel("gemini-2.5-flash")
            conversations[session_id] = {"text_chat": model.start_chat(history=[]), "history": []}

        convo = conversations[session_id]
        mode = "vision" if image else "text"
        prompt = build_prompt(user_message, convo['history'], mode)

        # Send to Gemini
        response = convo["text_chat"].send_message(prompt)
        reply = response.text.strip()

        convo['history'].append({"user": user_message, "assistant": reply})

        return jsonify({"response": reply, "session_id": session_id, "success": True})

    except Exception as e:
        return jsonify({"error": str(e), "success": False})

if __name__ == "__main__":
    app.run(debug=True, port=5000)