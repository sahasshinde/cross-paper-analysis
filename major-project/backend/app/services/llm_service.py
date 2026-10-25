"""OPTIONAL wording by a local open-source LLM (Ollama). Nothing here is
needed for the core system; if Ollama is off, the template wording is used."""
import json
import urllib.request
from app import config


def is_enabled():
    return bool(config.OLLAMA_MODEL)


def _post(prompt):
    body = json.dumps({"model": config.OLLAMA_MODEL, "prompt": prompt, "stream": False,
                       "format": "json", "options": {"temperature": 0.2}}).encode()
    req = urllib.request.Request(config.OLLAMA_URL + "/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())["response"]


def build_prompt(statements, n_papers):
    lines = "\n".join(f"{i}. {s['text']}" for i, s in enumerate(statements, 1))
    return (
        f"The statements below come from {n_papers} different research papers. They describe "
        "a related unresolved issue (a limitation or future work).\n"
        "Write ONE concise candidate research gap (at most 25 words) and a one or two sentence "
        "explanation. Use ONLY information found in the statements. Do not add facts, numbers "
        "or claims that are not in them. Do not claim the gap is novel.\n"
        'Answer as JSON: {"title": "...", "explanation": "..."}\n\n'
        f"STATEMENTS:\n{lines}\n")


def generate_gap(statements, n_papers):
    """Returns (title, explanation) or raises if the model output is unusable."""
    data = json.loads(_post(build_prompt(statements, n_papers)))
    title, expl = str(data["title"]).strip(), str(data["explanation"]).strip()
    if not title or len(title) > 220:
        raise ValueError("unusable title")
    return title, expl
