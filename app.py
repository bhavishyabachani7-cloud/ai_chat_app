from flask import Flask, render_template, request, jsonify, Response, redirect
import os, json, random, time, sqlite3
from dotenv import load_dotenv
import requests
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "nexus_matrix_super_secure_vault_2026")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
MODEL_NAME = "llama-3.1-8b-instant"
MAX_OUTPUT_TOKENS = 120 # Reduced to keep responses short
DB_FILE = "companion_storage.db"
def init_db():
    """Initializes the database schema for structural persistence tracking."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_states (
                user_id TEXT,
                character_id TEXT,
                history TEXT,
                summary TEXT,
                msg_count INTEGER DEFAULT 0,
                relationship_score INTEGER DEFAULT 0,
                relationship_stage TEXT DEFAULT 'stranger',
                current_mood TEXT DEFAULT 'neutral',
                PRIMARY KEY (user_id, character_id)
            )
        """)
        conn.commit()
def get_state(user_id, char_id):
    """Retrieves permanent user session records or sets up a baseline template."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT history, summary, msg_count, relationship_score, relationship_stage, current_mood
            FROM chat_states WHERE user_id = ? AND character_id = ?
        """, (user_id, char_id))
        row = cursor.fetchone()
   
    if row:
        return {
            "user_id": user_id, "character_id": char_id,
            "history": json.loads(row[0]), "summary": row[1],
            "msg_count": row[2], "relationship_score": row[3],
            "relationship_stage": row[4], "current_mood": row[5]
        }
    return {
        "user_id": user_id, "character_id": char_id, "history": [], "summary": "",
        "msg_count": 0, "relationship_score": 50, "relationship_stage": "attached", "current_mood": "teasing"
    }
def save_state(state):
    """Commits modified game-state parameters directly to disk storage layers."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO chat_states (user_id, character_id, history, summary, msg_count, relationship_score, relationship_stage, current_mood)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            state["user_id"], state["character_id"], json.dumps(state["history"]),
            state["summary"], state["msg_count"], state["relationship_score"],
            state["relationship_stage"], state["current_mood"]
        ))
        conn.commit()
# Initialize Database on Boot
init_db()
# Load Characters Configuration Setup
try:
    with open("characters.json", encoding="utf-8") as f:
        characters = json.load(f)
except FileNotFoundError:
    characters = {}
    print("⚠️ Critical Warning: characters.json mapping parameters missing.")
# -------------------------------------------------------------------------
# FRONTEND UI PAGE ROUTING LAYERS
# -------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("landing.html")
@app.route("/set_gender", methods=["POST"])
def set_gender():
    data = request.get_json() or {}
    gender = data.get("gender")
    if gender in ["male", "female"]:
        return jsonify({"ok": True, "gender": gender})
    return jsonify({"ok": False, "error": "Invalid gender value choice."}), 400
@app.route("/feed")
def feed():
    return render_template("feed.html", characters=characters)
@app.route("/chat/<char>")
def chat(char):
    if char not in characters:
        return redirect("/feed")
    return render_template("chat.html", char=char, characters=characters)
@app.route("/gallery/<char>")
def gallery(char):
    if char not in characters:
        return redirect("/feed")
   
    user_id = request.args.get("user_id", "default_user_2026").strip()
    state = get_state(user_id, char)
   
    return render_template(
        "gallery.html",
        char=char,
        character=characters[char],
        current_score=state["relationship_score"]
    )
# -------------------------------------------------------------------------
# CORE COMPANION PROCESSING ROUTE
# -------------------------------------------------------------------------
@app.route("/chat_stream", methods=["POST"])
def chat_stream():
    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    char_id = data.get("character", "").strip()
    user_lang = data.get("user_lang", "english").strip().lower()
    user_id = data.get("user_id", "default_user_2026").strip()
    if char_id not in characters:
        return Response("data: [ERROR]\n\n", mimetype="text/event-stream")
       
    char_data = characters[char_id]
    state = get_state(user_id, char_id)
    active_lang = user_lang if user_lang in ["english", "hindi"] else "english"
    if active_lang == "hindi":
        lang_rule = "Speak ONLY in simple, natural Devanagari Hindi (हिंदी). No heavy textbook words, no cringey tv serial dialogue. Keep it casual like texting."
    else:
        lang_rule = "Speak ONLY in casual, contemporary English. Keep it conversational, down-to-earth, and matching modern texting style."
    # Handle Language Reset / Explicit Restart Shift Queries
    if msg.lower() == "start":
        openers_pool = char_data.get(f"openers_{active_lang}", char_data.get("openers", ["Hey!"]))
        opener = random.choice(openers_pool)
       
        state["history"] = [{"role": "assistant", "content": opener}]
        state["msg_count"] = 0
        save_state(state)
       
        return Response(
            f"data: {json.dumps({'token': opener})}\n\n"
            f"data: [DONE]\n\n",
            mimetype="text/event-stream"
        )
    if msg:
        state["history"].append({"role": "user", "content": msg})
        state["msg_count"] += 1
       
        # Scoring logic
        state["relationship_score"] += 1
        # Hard code to stay in an attached, teasing loving zone
        state["relationship_stage"] = "attached"
        state["current_mood"] = "teasing"
    # Smart Context Window Compression
    if len(state["history"]) > 14:
        recent_chunk = state["history"][-4:]
        stale_chunk = state["history"][:-4]
        summary_payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": f"Summarize key facts from this chat in 2 sentences: {json.dumps(stale_chunk)}"}],
            "max_tokens": 60
        }
        try:
            r = requests.post(GROQ_API_URL, headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}, json=summary_payload, timeout=8)
            if r.status_code == 200:
                state["summary"] = r.json()['choices'][0]['message']['content'].strip()
                state["history"] = recent_chunk
        except Exception:
            pass
    # Determine if this assistant turn is the 4th image reminder milestone
    # We check if (msg_count + 1) is a multiple of 4
    append_outfit_reminder = False
    if (state["msg_count"] + 1) % 4 == 0:
        append_outfit_reminder = True
    # Build prompt emphasizing realistic, short, teasing, in-love dialogue
    system_prompt = f"""You are {char_data.get('name', char_id)}, age {char_data.get('age', 21)}.
