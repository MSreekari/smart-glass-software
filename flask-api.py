from flask import Flask, request, jsonify, render_template_string, session
import google.generativeai as genai
import os
from PIL import Image
import io
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyAbUKgJFbQHKM1O_4x7jm_kWy-b_a3wrNw"

genai.configure(api_key=GEMINI_API_KEY)

# Store conversation sessions (in production, use a database)
conversations = {}

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Gemini Chat with History</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .chat-container {
            width: 100%;
            max-width: 1000px;
            height: 90vh;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .chat-header h1 {
            font-size: 24px;
            font-weight: 600;
        }
        .clear-btn {
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .clear-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f5f7fa;
        }
        .message {
            margin-bottom: 20px;
            display: flex;
            gap: 12px;
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.user {
            flex-direction: row-reverse;
        }
        .message-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            flex-shrink: 0;
        }
        .message.user .message-avatar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .message.assistant .message-avatar {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 12px;
            line-height: 1.6;
            white-space: pre-wrap;
        }
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .message.assistant .message-content {
            background: white;
            color: #333;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .message-image {
            max-width: 300px;
            border-radius: 8px;
            margin-top: 8px;
            cursor: pointer;
        }
        .chat-input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }
        .image-preview-container {
            display: none;
            margin-bottom: 15px;
            position: relative;
        }
        .image-preview-container img {
            max-width: 150px;
            max-height: 150px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .remove-preview {
            position: absolute;
            top: -8px;
            right: -8px;
            background: #f44336;
            color: white;
            border: none;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            cursor: pointer;
            font-size: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .input-wrapper {
            display: flex;
            gap: 10px;
            align-items: flex-end;
        }
        .file-input-label {
            background: #f5f7fa;
            border: 2px solid #e0e0e0;
            padding: 12px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .file-input-label:hover {
            background: #e3f2fd;
            border-color: #4285f4;
        }
        input[type="file"] {
            display: none;
        }
        textarea {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            resize: none;
            font-family: inherit;
            transition: border-color 0.3s;
        }
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        .send-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: transform 0.2s;
        }
        .send-btn:hover:not(:disabled) {
            transform: translateY(-2px);
        }
        .send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .loading-indicator {
            display: none;
            text-align: center;
            padding: 10px;
            color: #666;
        }
        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 12px 16px;
        }
        .typing-indicator span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #999;
            animation: typing 1.4s infinite;
        }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        .empty-state h2 {
            font-size: 24px;
            margin-bottom: 10px;
        }
        .empty-state p {
            font-size: 16px;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🤖 Gemini Chat</h1>
            <button class="clear-btn" onclick="clearConversation()">🗑️ Clear Chat</button>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="empty-state">
                <h2>👋 Welcome to Gemini Chat!</h2>
                <p>Start a conversation by typing a message below</p>
                <p style="margin-top: 10px; font-size: 14px;">💡 You can also upload images to ask questions about them</p>
            </div>
        </div>
        
        <div class="chat-input-area">
            <div class="image-preview-container" id="imagePreviewContainer">
                <img id="previewImg" src="" alt="Preview">
                <button class="remove-preview" onclick="removeImage()">×</button>
            </div>
            
            <div class="input-wrapper">
                <label for="imageInput" class="file-input-label" title="Upload image">
                    📷
                </label>
                <input type="file" id="imageInput" accept="image/*" onchange="handleFileSelect(event)">
                
                <textarea 
                    id="messageInput" 
                    rows="1" 
                    placeholder="Type your message here..."
                    onkeydown="handleKeyPress(event)"
                ></textarea>
                
                <button class="send-btn" onclick="sendMessage()" id="sendBtn">Send</button>
            </div>
        </div>
    </div>

    <script>
        let selectedFile = null;
        let sessionId = null;

        // Initialize session
        async function initSession() {
            try {
                const response = await fetch('/init-session', { method: 'POST' });
                const data = await response.json();
                sessionId = data.session_id;
            } catch (error) {
                console.error('Error initializing session:', error);
            }
        }

        initSession();

        function handleFileSelect(event) {
            const file = event.target.files[0];
            if (file) {
                selectedFile = file;
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('previewImg').src = e.target.result;
                    document.getElementById('imagePreviewContainer').style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        }

        function removeImage() {
            selectedFile = null;
            document.getElementById('imageInput').value = '';
            document.getElementById('imagePreviewContainer').style.display = 'none';
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        function addMessage(role, content, imageUrl = null) {
            const messagesDiv = document.getElementById('chatMessages');
            
            // Remove empty state if exists
            const emptyState = messagesDiv.querySelector('.empty-state');
            if (emptyState) {
                emptyState.remove();
            }

            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            
            const avatar = role === 'user' ? '👤' : '🤖';
            
            let imageHtml = '';
            if (imageUrl) {
                imageHtml = `<img src="${imageUrl}" class="message-image" alt="Uploaded image">`;
            }
            
            messageDiv.innerHTML = `
                <div class="message-avatar">${avatar}</div>
                <div>
                    ${imageHtml}
                    <div class="message-content">${content}</div>
                </div>
            `;
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function showTypingIndicator() {
            const messagesDiv = document.getElementById('chatMessages');
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message assistant';
            typingDiv.id = 'typingIndicator';
            typingDiv.innerHTML = `
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            `;
            messagesDiv.appendChild(typingDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function removeTypingIndicator() {
            const indicator = document.getElementById('typingIndicator');
            if (indicator) {
                indicator.remove();
            }
        }

        async function sendMessage() {
            const messageInput = document.getElementById('messageInput');
            const message = messageInput.value.trim();
            const sendBtn = document.getElementById('sendBtn');

            if (!message) {
                alert('Please enter a message');
                return;
            }

            sendBtn.disabled = true;

            // Create image URL if image is selected
            let imageUrl = null;
            if (selectedFile) {
                imageUrl = URL.createObjectURL(selectedFile);
            }

            // Add user message
            addMessage('user', message, imageUrl);
            messageInput.value = '';

            // Show typing indicator
            showTypingIndicator();

            try {
                const formData = new FormData();
                formData.append('message', message);
                formData.append('session_id', sessionId);
                
                if (selectedFile) {
                    formData.append('image', selectedFile);
                }

                const response = await fetch('/chat', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                removeTypingIndicator();

                if (data.error) {
                    addMessage('assistant', 'Error: ' + data.error);
                } else {
                    addMessage('assistant', data.response);
                }

                // Clear image after sending
                removeImage();
            } catch (error) {
                removeTypingIndicator();
                addMessage('assistant', 'Error: ' + error.message);
            } finally {
                sendBtn.disabled = false;
                messageInput.focus();
            }
        }

        async function clearConversation() {
            if (confirm('Are you sure you want to clear the conversation?')) {
                try {
                    await fetch('/clear-session', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ session_id: sessionId })
                    });

                    const messagesDiv = document.getElementById('chatMessages');
                    messagesDiv.innerHTML = `
                        <div class="empty-state">
                            <h2>👋 Welcome to Gemini Chat!</h2>
                            <p>Start a conversation by typing a message below</p>
                            <p style="margin-top: 10px; font-size: 14px;">💡 You can also upload images to ask questions about them</p>
                        </div>
                    `;
                    removeImage();
                } catch (error) {
                    console.error('Error clearing session:', error);
                }
            }
        }

        // Auto-resize textarea
        const textarea = document.getElementById('messageInput');
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 150) + 'px';
        });
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/init-session', methods=['POST'])
def init_session():
    """Initialize a new conversation session"""
    session_id = str(uuid.uuid4())
    
    # Initialize both text and vision models with chat
    text_model = genai.GenerativeModel('gemini-2.5-flash')
    vision_model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    conversations[session_id] = {
        'text_chat': text_model.start_chat(history=[]),
        'vision_model': vision_model,
        'history': []
    }
    
    return jsonify({'session_id': session_id})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        message = request.form.get('message', '')
        session_id = request.form.get('session_id', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        if not session_id or session_id not in conversations:
            return jsonify({'error': 'Invalid session'}), 400
        
        conversation = conversations[session_id]
        
        # Check if an image was uploaded
        if 'image' in request.files and request.files['image'].filename != '':
            image_file = request.files['image']
            img = Image.open(io.BytesIO(image_file.read()))
            
            # For vision requests, we need to include context from history
            context = ""
            if conversation['history']:
                context = "Previous conversation:\n"
                for item in conversation['history'][-5:]:  # Last 5 exchanges
                    context += f"User: {item['user']}\nAssistant: {item['assistant']}\n\n"
                context += f"Current question: {message}"
            else:
                context = message
            
            # Generate response with vision model
            response = conversation['vision_model'].generate_content([context, img])
            response_text = response.text
        else:
            # Use the chat session for text-only
            response = conversation['text_chat'].send_message(message)
            response_text = response.text
        
        # Save to history
        conversation['history'].append({
            'user': message,
            'assistant': response_text
        })
        
        return jsonify({
            'response': response_text,
            'success': True
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/clear-session', methods=['POST'])
def clear_session():
    try:
        data = request.get_json()
        session_id = data.get('session_id', '')
        
        if session_id in conversations:
            # Reinitialize the session
            text_model = genai.GenerativeModel('gemini-pro')
            vision_model = genai.GenerativeModel('gemini-pro-vision')
            
            conversations[session_id] = {
                'text_chat': text_model.start_chat(history=[]),
                'vision_model': vision_model,
                'history': []
            }
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)