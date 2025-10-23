import speech_recognition as sr
from gtts import gTTS
import os
import requests
from playsound import playsound

# ---- CONFIG ----
SERVER_URL = "https://your-server-url/api/respond"  # should replace with server endpoint

def record_and_recognize():
    r = sr.Recognizer()
    with sr.Microphone() as source:  # USB mic gets detected automatically
        print("Say something...")
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio)  # Google STT API (online)
        print("You said:", text)
        return text
    except sr.UnknownValueError:
        print("Sorry, I didn’t catch that.")
        return None
    except sr.RequestError as e:
        print("Speech recognition error: ", e)
        return None

def send_to_server(text):
    # Sends text to backend and get response
    try:
        response = requests.post(SERVER_URL, json={"query": text})
        if response.status_code == 200:
            return response.json().get("reply", "Sorry, no response from server.")
        else:
            return "Server error."
    except:
        return "Server unreachable."

def speak_text(reply_text):
    print("Speaking:", reply_text)
    tts = gTTS(reply_text, lang="en")
    tts.save("reply.mp3")
    playsound("reply.mp3")
    os.remove("reply.mp3")

if __name__ == "__main__":
    print("Smart Glass Assistant Ready 🕶️")
    while True:
        user_text = record_and_recognize()
        if user_text:
            reply = send_to_server(user_text)
            speak_text(reply)
