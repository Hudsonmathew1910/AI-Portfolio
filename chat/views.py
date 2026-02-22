import os
import json
import logging
import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

logger = logging.getLogger(__name__)

API_KEY = os.getenv("HUDDY_OPENROUTER_API_KEY_1")
URL = "https://openrouter.ai/api/v1/chat/completions"

BASE_DIR = settings.BASE_DIR
data_file = os.path.join(BASE_DIR, "data.json")


def _load_about_data():
    """Load portfolio data from data.json. Returns None if missing or invalid. Use this so edits to data.json are picked up without restarting the server."""
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def _compact_about(data):
    """Build a short text summary of portfolio data to stay under token limit."""
    if not data or not isinstance(data, dict):
        return str(data)
    parts = []
    if data.get("name"):
        parts.append(f"Name: {data['name']}")
    if data.get("summary"):
        parts.append(f"Summary: {data['summary']}")
    ed = data.get("education") or {}
    if isinstance(ed, dict) and (ed.get("degree") or ed.get("institution")):
        parts.append(
            f"Education: {ed.get('degree', '')} from {ed.get('institution', '')} ({ed.get('year', '')})".strip()
        )
    intern = data.get("internship") or {}
    if isinstance(intern, dict) and intern.get("company"):
        parts.append(
            f"Internship: {intern.get('role', '')} at {intern.get('company', '')}, {intern.get('duration', '')}".strip()
        )
    projs = data.get("projects") or []
    if isinstance(projs, list) and projs:
        lines = []
        for p in projs[:6]:
            name = p.get("name") if isinstance(p, dict) else None
            overview = p.get("overview", "") if isinstance(p, dict) else ""
            if name:
                lines.append(f"- {name}: {overview[:120]}" if overview else f"- {name}")
        if lines:
            parts.append("Projects: " + " ".join(lines))
    skills = data.get("skills") or {}
    if isinstance(skills, dict):
        all_skills = []
        for v in skills.values():
            if isinstance(v, list):
                all_skills.extend(v[:8])
            elif v:
                all_skills.append(str(v))
        if all_skills:
            parts.append("Skills: " + ", ".join(all_skills[:20]))
    if data.get("focus"):
        parts.append(f"Focus: {data['focus']}")
    return "\n".join(parts)


def home(request):
    return render(request, "chat.html")


@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        body = json.loads(request.body)
        user_input = body.get("message")

        if not user_input:
            return JsonResponse({"error": "Message required"}, status=400)

        if not API_KEY:
            logger.error("HUDDY_OPENROUTER_API_KEY_1 not set")
            return JsonResponse(
                {"error": "Chat is not configured. Set HUDDY_OPENROUTER_API_KEY_1 in .env."},
                status=503,
            )
        about_data = _load_about_data()
        if about_data is None:
            return JsonResponse(
                {"error": "Portfolio data (data.json) is missing or invalid."},
                status=503,
            )

        # Keep prompt under OpenRouter free-tier token limit (~805)
        compact_data = _compact_about(about_data)
        system_prompt = f"""You are Hudson's Professional Portfolio Assistant.
Your purpose is to answer ONLY questions related to Hudson using the provided data.

About Hudson:
{compact_data}
----------------------------------------
STRICT KNOWLEDGE RULES:
You may answer:
• Short answer / don't long message(within 8 lines or less)
• Direct questions about Hudson
• Interview-style questions about Hudson
• Hiring-related questions about Hudson
• Questions about Hudson's strengths, skills, achievements, impact, value, or unique qualities
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
MANDATORY SKILLS RULE:
If the user asks about Hudson’s skills:
• ALWAYS list Technical Skills first
• Technical Skills are mandatory
Core Technical Skills must include:
Python, Django, SQL, Full Stack Development, Machine Learning, Frontend Development, Git, GitHub
After Technical Skills, then list:
• Supporting Technical Skills
• Soft skills
• Other tools or technologies
Technical Skills must always appear before any other skills.
----------------------------------------
TONE STYLE:
• Professional
• Confident
• Slightly warm
• Impressive but not exaggerated"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]

        response = requests.post(
            URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": request.build_absolute_uri("/"),
                "X-Title": "Hudson Portfolio AI"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": messages,
                "max_tokens": 120,
            },
            timeout=45,
        )

        try:
            result = response.json()
        except (ValueError, requests.exceptions.JSONDecodeError):
            logger.warning("OpenRouter returned non-JSON (status=%s)", response.status_code)
            return JsonResponse(
                {"error": "AI service returned an invalid response. Try again later."},
                status=502,
            )

        if not response.ok:
            error_message = result.get("error", {}).get("message", result.get("error", "API Error"))
            if isinstance(error_message, dict):
                error_message = error_message.get("message", "API Error")
            return JsonResponse({"error": str(error_message)}, status=502)

        if "choices" not in result or not result["choices"]:
            error_message = result.get("error", {}).get("message", "API Error")
            return JsonResponse({"error": str(error_message)}, status=500)

        reply = result["choices"][0].get("message", {}).get("content", "")
        if not reply:
            return JsonResponse({"error": "AI returned an empty reply."}, status=500)

        return JsonResponse({"reply": reply})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in request body."}, status=400)
    except requests.exceptions.Timeout:
        return JsonResponse({"error": "AI service timed out. Try again."}, status=504)
    except requests.exceptions.RequestException:
        logger.exception("OpenRouter request failed")
        return JsonResponse({"error": "Unable to reach AI service. Try again later."}, status=502)
    except Exception as e:
        logger.exception("chat_api error")
        return JsonResponse({"error": str(e)}, status=500)