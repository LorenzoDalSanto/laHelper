# 🎓 Erasmus LA Helper

**Strumento AI per la compilazione del Learning Agreement Erasmus**

Analizza i cataloghi corsi della tua università di casa e delle università estere, 
e ti suggerisce automaticamente quali corsi inserire nel Learning Agreement.

---

## 🚀 Avvio rapido

### 1. Configura la tua API Key

Apri il file `config.py` e inserisci la tua API key:

```python
API_KEY      = "sk-la-tua-chiave-qui"
API_PROVIDER = "openai"     # openai | anthropic | google
API_MODEL    = "gpt-4o"     # il modello che vuoi usare
```

**Provider supportati:**
| Provider   | Modelli consigliati                        | Dove ottenere la key |
|------------|--------------------------------------------|----------------------|
| OpenAI     | `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`  | platform.openai.com  |
| Anthropic  | `claude-sonnet-4-6`, `claude-opus-4-6`    | console.anthropic.com|
| Google     | `gemini-1.5-pro`, `gemini-1.5-flash`      | aistudio.google.com  |

> ⚠️ Puoi anche inserire la key direttamente nell'interfaccia grafica al passo 1 senza toccare il file.

---

### 2. Avvia il programma

**Tutti i sistemi — doppio click su `AVVIA.py`**

Il file fa tutto da solo:
- installa le dipendenze mancanti al primo avvio
- avvia il server
- apre il browser sulla pagina dell'app

> Su macOS potrebbe apparire un avviso di sicurezza la prima volta:
> vai in *Impostazioni → Privacy e Sicurezza → Apri comunque*

**Alternativa manuale:**
```bash
python AVVIA.py
```

---

## 📋 Come si usa

### Step 1 — Configurazione
- Inserisci o verifica la tua API key
- Scegli provider e modello
- Imposta la soglia di similarità (default 60%)

### Step 2 — Università
- Clicca **"Aggiungi università"** per aggiungere la tua università di casa
- Aggiungi anche le università estere che ti interessano
- Per ogni università aggiungile le **fonti**:
  - 🔗 **URL**: incolla il link alla pagina del catalogo corsi
  - 📄 **PDF**: carica il file con i corsi (funziona anche con file .txt e .csv)

### Step 3 — Analisi Corsi
- Clicca **"Analizza"** per ogni università
- L'AI estrarrà tutti i corsi trovati nelle fonti
- Puoi scaricare il risultato come CSV
- Rianalizza quando vuoi aggiungendo nuove fonti

### Step 4 — Match Learning Agreement
- Seleziona la tua università di casa e una estera
- Clicca **"Trova Match"**
- L'AI confronta i cataloghi e mostra le coppie di corsi sovrapponibili
- Ogni match ha un **punteggio %** e una spiegazione
- Scarica i risultati come **PDF** per condividerli con il tuo coordinatore

---

## 📁 Struttura del progetto

```
erasmus-la-helper/
├── config.py           ← ✏️  INSERISCI QUI LA TUA API KEY
├── app.py              ← Server Flask (backend)
├── index.html          ← Interfaccia grafica (frontend)
├── ai_client.py        ← Astrazione multi-provider AI
├── extractor.py        ← Estrazione testo da URL e PDF
├── analyzer.py         ← Analisi corsi e matching AI
├── pdf_generator.py    ← Generazione PDF report
├── requirements.txt    ← Dipendenze Python
├── start.bat           ← Avvio su Windows
├── start.sh            ← Avvio su macOS/Linux
├── uploads/            ← File caricati dagli utenti
└── output/             ← PDF generati
```

---

## ⚠️ Note importanti

- I match sono **suggerimenti AI**, non approvazioni ufficiali
- Verifica sempre con il tuo coordinatore Erasmus prima di inviare il LA
- La tua API key non viene mai salvata sul disco dal programma
- Per cataloghi molto grandi, l'analisi potrebbe richiedere 1-2 minuti
- Se un URL non funziona, prova a scaricare la pagina come PDF e caricala

---

## 🔧 Requisiti

- Python 3.9 o superiore
- Connessione internet (per le API AI e per scaricare le pagine web)
- Una API key valida di OpenAI, Anthropic o Google

---

## 💡 Suggerimenti

**Fonti migliori da usare:**
- Pagina ufficiale del catalogo corsi dell'università
- PDF del programma dei corsi scaricato dal sito
- Pagina del corso singolo (per corsi specifici)

**Per risultati migliori:**
- Aggiungi più fonti per la stessa università
- Usa un modello potente (gpt-4o, claude-opus) per analisi complesse
- Abbassa la soglia a 50% se non trovi abbastanza match

---

