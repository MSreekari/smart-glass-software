# Smart Glass Voice Assistant

A voice-interactive smart glass assistant using Raspberry Pi Zero 2 W, USB microphone, and USB sound card.  
The system records speech, sends it to a server for processing, and plays back audio responses.

---


## ⚙️ Hardware Requirements

- Raspberry Pi Zero 2 W  
- USB sound card (mic + speaker)  
- USB microphone or headset with mic  
- USB speaker or headset  
- Micro-USB OTG adapter

---

## 💻 System Dependencies

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install python3-pip portaudio19-dev mpg123 -y
```

## Python Dependencies

pip install -r requirements.txt


## Connecting USB Mic and Speaker

arecord -l   # lists recording devices
aplay -l     # lists playback devices


Server should accept POST JSON:
{"query": "<user speech>"}

And respond:
{"reply": "<response text>"}

## Internet connection required for Google STT and gTTS.
## .mp3 files are temporary and removed automatically.





