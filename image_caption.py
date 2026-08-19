# -*- coding: utf-8 -*-
"""
image_caption.py — medical image analysis with a text note.
Flow: red flag check -> offline type detection (image_type_detector) ->
optional external vision model with a type-specific prompt -> honest offline
answer otherwise. The detected type also feeds the learning memory.
"""
from __future__ import annotations

import base64
import io
from typing import Any

from i18n import is_fa


def prepare_image(image_bytes: bytes, max_side: int = 1024, quality: int = 82) -> tuple[str, str]:
    """Resize/compress with Pillow, return (b64, mime)."""
    from PIL import Image
    im = Image.open(io.BytesIO(image_bytes))
    im = im.convert("RGB")
    w, h = im.size
    scale = min(1.0, max_side / max(w, h))
    if scale < 1.0:
        im = im.resize((int(w * scale), int(h * scale)))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode("ascii"), "image/jpeg"


# --------------------------------------------------------------------------
# Type-specific instructions for the external vision model
# --------------------------------------------------------------------------

PROMPT_FRAGMENTS: dict[str, dict[str, str]] = {
    "skin_photo": {
        "fa": """تصویر یک ضایعه‌ی پوستی است. توصیف عینی بده: رنگ، مرز (منظم/نامنظم)، تعداد و پراکندگی، اندازه‌ی تقریبی، وجود پوسته‌ریز/ترشح/تاول.
چند احتمال مطرح را با لحن محتاط بیاور (آلرژیک/عفونی/تحریکی و…) بدون قطعیت. بگو چه چیزی از عکس معلوم نیست.
علائم هشدار برای مراجعه‌ی فوری: پخش سریع قرمزی، تب، تاول روی مخاط‌ها، کهیر با تورم صورت/گلو، لک‌های بنفش که زیر فشار محو نمی‌شوند.""",
        "en": """This is a photo of a skin lesion. Describe objectively: color, border (regular/irregular), number and distribution, approximate size, any scaling/discharge/blistering.
List a few cautious possibilities (allergic/infectious/irritant and so on) without certainty. Say what cannot be judged from the photo.
Red flags that mean urgent care: rapidly spreading redness, fever, blisters on mucous membranes, hives with face/throat swelling, purple spots that do not fade under pressure.""",
    },
    "wound_photo": {
        "fa": """تصویر یک زخم/سوختگی است. توصیف عینی: ظاهر بستر زخم، لبه‌ها، قرمزی اطراف، ترشح/چرک، تورم، رنگ.
نشانه‌های عفونت را جدا ذکر کن (قرمزی پخش‌شونده، چرک، بو، تب). سوال درباره‌ی زمان ایجاد زخم، عامل آن و وضعیت واکسن تتانوس مطرح کن.
مراقبت عمومی امن و زمان مراجعه را بگو؛ دیبریدمان/دارو فقط با پزشک.""",
        "en": """This is a wound or burn photo. Describe objectively: wound bed, edges, surrounding redness, discharge/pus, swelling, color.
Separately list infection signs (spreading redness, pus, odor, fever). Ask about when it happened, the cause, and tetanus vaccination status.
Give safe general care and when to seek care; debridement and medication belong to a clinician.""",
    },
    "radiograph": {
        "fa": """تصویر احتمالاً رادیولوژیک است (رادیوگرافی/سی‌تی/ام‌آرآی). اگر نوع اموج و ناحیه‌ی بدن از خود تصویر مشخص است بگو؛ اگر مطمئن نیستی صریح بگو.
فقط یافته‌های درشتِ قابل مشاهده را با احتیاط توصیف کن و تأکید کن گزارش رسمی فقط توسط رادیولوژیست است.
سوال درباره‌ی علت انجام عکس (ضربه/درد مزمن/پیگیری) و علائم همراه بپرس. هیچ‌گونه «طبیعی است» قطعی نگو.""",
        "en": """This is probably a radiological image (X-ray/CT/MRI). If the modality and body region are evident from the image, say so; if not, say so honestly.
Describe only gross visible findings cautiously, and stress that an official read belongs to a radiologist.
Ask why the image was taken (trauma/chronic pain/follow-up) and about accompanying symptoms. Never declare it 'normal' with certainty.""",
    },
    "ecg_strip": {
        "fa": """این تصویر نوار قلب است. فقط اگر کاملاً واضح است، ریتم ظاهری و نرخ تقریبی را با احتیاط توصیف کن.
هیچ تفسیر ایسکمی/انفارکتوس نده و نگو «نوار طبیعی است». تأکید کن تفسیر نهایی فقط توسط پزشک/قلب‌شناس است.
اگر کاربر درد قفسه سینه/تنگی نفس/غش دارد → فوراً اورژانس. بگو کدام علامت روی نوار باید سریع دیده شود (مثلاً ریتم خیلی تند/کند) و مراجعه فوری یعنی چه.""",
        "en": """This is an ECG strip. Only if it is clearly legible, cautiously describe the apparent rhythm and approximate rate.
Do not interpret ischemia/infarction and never say 'the ECG is normal'. The final read belongs to a physician/cardiologist.
If the user has chest pain/breathlessness/fainting -> emergency immediately. Mention which patterns need urgent attention (extremely fast/slow rhythm) and what urgent care means.""",
    },
    "document_report": {
        "fa": """این تصویر یک برگه‌ی آزمایش/نسخه است. مقادیر خوانا را فهرست کن (نام آزمایش، عدد، واحد، بازه‌ی مرجع اگر چاپ شده).
برای هر مورد خارج از بازه توضیح عمومی کوتاه بده و تأکید کن تفسیر بالینی با پزشک است. اگر متنی خوانا نیست صادقانه بگو و از کاربر بخواه اعداد را تایپ کند تا در ماژول تحلیل آزمایش بررسی شوند.
داروهای نوشته‌شده را فقط نام ببر و تأکید کن مصرف فقط با تجویز پزشک.""",
        "en": """This is a scanned lab report or prescription. List legible values (test name, number, unit, reference range if printed).
For each out-of-range item give a short general note and stress that clinical interpretation belongs to a doctor. If text is not legible, say so and ask the user to type the numbers so the lab module can analyze them.
Name any written medications but stress they are taken only as prescribed.""",
    },
    "eye_photo": {
        "fa": """تصویر چشم است. توصیف عینی: قرمزی (موضعی/پخش)، ترشح، پلک، مشخص بودن مردمک، تورم اطراف.
سوال درباره‌ی درد، نورآزار بودن، تغییر دید، استفاده از لنز تماسی بپرس.
علائم هشدار: کاهش شدید دید، درد شدید، زخم قرنیه مشکوک، کتاراکت حاد — ارجاع فوری. توصیه لنز/قطره فقط با پزشک.""",
        "en": """This is an eye photo. Describe objectively: redness (localized/diffuse), discharge, eyelids, pupil visibility, surrounding swelling.
Ask about pain, light sensitivity, vision change, and contact lens use.
Red flags: severe vision loss, severe pain, suspected corneal ulcer, acute cataract - urgent referral. Lens or drop advice only from a clinician.""",
    },
    "dental_photo": {
        "fa": """تصویر دندان/داخل دهان است. توصیف عینی: تورم لثه، قرمزی، خونریزی، پوسیدگی قابل‌دید، جرم، زخب دهانی، لقی دندان.
علائم هشدار را ذکر کن: تورم صورت، تب، درد شدید یک‌طرفه (انتشار عفونت) → فوری. توصیه‌ی دارو/آنتی‌بیوتیک فقط با پزشک/دندانپزشک.""",
        "en": """This is a dental/oral photo. Describe objectively: gum swelling, redness, bleeding, visible decay, tartar, oral ulcer, loose teeth.
List red flags: facial swelling, fever, severe one-sided pain (spreading infection) - urgent. Any medication/antibiotic only via a dentist or doctor.""",
    },
    "device_screen": {
        "fa": """تصویر نمایشگر یک دستگاه پزشکی است (فشارسنج/قندسنج/دماسنج و…). اگر اعداد خواناست، آن‌ها را با واحدشان بازگو کن و با محدوده‌های مرجع عمومی مقایسه کن (با تأکید که ملاک بازه‌ی راهنمای دستگاه است).
اگر عدد خوانا نیست صادقانه بگو. برای فشار ≥۱۸۰/۱۲۰ یا قند خیلی بالا/پایین → مسیر اورژانس را بگو. هیچ تشخیصی از یک عدد نمی‌گذاری.""",
        "en": """This is a photo of a medical device screen (BP monitor, glucometer, thermometer...). If the numbers are legible, read them back with units and compare against general reference ranges (stressing that the device's own guide is what counts).
If not legible, say so honestly. For BP at or above 180/120 or very high/low sugar - give the emergency path. Never diagnose from a single number.""",
    },
    "other_photo": {
        "fa": """تصویر پزشکی عمومی است. فقط توصیف عینی قابل مشاهده بنویس و بگو چه چیزی قابل قضاوت نیست.
احتمالات را محتاط مطرح کن و مسیر درست ارجاع را بگو.""",
        "en": """This is a general medical photo. Describe only what is objectively visible and say what cannot be judged.
Raise possibilities cautiously and point to the right care path.""",
    },
}


