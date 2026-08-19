# 🤖 NexusMed 2077 — دستیار هوشمند پزشکی فارسی

**نکسوس ۲۰۷۷** یک دستیار پزشکی هوشمند فارسی‌زبان است که هم به‌صورت **دسکتاپ (Tkinter)** و هم **وب محلی (localhost:2077)** اجرا می‌شود و ترکیبی از:

- 🌐 **AI خارجی**: OpenRouter (مدل‌های رایگان) / OpenAI / DeepSeek — با تست اتصال فارسی و بدون نیاز به ری‌استارت
- 🧠 **مغز داخلی آفلاین**: پایه‌ی دانش بیماری‌ها، استدلال بیزین، طبقه‌بند ML (scikit-learn)، RAG داخلی، مکالمه‌ی بالینی قدم‌به‌قدم
- 🧬 **یادگیری خودکار**: هر پاسخ AI خارجی → `learned_knowledge.json` + `ai_behavior_profile.json` (حتی وقتی مغز داخلی خاموش است)
- 🎭 **تقلید رفتار**: مغز داخلی فقط «لحن/ساختار/همدلی» پاسخ‌های AI خارجی را تقلید می‌کند — هرگز محتوای پزشکی جعلی نمی‌سازد
- 🚨 **سلامت‌محور**: بررسی ۱۳ علامت خطر قبل از هر تشخیص؛ پاسخ اورژانسی فوری؛ بدون تشخیص قطعی

## ⚡ اجرای سریع (از سورس)

```bash
pip install -r requirements.txt
python run_2077.py        # دسکتاپ
python run_web.py         # یا وب: http://localhost:2077
```

## 📦 ساخت فایل نصبی ویندوز

روی ویندوز: `Python 3.10+` و `Inno Setup 6` را نصب کنید و دوبار کلیک کنید روی:

```
Create_Setup_Installer.bat   →   Output\NexusMed_Setup_v2.0.exe
```

جزئیات کامل: فایل `راهنمای_ساخت_فایل_نصبی_NexusMed_2077.txt`

## 🔑 کلید API

از داخل برنامه: **⚙️ تنظیمات API** → کلید OpenRouter را از [openrouter.ai/keys](https://openrouter.ai/keys) بگیرید و وارد کنید → تست اتصال → ذخیره. کلیدها فقط در `.env` روی سیستم شما ذخیره می‌شوند (نمونه: `.env.example`). هیچ کلیدی داخل کد/ZIP/Setup نیست.

## 🧰 ماژول‌ها

پروفایل بیمار • علائم حیاتی (BMI/فشار خون) • تحلیل آزمایش (FBS/CBC/TSH/چربی…) • اسکن نسخه (BID/TID/PO/PRN…) • دارو و تداخلات (۴۵+ دارو/گیاه) • سلامت روان (PHQ-9/GAD-7/تنفس) • تحلیل خواب (STOP-BANG/PSQI) • تقویم چکاپ و واکسن • کمک‌های اولیه + مترونوم CPR ۱۱۰BPM • تحلیل تصویر پزشکی + متن • گزارش ارجاع قابل چاپ • هوش محلی Ollama • دیتاست مصنوعی ۱۰۰۰ ردیفی برای تست ML

## 📁 ساختار

```
run_2077.py  run_web.py  ui_2077.py  clinic_2077.html
hybrid_engine.py  medical_engine.py  ai_client.py  ai_api_manager.py  free_ai.py
auto_learning.py  behavior_imitation.py  semantic_rag.py  bayesian_engine.py
ml_classifier.py  medical_nlg.py  clinical_dialogue.py  image_caption.py  local_llm.py
patient_profile.py  health_vitals.py  drug_interaction.py  first_aid.py
mental_health.py  checkup_calendar.py  lab_visualizer.py  lab_tests.py  lab_catalog.py
prescription_scanner.py  doctor_referral.py  sleep_analyzer.py
build_exe.py  Create_Setup_Installer.bat  NexusMed_Installer.iss
medical_ml_test_dataset.csv (synthetic_for_ml_testing_not_clinical)
```

> ⚠️ **سلب مسئولیت**: این نرم‌افزار جایگزین پزشک نیست، تشخیص قطعی نمی‌دهد و دارو تجویز نمی‌کند. اورژانس: ایران **۱۱۵** — اروپا/فنلاند **۱۱۲**.
