from datetime import datetime
import os

from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from sqlalchemy import create_engine, text
import requests

# Load environment variables
load_dotenv()

# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# Database setup: MySQL if URL exists, otherwise SQLite
MYSQL_URL = os.getenv("MYSQL_URL")
ENGINE_URL = MYSQL_URL if MYSQL_URL else "sqlite+pysqlite:///mood.db"
engine = create_engine(ENGINE_URL, echo=False, future=True)

# Hugging Face API settings
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
HF_MODEL = os.getenv("HF_MODEL", "cardiffnlp/twitter-roberta-base-sentiment-latest")
HF_ENDPOINT = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

# Initialize database
def init_db():
    if ENGINE_URL.startswith("sqlite"):
        ddl = """
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            mood_label TEXT NOT NULL,
            mood_score REAL NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    else:
        ddl = """
        CREATE TABLE IF NOT EXISTS entries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            text TEXT NOT NULL,
            mood_label VARCHAR(32) NOT NULL,
            mood_score FLOAT NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
        """
    with engine.begin() as conn:
        conn.exec_driver_sql(ddl)

init_db()

# Helper: sentiment analysis
def analyze_sentiment(text_input: str):
    if HF_API_TOKEN:
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        try:
            resp = requests.post(HF_ENDPOINT, headers=headers, json={"inputs": text_input}, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            top = None
            if isinstance(data, list):
                if data and isinstance(data[0], list) and data[0]:
                    top = max(data[0], key=lambda d: d.get("score", 0))
                elif data and isinstance(data[0], dict):
                    top = max(data, key=lambda d: d.get("score", 0))
            if top and "label" in top:
                return top["label"], float(top.get("score", 0.0))
        except Exception as e:
            app.logger.warning(f"HF API failed, using fallback. Error: {e}")

    # Fallback heuristic
    t = text_input.lower()
    positive_words = ["happy", "great", "good", "love", "excited", "grateful", "blessed", "amazing"]
    negative_words = ["sad", "bad", "angry", "upset", "tired", "anxious", "depressed", "worried"]
    score = sum(1 for w in positive_words if w in t) - sum(1 for w in negative_words if w in t)
    label = "POSITIVE" if score >= 0 else "NEGATIVE"
    conf = min(1.0, 0.5 + (abs(score) / 5.0))
    return label, conf

# Helper: convert DB row to dict
def row_to_dict(row):
    return {
        "id": row[0],
        "text": row[1],
        "mood_label": row[2],
        "mood_score": float(row[3]),
        "created_at": row[4],
    }

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.post("/api/entries")
def create_entry():
    data = request.get_json(force=True)
    text_input = (data.get("text") or "").strip()
    if not text_input:
        return jsonify({"error": "Text is required."}), 400

    label, score = analyze_sentiment(text_input)
    ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    with engine.begin() as conn:
        if ENGINE_URL.startswith("sqlite"):
            conn.execute(
                text("INSERT INTO entries (text, mood_label, mood_score, created_at) VALUES (:t, :l, :s, :c)"),
                {"t": text_input, "l": label, "s": score, "c": ts}
            )
            new_id = conn.execute(text("SELECT last_insert_rowid()")).scalar_one()
        else:
            res = conn.execute(
                text("INSERT INTO entries (text, mood_label, mood_score, created_at) VALUES (:t, :l, :s, :c)"),
                {"t": text_input, "l": label, "s": score, "c": ts}
            )
            new_id = res.lastrowid

    return jsonify({"id": new_id, "text": text_input, "mood_label": label, "mood_score": score, "created_at": ts})

@app.get("/api/entries")
def list_entries():
    with engine.begin() as conn:
        rows = conn.execute(text(
            "SELECT id, text, mood_label, mood_score, created_at FROM entries ORDER BY created_at ASC"
        )).all()
    return jsonify([row_to_dict(r) for r in rows])

@app.delete("/api/entries/<int:entry_id>")
def delete_entry(entry_id):
    with engine.begin() as conn:
        res = conn.execute(text("DELETE FROM entries WHERE id = :id"), {"id": entry_id})
    if res.rowcount == 0:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"ok": True})

# Run the app
if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
