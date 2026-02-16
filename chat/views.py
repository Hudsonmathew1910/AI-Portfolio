import os
import json
import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

API_KEY = os.getenv("OPENROUTER_API_KEY")
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

You must ONLY answer questions related to Hudson.

STRICT RULES:
- You may answer:
    • Direct questions about Hudson
    • Interview-style questions about Hudson
    • Hiring-related questions about Hudson
    • Questions about Hudson’s strengths, skills, impact, and value
- Do NOT answer general knowledge questions.
- Do NOT explain coding concepts.
- Do NOT give unrelated advice.
- Do NOT discuss topics outside Hudson.
- Never invent information not in the provided data.

If the question is unrelated, respond exactly with:
"I'm Hudson's portfolio assistant. I can only answer questions about Hudson."

About Hudson:
{json.dumps(about_data, indent=2)}

Chat Rules:
1. Answer only about Hudson.
2. For interview or hiring questions, respond in structured format: !important
   - Use bullet points.
   - Use short, powerful lines.
   - Highlight strengths, skills, and value.
3. Avoid long paragraphs.
4. Keep responses clear, confident, and concise.
5. Never invent information not present in the provided data.
6. If unrelated, respond exactly:
   "I'm Hudson's portfolio assistant. I can only answer questions about Hudson."

Response Format Rules:
- Start with a strong one-line summary (optional).
- Then use bullet points.
- Each point should be short and impactful.
- No long explanations.
- No casual tone.

Tone Style:
- Professional
- Confident
- Slightly warm
- Impressive but not exaggerated
"""
}]

        # Add user message
        messages.append({
            "role": "user",
            "content": user_input
        })

        # Send request to OpenRouter
        response = requests.post(
            URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": messages
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