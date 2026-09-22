"""
module_info.py — single source of module metadata for the home dashboard:
bilingual names, full descriptions (shown on hover) and web-panel key
mapping. Used by the desktop dashboard and embedded into the web UI.
"""
from __future__ import annotations

from typing import Any

ORBIT_KEYS = ["symptoms", "diseases", "drugsdb", "labs", "risk", "pregnancy",
              "sidefx", "tools", "chat", "renal", "vaccine", "brain", "passport"]

MODULE_INFO: dict[str, dict[str, Any]] = {
    "home": {
        "en": "Home", "fa": "خانه",
        "d_en": "Animated dashboard of all modules — hover any tile for its full description, click to open.",
        "d_fa": "داشبورد متحرک همه‌ی ماژول‌ها — روی هر خانه ماوس را ببر تا توضیح کاملش را ببینی، کلیک کن تا باز شود.",
        "web": None},
    "chat": {
        "en": "Talk to Nexus", "fa": "گفتگو با نکسوس",
        "d_en": "The main chat. Describe symptoms in Farsi or English; answers stream live. Emergency signs get immediate guidance. Works offline, with LM Studio, or with cloud AI keys.",
        "d_fa": "چت اصلی. علائم را فارسی یا انگلیسی بنویس؛ جواب‌ها زنده و استریمی می‌آیند. علائم اورژانسی فوراً راهنمایی می‌گیرند. آفلاین، با LM Studio یا با کلید ابری کار می‌کند.",
        "web": "chat"},
    "image": {
        "en": "Medical image analysis", "fa": "تحلیل تصویر پزشکی",
        "d_en": "Attach X-rays, skin photos or ECG strips: type detection, offline analysis and AI captioning with red-flag checks.",
        "d_fa": "عکس رادیولوژی، ضایعه‌ی پوستی یا نوار قلب بفرست: تشخیص نوع تصویر، تحلیل آفلاین و توضیح هوشمند با بررسی علائم خطر.",
        "web": "image"},
    "profile": {
        "en": "Patient profile", "fa": "پروفایل بیمار",
        "d_en": "Name, age, weight, conditions, allergies and medications. Everything the assistant knows about you — used in every analysis, interaction check and report.",
        "d_fa": "نام، سن، وزن، بیماری‌ها، حساسیت‌ها و داروها. همه‌چیزی که دستیار درباره‌ی تو می‌داند — در هر تحلیل، بررسی تداخل و گزارش استفاده می‌شود.",
        "web": "profile"},
    "vitals": {
        "en": "Vitals", "fa": "علائم حیاتی",
        "d_en": "Record blood pressure, pulse, glucose, weight, oxygen and temperature with instant categorization (BMI, BP stages) and a growing history.",
        "d_fa": "ثبت فشار، ضربان، قند، وزن، اکسیژن و دما با دسته‌بندی لحظه‌ای (BMI، مراحل فشار) و تاریخچه‌ی رو به رشد.",
        "web": "vitals"},
    "charts": {
        "en": "Vitals charts", "fa": "نمودار روند",
        "d_en": "Trend charts of blood pressure, glucose and weight from your recorded history — see the direction of your numbers.",
        "d_fa": "نمودار روند فشار خون، قند و وزن از تاریخچه‌ی ثبت‌شده — جهت تغییر اعدادت را ببین.",
        "web": "charts"},
    "labs": {
        "en": "Lab analysis", "fa": "تحلیل آزمایش",
        "d_en": "Paste lab lines like FBS 132 / Hb 10.5 / TSH 6.2 and get interpretation with reference ranges, critical-value alerts and diet advice. Photo OCR on Windows.",
        "d_fa": "خطوط آزمایش را بچسبان مثل FBS 132 / Hb 10.5 / TSH 6.2 و تفسیر با محدوده‌ی مرجع، هشدار مقادیر بحرانی و توصیه‌ی تغذیه بگیر. عکس آزمایش روی ویندوز OCR می‌شود.",
        "web": "labs"},
    "lab": {
        "en": "Laboratory", "fa": "آزمایشگاه",
        "d_en": "Catalog of 96 lab tests: sample type, preparation, reference ranges and what abnormal results mean.",
        "d_fa": "کاتالوگ ۹۶ آزمایش: نوع نمونه، آمادگی، محدوده‌ی مرجع و معنای نتایج غیرطبیعی.",
        "web": "lab"},
    "rx": {
        "en": "Prescription scan", "fa": "اسکن نسخه",
        "d_en": "Expands prescription shorthand (BID, PO, PRN) into plain language and checks the drugs against your allergy list.",
        "d_fa": "مخفف‌های نسخه (BID، PO، PRN) را به زبان ساده باز می‌کند و داروها را با لیست حساسیتت چک می‌کند.",
        "web": "rx"},
    "drugs": {
        "en": "Drugs & interactions", "fa": "دارو و تداخلات",
        "d_en": "189 curated drugs with Persian names: search, interaction checking (A-B) and allergy warnings.",
        "d_fa": "۱۸۹ داروی منتخب با نام فارسی: جستجو، بررسی تداخل دو دارو و هشدار حساسیت.",
        "web": "drugs"},
    "drugsdb": {
        "en": "Drugs database", "fa": "بانک داروها",
        "d_en": "The complete FDA bank: 19,149 drugs, many with official label sections (uses, warnings, adverse reactions, boxed warning).",
        "d_fa": "بانک کامل FDA: ۱۹,۱۴۹ دارو، بسیاری با بخش‌های رسمی برچسب (کاربرد، هشدارها، عوارض، هشدار جعبه‌ای).",
        "web": "drugs_browser"},
    "sidefx": {
        "en": "Drug side effects", "fa": "عارضه دارویی",
        "d_en": "Is this new symptom a side effect of my medication? Checks 14,259 FDA labels offline — and answers the same question inside the chat.",
        "d_fa": "این علامت جدید عارضه‌ی داروی من هست؟ ۱۴,۲۵۹ برچسب FDA را آفلاین بررسی می‌کند — و همین سؤال را داخل چت هم جواب می‌دهد.",
        "web": "sidefx"},
    "renal": {
        "en": "Renal dosing", "fa": "دوز کلیوی",
        "d_en": "Creatinine clearance (Cockcroft-Gault) with kidney-function bands and dose-adjustment warnings for 30 common drugs.",
        "d_fa": "کلیرانس کراتینین (کاککرافت-گالت) با دسته‌بندی عملکرد کلیه و هشدار تنظیم دوز برای ۳۰ داروی رایج.",
        "web": "renal"},
    "risk": {
        "en": "Risk scores", "fa": "ریسک قلب و دیابت",
        "d_en": "Validated calculators: Framingham 10-year heart risk and FINDRISC 10-year diabetes risk, with point breakdown and plain-language advice.",
        "d_fa": "ماشین‌حساب‌های معتبر: ریسک ۱۰ ساله‌ی قلبی فرامینگهام و ریسک دیابت FINDRISC، با تفکیک امتیاز و توصیه‌ی ساده.",
        "web": "risk"},
    "assess": {
        "en": "Disease likelihood", "fa": "ارزیابی احتمال بیماری",
        "d_en": "Type your symptoms and get ranked likely conditions with percentages and urgency, combining Bayesian scoring and a trained classifier.",
        "d_fa": "علائمت را بنویس و بیماری‌های محتمل را با درصد و فوریت مرتب‌شده بگیر — ترکیب امتیازدهی بیزی و طبقه‌بند آموزش‌دیده.",
        "web": "assess"},
    "symptoms": {
        "en": "Symptoms checklist", "fa": "علائم (تیک و تحلیل)",
        "d_en": "240 common symptoms as a checklist: tick what you have and analyze — plus the full HPO vocabulary (~19,800 signs) for lookup.",
        "d_fa": "۲۴۰ علامت رایج به‌صورت چک‌لیست: تیک بزن و تحلیل کن — به‌علاوه‌ی واژگان کامل HPO (حدود ۱۹,۸۰۰ نشانه) برای جستجو.",
        "web": "symptoms_browser"},
    "diseases": {
        "en": "Diseases database", "fa": "بانک بیماری‌ها",
        "d_en": "44,990 diseases behind one search box: ICD-10 (27,168), Disease Ontology (14,762) and Wikidata (6,346) with full profiles — About, Symptoms, Medications, Treatment — in both languages.",
        "d_fa": "۴۴,۹۹۰ بیماری پشت یک جستجو: ICD-10 (۲۷,۱۶۸)، آنتولوژی بیماری (۱۴,۷۶۲) و ویکی‌دیتا (۶,۳۴۶) با پروفایل کامل — درباره، علائم، داروها، درمان — به هر دو زبان.",
        "web": "diseases_browser"},
    "research": {
        "en": "Research & articles", "fa": "پژوهش و مقالات",
        "d_en": "Live search in PubMed, ClinicalTrials.gov, the FDA adverse-event database and RxNorm (needs internet; everything else works offline).",
        "d_fa": "جستجوی زنده در PubMed، ClinicalTrials.gov، بانک عوارض FDA و RxNorm (اینترنت می‌خواهد؛ بقیه‌ی برنامه آفلاین کار می‌کند).",
        "web": "research"},
    "tools": {
        "en": "Health tools", "fa": "ابزار سلامت",
        "d_en": "Unit converter, weight-based dose calculator, pregnancy safety, multi-drug check, due date, symptom diary, growth percentiles, reminders, chat search and backup — plus .ics calendar export.",
        "d_fa": "تبدیل واحد، محاسبه‌ی دوز بر اساس وزن، ایمنی بارداری، بررسی چند دارو، تاریخ زایمان، دفترچه‌ی علائم، صدک رشد، یادآورها، جستجوی چت و بکاپ — به‌علاوه‌ی خروجی تقویم ics.",
        "web": "tools"},
    "pregnancy": {
        "en": "Pregnancy / period", "fa": "بارداری / قاعدگی",
        "d_en": "Period tracker with cycle and fertile-window predictions, plus a 40-week offline pregnancy guide with trimester danger signs.",
        "d_fa": "دنبال‌کننده‌ی قاعدگی با پیش‌بینی سیکل و پنجره‌ی باروری، به‌علاوه‌ی راهنمای آفلاین ۴۰ هفته‌ای بارداری با علائم خطر هر سه‌ماهه.",
        "web": "pregnancy"},
    "family": {
        "en": "Family risk", "fa": "ریسک خانوادگی",
        "d_en": "Add relatives' conditions and get your personal screening plan — when to start colonoscopy, mammography, lipid testing and more, based on degree and age.",
        "d_fa": "بیماری‌های بستگان را اضافه کن و برنامه‌ی غربالگری شخصی‌ات را بگیر — شروع کولونوسکوپی، ماموگرافی، چربی خون و بیشتر، بر اساس درجه‌ی قرابت و سن.",
        "web": "family"},
    "correlate": {
        "en": "Correlations", "fa": "تحلیل هم‌ربتگی",
        "d_en": "Cross-analyzes your symptom diary against vitals: on headache days your average systolic BP was 142 vs 127 on other days.",
        "d_fa": "دفترچه‌ی علائم را با علائم حیاتی کنار هم تحلیل می‌کند: روزهای سردرد میانگین فشار سیستولیک تو ۱۴۲ بوده در برابر ۱۲۷ در بقیه‌ی روزها.",
        "web": "correlate"},
    "second": {
        "en": "Second opinion", "fa": "نظر دوم AI",
        "d_en": "Ask one question and two AI providers answer in parallel, side by side — compare cloud and local models.",
        "d_fa": "یک سؤال بپرس و دو هوش مصنوعی همزمان، کنار هم جواب می‌دهند — ابری و محلی را مقایسه کن.",
        "web": "second"},
    "passport": {
        "en": "Health passport", "fa": "پاسپورت سلامت",
        "d_en": "One printable HTML file with your profile, medications, recent vitals and trend charts — print it or show it to your doctor.",
        "d_fa": "یک فایل HTML قابل چاپ با پروفایل، داروها، علائم حیاتی اخیر و نمودارهای روند — پرینتش کن یا به پزشک نشان بده.",
        "web": "passport"},
    "vaccine": {
        "en": "Child vaccination", "fa": "واکسیناسیون کودک",
        "d_en": "Iran's national immunization program by birth date: full schedule from birth to 6 years with next-due calculation and catch-up notes.",
        "d_fa": "برنامه‌ی ایمن‌سازی کشوری ایران بر اساس تاریخ تولد: جدول کامل از تولد تا ۶ سالگی با محاسبه‌ی نوبت بعدی و نکات جبرانی.",
        "web": "vaccine"},
    "ice": {
        "en": "Emergency card", "fa": "کارت اضطراری",
        "d_en": "ICE card with blood type, allergies, conditions and medications plus a scannable QR — keep it on your lock screen for paramedics.",
        "d_fa": "کارت ICE با گروه خونی، حساسیت‌ها، بیماری‌ها و داروها به‌علاوه‌ی QR قابل اسکن — روی قفل گوشی برای امدادگر نگهش دار.",
        "web": "ice"},
    "import": {
        "en": "Import health data", "fa": "ورود داده سلامت",
        "d_en": "CSV exports of smartwatches and fitness apps (Google Fit, Apple Health, BP/glucose meters) with automatic column detection.",
        "d_fa": "خروجی CSV ساعت هوشمند و اپ‌های سلامت (گوگل‌فیت، اپل‌هلث، فشارسنج و قندسنج) با تشخیص خودکار ستون‌ها.",
        "web": "import"},
    "vault": {
        "en": "Data vault", "fa": "قفل داده‌ها",
        "d_en": "Lock all personal health files with ChaCha20 encryption, or make one encrypted backup file to move between computers.",
        "d_fa": "همه‌ی فایل‌های سلامت شخصی را با رمزنگاری ChaCha20 قفل کن، یا یک فایل پشتیبان رمزنگاری‌شده برای انتقال بین کامپیوترها بساز.",
        "web": "vault"},
    "mental": {
        "en": "Mental health", "fa": "سلامت روان",
        "d_en": "PHQ-9 and GAD-7 screeners with scoring bands, crisis resources and a breathing exercise.",
        "d_fa": "آزمون‌های PHQ-9 و GAD-7 با باندهای نمره، منابع بحران و تمرین تنفس.",
        "web": "mental"},
    "sleep": {
        "en": "Sleep analysis", "fa": "تحلیل خواب",
        "d_en": "STOP-BANG sleep-apnea screening and a lite sleep-quality index with clear next steps.",
        "d_fa": "غربالگری آپنه‌ی خواب STOP-BANG و شاخص سبک کیفیت خواب با قدم‌های بعدی روشن.",
        "web": "sleep"},
    "checkup": {
        "en": "Checkup calendar", "fa": "تقویم چکاپ",
        "d_en": "Age- and sex-based checkup recommendations (screenings, vaccines, labs) with reminders.",
        "d_fa": "توصیه‌های چکاپ بر اساس سن و جنسیت (غربالگری‌ها، واکسن‌ها، آزمایش‌ها) با یادآور.",
        "web": "checkup"},
    "aid": {
        "en": "First aid / CPR", "fa": "کمک‌های اولیه / CPR",
        "d_en": "Seven first-aid guides (CPR with 110 bpm metronome, choking, bleeding, burns, seizure, poisoning, fainting) in both languages.",
        "d_fa": "هفت راهنمای کمک‌های اولیه (CPR با مترونوم ۱۱۰، خفگی، خونریزی، سوختگی، تشنج، مسمومیت، غش) به هر دو زبان.",
        "web": "aid"},
    "referral": {
        "en": "Referral report", "fa": "گزارش ارجاع",
        "d_en": "A printable referral report for your doctor: summary, vitals, medications and suggested basic workup.",
        "d_fa": "گزارش ارجاع قابل چاپ برای پزشکت: خلاصه، علائم حیاتی، داروها و آزمایش‌های پایه‌ی پیشنهادی.",
        "web": "referral"},
    "brain": {
        "en": "Brain & learning", "fa": "مغز داخلی / یادگیری",
        "d_en": "The offline brain's status: learned entries, style samples and indexed knowledge — learning from external answers runs in the background.",
        "d_fa": "وضعیت مغز آفلاین: موارد آموخته‌شده، نمونه‌های سبک و دانش نمایه‌شده — یادگیری از پاسخ‌های خارجی در پس‌زمینه اجرا می‌شود.",
        "web": "brain"},
    "doctor": {
        "en": "Doctor Mode", "fa": "حالت دکتر",
        "d_en": "Describe a patient scenario and get a clinical differential-diagnosis discussion, as one physician to another.",
        "d_fa": "سناریوی بیمار را بنویس و بحث بالینی تشخیص افتراقی بگیر، مثل گفتگوی دو پزشک.",
        "web": "chat"},
    "lmstudio": {
        "en": "LM Studio (local AI)", "fa": "LM Studio (هوش محلی)",
        "d_en": "Zero-configuration local AI: the app detects LM Studio by itself and uses it with priority while it runs. Free, offline, unlimited.",
        "d_fa": "هوش مصنوعی محلی بدون تنظیم: برنامه خودش LM Studio را پیدا می‌کند و تا وقتی روشن است با اولویت از آن استفاده می‌کند. رایگان، آفلاین، نامحدود.",
        "web": "lmstudio"},
    "gpu": {
        "en": "Local AI (Ollama)", "fa": "هوش محلی (Ollama)",
        "d_en": "Connect a local Ollama server as another AI provider.",
        "d_fa": "سرور Ollama محلی را به‌عنوان یک هوش مصنوعی دیگر وصل کن.",
        "web": "gpu"},
    "profiles": {
        "en": "User profiles", "fa": "پروفایل‌های کاربران",
        "d_en": "Multiple users on one installation: each profile keeps its own data, switching archives and restores files.",
        "d_fa": "چند کاربر روی یک نصب: هر پروفایل داده‌ی خودش را دارد؛ تغییر پروفایل، فایل‌ها را بایگانی و بازگردانی می‌کند.",
        "web": None},
}


def get(key: str) -> dict[str, Any]:
    return MODULE_INFO.get(key) or {}


def web_key(key: str) -> str | None:
    m = MODULE_INFO.get(key) or {}
    return m.get("web")


def orbit_plan() -> list[dict[str, Any]]:
    outer = ORBIT_KEYS[:8]
    inner = ORBIT_KEYS[8:]
    return [
        {"keys": outer, "radius": 128, "speed": 1.0, "direction": 1},
        {"keys": inner, "radius": 76, "speed": 1.7, "direction": -1},
    ]