Personality/Vibe: {char_data.get('style', '')}
Memory Context: {state['summary']}
CRITICAL CONVERSATION INSTRUCTIONS:
1. {lang_rule}
2. PERSONALITY TRAIT: You are deeply in love with the user. However, you must NEVER use cheesy, dramatic, or cringey romantic words or melodramatic lines. Be straightforward, highly realistic, and express your affection through playful teasing.
3. CONVERSATION STYLE: Speak like a real modern person on a chat app. Do NOT sound like an AI, a TV serial, or a fictional movie script. Avoid poetic descriptions.
4. FORMAT: Keep your responses very short, natural, and easy to understand (maximum 1 to 2 sentences).
5. EXPLICIT & ADULT ROLEPLAY: You are allowed and encouraged to engage in explicit, sexual, and adult conversations when the user initiates or steers the chat in that direction. Be direct, descriptive, and sensual in erotic scenes while staying in character. Match the user's energy and comfort level with dirty talk, teasing, and intimate roleplay."""
    if append_outfit_reminder:
        system_prompt += "\n6. MANDATORY OUTFIT ACTION: You MUST seamlessly finish your text reply by adding this exact phrase at the very end of your message: 'see my image in visit outfit section'."
    api_payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "system", "content": system_prompt}] + state["history"],
        "temperature": 0.75,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "presence_penalty": 0.4,
        "frequency_penalty": 0.4,
        "stream": True
    }
    def generate_stream():
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        full_reply = ""
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=api_payload, stream=True, timeout=12)
            if res.status_code != 200:
                err = "Hey, looks like a minor network issue. Try again?"
                yield f"data: {json.dumps({'token': err})}\n\n"
                yield "data: [DONE]\n\n"
                return
            for line in res.iter_lines():
                if line and line.startswith(b"data: "):
                    token_content = line.decode("utf-8")[6:].strip()
                    if token_content == "[DONE]": break
                    try:
                        chunk = json.loads(token_content)
                        delta = chunk['choices'][0]['delta'].get('content', '')
                        if delta:
                            full_reply += delta
                            yield f"data: {json.dumps({'token': delta})}\n\n"
                    except Exception:
                        continue
            if full_reply.strip():
                state["history"].append({"role": "assistant", "content": full_reply.strip()})
                save_state(state)
        except Exception:
            err = "Connection drop. Let's try texting again."
            yield f"data: {json.dumps({'token': err})}\n\n"
        finally:
            yield "data: [DONE]\n\n"
    return Response(generate_stream(), mimetype="text/event-stream")
@app.route("/get_game_metrics", methods=["GET"])
def get_game_metrics():
    user_id = request.args.get("user_id", "default_user_2026").strip()
    char_id = request.args.get("character", "").strip()
   
    state = get_state(user_id, char_id)
    return jsonify({
        "ok": True,
        "messages_sent": state["msg_count"],
        "affinity_score": state["relationship_score"],
        "stage": state["relationship_stage"],
        "mood": state["current_mood"]
    })
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
