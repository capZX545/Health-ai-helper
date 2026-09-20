# NexusMed 2077 — Review Guide / راهنمای بازبینی

Excellence from here on is not more code — it is **verified accuracy and real usage**.
This document is the hand-off package: what a doctor should check, what a real user should test, and how to put the app online.

عالی‌شدن از اینجا به بعد کد نیست — **تأیید صحت و استفاده‌ی واقعی** است. این سند بسته‌ی تحویل است: پزشک چه چیزهایی را بررسی کند، کاربر واقعی چه چیزهایی را بسنجد، و برنامه چطور آنلاین شود.

---

## 1. Doctor review checklist / چک‌لیست بازبینی پزشک

Priority: **P1** = wrong content could harm → review first. **P2** = review when possible.

| # | File (فایل) | Content (محتوا) | Basis (مبنای فعلی) | Verify (چه چیزی بررسی شود) | Pri |
|---|------|-----------|--------|--------|-----|
| 1 | `medical_engine.py` | 12 emergency red-flag triggers, 104 diseases, urgency levels, 81 symptom keywords | hand-built |红线触发条件是否完整、阈值是否符合当地指南 (Iran 115 practice) | P1 |
| 2 | `renal_dosing.py` | 30 drug rules: cutoffs (30/60), messages for kidney impairment | FDA labels + common references | دوز و آستانه‌های هر دارو؛ داروی پر مصرف جاافتاده؟ | P1 |
| 3 | `risk_scores.py` | Framingham ATP-III point tables + FINDRISC scoring | NCEP ATP III tables, FINDRISC (validated) | فقط صحت جدول‌ها را تأیید کنید — فرمول‌ها با وکتور تست شده‌اند | P1 |
| 4 | `vaccine_schedule.py` | Iran EPI: 7 visits, birth to 6 years | برنامه‌ی ایمن‌سازی ۱۴۰۳ (وزارت بهداشت) | هماهنگی با آخرین ابلاغیه‌ی کمیته‌ی ایمن‌سازی | P1 |
| 5 | `pregnancy_tracker.py` | 40-week guide, trimester danger signs, cycle/fertile estimates | standard obstetric references | علائم خطر هر سه‌ماهه؛ پیام‌های هفته‌به‌هفته | P1 |
| 6 | `family_risk.py` | 9 screening rules (colon, breast, ovarian, cardiac, diabetes, glaucoma, osteoporosis, stroke, prostate) | USPSTF-style general guidance | سن شروع و فاصله‌ی غربالگری‌ها با نظر local guidelines | P1 |
| 7 | `medical_qa.py` | 50 curated bilingual Q&A (BP, glucose, HbA1c, lipids, TSH, B12, ferritin, WBC, creatinine, electrolytes, liver, CRP, pregnancy test, folic acid, fever adult/child, paracetamol/ibuprofen dosing, antibiotics misuse, water/sleep/exercise/salt/caffeine, BMI/waist, smoking cessation, headache red flags, dizziness, leg swelling, epistaxis, diarrhea, constipation, heartburn, UTI, kidney stone, back pain, tetanus, rabies, honey-infant, weight-loss rate, colonoscopy age) | WHO / standard patient-education sources | دوزها و آستانه‌ها؛ لحن توصیه‌ها | P1 |
| 8 | `first_aid.py` | 7 topics (CPR, choking, bleeding, burns, seizure, poisoning, fainting) + 110 bpm metronome | AHA-style lay guidance | عمق فشردگی، نرخ، نکات قطع فیزیکی | P1 |
| 9 | `mental_health.py` | PHQ-9 / GAD-7 scoring bands + crisis resources | standard instrument scoring | باندهای نمره و مسیر ارجاع | P1 |
| 10 | `health_tools.py` | pregnancy categories, dose calculators, growth percentiles | standard pediatric references | صدک‌های رشد و دسته‌های بارداری | P2 |
| 11 | `lab_catalog.py` + `lab_full.py` | 32 + 96 test reference ranges and critical values | typical lab ranges | محدوده‌ی مرجع آزمایشگاه‌های ایران اگر متفاوت است | P2 |
| 12 | `drug_interaction.py` | 189 curated drugs, interaction pairs, allergy lists | curated bilingual bank | جفت‌های تداخل پر مصرف | P2 |
| 13 | `knowledge_browser.py` | 44,990 diseases (ICD-10 27,168 / DOID 14,762 / Wikidata 6,346), auto-generated About/Symptoms/Meds/Treatment | public datasets (NLM, DOID, Wikidata, FDA) | محتوای تولیدشده خودکار را نمونه‌گیری کنید؛ منبع در هر پروفایل ذکر شده | P2 |
| 14 | `side_effect_checker.py` | matches symptoms against 14,259 FDA label adverse-reaction sections | official FDA labels (offline bank) | ریسک مثبت کاذب/منفی کاذب روی ۱۰ داروی پر مصرف | P2 |
| 15 | `doctor_referral.py` | referral report structure and recommended workup lines | — | آزمایش‌های پیشنهادی هر سناریو | P2 |

