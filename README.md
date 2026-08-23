# NexusMed 2077

This is my own medical assistant project. The whole point of it: everything runs on
*your* computer. No account, no cloud, nothing phoning home. I'm a Persian speaker
so the app is bilingual — one button in the header flips the entire thing between
Farsi and English, and it even understands symptoms in both languages ("chest
pain" or its Persian equivalent are treated the same way).

There are two frontends sharing one engine:

- a **desktop app** in plain Tkinter (I deliberately avoided heavy UI libraries)
- a **local web app** — a small server that opens at `http://localhost:2077`
  (if the port is busy it just tries 2078 up to 2087 until one is free)

Quick start:

```
pip install -r requirements.txt
python run_2077.py     # desktop
python run_web.py      # web
```

On Windows you can just run `START.bat` and pick. I've kept dependencies short on
purpose — requests, Pillow, numpy, scikit-learn. No Node, no Electron, no web
framework; the web server is Python's own `http.server`.

## How it answers

The engine is a hybrid. If you plug in an external AI key (OpenRouter, OpenAI or
DeepSeek) it talks to that model first. No key or no internet? An offline engine I
wrote myself takes over: a hand-built knowledge base of common conditions, Bayesian
scoring, a small scikit-learn classifier and TF-IDF retrieval over the local
knowledge. I made sure it doesn't invent things — if it has no trusted source for
something, the field stays empty, and when there isn't enough information it asks a
follow-up question instead of guessing.

One feature I care about: every time the external AI answers, the program learns
from it on the spot — the topic, symptoms, advice, even the tone and section layout.
Later, when the AI is unreachable, the offline brain formats its own answers in that
learned style. To be clear about what that means in a medical tool: it copies style
only, never medical facts, and emergency answers are never rewritten.

## Modules

Things got added over time as I needed them:

- **Talk** — the main chat, with automatic symptom detection
- **Symptoms** — every symptom in the program as a checklist. Tick what you have,
  hit Analyze, and it ranks likely conditions with percentages and urgency.
  There's also the full HPO vocabulary here (~19,800 medical signs) for lookup
- **Diseases** — the 104 conditions the diagnostic engine knows, the full
  ICD-10-CM catalog (27,168 entries), the Human Disease Ontology (14,762 with
  definitions) and every Wikidata disease with its Persian name, symptoms and
  treatments. That's roughly 45k disease records behind one search box.
  Persian queries work too - "diabetes" or "high blood pressure" typed in
  Persian both work, and so does a code like E11
- **Drugs** — 189 curated drugs with interactions in Persian, plus the complete FDA
  bank with 19,149 drugs. Many of them also carry the official FDA label sections
  (indications, warnings, adverse reactions, boxed warning)
- **Research** — live search in PubMed, ClinicalTrials.gov, the FDA FAERS
  adverse-event database and RxNorm. This one needs internet; the rest doesn't
- Lab interpretation for the common tests (CBC, glucose, thyroid, lipids, vitamin D
  ...) with reference ranges and critical-value alerts
- Prescription scanner — expands shorthand like BID, PO, PRN into Persian and
  checks them against your allergy list
- Medical image analysis, vitals tracking, PHQ-9/GAD-7 screeners, sleep screening,
  a checkup calendar, first aid guides with a 110 bpm CPR metronome, a printable
  referral report for your doctor, and a local-AI (Ollama) panel

## Where the data comes from

Everything bundled with the app is open, official data stored offline: the FDA NDC
directory and official drug labels (openFDA), the ICD-10-CM catalog from CMS, and
Persian names from Wikidata. Four services are queried live when online: PubMed,
ClinicalTrials.gov, FAERS and RxNorm. When I want to refresh the local banks I run
`build_fda_drugs.py` and `build_drug_labels.py`.

## Connecting an AI (optional)

Open settings inside the app, paste the key, press Test, press Save — no restart
needed. The key goes into a local `.env` file only. It never enters the code, the
ZIP or the installer, and `.gitignore` keeps it out of git for good. I use
OpenRouter myself since it has free models; the current default is
`nvidia/nemotron-3-super-120b-a12b:free` and a few more free models are listed in
settings. If a free model happens to be busy, the app quietly falls back to the
offline brain.

If you run Ollama, the local-AI panel is ready for it — default
`qwen2.5:7b-instruct` on port 11434.

## Safety rules

Some things I hardcoded and they cannot be turned off:

- every message is screened for red flags first (chest pain, severe breathlessness,
  heavy bleeding, unconsciousness, seizure, sudden weakness, slurred speech ...).
  If one shows up, everything else stops and you get emergency instructions
  (115 in Iran, 112 in Europe)
- it never gives a definitive diagnosis; the percentages exist for prioritization
- drug info always comes back to "as prescribed by your doctor"

This software is not a doctor and doesn't replace one. Think you're having an
emergency? Stop reading and call.

## Building the Windows installer

I build it on Windows with Python 3.10+ and Inno Setup 6: run
`Create_Setup_Installer.bat`. It installs the requirements, compiles every Python
file as a sanity check, builds with PyInstaller, then Inno Setup produces
`Output\NexusMed_Setup_v2.0.exe`. A step-by-step guide with the usual
troubleshooting lives in `BUILD_SETUP_GUIDE.txt`.

## Files that never leave your machine

`.env`, `patient_profile.json`, `vitals_history.json`, `learned_knowledge.json`,
`ai_behavior_profile.json` and friends hold secrets or personal data. They're
excluded from git, from the ZIP and from the installer — keep it that way.

The `medical_ml_test_dataset.csv` file is 1000 synthetic rows generated by
`generate_dataset.py` for testing ML pipelines. Not for anything clinical.

## License

Provided as is, no warranty. This is an educational/informational tool, not a
medical device. For anything that matters, see a doctor.
