# PDF-Chat mit RAG-Leitfaden – Deployment

Chat-Web-App basierend auf Streamlit und rag_core. Neue Kolleg:innen können Fragen zu einem PDF-Leitfaden stellen, statt das Dokument komplett durchzulesen.

## Schnellstart

### Local Development

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Die App lädt unter `http://localhost:8501`.

### Mit .env konfigurieren

Erstelle eine `.env`-Datei im gleichen Verzeichnis wie `app.py`:

```env
# Automatisch erkannt – einer davon:
OPENROUTER_API_KEY=your_key_here
# oder
ANTHROPIC_API_KEY=your_key_here

# Optional: LLM-Modell wählen (siehe rag_core.py)
RAG_OPENROUTER_MODEL=z-ai/glm-5.3-flash
RAG_ANTHROPIC_MODEL=claude-haiku-5-5

# Optional: Mock-Modus (antwortet ohne LLM)
RAG_MOCK=1
RAG_MOCK_DELAY=3
```

## Deployment

### Streamlit Cloud

1. Repo zu GitHub pushen (`.env` ist in `.gitignore` – nicht committed)
2. [Streamlit Cloud](https://streamlit.io/cloud) → "New app"
3. GitHub repo + `app.py` Pfad wählen
4. Secrets im Dashboard setzen:
   - `OPENROUTER_API_KEY` oder `ANTHROPIC_API_KEY`

### Docker (selbst-gehostet)

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Starten:
```bash
docker build -t rag-chat .
docker run -p 8501:8501 -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY rag-chat
```

### Systemd Service (Linux)

Erstelle `/etc/systemd/system/rag-chat.service`:

```ini
[Unit]
Description=RAG Chat Streamlit App
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/rag-chat
Environment="PATH=/opt/rag-chat/venv/bin"
Environment="ANTHROPIC_API_KEY=your-key-here"
ExecStart=/opt/rag-chat/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable rag-chat
systemctl start rag-chat
```

## Wichtig vor Deployment

### Sicherheit
- ✅ Keine API-Keys im Code (alles über .env)
- ✅ `.env` und `.streamlit/secrets.toml` in `.gitignore`
- ⚠️ **NIEMALS** `.env` committen oder in Git pushen
- ⚠️ Secrets nur über Deployment-Plattform setzen (Streamlit Secrets, Docker ENV, etc.)

### Performance
- PDF wird beim Start indexiert (~2 Sekunden mit Fake-Delay)
- TF-IDF Retrieval ist schnell (Millisekunden)
- LLM-Antwort-Zeit hängt vom Provider ab (OpenRouter/Anthropic)
- Session State bleibt nur während Nutzersession in RAM

### Ressourcen
- **RAM:** ~200 MB für Streamlit + PDF-Index
- **CPU:** Minimal (TF-IDF ist leicht)
- **Disk:** ~1 MB Code, PDF-Größe abhängig (rag_leitfaden.pdf = 71 KB)
- **Netzwerk:** LLM-API-Calls (abhängig von Nutzung)

### Skalierung
- **Single-User:** Reicht ein Basic-Dyno (Heroku) oder t2.micro (EC2)
- **Multi-User:** Streamlit skaliert bedingt – bei >100 Nutzern besser in FastAPI neu bauen
- **Session Persistence:** Derzeit keine (Chat wird nicht gespeichert)

## Fehlerbehandlung in Produktion

| Fehler | Ursache | Lösung |
|--------|--------|--------|
| "Index nicht ladbar" | PDF nicht vorhanden | `data/rag_leitfaden.pdf` prüfen |
| "Kein LLM konfiguriert" | Keine API-Keys | `OPENROUTER_API_KEY` oder `ANTHROPIC_API_KEY` setzen |
| "Timeout" | LLM antwortet nicht | Timeout erhöhen oder Provider wechseln |
| "Keine Quellen gefunden" | PDF zu klein/irrelevant | Frage präzisieren oder PDF austauschen |

## Monitoring

Logs in Streamlit anschauen:
```bash
streamlit run app.py --logger.level=debug
```

### Was überwachen
- **Fehler:** `ERROR` in Logs (Index, LLM, API)
- **Latenz:** Response-Zeit für Fragen (sollte <30s sein)
- **LLM-Kosten:** OpenRouter/Anthropic API-Verbrauch
- **Uptime:** Streamlit-Prozess am Laufen?

## Files

- `app.py` – Streamlit UI
- `rag_core.py` – RAG-Backend (TF-IDF + LLM)
- `data/rag_leitfaden.pdf` – Input-PDF
- `requirements.txt` – Python-Dependencies
- `.gitignore` – Was nicht committed werden darf
- `.env.example` – Template für .env (nicht committen)

## Support

Fragen zu RAG/LLM? Siehe `AGENTS.md` im Kurs-Repo (Modul M07).