def lesion_summary_for_ai(image_bytes: bytes | None, tkey: str) -> str:
    """اندازه‌گیری‌های عینی برای مدل تصویری — تحلیل خود عکس، نه فقط نوع آن."""
    if not image_bytes or tkey not in ("skin_photo", "wound_photo", "eye_photo"):
        return ""
    try:
        from lesion_analyzer import analyze_lesion
        les = analyze_lesion(image_bytes)
        if not les.get("found"):
            return ""
        lines = [f"- {f['en']}" for f in les["findings"]]
        m = les.get("measures", {})
        lines.append(f"- measured: affected area ~{m.get('affected_area_pct', '?')}% of frame, redness index {m.get('redness_index', '?')}")
        return ("Offline preprocessing measured these objective findings in the image "
                "(use them, correct them if they look wrong, and stay cautious):\n" + "\n".join(lines) + "\n")
    except Exception:
        return ""


def _vision_prompt(note: str, type_info: dict | None, lesion_block: str = "") -> str:
    tkey = (type_info or {}).get("type", "other_photo")
    frag = PROMPT_FRAGMENTS.get(tkey, PROMPT_FRAGMENTS["other_photo"])
    tline = ""
    if type_info and not type_info.get("user_hint"):
        tline = f"\nOffline preprocessing guesses the image type as: {type_info.get('label')} (heuristic, {int(type_info.get('confidence', 0) * 100)}%) - correct it if it is wrong.\n"
    elif type_info:
        tline = f"\nThe user says the image type is: {type_info.get('label')}.\n"
    if is_fa():
        return f"""این تصویر پزشکی توسط کاربر با توضیح «{note or 'توضیحی داده نشده'}» ارسال شده.{tline}
{lesion_block}
{frag['fa']}

قوانین: هیچ‌گاه تشخیص قطعی نده؛ اطلاعات جعلی نساز؛ فارسی همدلانه؛ بخش‌بندی با عنوان‌های کوتاه (یافته‌ها، احتمالات، مراقبت، سوال بعدی)."""
    return f"""This medical image was sent by the user with the note: '{note or 'no note given'}'.{tline}
{lesion_block}
{frag['en']}

Rules: never give a definitive diagnosis; never fabricate information; warm clear English; short section titles (findings, possibilities, care, next question)."""


