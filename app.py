"""
app.py
Server Flask — backend dell'applicazione Erasmus LA Helper.
"""

import os
import json
import uuid
import csv
import io
import traceback
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from extractor import extract_from_url, extract_from_file
from analyzer  import extract_courses, courses_to_csv, find_matches
from pdf_generator import generate_pdf

# Carica la config
try:
    import config
    DEFAULT_API_KEY  = getattr(config, "API_KEY",      "")
    DEFAULT_PROVIDER = getattr(config, "API_PROVIDER", "openai")
    DEFAULT_MODEL    = getattr(config, "API_MODEL",    "gpt-4o")
    DEFAULT_THRESHOLD = getattr(config, "MATCH_THRESHOLD", 60)
    SERVER_PORT      = getattr(config, "SERVER_PORT",  5050)
except ImportError:
    DEFAULT_API_KEY  = ""
    DEFAULT_PROVIDER = "openai"
    DEFAULT_MODEL    = "gpt-4o"
    DEFAULT_THRESHOLD = 60
    SERVER_PORT      = 5050

# ── App setup ────────────────────────────────────────────────────────────────

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR  = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR  = os.path.join(BASE_DIR, "output")
STATIC_DIR  = os.path.join(BASE_DIR, "static")

os.makedirs(UPLOAD_DIR,  exist_ok=True)
os.makedirs(OUTPUT_DIR,  exist_ok=True)

app = Flask(__name__, static_folder=STATIC_DIR, template_folder=BASE_DIR)
CORS(app)

ALLOWED_EXTENSIONS = {"pdf", "txt", "md", "csv"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Sessioni in memoria (semplice dizionario) ────────────────────────────────
# Struttura: sessions[session_id] = {
#   "universities": { uni_id: {"name": str, "sources": [...], "courses": [...], "csv": str} },
#   "matches":      { "home_id+abroad_id": [...] }
# }
sessions: dict = {}


def get_session(sid: str) -> dict:
    if sid not in sessions:
        sessions[sid] = {"universities": {}, "matches": {}}
    return sessions[sid]


# ── Route statiche ───────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)


# ── API: Config ──────────────────────────────────────────────────────────────

@app.route("/api/config", methods=["GET"])
def get_config():
    return jsonify({
        "api_key":   DEFAULT_API_KEY[:6] + "***" if DEFAULT_API_KEY else "",
        "provider":  DEFAULT_PROVIDER,
        "model":     DEFAULT_MODEL,
        "threshold": DEFAULT_THRESHOLD,
        "has_key":   bool(DEFAULT_API_KEY and DEFAULT_API_KEY != "INSERISCI_QUI_LA_TUA_API_KEY"),
    })


# ── API: Sessione ────────────────────────────────────────────────────────────

@app.route("/api/session/new", methods=["POST"])
def new_session():
    sid = str(uuid.uuid4())
    sessions[sid] = {"universities": {}, "matches": {}}
    return jsonify({"session_id": sid})


# ── API: Università ──────────────────────────────────────────────────────────

@app.route("/api/university/add", methods=["POST"])
def add_university():
    data = request.json or {}
    sid  = data.get("session_id", "default")
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Nome università obbligatorio"}), 400

    sess = get_session(sid)
    uid  = str(uuid.uuid4())
    sess["universities"][uid] = {
        "name":    name,
        "sources": [],   # {type: "url"|"file", value: str, label: str}
        "courses": [],
        "csv":     "",
    }
    return jsonify({"university_id": uid, "name": name})


@app.route("/api/university/list", methods=["POST"])
def list_universities():
    data = request.json or {}
    sid  = data.get("session_id", "default")
    sess = get_session(sid)
    unis = [
        {"id": uid, "name": u["name"],
         "source_count": len(u["sources"]),
         "course_count": len(u["courses"])}
        for uid, u in sess["universities"].items()
    ]
    return jsonify({"universities": unis})


@app.route("/api/university/remove", methods=["POST"])
def remove_university():
    data = request.json or {}
    sid  = data.get("session_id", "default")
    uid  = data.get("university_id", "")
    sess = get_session(sid)
    if uid in sess["universities"]:
        del sess["universities"][uid]
    return jsonify({"ok": True})


# ── API: Sorgenti ────────────────────────────────────────────────────────────

@app.route("/api/source/add_url", methods=["POST"])
def add_url():
    data = request.json or {}
    sid  = data.get("session_id", "default")
    uid  = data.get("university_id", "")
    url  = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "URL obbligatorio"}), 400

    sess = get_session(sid)
    if uid not in sess["universities"]:
        return jsonify({"error": "Università non trovata"}), 404

    sess["universities"][uid]["sources"].append({
        "type": "url", "value": url, "label": url
    })
    return jsonify({"ok": True, "source_count": len(sess["universities"][uid]["sources"])})


