# GTA 6 ClipBot

Schaut mehrere Twitch-Streams gleichzeitig, erkennt Hype-Momente (Chat-Spike), schneidet den Clip
(25s davor, 10s danach) und rendert ihn als **1080x1920 (9:16)** mit unscharfem Hintergrund und
Streamer-Credit. Ergebnis landet in `out/ready/` als `.mp4` + `.json` (Caption, Quelle).

## Setup
```
sudo apt install ffmpeg && pip install streamlink pytest
# config.toml: Streamer eintragen (nur mit deren Erlaubnis!)
python -m clipbot run --config config.toml
python -m clipbot render input.mp4 output.mp4   # Einzeltest 9:16
python -m pytest tests
```

## Wie es funktioniert
1. `chat.py` liest anonym den Twitch-Chat (nur Nachrichtentext, **keine Usernamen, nichts wird gespeichert**).
2. `detector.py` zaehlt gewichtete Nachrichten (Hype-Woerter, "GTA 6") und triggert bei Spike ueber dem Normalniveau.
3. `recorder.py` haelt pro Stream einen Rolling-Buffer (streamlink -> ffmpeg), alte Segmente werden geloescht.
4. `render.py` schneidet + konvertiert in 9:16.

## Rechtliches (kein Rechtsrat)
- **Urheberrecht**: Streams gehoeren den Streamern (und Rockstar/Take-Two fuer das Spiel). Ohne Erlaubnis
  hochladen kann zu Takedowns/Strikes fuehren. -> Schriftliche Erlaubnis einholen, Streamer immer credit'en.
- **Datenschutz/DSGVO**: Der Bot speichert keine Chat-Usernamen oder -Texte, nur Zaehlwerte im Speicher. Verarbeite in Clips
  keine Chat-Overlays/Facecams von Dritten ohne Einwilligung.
- **Plattform-AGB**: Twitch erlaubt kein massenhaftes Re-Streaming ohne Genehmigung; TikTok verlangt Rechte am Content.
- **Kein Auto-Upload**: Clips haben `"approved": false`. Du pruefst jeden Clip manuell vor dem Posten
  (TikToks Upload-API braucht ohnehin eine App-Freigabe).