def analyze_image_with_ai(image_b64: str, mime: str, note: str, engine=None,
                          type_info: dict | None = None) -> dict[str, Any]:
    """Send image + note (+ detected type context) to a vision model."""
    from ai_api_manager import get_api_key, get_settings
    from ai_client import chat as ext_chat
    from free_ai import is_vision_model, vision_models
    s = get_settings()
    order = [p for p in s["provider_order"] if p != "local" and get_api_key(p)]
    try:
        import base64 as _b64
        _raw_img = _b64.b64decode(image_b64.split(",")[-1])
        _lesion_block = lesion_summary_for_ai(_raw_img, (type_info or {}).get("type", ""))
    except Exception:
        _lesion_block = ""
    for p in order:
        model = s.get("openrouter_model") if p == "openrouter" else ("gpt-4o-mini" if p == "openai" else None)
        if p == "openrouter" and not is_vision_model(model or ""):
            model = vision_models()[0]
        if p == "deepseek":
            continue  # DeepSeek has no vision endpoint
        r = ext_chat(p, [{"role": "user", "content": _vision_prompt(note, type_info, _lesion_block)}],
                     model=model, image_b64=image_b64, image_mime=mime, max_tokens=1100)
        if r.get("ok"):
            r["provider"] = p
            return r
    return {"ok": False, "error": "no_vision_ai", "error_fa": "no vision model available" if not is_fa() else "مدل تصویری خارجی در دسترس نیست"}


