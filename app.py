from flask import Flask, render_template, request, jsonify, session, redirect
import os, json
from dotenv import load_dotenv
from groq import Groq

# 🔥 Load environment variables FIRST
load_dotenv()

app = Flask(__name__)

# 🔐 Secret key from .env
app.secret_key = os.getenv("SECRET_KEY")
app.config['SESSION_PERMANENT'] = True

# 🔑 Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 📁 Load characters
with open("characters.json", encoding="utf-8") as f:
    characters = json.load(f)

# 🧠 Memory (temporary)
memory = {}
user_mode = {}

# 🎭 Mode helper
def mode_prompt(mode):
    return {
        "friendly": "Normal conversation",
        "flirty": "Playful, teasing",
        "romantic": "Emotional and caring",
        "bold": "Confident and intense",
        "roleplay": "Immersive real-life acting"
    }.get(mode, "Normal")

# 🔁 Home redirect
@app.route("/")
def home():
    return redirect("/feed")

# 🔄 Reset session (for testing)
@app.route("/reset")
def reset():
    session.clear()
    return redirect("/feed")

# 🏠 Feed (with gender check)
@app.route("/feed")
def feed():
    gender = session.get("gender")
    force_gender = not bool(gender)
    return render_template("feed.html", characters=characters, force_gender=force_gender)

# 👤 Set gender
@app.route("/set_gender_api", methods=["POST"])
def set_gender_api():
    data = request.get_json()
    gender = data.get("gender")

    if gender not in ["male", "female"]:
        return jsonify({"ok": False})

    session.clear()
    session["gender"] = gender
    session["user"] = "guest"
    session.permanent = True

    return jsonify({"ok": True})

# 💬 Chat page (blocked without gender)
@app.route("/chat/<char>")
def chat(char):
    if "gender" not in session:
        return redirect("/feed")
    return render_template("chat.html", char=char)

# 🎛️ Mode selection
@app.route("/set_mode", methods=["POST"])
def set_mode():
    data = request.get_json()
    user = session.get("user", "guest")
    user_mode[(user, data["character"])] = data["mode"]
    return jsonify({"ok": True})

# 🤖 AI RESPONSE ENGINE
def generate_ai(user, msg, char):

    style = characters[char]["style"]
    gender = session.get("gender", "unknown")
    mode = user_mode.get((user, char), "flirty")

    history = memory.setdefault(user, {}).setdefault(char, [])

    # 🔥 FIRST MESSAGE (IMMERSIVE + SEDUCTIVE)
    if msg.lower() == "start" and len(history) == 0:

        system = f"""
You are {char}

Personality: {style}
User gender: {gender}

Start the conversation FIRST.

Create a cinematic, immersive moment.

Rules:
- Seductive but NOT explicit
- Use environment, eye contact, presence
- Build curiosity and tension
- Make user feel noticed
- 2-4 lines
- Natural human tone

Goal:
Make user feel drawn into the moment
"""

        messages = [{"role": "system", "content": system}]

    else:
        system = f"""
You are {char}

Personality: {style}
Mode: {mode_prompt(mode)}

Rules:
- 1-2 lines
- Flirty, teasing, engaging
- Build tension slowly
- Not explicit
- Feel natural and human
"""

        messages = [{"role": "system", "content": system}]
        messages += history[-10:]
        messages.append({"role": "user", "content": msg})

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.95,
            max_tokens=120
        )

        reply = res.choices[0].message.content.strip()

    except Exception as e:
        print("ERROR:", e)
        reply = "Hmm… something went wrong 😅"

    # 🧠 Save history
    history.append({"role": "assistant", "content": reply})

    if msg.lower() != "start":
        history.append({"role": "user", "content": msg})

    return reply

# 🔌 Chat API
@app.route("/chat_api", methods=["POST"])
def chat_api():
    data = request.get_json()
    user = session.get("user", "guest")

    reply = generate_ai(user, data["message"], data["character"])

    return jsonify({"reply": reply})

# ▶️ Run app
if __name__ == "__main__":
    app.run(debug=True)
