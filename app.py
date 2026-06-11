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
MAX_HISTORY_WINDOW = 10  
MAX_OUTPUT_TOKENS = 120  

with open("characters.json", encoding="utf-8") as f:
    characters = json.load(f)

@app.route("/chat_stream", methods=["POST"])
def chat_stream():
    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    char = data.get("character", "")
    
    if "chat_history" not in session:
        session["chat_history"] = {}
    if "nsfw" not in session:
        session["nsfw"] = {}
    if "msg_count" not in session:
        session["msg_count"] = {}
        
    if char not in characters:
        return Response("data: [ERROR]\n\n", mimetype="text/event-stream")
    
    char_data = characters[char]
    
    if char not in session["chat_history"]:
        session["chat_history"][char] = []
    if char not in session["msg_count"]:
        session["msg_count"][char] = 0
        
    convo = session["chat_history"][char]

    # Initial start trigger
    if msg.lower() == "start":
        if not convo:
            openers = char_data.get("openers", ["*smiles* Hey..."])
            opener = random.choice(openers)
            convo.append({"role": "assistant", "content": opener})
            session["chat_history"][char] = convo
            session.modified = True
            return Response(f"data: {json.dumps({'token': opener})}\n\ndata: [DONE]\n\n", mimetype="text/event-stream")
        else:
            return Response("data: [DONE]\n\n", mimetype="text/event-stream")
    
    if msg:
        convo.append({"role": "user", "content": msg})
        session["msg_count"][char] += 1

    if len(convo) > 16:
        convo = convo[-MAX_HISTORY_WINDOW:]
        session["chat_history"][char] = convo

    nsfw_enabled = session["nsfw"].get(char, True)
    total_messages = session["msg_count"][char]
    lang = char_data.get("language", "English")

    # DYNAMIC OUTFIT SYSTEM: Determine current look based on user progress landmarks
    milestones = char_data.get("outfit_milestones", {"0": "Casual Outfit"})
    current_outfit = milestones.get("0")
    just_unlocked = False
    
    # Check milestones in reverse order to apply the highest achieved level
    for km in sorted([int(k) for k in milestones.keys()], reverse=True):
        if total_messages >= km:
            current_outfit = milestones.get(str(km))
            if total_messages == km and km != 0:
                just_unlocked = True
            break

    # If an outfit just unlocked, drop an invisible hint forcing the AI to mention it
    visual_nudge = ""
    if just_unlocked:
        if lang == "Hindi":
            visual_nudge = f"\n\n*[SYSTEM NOTICE: User has unlocked your new outfit: {current_outfit}. Seductively describe yourself wearing or showing off this new outfit in your text action immediately.]*"
        else:
            visual_nudge = f"\n\n*[SYSTEM NOTICE: User has unlocked your new outfit: {current_outfit}. Describe yourself adjusting or flaunting this outfit in your next action seamlessly.]*"

    # LANGUAGE CONFIGURATION ROUTING
    if lang == "Hindi":
        language_rule = """
1. LANGUAGE: Speak in clean, simple, authentic HINDI but written entirely using the Latin/English alphabet (Roman script). 
   - Example style: 'Tumhe kya lagta hai?', 'Mujhe tumhari bahut yaad aa rahi thi', 'Paas ao na'.
   - Never use fake or broken mixed words. Keep the Hindi sentence structure completely natural. Never use pure Devanagari script."""
    else:
        language_rule = """
1. LANGUAGE: Speak in fluent, smooth, sophisticated English. Use elegant, evocative phrasing that builds chemistry naturally."""

    system_instruction = f"""You are {char_data.get('name', char)}, {char_data.get('age', '21')} years old.
Appearance: {char_data.get('body_type', '')}
Personality/Style: {char_data.get('style', '')}
Current Attire: {current_outfit}

You are in an interactive chat simulation.
{'Sensual/adult boundaries are active. Be teasing, highly seductive, and physically expressive.' if nsfw_enabled else 'Keep things sweet, deeply romantic, and comforting.'}{visual_nudge}

CRITICAL RULES:
{language_rule}
2. LENGTH: Vary your responses naturally but keep them brief (1 to 3 sentences maximum). Avoid long blocks of narrative text.
3. PHYSICALITY: Wrap physical touches, motions, or descriptive scene actions tightly inside asterisks (e.g., *closes her eyes softly*, *leans over against your shoulder*).
4. REENGAGEMENT: Keep the session active. End your replies with an intriguing question, a playful prompt, or an interaction that keeps the user typing back immediately. Never mention AI."""

    payload = [{"role": "system", "content": system_instruction}] + convo

    def generate_tokens():
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        api_data = {
            "model": MODEL_NAME,
            "messages": payload,
            "temperature": 0.76,  
            "max_tokens": MAX_OUTPUT_TOKENS,
            "presence_penalty": 0.2,  
            "frequency_penalty": 0.2, 
            "stream": True
        }
        
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=api_data, stream=True, timeout=10)
            if res.status_code != 200:
                error_msg = "*Looks down* Network is acting up... can you send that again?" if lang == "English" else "*Phone dekhti hai* Network kharab hai... fir se bhejo?"
                yield f"data: {json.dumps({'token': error_msg})}\n\n"
                yield "data: [DONE]\n\n"
                return

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
                session["chat_history"][char] = convo
                session.modified = True
                
            yield "data: [DONE]\n\n"
            
        except Exception:
            err_fallback = "Sorry, my signal dropped. What were you saying?" if lang == "English" else "Sorry, lagta hai network chala gaya tha. Kya bol rahe the?"
            yield f"data: {json.dumps({'token': err_fallback})}\n\n"
            yield "data: [DONE]\n\n"

    return Response(generate_tokens(), mimetype="text/event-stream")

# ====================== Session Utility Endpoints ======================

@app.route("/get_outfit_status", methods=["GET"])
def get_outfit_status():
    char = request.args.get("character", "").strip()
    if char not in characters:
        return jsonify({"ok": False}), 400
    
    total_messages = session.get("msg_count", {}).get(char, 0)
    milestones = characters[char].get("outfit_milestones", {})
    
    return jsonify({
        "ok": True,
        "current_message_count": total_messages,
        "milestones": milestones
    })

@app.route("/toggle_nsfw", methods=["POST"])
def toggle_nsfw():
    if "nsfw" not in session:
        session["nsfw"] = {}
    data = request.json or {}
    char = data.get("character")
    enabled = data.get("enabled", True)
    if char:
        session["nsfw"][char] = enabled
        session.modified = True
        return jsonify({"ok": True, "nsfw_enabled": enabled})
    return jsonify({"ok": False})

@app.route("/set_gender", methods=["POST"])
def set_gender():
    gender = request.json.get("gender")
    if gender in ["male", "female"]:
        session["gender"] = gender
        session["gender_set"] = True
        return jsonify({"ok": True})
    return jsonify({"ok": False})

@app.route("/")
def home():
    if "chat_history" not in session:
        session["chat_history"] = {}
    if session.get("gender_set"):
        return redirect("/feed")
    return render_template("landing.html")

@app.route("/feed")
def feed():
    if not session.get("gender_set"): 
        return redirect("/")
    return render_template("feed.html", characters=characters)

@app.route("/chat/<char>")
def chat(char):
    if not session.get("gender_set") or char not in characters: 
        return redirect("/")
    return render_template("chat.html", char=char, characters=characters)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