@app.route("/api/source/upload_file", methods=["POST"])
def upload_file():
    sid = request.form.get("session_id", "default")
    uid = request.form.get("university_id", "")

    if "file" not in request.files:
        return jsonify({"error": "Nessun file inviato"}), 400

    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Tipo di file non supportato"}), 400

    sess = get_session(sid)
    if uid not in sess["universities"]:
        return jsonify({"error": "Università non trovata"}), 404

    filename  = secure_filename(file.filename)
    save_name = f"{uid}_{filename}"
    save_path = os.path.join(UPLOAD_DIR, save_name)
    file.save(save_path)

    sess["universities"][uid]["sources"].append({
        "type": "file", "value": save_path, "label": filename
    })
    return jsonify({"ok": True, "filename": filename,
                    "source_count": len(sess["universities"][uid]["sources"])})


@app.route("/api/source/remove", methods=["POST"])
def remove_source():
    data  = request.json or {}
    sid   = data.get("session_id", "default")
    uid   = data.get("university_id", "")
    index = data.get("index", -1)

    sess = get_session(sid)
    if uid not in sess["universities"]:
        return jsonify({"error": "Università non trovata"}), 404

    sources = sess["universities"][uid]["sources"]
    if 0 <= index < len(sources):
        sources.pop(index)
    return jsonify({"ok": True})


