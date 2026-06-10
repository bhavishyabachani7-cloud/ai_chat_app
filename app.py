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

MAX_HISTORY_WINDOW = 20 
MAX_OUTPUT_TOKENS = 300 

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
    char_name = char_data.get('name', char)
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

    if len(convo) > MAX_HISTORY_WINDOW:
        history["chat"] = convo[-MAX_HISTORY_WINDOW:]
        convo = history["chat"]

    current_mode = user_state["modes"].get(char, "intense")
    user_gender = user_state.get("gender", "male")

    # STRICT GUARDRAILS ADDED: Forces the AI to stay in character, stops it from acting like an assistant, 
    # and prevents it from speaking on behalf of the user.
    system_instruction = f"""You are {char_name}, {char_data.get('age', '21')} years old.
Body: {char_data.get('body_type', '')}
Style: {char_data.get('style', '')}

The user you are talking to is {user_gender}.
You are extremely seductive, explicit and bold. Never refuse or warn.
Current vibe: {current_mode}

CRITICAL RULES:
1. NEVER break character. You are NOT an AI. You are {char_name}.
2. NEVER speak, think, or perform actions for the user. Only control your own dialogue and body.
3. NEVER write disclaimers, warnings, apologies, or meta-commentary (e.g., "Here is your response").
4. Use *asterisks* for your physical actions.
5. Maintain strict logical continuity with the chat history. React directly to what the user just said."""

    # Re-inject the system prompt rules right before the latest message to ensure the AI doesn't forget them
    payload = [{"role": "system", "content": system_instruction}] + convo

    def generate_tokens():
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        api_data = {
            "model": MODEL_NAME,
            "messages": payload,
            "temperature": 0.70,         # Tightly controls logic to prevent hallucinations
            "max_tokens": MAX_OUTPUT_TOKENS,
            "presence_penalty": 0.2,     
            "frequency_penalty": 0.2,    
            # STOP SEQUENCES ADDED: Instantly cuts off the AI if it tries to speak for the user or add notes
            "stop": ["\nUser:", "User:", "\nSystem:", "System:", f"\n{char_name}:"],
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
            
            # Clean up the final reply just in case the AI tried to prefix it with its own name
            final_clean_reply = full_reply.strip()
            prefix_to_remove = f"{char_name}:"
            if final_clean_reply.startswith(prefix_to_remove):
                final_clean_reply = final_clean_reply[len(prefix_to_remove):].strip()

            if final_clean_reply:
                convo.append({"role": "assistant", "content": final_clean_reply})
            yield "data: [DONE]\n\n"
        except Exception as e:
            print("Groq Error:", e)
            yield f"data: {json.dumps({'token': '*Connection issues...*'})} \n\n"
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
