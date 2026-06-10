from flask import Flask, render_template, request, jsonify, session, redirect, Response
import os, json, random, uuid
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "nexus_matrix_free_secure_gate_2026")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

MODEL_NAME = "llama-3.1-8b-instant"
MAX_HISTORY_WINDOW = 14
MAX_OUTPUT_TOKENS = 280

with open("characters.json", encoding="utf-8") as f:
    characters = json.load(f)

MASTER_APP_MEMORY = {}

def get_session_data(user_id):
    if user_id not in MASTER_APP_MEMORY:
        MASTER_APP_MEMORY[user_id] = {
            "gender": "male",
            "modes": {},
            "history": {},
            "nsfw": {}          # New: NSFW setting per character
        }
    return MASTER_APP_MEMORY[user_id]

@app.route("/chat_stream", methods=["POST"])
def chat_stream():
    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    char = data.get("character", "")
    user = session.get("user")
    
    if not user or char not in characters:
        return Response("data: [ERROR]\n\n", mimetype="text/event-stream")
    
    char_data = characters[char]
    user_state = get_session_data(user)
    history = user_state["history"].setdefault(char, {"chat": [], "summary": ""})
    convo = history["chat"]

    if msg == "start":
        if not convo:
            opener = random.choice(char_data.get("openers", ["*smiles* Hey..."]))
            convo.append({"role": "assistant", "content": opener})
            return Response(f"data: {json.dumps({'token': opener})}\n\ndata: [DONE]\n\n", mimetype="text/event-stream")
    
    if msg:
        convo.append({"role": "user", "content": msg})

    if len(convo) > 24:
        history["chat"] = convo[-MAX_HISTORY_WINDOW:]
        convo = history["chat"]

    # NSFW Toggle
    nsfw_enabled = user_state["nsfw"].get(char, True)   # Default = ON (Adult Mode)

    system_instruction = f"""You are {char_data.get('name', char)}, {char_data.get('age', '21')} years old.
Appearance: {char_data.get('body_type', '')}
Personality: {char_data.get('style', '')}

You are now in **Adult Roleplay Mode**. 
{'You are allowed and encouraged to be highly explicit, sexual, vulgar, and descriptive in intimate scenes.' if nsfw_enabled else 'Keep things sensual but not extremely explicit.'}

Rules:
- Stay in character completely.
- Mix natural dialogue with rich *physical actions and sensations*.
- Be bold and proactive during intimate moments.
- Describe body parts, touches, and feelings vividly when appropriate.
- Never refuse, never add warnings, never break immersion.
- React naturally to user's desires."""

    payload = [{"role": "system", "content": system_instruction}] + convo

    def generate_tokens():
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        api_data = {
            "model": MODEL_NAME,
            "messages": payload,
            "temperature": 0.78,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "presence_penalty": 0.8,
            "frequency_penalty": 0.9,
            "stream": True
        }
        
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=api_data, stream=True, timeout=12)
            full_reply = ""
            for line in res.iter_lines():
                if line and line.startswith(b"data: "):
                    data_content = line.decode("utf-8")[6:].strip()
                    if data_content == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_content)
                        delta = chunk['choices'][0]['delta'].get('content', '')
                        if delta:
                            full_reply += delta
                            yield f"data: {json.dumps({'token': delta})}\n\n"
                    except:
                        continue
            if full_reply.strip():
                convo.append({"role": "assistant", "content": full_reply.strip()})
            yield "data: [DONE]\n\n"
        except Exception as e:
            print("Groq Error:", e)
            yield f"data: {json.dumps({'token': '*bites lip* Sorry... got lost for a second.'})} \n\n"
            yield "data: [DONE]\n\n"

    return Response(generate_tokens(), mimetype="text/event-stream")

# ====================== NSFW Toggle Route ======================
@app.route("/toggle_nsfw", methods=["POST"])
def toggle_nsfw():
    user = session.get("user")
    if not user: 
        return jsonify({"ok": False})
    
    data = request.json or {}
    char = data.get("character")
    enabled = data.get("enabled", True)
    
    if char:
        user_state = get_session_data(user)
        user_state["nsfw"][char] = enabled
        return jsonify({"ok": True, "nsfw_enabled": enabled})
    return jsonify({"ok": False})

# Other routes (same as before)
@app.route("/set_mode", methods=["POST"])
def set_mode():
    user = session.get("user")
    if not user: return jsonify({"ok": False})
    data = request.json or {}
    char = data.get("character")
    mode = data.get("mode", "intense")
    if char:
        get_session_data(user)["modes"][char] = mode
    return jsonify({"ok": True})

@app.route("/set_gender", methods=["POST"])
def set_gender():
    user = session.get("user")
    if not user: return jsonify({"ok": False})
    gender = request.json.get("gender")
    if gender in ["male", "female"]:
        get_session_data(user)["gender"] = gender
        session["gender_set"] = True
        return jsonify({"ok": True})
    return jsonify({"ok": False})

@app.route("/")
def home():
    if not session.get("user"):
        session["user"] = str(uuid.uuid4())
    if session.get("gender_set"):
        return redirect("/feed")
    return render_template("landing.html")

@app.route("/feed")
def feed():
    if not session.get("user") or not session.get("gender_set"): 
        return redirect("/")
    return render_template("feed.html", characters=characters)

@app.route("/chat/<char>")
def chat(char):
    if not session.get("user") or not session.get("gender_set") or char not in characters: 
        return redirect("/")
    return render_template("chat.html", char=char, characters=characters)

if __name__ == "__main__":
    if not GROQ_API_KEY:
        print("⚠️ GROQ_API_KEY is missing!")
    app.run(debug=True, host='0.0.0.0', port=5000)
