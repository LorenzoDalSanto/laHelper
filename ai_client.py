"""
ai_client.py
Astrazione multi-provider: OpenAI / Anthropic / Google Gemini

Fix: il client OpenAI viene costruito con un httpx.Client esplicito
senza proxies, per evitare il crash:
  "Client.__init__() got an unexpected keyword argument 'proxies'"
che si verifica quando requests/httpx leggono le variabili d'ambiente
HTTP_PROXY / HTTPS_PROXY e cercano di passarle al costruttore.
"""

import sys


def get_completion(prompt: str, system: str = "", api_key: str = "",
                   provider: str = "openai", model: str = "gpt-4o") -> str:
    provider = provider.lower().strip()
    if provider == "openai":
        return _openai(prompt, system, api_key, model)
    elif provider == "anthropic":
        return _anthropic(prompt, system, api_key, model)
    elif provider in ("google", "gemini"):
        return _google(prompt, system, api_key, model)
    else:
        raise ValueError(f"Provider non supportato: '{provider}'. Usa openai, anthropic o google.")


# ── OpenAI ────────────────────────────────────────────────────────────────────

def _openai(prompt: str, system: str, api_key: str, model: str) -> str:
    try:
        from openai import OpenAI
        import httpx
    except ImportError:
        raise ImportError("Pacchetto 'openai' non installato. Esegui: pip install openai httpx")

    # Crea un httpx.Client esplicito senza proxies.
    # Questo evita il bug "unexpected keyword argument 'proxies'" causato da
    # versioni di httpx che leggono HTTP_PROXY dalle variabili d'ambiente
    # e cercano di passarle al costruttore OpenAI.
    http_client = httpx.Client(
        timeout=httpx.Timeout(120.0),
        follow_redirects=True,
    )

    client = OpenAI(api_key=api_key, http_client=http_client)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        max_tokens=4096,
    )
    return response.choices[0].message.content.strip()


# ── Anthropic ─────────────────────────────────────────────────────────────────

def _anthropic(prompt: str, system: str, api_key: str, model: str) -> str:
    try:
        import anthropic
        import httpx
    except ImportError:
        raise ImportError("Pacchetto 'anthropic' non installato. Esegui: pip install anthropic httpx")

    http_client = httpx.Client(
        timeout=httpx.Timeout(120.0),
        follow_redirects=True,
    )

    client = anthropic.Anthropic(api_key=api_key, http_client=http_client)
    kwargs = dict(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    if system:
        kwargs["system"] = system

    response = client.messages.create(**kwargs)
    return response.content[0].text.strip()


# ── Google Gemini ─────────────────────────────────────────────────────────────

def _google(prompt: str, system: str, api_key: str, model: str) -> str:
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("Pacchetto 'google-generativeai' non installato. Esegui: pip install google-generativeai")

    genai.configure(api_key=api_key)
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    gemini = genai.GenerativeModel(model)
    response = gemini.generate_content(full_prompt)
    return response.text.strip()
