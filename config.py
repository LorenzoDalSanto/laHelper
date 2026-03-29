# ============================================================
#  ERASMUS LA HELPER — CONFIGURAZIONE
# ============================================================
#
#  Inserisci qui la tua API key e seleziona il provider.
#  Supportati: openai | anthropic | google
#
# ============================================================

API_KEY = "INSERISCI_QUI_LA_TUA_API_KEY"

# Provider: "openai" | "anthropic" | "google"
API_PROVIDER = "openai"

# Modello da usare (esempi per ogni provider):
#   OpenAI:    "gpt-4o"  /  "gpt-4-turbo"  /  "gpt-3.5-turbo"
#   Anthropic: "claude-opus-4-6"  /  "claude-sonnet-4-6"
#   Google:    "gemini-1.5-pro"   /  "gemini-1.5-flash"
API_MODEL = "gpt-4o"

# ============================================================
#  Impostazioni avanzate (opzionali)
# ============================================================

# Soglia di somiglianza per considerare due corsi "sovrapponibili"
# Valore tra 0 e 100 (default: 60)
MATCH_THRESHOLD = 60

# Porta su cui gira il server locale
SERVER_PORT = 5050