**How to review efficiently / بازبینی سریع:** open each file, the content is in plain data structures at the top (`_QA`, `_DRUGS`, `_RULES`, `SCHEDULE`, `_WEEKS`, `RED_FLAGS`, `DRUGS`). Suggested edits as a simple list of `file → item → correct value`; the developer applies them in one commit.

---

## 2. Real-user test plan / برنامه‌ی تست با کاربر واقعی (1 week, 3-5 users)

- Day 1: onboarding wizard + profile + language switch — does a non-technical user get through without help?
- Day 2-3: daily chat use — log every wrong/absurd/confusing answer (screenshot + the exact message)
- Day 3: log one vital + one lab + one medication reminder; export the .ics into their phone calendar
- Day 4: emergency dry-run — say "درد قفسه سینه" — is the response fast, clear, correct number shown?
- Day 5: elder mode with one senior user; voice read-aloud on Windows
- Day 6: ICE card + health passport — print it, show to a nurse/pharmacist, note their reaction
- Day 7: collect: top 3 confusions, top 3 wrong answers, top 3 missing wishes → one issue list

**Metric of "excellent": a user completes symptom→triage→lab→referral-report without any explanation from you.**

---

## 3. Put it online / آنلاین‌کردن (5 minutes)

1. Go to render.com → sign up with GitHub → New → Web Service → pick `Health-ai-helper`
2. Render auto-detects the `Dockerfile` (already in the repo) → keep defaults (port 2077) → Create
3. You get a public `https://....onrender.com` link — free tier is enough
4. Optional: set `NEXUSMED_PUBLIC=1` env var to show the public footer

Files already prepared: `Dockerfile`, `render.yaml`, `DEPLOY.md`.
Public link ≠ local data: the web version keeps each user's data on the server it runs on — for a truly public deployment, enable HTTPS only and rebuild trust boundaries first (currently designed personal/single-family).

---

## 4. Version inventory / انبار نسخه‌ها (what "excellent" already includes)

- v8.0.0: Framingham + FINDRISC, Cockcroft-Gault + 30 renal rules, FDA side-effect checker (in-chat), Iran vaccination, ICE card + QR, voice I/O, smartwatch CSV import, ChaCha20 vault, auto-updater
- v9.0.0: GPT-style streaming (desktop+web), lab-photo OCR (Windows engine), symptom-vitals correlator, period tracker + 40-week pregnancy guide, family-history screening, second opinion, health passport, encrypted single-file backup, elder mode
- v9.1.0: 50-answer curated QA brain, onboarding wizard, .ics calendar export, deploy badge

**Status: 54/54 automated module tests · bilingual audit clean · ~20,900 lines of Python · Windows EXE + Android APK + local web + PWA.**
