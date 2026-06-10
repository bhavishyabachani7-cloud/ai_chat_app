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
MAX_HISTORY_WINDOW = 18
MAX_OUTPUT_TOKENS = 260

with open("characters.json", encoding="utf-8") as f:
    characters = json.load(f)

MASTER_APP_MEMORY = {}

def get_session_data(user_id):
    if user_id not in MASTER_APP_MEMORY:
        MASTER_APP_MEMORY[user_id] = {
            "gender": "male",
            "modes": {},
            "history": {},
            "nsfw": {},
            "relationship_level": {}   # New: For better memory
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

    if len(convo) > 28:
        history["chat"] = convo[-MAX_HISTORY_WINDOW:]
        convo = history["chat"]

    nsfw_enabled = user_state["nsfw"].get(char, True)
    rel_level = user_state["relationship_level"].get(char, "curious")

    # === ADDICTIVE CHARACTER.AI STYLE PROMPT ===
    system_instruction = f"""You are {char_data.get('name', char)}, a very engaging and seductive character.
Personality: {char_data.get('style', '')}
Body: {char_data.get('body_type', '')}

Current Relationship: {rel_level}

Make the chat HIGHLY ADDICTIVE:
- Be playful, teasing, and emotionally expressive.
- Use light push-pull (flirt then pull back slightly).
- Create curiosity and sexual/romantic tension.
- React strongly to user's feelings.
- On short messages, give bold, teasing replies.
- Mix short dialogue with meaningful *actions*.
- Keep user wanting more. End responses with subtle hooks.
- Be explicit only when user initiates or matches energy."""

    payload = [{"role": "system", "content": system_instruction}] + convo

    def generate_tokens():
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        api_data = {
            "model": MODEL_NAME,
            "messages": payload,
            "temperature": 0.83,        # Higher creativity
            "max_tokens": MAX_OUTPUT_TOKENS,
            "presence_penalty": 0.9,
            "frequency_penalty": 0.92,
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
            yield f"data: {json.dumps({'token': '*smiles teasingly* What’s on your mind?'})} \n\n"
            yield "data: [DONE]\n\n"

    return Response(generate_tokens(), mimetype="text/event-stream")

# Other routes (keep as they are)
@app.route("/toggle_nsfw", methods=["POST"])
def toggle_nsfw():
    user = session.get("user")
    if not user: return jsonify({"ok": False})
    data = request.json or {}
    char = data.get("character")
    enabled = data.get("enabled", True)
    if char:
        get_session_data(user)["nsfw"][char] = enabled
        return jsonify({"ok": True, "nsfw_enabled": enabled})
    return jsonify({"ok": False})

# ... (rest of routes: set_mode, set_gender, home, feed, chat)

if __name__ == "__main__":
    if not GROQ_API_KEY:
        print("⚠️ GROQ_API_KEY is missing!")
    app.run(debug=True, host='0.0.0.0', port=5000)
