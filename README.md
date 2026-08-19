# NexusMed 2077

NexusMed 2077 is a bilingual (English/Farsi) medical assistant that runs entirely
on your own computer. No account, no cloud, no telemetry. It has two frontends: a
desktop app written in Tkinter, and a local web app served at
`http://localhost:2077` (if that port is busy, it keeps trying 2078 through 2087
until it finds a free one).

English is the default language. One button in the header switches the whole
thing to Farsi and back - the choice is saved, applies without a restart, and
covers the interface, the assistant's answers, the offline engine, red flag
warnings, lab interpretations, drug notes and the printed referral report.
Symptom detection itself is bilingual too, so "chest pain" and "درد قفسه سینه"
are understood the same way.

The core of the project is a hybrid engine.

When an external provider is configured (OpenRouter, OpenAI or DeepSeek), the
assistant talks to that model. When nothing is configured, or the network is down,
an offline engine takes over. The offline side is not a chatbot that makes things
up: it is a small hand-written knowledge base of common conditions, a Bayesian
scoring engine, a scikit-learn classifier, a TF-IDF retrieval layer over the local
knowledge, and a clinical dialogue manager that asks one question at a time. Answers
come out in plain conversational Persian, the way a careful doctor would explain
things.

Every exchange with an external model is also recorded on the spot. The program
saves the topic, the symptoms that came up, the advice that was given and the
follow-up questions into `learned_knowledge.json`, and it builds a style profile
(`ai_behavior_profile.json`) from the wording, section layout and bullet habits of
those answers. Later, when no external AI is reachable, the offline engine formats
its own answers using that learned tone and structure.

To be precise about what that imitation means, because it matters in a medical
tool: it copies tone, empathy, section order and formatting only. It never reuses
or invents medical facts, and emergency answers are never rewritten by the style
layer. Learning also runs in the background even when the offline brain is switched
off in the settings, so the assistant keeps getting familiar with how you and your
model talk.

## Safety rules

A few things are hardcoded and cannot be turned off:

- Every message is screened for red flag symptoms before anything else: chest pain,
  severe shortness of breath, heavy bleeding, unconsciousness, seizure, sudden
  weakness or paralysis, slurred speech, facial droop, decreased consciousness, very
  high or persistent fever, and sudden severe pain. If one of these is found, normal
  assessment stops immediately and the assistant gives emergency instructions
  instead (115 in Iran, 112 in Europe).
- It never gives a definitive diagnosis. Probabilities are labelled as possible and
  exist for prioritization, not for conclusions.
- No medication is presented as a final decision; drug information always goes back
  to "prescribed by your doctor".
- If there is not enough information, it asks a follow-up question instead of
  guessing, and fields without a trusted source stay empty.

This software is not a doctor and does not replace one. If you think you are having
an emergency, stop reading and call emergency services.

## Running from source

You need Python 3.10 or newer.

    pip install -r requirements.txt
    python run_2077.py        # desktop app
    python run_web.py         # web app at http://localhost:2077

I kept the dependency list short on purpose: requests, Pillow, numpy, scikit-learn
and pyinstaller. The desktop UI is plain Tkinter and the web server is the standard
library `http.server`, so there is no Node, no Electron and no web framework
anywhere in the project.

## Connecting an AI provider

Open the settings from inside the app (the settings button in the header on either
frontend). Paste your key, press Test, press Save. Changes apply immediately, no
restart needed. Persian status messages tell you exactly what happened: connection
ok, invalid key, model not found, not enough credit, rate limited, or no internet.

Keys are written to a local `.env` file and never end up in the code, in the ZIP or
in the installer. A free OpenRouter key can be created at openrouter.ai/keys.

The default model is `openai/gpt-oss-120b:free`, with
`qwen/qwen3-next-80b-a3b-instruct:free` as an automatic fallback. Optional reasoning
support is off by default, since not every model handles it and it burns tokens.

Ollama works too, if you prefer fully local inference. Default setup is
`qwen2.5:7b-instruct` at `localhost:11434`, configurable from the local AI panel.

## What is included

- Patient profile with conditions and allergies, stored in `patient_profile.json`
- Vitals tracking with BMI and blood pressure categories, plus a history log
- Lab interpretation for the common tests (CBC, FBS, HbA1c, lipids, TSH, enzymes,
  electrolytes, iron, vitamin D and more) with Persian explanations and critical
  value alerts. Reference ranges differ between labs, and the tool says so.
- Prescription scanner: translates shorthand like BID, TID, PO, PRN, AC, QHS, WBC,
  FBS, TSH into Persian and checks what it finds against your allergy list
- Drug and herbal interaction checker with around 45 entries. Small on purpose; a
  short honest list beats a long wrong one.
- PHQ-9 and GAD-7 screeners with a hard crisis path on question 9, plus a guided
  breathing exercise
- Sleep screening with STOP-BANG and a simplified PSQI
- Checkup and vaccine suggestions based on age and sex, with local reminders
- First aid guides (CPR, heart attack, stroke, choking, burns, seizure, bleeding)
  including a CPR metronome at 110 beats per minute
- Medical image analysis with a text note: uses a vision model when one is
  configured, and answers honestly that it cannot diagnose an image offline when
  one is not
- A printable referral report for your doctor, generated as `referral_report.html`

## The dataset

`medical_ml_test_dataset.csv` holds 1000 synthetic rows for testing machine learning
approaches. It is produced by `generate_dataset.py`. The `dataset_note` column reads
`synthetic_for_ml_testing_not_clinical`, and that is exactly what it means: use it
to test pipelines, never for anything clinical.

## Building the Windows installer

This part has to happen on Windows, with Python 3.10+ and Inno Setup 6 installed.
Then double-click:

    Create_Setup_Installer.bat

It installs the requirements, compiles every Python file as a sanity check, builds
the executable with PyInstaller, and hands the result to Inno Setup. You end up
with:

    Output\NexusMed_Setup_v2.0.exe

That installer is self-contained, so target machines do not need Python. The repo
root also has a step-by-step guide (`BUILD_SETUP_GUIDE.txt`) with troubleshooting
for the usual problems: PATH not set, Inno Setup not found, antivirus complaining
about PyInstaller builds, busy ports.

## Files that never leave your machine

`.env`, `patient_profile.json`, `vitals_history.json`, `learned_knowledge.json`,
`ai_behavior_profile.json`, `local_llm_config.json`, `referral_report.html` and
`reminders.json` hold either secrets or personal data. They are excluded from the
ZIP, from the installer and from git. Keep it that way.

## License and disclaimer

Provided as is, no warranty. This is an informational and educational tool, not a
medical device, and it makes no claim of clinical accuracy. For anything that
matters, see a doctor.
