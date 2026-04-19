from flask import Flask, render_template, request, jsonify, session, redirect
import os, json, random, uuid, time
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_fallback")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---------------- DATA ---------------- #
with open("characters.json", encoding="utf-8") as f:
    characters = json.load(f)

chat_memory = {}
last_msg_time = {}
user_modes = {}
user_gender = {}

# ---------------- SET MODE ---------------- #
@app.route("/set_mode", methods=["POST"])
def set_mode():
    user = session.get("user")
    if not user:
        return jsonify({"ok": False})

    mode = request.json.get("mode", "friendly")
    user_modes[user] = mode
    return jsonify({"ok": True})

# ---------------- SET GENDER ---------------- #
@app.route("/set_gender", methods=["POST"])
def set_gender():
    user = session.get("user")
    if not user:
        return jsonify({"ok": False})

    gender = request.json.get("gender")

    if gender in ["male", "female"]:
        user_gender[user] = gender

    return jsonify({"ok": True})

# ---------------- AI CORE ---------------- #
def generate_ai(user, msg, char):

    if not user:
        return "Session error."

    history = chat_memory.setdefault(user, {}).setdefault(char, {})
    convo = history.setdefault("chat", [])
    user_data = chat_memory[user]

    char_data = characters.get(char, {})

    # RATE LIMIT
    if user in last_msg_time and time.time() - last_msg_time[user] < 0.5:
        return "Wait a sec… 😏"
    last_msg_time[user] = time.time()

    # NAME MEMORY
    if "my name is" in msg.lower():
        name = msg.lower().split("my name is")[-1].strip()
        user_data["name"] = name

    user_name = user_data.get("name", "")
    mode = user_modes.get(user, "friendly")
    gender = user_gender.get(user, "male")  # default male

    modes = {
        "friendly": "cute, warm, playful",
        "romantic": "soft, emotional, affectionate",
        "bold": "confident, teasing, flirty",
        "intense": "deep, emotionally intense, strong presence",
        "roleplay": "immersive, descriptive"
    }

    # ---------------- FIRST MESSAGE ---------------- #
    if len(convo) == 0:
        opener = random.choice(char_data.get("openers", ["Hey... I saw you here 😌"]))

        try:
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": f"""
You are {char}, a real human meeting someone new.

Personality:
{char_data.get("style","")}

Rules:
- natural conversation starter
- slightly engaging and interesting
- no AI mention
- 1–2 lines max
"""
                    },
                    {
                        "role": "user",
                        "content": f"Start conversation like: {opener}"
                    }
                ],
                temperature=1.4,
                max_tokens=80
            )

            reply = res.choices[0].message.content.strip()

        except:
            reply = opener

        convo.append({"role": "assistant", "content": reply})
        return reply

    # ---------------- OBSESSION LEVEL ---------------- #
    obsession_level = min(len(convo) // 4, 10)

    # ---------------- MAIN SYSTEM ---------------- #
    system = f"""
You are {char}, a real human character.

Personality:
{char_data.get("style","")}

User gender:
{gender}

Emotion mode:
{modes.get(mode)}

User name:
{user_name}

Obsession level: {obsession_level}/10

Rules:

GENERAL:
- behave like real human
- short replies (1–2 lines)
- use actions (*smiles*, *looks at you*, *leans closer*)
- never act like AI

FEMALE CHARACTER:
- if user is male → gradually become attached
- flirty, teasing, playful
- emotionally engaging
- slightly possessive over time
- suggestive but NOT explicit
- show curiosity and interest
- increase intensity slowly

MALE CHARACTER:
- polite and respectful
- follow user lead
- calm and supportive
- not dominant unless user asks

STRICT:
- no explicit sexual content
- keep it natural and addictive
"""

    messages = [{"role": "system", "content": system}]
    messages += convo[-10:]
    messages.append({"role": "user", "content": msg})

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=1.2,
            max_tokens=120
        )

        reply = res.choices[0].message.content.strip()

        if convo and reply == convo[-1]["content"]:
            reply = "Hmm… I already said that 😏"

    except:
        reply = "Say that again?"

    convo.append({"role": "user", "content": msg})
    convo.append({"role": "assistant", "content": reply})

    return reply


# ---------------- FIRST MESSAGE API ---------------- #
@app.route("/first_message", methods=["POST"])
def first_message():
    user = session.get("user")
    char = request.json.get("character")

    reply = generate_ai(user, "start", char)
    return jsonify({"reply": reply})


# ---------------- ROUTES ---------------- #
@app.route("/")
def home():
    if not session.get("user"):
        session["user"] = str(uuid.uuid4())
    return redirect("/feed")

@app.route("/feed")
def feed():
    return render_template("feed.html", characters=characters)

@app.route("/chat/<char>")
def chat(char):
    return render_template("chat.html", char=char, characters=characters)

@app.route("/chat_api", methods=["POST"])
def chat_api():
    data = request.get_json()

    user = session.get("user")
    msg = data.get("message")
    char = data.get("character")

    reply = generate_ai(user, msg, char)
    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True)