# --------------------------------------------------------------------------
# Honest offline answers, tailored per detected type
# --------------------------------------------------------------------------

def _type_header(type_info: dict, fa: bool) -> str:
    if fa:
        how = "انتخاب شما" if type_info.get("user_hint") else f"حدس آفلاین (~{int(type_info.get('confidence', 0) * 100)}٪)"
        return f"نوع تصویر ({how}): {type_info.get('label')} | اندازه: {type_info.get('size')}"
    how = "your selection" if type_info.get("user_hint") else f"offline guess (~{int(type_info.get('confidence', 0) * 100)}%)"
    return f"Image type ({how}): {type_info.get('label')} | size: {type_info.get('size')}"


OFFLINE_BODIES: dict[str, dict[str, str]] = {
    "skin_photo": {
        "fa": """سوال‌های کلیدی:
• چند روز/هفته است؟ خارش، درد یا ترشف دارد؟
• پس از چه چیزی شروع شد (دارو، غذا، نیش، تماس با ماده‌ی جدید)؟
• تب یا علائم عمومی هم داری؟

مسیر درست:
• ضایعه‌ی جدید با رشد یا خارش شدید -> معاینه‌ی پزشک/پوست‌شناس در چند روز آینده
• تورم لب/زبان/گلو یا تنگی نفس -> اورژانس فوری (۱۱۵ / ۱۱۲)
• تب با لک‌های بنفش که زیر فشار محو نمی‌شود -> اورژانس فوری

تا معاینه: ناحیه تمیز و خشک، بدون خاراندن، مرطوب‌کننده‌ی ساده‌ی بدون عطر.""",
        "en": """Key questions:
- How many days/weeks has it been there? Itchy, painful or oozing?
- What appeared right before it (medication, food, a bite, contact with something new)?
- Any fever or general symptoms?

The right path:
- A new lesion that grows or itches badly -> clinician/dermatologist in the next few days
- Swelling of lips/tongue/throat or trouble breathing -> emergency now (115 / 112)
- Fever with purple spots that do not fade under pressure -> emergency now

Until examined: keep it clean and dry, no scratching, plain fragrance-free moisturizer.""",
    },
    "wound_photo": {
        "fa": """سوال‌های کلیدی:
• زخم کِی و با چه عاملی ایجاد شد؟ آخرین واکسن تتانوس کِی بوده؟
• تب، قرمزی پخش‌شونده، چرک یا دردِ رو به افزایش دارد؟
• دیابت یا مشکل ایمنی داری؟

مسیر درست:
• قرمزی پخش‌شونده/تب/چرک -> مراجعه‌ی فوری (عفونت)
• زخم عمیق یا ناشی از گاز گرفتن/شیء کثیف -> همان روز پزشک
• سوختگی وسیع یا در صورت/دست -> اورژانس

تا مراجعه: شست‌وشو با آب و صابون ملایم، پوشش تمیز، بدون الکل/پمادهای سنتی.""",
        "en": """Key questions:
- When did it happen and what caused it? When was your last tetanus shot?
- Any fever, spreading redness, pus or growing pain?
- Any diabetes or immune problems?

The right path:
- Spreading redness/fever/pus -> urgent care (infection)
- Deep wound, bite, or dirty object -> same-day clinician
- Large burn, or burn on face/hands -> emergency

Until care: wash gently with water and mild soap, clean cover, no alcohol or folk remedies.""",
    },
    "radiograph": {
        "fa": """مهم: من آفلاین نمی‌توانم عکس رادیولوژیک را «بخوانم» و هیچ حدسی درباره‌ی محتوای آن نمی‌زنم؛ گزارش رسمی فقط توسط رادیولوژیست انجام می‌شود.

سوال‌های کلیدی:
• این عکس برای چه علامتی گرفته شد (ضربه، درد مزمن، پیگیری)؟
• درد فعلی، تورم یا محدودیت حرکت داری؟

مسیر درست:
• نتیجه را همراه توضیح پزشکِ تجویزکننده بخواه؛ عکس بدون گزارش رادیولوژیست معناگذاری نمی‌شود.
• اگر پس از ضربه درد شدید/بی‌شکستگی مشکوک داری -> همان روز اورژانس/مطب.

اگر کلید OpenRouter را در تنظیمات وارد کنی، مدل تصویری می‌تواند توصیف محتاطانه‌ای هم بدهد.""",
        "en": """Important: offline, I cannot 'read' a radiological image and I will not guess at its content; the official read belongs to a radiologist.

Key questions:
- Why was this taken (trauma, chronic pain, follow-up)?
- Current pain, swelling, or limited movement?

The right path:
- Ask for the result together with the ordering doctor's explanation; an image without a radiologist read has no meaning.
- Severe pain or suspected fracture after trauma -> same-day emergency/clinic.

If you add an OpenRouter key in settings, a vision model can also give a cautious description.""",
    },
    "ecg_strip": {
        "fa": """مهم: من آفلاین نوار قلب را تفسیر نمی‌کنم؛ تفسیر فقط توسط پزشک/قلب‌شناس است.

سوال‌های کلیدی:
• نوار برای چه علامتی زده شد (درد سینه، تپش، غش)؟
• الان هم علامت داری؟

مسیر درست:
• درد قفسه سینه، غش یا تنگی نفس -> همین حالا اورژانس (۱۱۵ / ۱۱۲)
• نوارِ بی‌علامت را همراه پزشک بخواه؛ «طبیعی بودن» از روبات پرسیده نشود
• ریتم خیلی تند/کند با ضعف -> مراجعه‌ی فوری""",
        "en": """Important: offline, I do not interpret ECGs; interpretation belongs to a physician/cardiologist.

Key questions:
- Why was it recorded (chest pain, palpitations, fainting)?
- Do you have symptoms right now?

The right path:
- Chest pain, fainting or breathlessness -> emergency now (115 / 112)
- A symptom-free tracing should be reviewed with your doctor; 'is it normal' is not a question for software
- Very fast/slow rhythm with weakness -> urgent care""",
    },
    "document_report": {
        "fa": """برگه‌ی آزمایش/نسخه را دیدم، ولی آفلاین OCR قابل‌اعتماد ندارم و عددی را حدس نمی‌زنم — این کار را درست انجام بده:

• مقادیر را همین‌طور تایپ کن (مثلاً: FBS 105 و Hb 13) تا ماژول «تحلیل آزمایش» با بازه‌ی مرجع و تفسیر فارسی بررسی‌شان کند.
• برای نسخه: متن دستورها را بنویس (BID، PO و…) تا «اسکن نسخه» ترجمه کند.
• تفسیر نهایی همیشه با پزشک است.""",
        "en": """I can see this is a report/prescription scan, but offline I have no reliable OCR and I will not guess numbers - do this instead:

- Type the values here (e.g. FBS 105, Hb 13) and the Lab analysis module will check them against reference ranges.
- For a prescription: type the directions (BID, PO, ...) and the Prescription scan module will translate them.
- Final interpretation always belongs to your doctor.""",
    },
    "eye_photo": {
        "fa": """سوال‌های کلیدی:
• درد، نورآزاری، ترشح یا تغییر دید داری؟ لنز تماسی می‌زنی؟
• قرمزی از کِی شروع شده و یک‌چشمی است یا دوجهت؟

مسیر درست:
• کاهش شدید دید، درد شدید یا زخم مشکوک قرنیه -> همان روز چشم‌پزشک/اورژانس
• قرمزی ساده‌ی بدون درد و بدون تغییر دید -> بررسی پزشک در چند روز
• بدون قطره/لنز خودسرانه.""",
        "en": """Key questions:
- Pain, light sensitivity, discharge or vision change? Contact lens user?
- When did the redness start, one eye or both?

The right path:
- Severe vision loss, severe pain or suspected corneal ulcer -> ophthalmologist/emergency the same day
- Simple redness without pain or vision change -> clinician within days
- No self-prescribed drops or lenses.""",
    },
    "dental_photo": {
        "fa": """سوال‌های کلیدی:
• درد دندان از کِی و با چه محرکی (گرم/سرد/جویدن)؟
• تورم صورت، تب یا طعم بد دهان داری؟

مسیر درست:
• تورم صورت/تب/درد شدید → همان روز دندانپزشک/اورژانس (انتشار عفونت)
• درد خفیف بدون تورم → نوبت دندانپزشکی + مسکن ساده در صورت نیاز
• نخ دندان و مسواک منظم؛ گرمای موضعی روی تورم نگذار بدون نظر پزشک""",
        "en": """Key questions:
- Since when does the tooth hurt, and what triggers it (hot/cold/chewing)?
- Any facial swelling, fever, or bad taste?

The right path:
- Facial swelling/fever/severe pain -> dentist or emergency the same day (spreading infection)
- Mild pain without swelling -> dental appointment plus simple pain relief if needed
- Regular brushing and flossing; no hot compress on swelling without advice""",
    },
    "device_screen": {
        "fa": """اعداد نمایشگر را برایم تایپ کن تا با محدوده‌ی مرجع بررسی‌شان کنم:
• فشارسنج: «فشار ۱۲۵ روی ۸۰، نبض ۷۲»
• قندسنج: «قند ۱۴۵»
• دماسنج: «تب ۳۸.۵»

می‌توانم در ماژول «تحلیل آزمایش» و «علائم حیاتی» تفسیر عمومی بدهم.
هشدار: فشار ≥۱۸۰/۱۲۰ یا قند بالای ۴۰۰/زیر ۵۰ یا تب ≥۴۰ → اورژانس (۱۱۵/۱۱۲).""",
        "en": """Type the numbers from the display and I will check them against reference ranges:
- BP monitor: "BP 125/80, pulse 72"
- Glucometer: "sugar 145"
- Thermometer: "temp 38.5"

I can interpret them in the Lab analysis and Vitals modules.
Warning: BP at or above 180/120, sugar above 400 or below 50, or fever 40+ -> emergency (115/112).""",
    },
    "other_photo": {
        "fa": """سوال‌های کلیدی:
• این عکس مربوط به کدام ناحیه است و چه علامتی داری؟
• از کِی شروع شده و چه چیزی آن را بدتر می‌کند؟

توضیح بده تا احتمالات دقیق‌تر شود؛ اگر کلید OpenRouter فعال باشد تحلیل تصویری هم انجام می‌شود.""",
        "en": """Key questions:
- Which body area is this, and what symptom do you have?
- When did it start and what makes it worse?

Describe it and I can weigh possibilities better; with an OpenRouter key configured, real image analysis also runs.""",
    },
}


