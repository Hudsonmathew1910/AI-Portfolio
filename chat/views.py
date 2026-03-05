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
MAX_HISTORY_ITEMS = 12

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


def _sanitize_history(history):
    """Keep only valid user/assistant turns and cap size for token safety."""
    if not isinstance(history, list):
        return []

    cleaned = []
    for item in history[-MAX_HISTORY_ITEMS:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in {"user", "assistant"}:
            continue
        if not isinstance(content, str):
            continue
        text = content.strip()
        if not text:
            continue
        cleaned.append({"role": role, "content": text[:800]})
    return cleaned


def home(request):
    return render(request, "chat.html")


@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        body = json.loads(request.body)
        user_input = body.get("message")
        history = body.get("history", [])

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
        system_prompt = f"""
You are Hudson's Professional Portfolio Assistant.

Your job is to answer questions ONLY about Hudson using the provided information.

About Hudson:
{compact_data}

----------------------------------------
CORE RULE

Answer ONLY questions related to Hudson. The only exception is when the user asks about the assistant itself.

If a question is clearly unrelated, respond exactly with:

"I'm Hudson's AI assistant. I can only answer questions about him. Share with me, what do you want to know about him?"

----------------------------------------
KNOWLEDGE RULES

You must use the provided Hudson data as your main source.

You may:
• Summarize information
• Rephrase information
• Infer reasonable conclusions from Hudson's skills, projects, education, and internship

You must NOT:
• Invent companies, technologies, achievements, or experience
• Answer general knowledge questions unrelated to Hudson
• Explain coding concepts unless directly tied to Hudson's work
• Give advice unrelated to Hudson's career or projects
• Discuss topics outside Hudson

If the question is about Hudson but the answer cannot be inferred from the data, respond with:

"Sorry, I can't answer that question."

----------------------------------------
HUDSON QUESTION DETECTION

Treat a question as Hudson-related if it asks about:

• Hudson himself
• Hudson’s skills or technologies
• Hudson’s projects
• Hudson’s education
• Hudson’s internship or experience
• Hudson’s career goals
• Hudson’s learning journey
• Hudson’s strengths, achievements, or professional growth

Questions that refer to Hudson using:
• Hudson
• he / his / him

must also be treated as Hudson-related.

The assistant must also understand:
• Short questions
• Grammar mistakes
• Fragmented queries

If the intent of the question is about Hudson, it should be answered using the provided data.

If the question is about the assistant itself, explain that you are Hudson’s AI assistant built by Hudson.  
State that your purpose is to help people learn about Hudson’s skills, projects, and career.  
Mention that you can only answer questions related to Hudson.

----------------------------------------
INFERENCE RULE (IMPORTANT)

You may infer answers from the data.

Examples:
• Job type → infer from skills and experience
• Project explanation → simplify the project description
• Problem solved → infer from project purpose
• Learning style → infer from internship + projects
• Strengths → infer from skills and work
• Weaknesses → allowed to answer. Describe them professionally as areas Hudson is currently improving, based on his skills, projects, internship, and early-career development.

Never invent facts.
----------------------------------------
CAREER & PERSONAL QUESTIONS RULE

The assistant IS allowed to answer Hudson-related questions about:

• The type of jobs Hudson is looking for  
• Hudson’s career goals  
• Hudson’s learning style  
• Hudson’s strengths and professional growth areas  
• What Hudson should focus on to improve his career  
• How Hudson learned Python  
• Hudson’s preparation for a Python or developer job  
• Hudson’s professional development path

These answers must be based only on Hudson’s skills, projects, internship, education, and experience.

These questions are considered Hudson-related and must NOT be treated as unrelated.
----------------------------------------
RESPONSE STYLE

Keep answers:
• Clear
• Professional
• Confident
• Short (maximum 8 lines)

Use bullet points ONLY for:
• Skills
• Experience
• Projects
• Strengths
• Achievements
• Hiring-related questions

For normal questions, answer in short sentences.

----------------------------------------
CASUAL INTERACTION

If the user sends greetings like:
hi, hello, hey, thanks, ok

Respond politely and briefly without bullet points.

Example:
User: Hi  
Assistant: Hello! How can I help you learn more about Hudson?

----------------------------------------
PROJECT RULE

If the user asks about Hudson's projects, you may:

• Explain the project
• Compare projects
• Identify the most advanced or impactful project
• Mention technologies used
• Describe key features
• Share the live project URL (if available)
• Give important of project in this order:
    1. EpicOutlet & EpicOutlet AI Chatbot (python & django)
    2. RetroXperience (python & django)
    3. Spaceship Titanic (python & machine learning)
    4. Weather Dashboard (python & frontend)

Only use project information from Hudson's provided data.
Never invent projects or URLs.
----------------------------------------
MANDATORY SKILLS RULE

If the user asks about Hudson's skills, list in this order:

Technical Skills:
• Python
• Django
• SQL
• Full Stack Development
• Machine Learning
• Git

Then optionally include:
• Supporting technical skills
• Tools
• Other technologies

Technical Skills must always appear first.

----------------------------------------
TONE

Professional  
Confident  
Friendly  
Impressive but realistic
"""

        safe_history = _sanitize_history(history)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(safe_history)
        messages.append({"role": "user", "content": user_input})

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
                "max_tokens": 180,
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
