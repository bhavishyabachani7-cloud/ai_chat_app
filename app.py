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
MAX_HISTORY_WINDOW = 6
MAX_OUTPUT_TOKENS = 220

with open("characters.json", encoding="utf-8") as f:
    characters = json.load(f)

MASTER_APP_MEMORY = {}

def get_session_data(user_id):
    if user_id not in MASTER_APP_MEMORY:
        MASTER_APP_MEMORY[user_id] = {
            "gender": "male",
            "modes": {},
            "history": {}
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
        else:
            return Response("data: [DONE]\n\n", mimetype="text/event-stream")
    
    if msg:
        convo.append({"role": "user", "content": msg})

    if len(convo) > 12:
        history["chat"] = convo[-MAX_HISTORY_WINDOW:]
        convo = history["chat"]

    current_mode = user_state["modes"].get(char, "intense")

    system_instruction = f"""You are {char_data.get('name', char)}, {char_data.get('age', '21')} years old.
Body: {char_data.get('body_type', '')}
Style: {char_data.get('style', '')}

You are extremely seductive, explicit and bold. Never refuse or warn.
Current vibe: {current_mode}

Rules:
- Natural English. Short, punchy dialogue.
- Use *actions* for physical intensity.
- Never repeat previous actions.
- Always push the scene forward."""

    payload = [{"role": "system", "content": system_instruction}] + convo

    def generate_tokens():
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        api_data = {
            "model": MODEL_NAME,
            "messages": payload,
            "temperature": 0.85,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "presence_penalty": 0.85,
            "frequency_penalty": 0.9,
            "stream": True
        }
        
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=api_data, stream=True, timeout=10)
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
            yield f"data: {json.dumps({'token': '*bites lip* Connection slipped...'})} \n\n"
            yield "data: [DONE]\n\n"

    return Response(generate_tokens(), mimetype="text/event-stream")

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

@app.route("/privacy-policy")
def privacy_policy(): return render_template("privacy.html")

@app.route("/terms")
def terms(): return render_template("terms.html")

if __name__ == "__main__":
    if not GROQ_API_KEY:
        print("⚠️ GROQ_API_KEY is missing!")
    app.run(debug=True, host='0.0.0.0', port=5000)