def offline_analysis(type_info: dict, note: str, image_bytes: bytes | None = None) -> dict[str, Any]:
    from common_2077 import MEDICAL_DISCLAIMER
    fa = is_fa()
    tkey = type_info.get("type", "other_photo")
    body = OFFLINE_BODIES.get(tkey, OFFLINE_BODIES["other_photo"])[ "fa" if fa else "en"]
    head = ("تحلیل تصویر آفلاین (بدون AI خارجی)\n\n" if fa else "Offline image analysis (no external AI)\n\n")
    q = [head + _type_header(type_info, fa)]
    if type_info.get("quality"):
        q.append(("کیفیت عکس: " if fa else "Photo quality: ") + ("، ".join(type_info["quality"]) if fa else ", ".join(type_info["quality"])))
    # تحلیل آفلاین موج نوار قلب: شمارش ضربان‌ها و نظم — بدون تفسیر بالینی
    if tkey == "ecg_strip" and image_bytes:
        try:
            from ecg_analyzer import analyze_ecg
            ecg = analyze_ecg(image_bytes)
            note_txt = ecg.get("note_fa" if fa else "note_en", "")
            if note_txt:
                q.append(("بررسی آفلاین ریتم: " if fa else "Offline trace check: ") + note_txt)
        except Exception:
            pass
    # تحلیل عینیِ محتوای عکس (اندازه‌گیری؛ نه تشخیص)
    if image_bytes and tkey in ("skin_photo", "wound_photo", "eye_photo"):
        try:
            from lesion_analyzer import analyze_lesion
            les = analyze_lesion(image_bytes)
            if les.get("found") and les.get("findings"):
                head = ("یافته‌های عینی از خود عکس (اندازه‌گیری شده — تشخیص نیست):" if fa
                        else "Objective findings from the image itself (measured - not a diagnosis):")
                lines = [head]
                for f in les["findings"]:
                    lines.append(("• " if fa else "- ") + (f["fa"] if fa else f["en"]))
                    if f.get("meaning_fa" if fa else "meaning_en"):
                        lines.append("   " + ("معنی ممکن: " if fa else "What it can mean: ") + (f["meaning_fa"] if fa else f["meaning_en"]))
                if any(f.get("level") == "urgent" for f in les["findings"]):
                    lines.append(("توجه: یکی از یافته‌ها فوریت بالاتری دارد — مسیر ارجاع بالا را جدی بگیر." if fa
                                  else "Note: one of the findings carries higher urgency - take the referral path above seriously."))
                q.append("\n".join(lines))
        except Exception:
            pass
    elif isinstance(type_info.get("features"), dict) and tkey in ("skin_photo", "wound_photo"):
        red = type_info["features"].get("redness")
        if red is not None:
            q.append(("شاخص قرمزی تصویر: " if fa else "Image redness index: ") + f"{red:.2f}")
    q.append(body)
    # ارزیابی احتمالاتی از متنِ یادداشت (نه از خود تصویر — از عکس حدس بالینی نمی‌زنیم)
    if tkey in ("skin_photo", "wound_photo", "eye_photo", "other_photo") and note:
        try:
            from bayesian_engine import rank_diseases
            from medical_engine import detect_symptoms
            cands = rank_diseases(detect_symptoms(note), {})
            if cands:
                head2 = ("بر اساس متنِ توضیحت (نه خود عکس)، چند احتمال مطرح — احتمالی، نه تشخیص:" if fa
                         else "From your written note (not the image itself), possibilities to consider - probabilistic, not a diagnosis:")
                lines = []
                for c in cands[:3]:
                    pct = int(c["percent"])
                    lines.append(f"• {c['name']} ~{pct}" + ("٪" if fa else "%"))
                q.append(head2 + "\n" + "\n".join(lines))
        except Exception:
            pass
    if note:
        q.append(("یادداشت تو: " if fa else "Your note: ") + note)
    q.append(MEDICAL_DISCLAIMER())
    return {"ok": True, "text": "\n\n".join(q), "source": "internal-image",
            "red_flag": False, "image_type": type_info}


