"""
analyzer.py
Usa l'AI per estrarre un catalogo corsi strutturato da testo grezzo
e per confrontare due cataloghi producendo una lista di match.
"""

import csv
import io
import json
import re
from ai_client import get_completion


SYSTEM_EXTRACT = """Sei un assistente specializzato nell'analisi di cataloghi universitari per studenti Erasmus.
Il tuo compito è estrarre informazioni strutturate sui corsi accademici da testo grezzo.
Rispondi SOLO con JSON valido, senza markdown, senza spiegazioni."""

SYSTEM_MATCH = """Sei un consulente esperto di programmi Erasmus e Learning Agreement (LA).
Il tuo compito è confrontare due cataloghi di corsi universitari e identificare coppie di corsi
sovrapponibili che uno studente potrebbe inserire nel proprio Learning Agreement.
Due corsi sono sovrapponibili se hanno contenuti, obiettivi o competenze simili,
anche se il nome è diverso. Considera anche crediti e livello di studio.
Rispondi SOLO con JSON valido, senza markdown, senza spiegazioni."""


def extract_courses(raw_text: str, university_name: str,
                    api_key: str, provider: str, model: str) -> list[dict]:
    """
    Chiede all'AI di estrarre i corsi dal testo grezzo.
    Restituisce una lista di dizionari con le chiavi standard.
    """
    # Tronca a ~15k caratteri per non superare i limiti di contesto
    truncated = raw_text[:15000]

    prompt = f"""
Analizza il seguente testo proveniente dal catalogo corsi dell'università "{university_name}".

Estrai TUTTI i corsi che riesci a trovare. Per ogni corso fornisci:
- "nome": nome del corso (stringa)
- "ciclo": ciclo di studi (es. "Triennale", "Magistrale", "Bachelor", "Master", oppure "N/D")
- "lingua": lingua di insegnamento (es. "Italiano", "Inglese", oppure "N/D")
- "crediti": numero di crediti ECTS o CFU come numero intero (0 se non specificato)
- "descrizione": breve descrizione degli obiettivi e contenuti del corso (max 3 frasi)

Restituisci un oggetto JSON con questa struttura ESATTA:
{{
  "university": "{university_name}",
  "courses": [
    {{
      "nome": "...",
      "ciclo": "...",
      "lingua": "...",
      "crediti": 0,
      "descrizione": "..."
    }}
  ]
}}

TESTO DA ANALIZZARE:
{truncated}
"""

    raw_response = get_completion(prompt, SYSTEM_EXTRACT, api_key, provider, model)

    # Pulizia: rimuovi eventuali backtick markdown
    cleaned = re.sub(r"```json|```", "", raw_response).strip()

    try:
        data = json.loads(cleaned)
        courses = data.get("courses", [])
        # Normalizza ogni corso
        normalized = []
        for c in courses:
            normalized.append({
                "nome":        str(c.get("nome", "N/D")).strip(),
                "ciclo":       str(c.get("ciclo", "N/D")).strip(),
                "lingua":      str(c.get("lingua", "N/D")).strip(),
                "crediti":     int(c.get("crediti", 0)) if str(c.get("crediti", 0)).isdigit() else 0,
                "descrizione": str(c.get("descrizione", "")).strip(),
            })
        return normalized
    except (json.JSONDecodeError, ValueError):
        # Fallback: prova a estrarre manualmente
        return _fallback_extract(cleaned)


def _fallback_extract(text: str) -> list[dict]:
    """Fallback minimale se il JSON è malformato."""
    return [{
        "nome": "Errore di parsing",
        "ciclo": "N/D",
        "lingua": "N/D",
        "crediti": 0,
        "descrizione": f"Impossibile analizzare la risposta AI. Risposta: {text[:300]}",
    }]


def courses_to_csv(courses: list[dict], university_name: str) -> str:
    """Converte la lista corsi in una stringa CSV."""
    output = io.StringIO()
    fieldnames = ["nome", "ciclo", "lingua", "crediti", "descrizione"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for c in courses:
        writer.writerow({k: c.get(k, "") for k in fieldnames})
    return output.getvalue()


def find_matches(courses_home: list[dict], university_home: str,
                 courses_abroad: list[dict], university_abroad: str,
                 threshold: int,
                 api_key: str, provider: str, model: str) -> list[dict]:
    """
    Confronta i corsi di due università e restituisce i match.
    Processa a batch per gestire cataloghi grandi.
    """
    # Per cataloghi grandi, prendi i primi N corsi per non sforare il context
    home_sample  = courses_home[:40]
    abroad_sample = courses_abroad[:40]

    home_json   = json.dumps(home_sample,   ensure_ascii=False)
    abroad_json = json.dumps(abroad_sample, ensure_ascii=False)

    prompt = f"""
Hai due cataloghi di corsi universitari.

UNIVERSITÀ DI CASA ("{university_home}"):
{home_json}

UNIVERSITÀ ESTERA ("{university_abroad}"):
{abroad_json}

Identifica le coppie di corsi che sono SOVRAPPONIBILI per il Learning Agreement Erasmus.
Usa una soglia di somiglianza minima di {threshold}/100.

Per ogni coppia restituisci:
- "corso_casa": nome del corso dell'università di casa
- "corso_estero": nome del corso dell'università estera
- "crediti_casa": crediti del corso di casa (intero)
- "crediti_estero": crediti del corso estero (intero)
- "lingua_estero": lingua del corso estero
- "ciclo_estero": ciclo del corso estero
- "similarita": punteggio di somiglianza da 0 a 100 (intero)
- "motivazione": breve spiegazione (1-2 frasi) del perché i corsi sono sovrapponibili

Restituisci JSON con questa struttura ESATTA:
{{
  "university_home": "{university_home}",
  "university_abroad": "{university_abroad}",
  "matches": [
    {{
      "corso_casa": "...",
      "corso_estero": "...",
      "crediti_casa": 0,
      "crediti_estero": 0,
      "lingua_estero": "...",
      "ciclo_estero": "...",
      "similarita": 0,
      "motivazione": "..."
    }}
  ]
}}

Ordina i match dal più simile al meno simile.
Se non ci sono match con similarità >= {threshold}, restituisci "matches": [].
"""

    raw_response = get_completion(prompt, SYSTEM_MATCH, api_key, provider, model)
    cleaned = re.sub(r"```json|```", "", raw_response).strip()

    try:
        data = json.loads(cleaned)
        matches = data.get("matches", [])
        # Filtra per threshold e normalizza
        result = []
        for m in matches:
            sim = int(m.get("similarita", 0))
            if sim >= threshold:
                result.append({
                    "corso_casa":    str(m.get("corso_casa", "")).strip(),
                    "corso_estero":  str(m.get("corso_estero", "")).strip(),
                    "crediti_casa":  int(m.get("crediti_casa", 0)),
                    "crediti_estero": int(m.get("crediti_estero", 0)),
                    "lingua_estero": str(m.get("lingua_estero", "N/D")).strip(),
                    "ciclo_estero":  str(m.get("ciclo_estero", "N/D")).strip(),
                    "similarita":    sim,
                    "motivazione":   str(m.get("motivazione", "")).strip(),
                })
        return result
    except (json.JSONDecodeError, ValueError) as e:
        return [{
            "corso_casa": "Errore",
            "corso_estero": "Errore di parsing",
            "crediti_casa": 0,
            "crediti_estero": 0,
            "lingua_estero": "N/D",
            "ciclo_estero": "N/D",
            "similarita": 0,
            "motivazione": f"Impossibile analizzare la risposta AI: {e}",
        }]
