# -*- coding: utf-8 -*-
"""
image_caption.py — تحلیل تصویر پزشکی همراه متن توضیحی کاربر.
- اگر مدل تصویری خارجی در دسترس بود → تحلیل با AI + یادگیری خودکار
- اگر نه → پاسخ امن آفلاین (بدون تولید تشخیص جعلی): سوالات کلیدی + مسیر ارجاع
"""
from __future__ import annotations

import base64
import io
from typing import Any


def prepare_image(image_bytes: bytes, max_side: int = 1024, quality: int = 82) -> tuple[str, str]:
    """فشرده‌سازی تصویر با Pillow و خروجی (b64, mime)."""
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


def _vision_prompt(note: str) -> str:
    return f"""این تصویر پزشکی توسط کاربر ارسال شده همراه توضیح: «{note or 'توضیحی داده نشده'}»
به‌عنوان دستیار پزشکی فارسی:
1. فقط توصیفِ عینیِ قابل مشاهده بنویس (شکل، رنگ، پراکندگی، اندازه تقریبی) — بدون ادعای قطعی.
2. چند «احتمال مطرح» را با لحن احتمالی و محتاط بنویس (بدون قطعیت).
3. مواردی که در تصویر قابل تشخیص نیست را صادقانه بگو.
4. مراقبت عمومی امن + علائم هشدار برای مراجعه فوری.
5. تأکید کن تشخیص نهایی با معاینه‌ی حضوری پزشک/پوست/متخصص است.
قوانین: هیچ‌گاه تشخیص قطعی نده؛ اطلاعات جعلی نساز؛ فارسی همدلانه؛ بخش‌بندی با ایموجی (🔎 🎯 💊 ❓)."""


def analyze_image_with_ai(image_b64: str, mime: str, note: str, engine=None) -> dict[str, Any]:
    """ارسال تصویر + متن به مدل تصویری در دسترس."""
    from ai_api_manager import get_api_key, get_settings
    from ai_client import chat as ext_chat
    from free_ai import is_vision_model
    s = get_settings()
    order = [p for p in s["provider_order"] if p != "local" and get_api_key(p)]
    for p in order:
        model = s.get("openrouter_model") if p == "openrouter" else ("gpt-4o-mini" if p == "openai" else None)
        if p == "openrouter" and not is_vision_model(model or ""):
            from free_ai import vision_models
            model = vision_models()[0]
        if p == "deepseek":
            continue  # DeepSeek تصویر نمی‌پذیرد
        r = ext_chat(p, [{"role": "user", "content": _vision_prompt(note)}],
                     model=model, image_b64=image_b64, image_mime=mime, max_tokens=1100)
        if r.get("ok"):
            r["provider"] = p
            return r
    return {"ok": False, "error": "no_vision_ai", "error_fa": "مدل تصویری خارجی در دسترس نیست."}


OFFLINE_IMAGE_RESPONSE = """🔧 تحلیل تصویر آفلاین (بدون AI خارجی)

از اینکه عکس را فرستادی ممنونم؛ ولی بدون مدل تصویری فعال، من **حدس تصویری قطعی نمی‌زنم** — ایمنی‌ات مهم‌تر از جواب سریع است.

🔎 سوال‌های کلیدی که جوابشان کمک می‌کند:
• این ضایعه چند روز/هفته است؟
• خارش، درد، ترشح یا خونریزی دارد؟
• پس از چه چیزی شروع شد (دارو، غذا، نیش، تماس با ماده‌ی جدید)؟
• تب یا علائم عمومی هم داری؟

🎯 مسیر درست:
• ضایعه‌ی پوستی جدید با خارش/رشد → معاینه‌ی پزشک یا پوست‌شناس در چند روز آینده
• همراه با تورم صورت/لب/زبان یا تنگی نفس → اورژانس فوری (۱۱۵ / ۱۱۲)
• تب بالا با لک‌های پهن بنفش/قرمز که زیر فشار محو نمی‌شود → اورژانس فوری

💊 تا زمان معاینه: ناحیه را تمیز و خشک نگه دار، از خاراندن پرهیز کن، مرطوب‌کننده‌ی ساده بدون عطر.

❓ جواب سوال‌های بالا را بنویس تا مغز داخلی، احتمالات را دقیق‌تر کند؛ و اگر کلید OpenRouter را در تنظیمات وارد کنی، تحلیل تصویری واقعی هم فعال می‌شود.

⚠️ این برنامه جایگزین پزشک نیست."""


def analyze_image_file(path: str, note: str, engine=None) -> dict[str, Any]:
    """ورودی از فایل — برای UI دسکتاپ."""
    with open(path, "rb") as f:
        b = f.read()
    return analyze_image_bytes(b, note, engine)


def analyze_image_bytes(image_bytes: bytes, note: str, engine=None) -> dict[str, Any]:
    try:
        b64, mime = prepare_image(image_bytes)
    except Exception as e:
        return {"ok": False, "text": "تصویر قابل خواندن نبود (" + str(e)[:80] + "). فرمت JPG/PNG را امتحان کن.", "source": "image-error"}
    red = None
    try:
        from medical_engine import check_red_flags
        red = check_red_flags(note or "")
    except Exception:
        red = {"flag": False}
    if red and red.get("flag"):
        from medical_engine import emergency_response
        return {"ok": True, "text": emergency_response(red["reasons"]), "source": "internal-emergency", "red_flag": True}
    res = analyze_image_with_ai(b64, mime, note, engine)
    if res.get("ok"):
        try:
            from auto_learning import learn_from_exchange
            learn_from_exchange(f"[تصویر پزشکی] {note}", res["text"], provider=res.get("provider", ""),
                                model=res.get("model", ""), meta={"image": True})
        except Exception:
            pass
        return {"ok": True, "text": res["text"], "source": f"external:{res.get('provider')}", "red_flag": False}
    return {"ok": True, "text": OFFLINE_IMAGE_RESPONSE, "source": "internal", "red_flag": False}
