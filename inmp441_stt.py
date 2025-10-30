import sounddevice as sd
import numpy as np
import wavio
import speech_recognition as sr
import os

# Audio settings
duration = 5          # seconds
samplerate = 16000    # Hz (INMP441 typically works at 16k)
channels = 1          # mono

FILENAME = "recorded_audio.wav"

print("Recording... Speak now!")
recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=channels, dtype='int16')
sd.wait()
print("Recording complete.")

# Save WAV file
wavio.write(FILENAME, recording, samplerate, sampwidth=2)
print(f"Audio saved as {FILENAME}")

# Initialize speech recognizer
recognizer = sr.Recognizer()

# Load the recorded audio
with sr.AudioFile(FILENAME) as source:
    audio_data = recognizer.record(source)

print("Converting speech to text...")

try:
    # Uses Google Speech Recognition API (requires Internet)
    text = recognizer.recognize_google(audio_data)
    print("Recognized Text:")
    print(text)

except sr.UnknownValueError:
    print("Could not understand the audio.")
except sr.RequestError as e:
    print(f"Could not request results; check Internet connection. Error: {e}")