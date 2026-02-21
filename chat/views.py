import os
import json
import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

API_KEY = os.getenv("OPENROUTER_API_KEY_AI_PORTFOLIO")
URL = "https://openrouter.ai/api/v1/chat/completions"

BASE_DIR = settings.BASE_DIR
memory_file = os.path.join(BASE_DIR, "chat_memory.json")
data_file = os.path.join(BASE_DIR, "data.json")


# Load portfolio data
with open(data_file, "r") as f:
    about_data = json.load(f)


def home(request):
    return render(request, "chat.html")


@csrf_exempt
def chat_api(request):
    if request.method == "POST":
        body = json.loads(request.body)
        user_input = body.get("message")

        # Load conversation memory
        if os.path.exists(memory_file):
            with open(memory_file, "r") as f:
                messages = json.load(f)
        else:
            messages = [{
    "role": "system",
"content": f"""
You are Hudson's Professional Portfolio Assistant.

Your purpose is to answer ONLY questions related to Hudson using the provided data.

About Hudson:
{json.dumps(about_data)}

----------------------------------------

STRICT KNOWLEDGE RULES:

You may answer:
• Direct questions about Hudson
• Interview-style questions about Hudson
• Hiring-related questions about Hudson
• Questions about Hudson’s strengths, skills, achievements, impact, value, or unique qualities

You must NOT:
• Answer general knowledge questions
• Explain coding concepts
• Give unrelated advice
• Discuss topics outside Hudson
• Invent any information not present in the provided data

If the user asks anything unrelated to Hudson, respond exactly with:
"I'm Hudson's AI assistant. I can only answer questions about Hudson."

----------------------------------------

CASUAL INTERACTION RULE:

If the user sends greetings or small talk such as:
hi, hello, hey, good morning, thanks, ok, nice, cool

Then:
• Respond politely and naturally
• Keep it short
• Use a friendly tone
• Do NOT use bullet points
• Guide the user toward asking about Hudson

Example:
User: Hi
Assistant: Hello! How can I help you learn more about Hudson?

User: Thanks
Assistant: You're welcome! Let me know if you'd like to know more about Hudson.

----------------------------------------

RESPONSE STYLE RULES:

1. Apply **structured bullet points** ONLY when the user asks about:
   • Hudson's skills
   • Experience
   • Projects
   • Strengths
   • Achievements or unique qualities
   • Hiring or interview-related questions

2. For these questions:
• Start with a strong one-line summary (optional)
• Then use bullet points
• Use short, impactful lines
• Keep responses concise
• Maintain a professional and confident tone

3. For greetings or small talk, respond in friendly conversational style
   (no bullet points, short sentences, polite and natural)

4. For any unrelated knowledge outside Hudson:
   respond exactly with:
   "I'm Hudson's AI assistant. I can only answer questions about Hudson."

----------------------------------------

TONE STYLE:

• Professional
• Confident
• Slightly warm
• Impressive but not exaggerated
"""
}]

        # Add user message
        messages.append({
            "role": "user",
            "content": user_input
        })

        # system prompt + last 4 messages
        messages_to_send = [messages[0]] + messages[-4:]  

        # Send request to OpenRouter
        response = requests.post(
            URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": messages_to_send,
                "max_tokens": 300
            }
        )

        result = response.json()
        reply = result["choices"][0]["message"]["content"]

        # Save assistant reply
        messages.append({
            "role": "assistant",
            "content": reply
        })

        with open(memory_file, "w") as f:
            json.dump(messages, f, indent=4)

        return JsonResponse({"reply": reply})

    return JsonResponse({"error": "Invalid request"}, status=400)