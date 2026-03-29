"""
extractor.py
Estrae testo grezzo da URL (pagine web) e da file PDF.
"""

import os
import re
import requests
from bs4 import BeautifulSoup

try:
    import pdfplumber
    _PDF_LIB = "pdfplumber"
except ImportError:
    try:
        import PyPDF2
        _PDF_LIB = "pypdf2"
    except ImportError:
        _PDF_LIB = None


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}


def extract_from_url(url: str, timeout: int = 20) -> str:
    """Scarica una pagina web e restituisce il testo pulito."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Rimuovi script, stili, navigazione
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        # Riduci righe vuote consecutive
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
    except Exception as e:
        return f"[ERRORE nel recupero dell'URL: {e}]"


def extract_from_pdf(file_path: str) -> str:
    """Estrae il testo da un file PDF."""
    if _PDF_LIB is None:
        return "[ERRORE: nessuna libreria PDF disponibile. Installa pdfplumber o PyPDF2]"

    try:
        if _PDF_LIB == "pdfplumber":
            import pdfplumber
            pages = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        pages.append(t)
            return "\n\n".join(pages).strip()

        else:  # pypdf2
            import PyPDF2
            pages = []
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        pages.append(t)
            return "\n\n".join(pages).strip()

    except Exception as e:
        return f"[ERRORE nella lettura del PDF: {e}]"


def extract_from_file(file_path: str) -> str:
    """Dispatcher: riconosce il tipo di file e chiama l'estrattore corretto."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_from_pdf(file_path)
    elif ext in (".txt", ".md", ".csv"):
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    else:
        return f"[Tipo di file non supportato: {ext}]"
