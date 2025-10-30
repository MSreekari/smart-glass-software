import os
import io
import base64
from flask import Flask, request, render_template_string, send_file
from PIL import Image, ImageDraw
import google.generativeai as genai
import json

# Configure Gemini API
genai.configure(api_key="AIzaSyAbUKgJFbQHKM1O_4x7jm_kWy-b_a3wrNw")

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
  <head><title>Image Marker</title></head>
  <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
    <h2>Upload Image to Locate a Point</h2>
    <form action="/process" method="post" enctype="multipart/form-data">
      <input type="file" name="image" accept="image/*" required><br><br>
      <input type="text" name="instruction" placeholder="Enter what to mark..." required><br><br>
      <input type="submit" value="Upload & Process">
    </form>
  </body>
</html>
"""

def locate_region_with_gemini(image_path, instruction):
    """Ask Gemini to find where to mark on the image."""
    model = genai.TextModel("gemini-1.5")  # Use TextModel for now

    with open(image_path, "rb") as f:
        img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    # Craft a clear prompt for coordinates
    prompt = (
        f"Here is an image in base64: {img_b64}\n"
        f"Locate the point where the user should {instruction}. "
        "Return only coordinates as JSON, e.g. {\"x\":120,\"y\":300}."
    )

    response = model.generate_text(prompt)
    text = response.text.strip()
    print("Gemini raw response:", text)

    try:
        coords = json.loads(text)
        return coords
    except:
        return {"x": 100, "y": 100}  # fallback

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/process", methods=["POST"])
def process():
    file = request.files["image"]
    instruction = request.form["instruction"]

    if not file:
        return "No file uploaded", 400

    os.makedirs("uploads", exist_ok=True)
    img_path = os.path.join("uploads", file.filename)
    file.save(img_path)

    coords = locate_region_with_gemini(img_path, instruction)

    # Draw circle on image
    image = Image.open(img_path)
    draw = ImageDraw.Draw(image)
    x, y = coords.get("x", 100), coords.get("y", 100)
    r = 15
    draw.ellipse((x - r, y - r, x + r, y + r), outline="red", width=4)

    # Save output
    output_path = os.path.join("uploads", "output.jpg")
    image.save(output_path)

    return send_file(output_path, mimetype="image/jpeg")

if __name__ == "__main__":
    app.run(debug=True)