# ── API: Analisi corsi ───────────────────────────────────────────────────────

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data      = request.json or {}
    sid       = data.get("session_id",  "default")
    uid       = data.get("university_id", "")
    api_key   = data.get("api_key",   DEFAULT_API_KEY)
    provider  = data.get("provider",  DEFAULT_PROVIDER)
    model     = data.get("model",     DEFAULT_MODEL)

    if not api_key or api_key == "INSERISCI_QUI_LA_TUA_API_KEY":
        return jsonify({"error": "API key non configurata"}), 400

    sess = get_session(sid)
    if uid not in sess["universities"]:
        return jsonify({"error": "Università non trovata"}), 404

    uni = sess["universities"][uid]
    if not uni["sources"]:
        return jsonify({"error": "Nessuna sorgente aggiunta per questa università"}), 400

    try:
        # 1. Estrai testo da tutte le sorgenti
        all_text = []
        for src in uni["sources"]:
            if src["type"] == "url":
                text = extract_from_url(src["value"])
            else:
                text = extract_from_file(src["value"])
            all_text.append(f"--- Fonte: {src['label']} ---\n{text}")

        combined = "\n\n".join(all_text)

        # 2. Analisi AI
        courses = extract_courses(combined, uni["name"], api_key, provider, model)

        # 3. Salva risultati
        uni["courses"] = courses
        uni["csv"]     = courses_to_csv(courses, uni["name"])

        return jsonify({
            "ok":          True,
            "course_count": len(courses),
            "courses":     courses,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/courses", methods=["POST"])
def get_courses():
    data = request.json or {}
    sid  = data.get("session_id", "default")
    uid  = data.get("university_id", "")
    sess = get_session(sid)
    if uid not in sess["universities"]:
        return jsonify({"error": "Università non trovata"}), 404
    uni = sess["universities"][uid]
    return jsonify({"courses": uni["courses"], "csv": uni["csv"]})


@app.route("/api/courses/download_csv", methods=["POST"])
def download_csv():
    data = request.json or {}
    sid  = data.get("session_id", "default")
    uid  = data.get("university_id", "")
    sess = get_session(sid)
    if uid not in sess["universities"]:
        return jsonify({"error": "Università non trovata"}), 404
    uni = sess["universities"][uid]
    if not uni["csv"]:
        return jsonify({"error": "Nessun CSV disponibile, esegui prima l'analisi"}), 400

    buf = io.BytesIO(uni["csv"].encode("utf-8"))
    safe_name = uni["name"].replace(" ", "_")
    return send_file(buf, mimetype="text/csv",
                     as_attachment=True,
                     download_name=f"corsi_{safe_name}.csv")


# ── API: Match ────────────────────────────────────────────────────────────────

@app.route("/api/match", methods=["POST"])
def match():
    data         = request.json or {}
    sid          = data.get("session_id",      "default")
    home_id      = data.get("home_id",         "")
    abroad_id    = data.get("abroad_id",       "")
    api_key      = data.get("api_key",         DEFAULT_API_KEY)
    provider     = data.get("provider",        DEFAULT_PROVIDER)
    model        = data.get("model",           DEFAULT_MODEL)
    threshold    = int(data.get("threshold",   DEFAULT_THRESHOLD))

    if not api_key or api_key == "INSERISCI_QUI_LA_TUA_API_KEY":
        return jsonify({"error": "API key non configurata"}), 400

    sess = get_session(sid)
    if home_id not in sess["universities"]:
        return jsonify({"error": "Università di casa non trovata"}), 404
    if abroad_id not in sess["universities"]:
        return jsonify({"error": "Università estera non trovata"}), 404

    home_uni   = sess["universities"][home_id]
    abroad_uni = sess["universities"][abroad_id]

    if not home_uni["courses"]:
        return jsonify({"error": f"Analizza prima i corsi di '{home_uni['name']}'"}), 400
    if not abroad_uni["courses"]:
        return jsonify({"error": f"Analizza prima i corsi di '{abroad_uni['name']}'"}), 400

    try:
        matches = find_matches(
            home_uni["courses"],   home_uni["name"],
            abroad_uni["courses"], abroad_uni["name"],
            threshold,
            api_key, provider, model
        )

        match_key = f"{home_id}+{abroad_id}"
        sess["matches"][match_key] = {
            "home_name":   home_uni["name"],
            "abroad_name": abroad_uni["name"],
            "matches":     matches,
        }

        return jsonify({
            "ok":          True,
            "match_count": len(matches),
            "matches":     matches,
            "match_key":   match_key,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/match/download_pdf", methods=["POST"])
def download_match_pdf():
    data      = request.json or {}
    sid       = data.get("session_id", "default")
    match_key = data.get("match_key",  "")

    sess = get_session(sid)
    if match_key not in sess.get("matches", {}):
        return jsonify({"error": "Match non trovato, esegui prima il confronto"}), 404

    m_data     = sess["matches"][match_key]
    out_name   = f"LA_matches_{match_key[:8]}.pdf"
    out_path   = os.path.join(OUTPUT_DIR, out_name)

    try:
        generate_pdf(
            m_data["matches"],
            m_data["home_name"],
            m_data["abroad_name"],
            out_path
        )
        return send_file(out_path, mimetype="application/pdf",
                         as_attachment=True, download_name=out_name)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  🎓  Erasmus LA Helper — Server avviato")
    print(f"  👉  Apri il browser su: http://localhost:{SERVER_PORT}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=SERVER_PORT, debug=False)
