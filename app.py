from flask import Flask, render_template, request, jsonify, session, redirect
import os, json, random
from dotenv import load_dotenv
from groq import Groq

# ---------------- INIT ---------------- #
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_fallback")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---------------- LOAD CHARACTERS ---------------- #
with open("characters.json", encoding="utf-8") as f:
    characters = json.load(f)

# ---------------- MEMORY ---------------- #
chat_memory = {}

# ---------------- AI FUNCTION ---------------- #
def generate_ai(user, msg, char):

    history = chat_memory.setdefault(user, {}).setdefault(char, [])
    char_data = characters.get(char, {})

    # category mode
    mode = session.get("mode", "friendly")

    modes = {
        "friendly": "cute, warm, light playful",
        "romantic": "soft, emotional, affectionate",
        "bold": "confident, teasing, flirty",
        "intense": "dominant, deep, strong presence",
        "roleplay": "immersive, descriptive, scene-based"
    }

    base_personality = char_data.get("style", "")
    personality = base_personality + ", " + modes.get(mode, "playful")

    # ---------------- FIRST MESSAGE ---------------- #
    if len(history) == 0:
        intro = char_data.get("intro", "")
        first_lines = [
            f"{intro} *smiles softly* So… it’s just us now 😏",
            f"{intro} *leans a little closer* I was hoping you'd come 😌",
            f"{intro} *eyes lock on you* You look interesting… should I be curious? 😏"
        ]

        reply = random.choice(first_lines)
        history.append({"role": "assistant", "content": reply})
        return reply

    # ---------------- SYSTEM PROMPT ---------------- #
    system = f"""
You are {char}

Personality:
{personality}

Rules:
- Flirty, engaging (non-explicit)
- Use actions like (*smiles*, *leans closer*)
- Keep replies short (1-2 lines)
- NEVER repeat same sentence
- Be human-like and teasing 😏
"""

    messages = [{"role": "system", "content": system}]
    messages += history[-6:]
    messages.append({"role": "user", "content": msg})

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=1.0,
            max_tokens=120
        )

        reply = res.choices[0].message.content.strip()

        # anti repeat
        if history and reply == history[-1].get("content"):
            reply = "Hmm… trying to make me repeat? Not happening 😏"

    except Exception as e:
        print("ERROR:", e)
        reply = "Hmm… say that again 😅"

    history.append({"role": "user", "content": msg})
    history.append({"role": "assistant", "content": reply})

    return reply

# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    if not session.get("gender"):
        return render_template("gender.html")
    return redirect("/feed")

@app.route("/set_gender_api", methods=["POST"])
def set_gender():
    data = request.get_json()
    session["gender"] = data.get("gender")
    session["user"] = "guest"
    return jsonify({"ok": True})

@app.route("/set_mode", methods=["POST"])
def set_mode():
    data = request.get_json()
    session["mode"] = data.get("mode", "friendly")
    return jsonify({"ok": True})

@app.route("/feed")
def feed():
    return render_template("feed.html", characters=characters)

@app.route("/chat/<char>")
def chat(char):
    if char not in characters:
        return "Character not found", 404
    return render_template("chat.html", char=char, characters=characters)

@app.route("/chat_api", methods=["POST"])
def chat_api():
    data = request.get_json()

    user = session.get("user", "guest")
    message = data.get("message")
    character = data.get("character")

    if not message or not character:
        return jsonify({"reply": "Something went wrong 😅"})

    reply = generate_ai(user, message, character)
    return jsonify({"reply": reply})

# ---------------- RUN ---------------- #
if __name__ == "__main__":
    app.run(debug=True)
