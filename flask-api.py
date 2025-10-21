from flask import Flask, request, jsonify, render_template_string
import google.generativeai as genai
import os
from PIL import Image
import io

app = Flask(__name__)

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyAbUKgJFbQHKM1O_4x7jm_kWy-b_a3wrNw"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize models
text_model = genai.GenerativeModel('gemini-2.5-flash')
vision_model = genai.GenerativeModel('gemini-2.5-flash-lite')

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Gemini API Chat with Vision</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
        .input-section {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            resize: vertical;
            box-sizing: border-box;
            transition: border-color 0.3s;
        }
        textarea:focus {
            outline: none;
            border-color: #4285f4;
        }
        .file-input-wrapper {
            position: relative;
            display: inline-block;
            width: 100%;
        }
        input[type="file"] {
            display: none;
        }
        .file-input-label {
            display: block;
            padding: 15px;
            background-color: #f8f9fa;
            border: 2px dashed #ddd;
            border-radius: 5px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .file-input-label:hover {
            background-color: #e9ecef;
            border-color: #4285f4;
        }
        .file-input-label.has-file {
            background-color: #e3f2fd;
            border-color: #4285f4;
            border-style: solid;
        }
        .image-preview {
            margin-top: 15px;
            text-align: center;
            display: none;
        }
        .image-preview img {
            max-width: 100%;
            max-height: 300px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .remove-image {
            display: inline-block;
            margin-top: 10px;
            padding: 8px 16px;
            background-color: #f44336;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .remove-image:hover {
            background-color: #d32f2f;
        }
        button.send-btn {
            background-color: #4285f4;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
            transition: background-color 0.3s;
        }
        button.send-btn:hover {
            background-color: #357ae8;
        }
        button.send-btn:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        #response {
            margin-top: 30px;
            padding: 20px;
            background-color: #f9f9f9;
            border-left: 4px solid #4285f4;
            border-radius: 5px;
            white-space: pre-wrap;
            display: none;
            line-height: 1.6;
        }
        .loading {
            text-align: center;
            color: #666;
            margin: 20px 0;
            display: none;
        }
        .loading::after {
            content: '...';
            animation: dots 1.5s steps(4, end) infinite;
        }
        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }
        .info-box {
            background-color: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #2196f3;
        }
        .info-box p {
            margin: 5px 0;
            color: #1976d2;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Gemini API Chat</h1>
        <p class="subtitle">Ask questions with or without images</p>
        
        <div class="info-box">
            <p>💡 <strong>Tip:</strong> Upload an image to ask questions about it, or just type a text prompt!</p>
            <p>📷 Supported formats: JPG, PNG, GIF, WebP</p>
        </div>

        <div class="input-section">
            <label for="imageInput">Upload Image (Optional)</label>
            <div class="file-input-wrapper">
                <input type="file" id="imageInput" accept="image/*" onchange="handleFileSelect(event)">
                <label for="imageInput" class="file-input-label" id="fileLabel">
                    📁 Click to select an image or drag and drop
                </label>
            </div>
            <div class="image-preview" id="imagePreview">
                <img id="previewImg" src="" alt="Preview">
                <br>
                <button class="remove-image" onclick="removeImage()">Remove Image</button>
            </div>
        </div>

        <div class="input-section">
            <label for="prompt">Your Message</label>
            <textarea id="prompt" rows="6" placeholder="Enter your prompt here... (e.g., 'What's in this image?' or any question)"></textarea>
        </div>

        <button class="send-btn" onclick="sendPrompt()">Send</button>
        <div class="loading" id="loading">Processing</div>
        <div id="response"></div>
    </div>

    <script>
        let selectedFile = null;

        function handleFileSelect(event) {
            const file = event.target.files[0];
            if (file) {
                selectedFile = file;
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('previewImg').src = e.target.result;
                    document.getElementById('imagePreview').style.display = 'block';
                    document.getElementById('fileLabel').classList.add('has-file');
                    document.getElementById('fileLabel').innerHTML = '✓ Image selected: ' + file.name;
                };
                reader.readAsDataURL(file);
            }
        }

        function removeImage() {
            selectedFile = null;
            document.getElementById('imageInput').value = '';
            document.getElementById('imagePreview').style.display = 'none';
            document.getElementById('fileLabel').classList.remove('has-file');
            document.getElementById('fileLabel').innerHTML = '📁 Click to select an image or drag and drop';
        }

        async function sendPrompt() {
            const prompt = document.getElementById('prompt').value;
            const responseDiv = document.getElementById('response');
            const loading = document.getElementById('loading');
            const button = document.querySelector('.send-btn');

            if (!prompt.trim()) {
                alert('Please enter a prompt');
                return;
            }

            button.disabled = true;
            loading.style.display = 'block';
            responseDiv.style.display = 'none';

            try {
                const formData = new FormData();
                formData.append('prompt', prompt);
                
                if (selectedFile) {
                    formData.append('image', selectedFile);
                }

                const response = await fetch('/generate', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.error) {
                    responseDiv.textContent = 'Error: ' + data.error;
                    responseDiv.style.borderLeftColor = '#f44336';
                } else {
                    responseDiv.textContent = data.response;
                    responseDiv.style.borderLeftColor = '#4285f4';
                }

                responseDiv.style.display = 'block';
            } catch (error) {
                responseDiv.textContent = 'Error: ' + error.message;
                responseDiv.style.borderLeftColor = '#f44336';
                responseDiv.style.display = 'block';
            } finally {
                loading.style.display = 'none';
                button.disabled = false;
            }
        }

        // Allow Enter + Shift to send
        document.getElementById('prompt').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && e.shiftKey) {
                e.preventDefault();
                sendPrompt();
            }
        });

        // Drag and drop functionality
        const fileLabel = document.getElementById('fileLabel');
        
        fileLabel.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileLabel.style.backgroundColor = '#e3f2fd';
        });
        
        fileLabel.addEventListener('dragleave', () => {
            fileLabel.style.backgroundColor = '#f8f9fa';
        });
        
        fileLabel.addEventListener('drop', (e) => {
            e.preventDefault();
            fileLabel.style.backgroundColor = '#f8f9fa';
            
            const files = e.dataTransfer.files;
            if (files.length > 0 && files[0].type.startsWith('image/')) {
                document.getElementById('imageInput').files = files;
                handleFileSelect({ target: { files: files } });
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        prompt = request.form.get('prompt', '')
        
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400
        
        # Check if an image was uploaded
        if 'image' in request.files and request.files['image'].filename != '':
            image_file = request.files['image']
            
            # Read and process the image
            img = Image.open(io.BytesIO(image_file.read()))
            
            # Generate response with vision model
            response = vision_model.generate_content([prompt, img])
        else:
            # Generate response with text-only model
            response = text_model.generate_content(prompt)
        
        return jsonify({
            'response': response.text,
            'success': True
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Alternative endpoint for chat-style conversations"""
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        
        if not messages:
            return jsonify({'error': 'No messages provided'}), 400
        
        # Start a chat session
        chat = text_model.start_chat(history=[])
        
        # Send the last message
        response = chat.send_message(messages[-1])
        
        return jsonify({
            'response': response.text,
            'success': True
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)