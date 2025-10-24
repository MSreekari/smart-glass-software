
# Smart Glasses API Documentation

##  Overview

Smart glasses are used in configuring or repairing electronic devices to improve efficiency, accuracy, and hands-free operation during technical tasks.  
They display schematics, manuals, and step-by-step instructions directly in the user’s field of view, eliminating the need to switch between devices and external screens.  
These glasses also enable real-time remote assistance by streaming live video to experts for immediate guidance.  
With augmented reality overlays, they can highlight critical components or circuits, reducing errors and speeding up troubleshooting.  
They also support automatic documentation through photos or videos for records and training.  
Additionally, smart glasses can integrate with diagnostic tools to show live readings or error codes.  
Overall, they make the repair process faster, safer, and more intelligent by bringing digital assistance directly into the technician’s line of sight.

This API documentation defines the structure and logic for how smart glasses interact with a backend server to generate real-time assistance, images, and guidance through continuous request-response communication.

---

##  API Workflow Summary

The API enables a **continuous conversation loop** between the **user (smart glasses)** and the **server**.

1. The **user** sends a request to the `/generate` endpoint with:
   - A `session_id`
   - A `prompt` (mandatory)
   - Optionally, an `image` (based on use case)

2. The **server** processes the request and responds to the user's IP address with:
   - A generated text or visual instruction
   - The same `session_id`
   - A `response_time` and a `waiting_time`

3. The **server waits** (default 10 seconds) for the user’s next input.  
   If the user says or sends something new, the process repeats.

4. This **interaction loop continues** until the task or conversation is complete.

---

## 🔗 Base URL


## Example Request
{
  "session_id": "abc123",
  "prompt": "Show me how to connect a motherboard",
  "image": "https://example.com/motherboard.jpg"
}

## Example Response
{
  "session_id": "abc123",
  "response_text": "To connect the motherboard, first align it with the screw holes on the cabinet base. Attach the I/O shield, then connect the power supply cables and front panel connectors.",
  "response_time": "2.1s",
  "waiting_time": "10s"
}

## Example Conversation
user (via /generate request)
{
  "session_id": "xyz456",
  "prompt": "How to connect a motherboard?"
}

Server(Response)
{
  "session_id": "xyz456",
  "response_text": "To connect the motherboard, align it with the screw holes and secure it to the cabinet. Connect the main power supply cable and CPU power connector.",
  "response_time": "1.9s",
  "waiting_time": "10s"
}

User (next request, within 10s)
{
  "session_id": "xyz456",
  "prompt": "Where should I connect the fan cable?"
}

Server (response)
{
  "session_id": "xyz456",
  "response_text": "Connect the fan cable to the CPU_FAN header near the processor socket on the motherboard.",
  "response_time": "1.7s",
  "waiting_time": "10s"
}