def analyze_image_file(path: str, note: str, engine=None, hint: str | None = None) -> dict[str, Any]:
    with open(path, "rb") as f:
        return analyze_image_bytes(f.read(), note, engine, hint)


def analyze_image_bytes(image_bytes: bytes, note: str, engine=None, hint: str | None = None) -> dict[str, Any]:
    from image_type_detector import classify_image
    try:
        b64, mime = prepare_image(image_bytes)
    except Exception as e:
        from i18n import tt
        return {"ok": False, "text": tt("Could not read the image (" + str(e)[:60] + "). Try a JPG or PNG file.",
                                        "تصویر قابل خواندن نبود (" + str(e)[:60] + "). فرمت JPG/PNG را امتحان کن."),
                "source": "image-error"}
    # red flag check on the note first — before anything else
    from medical_engine import check_red_flags
    red = check_red_flags(note or "")
    if red and red.get("flag"):
        from medical_engine import emergency_response
        return {"ok": True, "text": emergency_response(red["reasons"]),
                "source": "internal-emergency", "red_flag": True, "image_type": classify_image(image_bytes, hint)}
    type_info = classify_image(image_bytes, hint)
    res = analyze_image_with_ai(b64, mime, note, engine, type_info)
    if res.get("ok"):
        try:
            from auto_learning import learn_from_exchange
            learn_from_exchange(f"[image:{type_info['type']}] {note}", res["text"],
                                provider=res.get("provider", ""), model=res.get("model", ""),
                                meta={"image": True, "image_type": type_info["type"]})
        except Exception:
            pass
        res["image_type"] = type_info
        return res
    return offline_analysis(type_info, note, image_bytes)
