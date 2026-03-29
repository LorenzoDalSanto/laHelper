#!/usr/bin/env python3
"""
AVVIA.py — Erasmus LA Helper
Doppio click su questo file per avviare tutto.
"""

import sys
import os
import subprocess
import time
import webbrowser
import threading

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BLUE   = "\033[94m"

def banner():
    print(f"""
{BLUE}{BOLD}╔══════════════════════════════════════════════════════╗
║         🎓  Erasmus LA Helper  — Avvio               ║
╚══════════════════════════════════════════════════════╝{RESET}
""")

def step(msg):  print(f"  {CYAN}▸{RESET} {msg}")
def ok(msg):    print(f"  {GREEN}✓{RESET} {msg}")
def warn(msg):  print(f"  {YELLOW}⚠{RESET}  {msg}")
def err(msg):   print(f"  {RED}✗{RESET} {msg}")

banner()
step("Controllo versione Python...")

if sys.version_info < (3, 9):
    err(f"Python 3.9+ richiesto. Versione attuale: {sys.version}")
    input("\nPremi INVIO per uscire...")
    sys.exit(1)

ok(f"Python {sys.version.split()[0]} — OK")

# Dipendenze — versioni senza pin fisso per compatibilità Python 3.14+
# lxml NON incluso: usa html.parser built-in, zero dipendenze C
REQUIRED = {
    "flask":        "flask>=3.0",
    "httpx":        "httpx>=0.27",
    "flask_cors":   "flask-cors>=4.0",
    "requests":     "requests>=2.28",
    "bs4":          "beautifulsoup4>=4.12",
    "pdfplumber":   "pdfplumber>=0.10",
    "reportlab":    "reportlab>=4.0",
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Rileva provider AI da config.py
try:
    import importlib.util as _ilu
    _s = _ilu.spec_from_file_location("_cfg", os.path.join(BASE_DIR, "config.py"))
    _c = _ilu.module_from_spec(_s); _s.loader.exec_module(_c)
    _provider = getattr(_c, "API_PROVIDER", "openai").lower()
    HAS_KEY   = getattr(_c, "API_KEY", "") not in ("", "INSERISCI_QUI_LA_TUA_API_KEY")
    PORT      = getattr(_c, "SERVER_PORT", 5050)
except Exception:
    _provider = "openai"; HAS_KEY = False; PORT = 5050

if _provider == "openai":
    REQUIRED["openai"] = "openai>=1.10"
elif _provider == "anthropic":
    REQUIRED["anthropic"] = "anthropic>=0.20"
elif _provider in ("google", "gemini"):
    REQUIRED["google.generativeai"] = "google-generativeai>=0.5"
else:
    REQUIRED["openai"] = "openai>=1.10"

# Installa mancanti
missing = [pkg for mod, pkg in REQUIRED.items() if not __import__("importlib").util.find_spec(mod)]
# Fallback più robusto
missing = []
for module, package in REQUIRED.items():
    try:
        __import__(module)
    except ImportError:
        missing.append(package)

if missing:
    step(f"Installo {len(missing)} pacchett{'o' if len(missing)==1 else 'i'} mancanti...")
    for pkg in missing:
        print(f"    → {pkg}", end="", flush=True)
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg,
             "--quiet", "--disable-pip-version-check"],
            capture_output=True, text=True
        )
        if r.returncode == 0:
            print(f"  {GREEN}✓{RESET}")
        else:
            print(f"  {RED}✗{RESET}")
            lines = [l for l in r.stderr.strip().splitlines() if l.strip()]
            if lines: print(f"    {RED}{lines[-1]}{RESET}")
    ok("Dipendenze pronte")
else:
    ok("Tutte le dipendenze sono presenti")

URL = f"http://localhost:{PORT}"

# Avvia Flask con make_server (thread-safe, nessun conflitto con Werkzeug 3.x)
# flask_app.run() NON va usato in thread: imposta WERKZEUG_SERVER_FD che
# il thread figlio non riesce a leggere -> KeyError crash.
step("Avvio del server...")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import logging
logging.getLogger("werkzeug").setLevel(logging.ERROR)

import importlib.util
spec2      = importlib.util.spec_from_file_location("_app", os.path.join(BASE_DIR, "app.py"))
app_module = importlib.util.module_from_spec(spec2)
sys.modules["_app"] = app_module
spec2.loader.exec_module(app_module)
flask_app = app_module.app

from werkzeug.serving import make_server

try:
    srv = make_server("127.0.0.1", PORT, flask_app)
except OSError as e:
    err(f"Porta {PORT} già in uso o non disponibile: {e}")
    err("Modifica SERVER_PORT in config.py o chiudi l'altra istanza.")
    input("\nPremi INVIO per uscire...")
    sys.exit(1)

threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.3)
ok(f"Server in ascolto su {URL}")

step("Apertura del browser...")
webbrowser.open(URL)
ok("Browser aperto!")

key_line = (
    f"{YELLOW}⚠  API KEY non configurata — vai allo Step 1 nell'app{RESET}"
    if not HAS_KEY else
    f"{GREEN}✓  API Key trovata in config.py{RESET}"
)

print(f"""
{BLUE}{'─'*54}{RESET}
  {BOLD}App in esecuzione su:{RESET}  {GREEN}{URL}{RESET}
{'─'*54}
  {key_line}
{'─'*54}

  Premi  {BOLD}Ctrl + C{RESET}  per fermare il server e chiudere.
""")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    srv.shutdown()
    print(f"\n  {YELLOW}Server fermato. Arrivederci! 👋{RESET}\n")
    sys.exit(0)
