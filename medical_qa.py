# -*- coding: utf-8 -*-
"""
medical_qa.py — hard-coded GPT-quality answers for common medical questions
that banks alone can't answer well. Concise, structured, bilingual.
"""
from __future__ import annotations


def _fa() -> bool:
    from i18n import is_fa
    return is_fa()


_QA: list[tuple[tuple, str, str]] = [
    # (keywords_fa, keywords_en, answer_fa, answer_en)
    (("فرق دیابت نوع ۱ و ۲", "فرق دیابت ۱ و ۲", "تفاوت دیابت"),
     ("difference between type 1 and type 2", "type 1 vs type 2"),
     """🩸 **فرق دیابت نوع ۱ و ۲:**

**نوع ۱:**
• بیماری خودایمنی — بدن سلول‌های انسولین‌ساز پانکراس را تخریب می‌کند
• معمولاً از کودکی یا نوجوانی شروع می‌شود
• بدن انسولین **نمی‌سازد**
• درمان: تزریق انسولین مادام‌العمر (اجباری)
• ~۵-۱۰٪ کل دیابت‌ها

**نوع ۲:**
• مقاومت به انسولین — بدن انسولین می‌سازد ولی استفاده نمی‌تواند بکند
• معمولاً بعد از ۳۰-۴۰ سالگی (در حال افزایش در جوان‌ترها)
• بدن انسولین **می‌سازد ولی کافی نیست**
• درمان: رژیم + ورزش → قرص (متفورمین) → گاهی انسولین
• ~۹۰-۹۵٪ کل دیابت‌ها

**خلاصه:** نوع ۱ = کمبود انسولین؛ نوع ۲ = مقاومت به انسولین""",

     """🩸 **Type 1 vs Type 2 Diabetes:**

**Type 1:**
• Autoimmune — body destroys insulin-producing cells
• Usually starts in childhood/teens
• Body makes **no insulin**
• Treatment: lifelong insulin injections (mandatory)
• ~5-10% of all diabetes

**Type 2:**
• Insulin resistance — body makes insulin but can't use it
• Usually after age 30-40
• Body makes insulin **but not enough**
• Treatment: diet + exercise → tablets (metformin) → sometimes insulin
• ~90-95% of all diabetes"""),

    (("ویتامین د چقدر", "ویتامین دی چقدر", "دوز ویتامین د", "ویتامین d چقدر", "ویتامین d بخورم"),
     ("vitamin d dose", "vitamin d how much", "vitamin d"),
     """💊 **دوز ویتامین D:**

• **بزرگسالان:** ۶۰۰-۸۰۰ واحد بین‌المللی (IU) در روز
• **بالای ۷۰ سال:** ۸۰۰ IU در روز
• **کمبود شدید (فقط با آزمایش و نظر پزشک):** ۵۰,۰۰۰ واحد هفته‌ای برای ۸ هفته
• **بارداری:** ۶۰۰ IU در روز

**منابع طبیعی:**
• نور خورشید: ۱۰-۱۵ دقیقه، ۲-۳ بار در هفته (بدید ضدآفتاب)
• ماهی چرب (سالمون، تن): ~۳۶۰-۶۰۰ IU در ۱۰۰ گرم
• زرده تخم‌مرغ: ~۴۰ IU

⚠️ دوز بالای ۴,۰۰۰ IU در روز بدون نظر پزشک **مسمومیت** ایجاد می‌کند (کلسیم بالا، سنگ کلیه).""",

     """💊 **Vitamin D dosage:**

• **Adults:** 600-800 IU/day
• **Over 70:** 800 IU/day
• **Severe deficiency (lab + doctor only):** 50,000 IU weekly for 8 weeks
• **Pregnancy:** 600 IU/day

**Sources:** sunlight 10-15 min 2-3×/week; fatty fish 360-600 IU/100g; egg yolk ~40 IU

⚠️ Over 4,000 IU/day without medical supervision can cause toxicity."""),

    (("چرا همیشه خسته", "همیشه خسته‌ام", "دلیل خستگی"),
     ("why am i always tired", "always fatigued"),
     """😴 **دلایل شایع خستگی مداوم:**

**سبک زندگی (شایع‌ترین):**
• کم‌خوابی (زیر ۷ ساعت) یا بی‌کیفیت بودن خواب
• کم‌تحرکی — پارادوکس‌طورانه ورزش انرژی می‌دهد
• تغذیه‌ی ضعیف (قند زیاد → افت انرژی)
• کم‌آبی
• استرس مزمن

**پزشکی (نیاز به آزمایش):**
• کم‌خونی (فقر آهن) → آزمایش CBC + فریتین
• کم‌کاری تیروئید → آزمایش TSH
• کمبود ویتامین D یا B12
• آپنه خواب (خروپف + خواب‌آلودگی روزانه)
• دیابت کنترل‌نشده

**چه کنم؟**
۱. خواب منظم ۷-۹ ساعت
۲. ورزش روزانه ۳۰ دقیقه پیاده‌روی
۳. آب کافی (۸ لیوان)
۴. اگر بعد از ۲-۳ هفته بهتر نشدی → آزمایش CBC، TSH، فریتین، ویتامین D""",

     """😴 **Common causes of persistent fatigue:**

**Lifestyle:** poor sleep (<7h), inactivity, poor diet, dehydration, chronic stress
**Medical (need labs):** anemia (CBC+ferritin), hypothyroidism (TSH), vitamin D/B12 deficiency, sleep apnea, diabetes

**Do:** 7-9h regular sleep, 30 min daily walk, adequate water
**If not better in 2-3 weeks → get CBC, TSH, ferritin, vitamin D checked**"""),
]


def answer_from_qa(message: str) -> str | None:
    """Match a question against the QA knowledge base."""
    fa = _fa()
    low = message.lower().strip()
    for fa_keys, en_keys, ans_fa, ans_en in _QA:
        keys = fa_keys if fa else (en_keys + fa_keys)
        for k in keys:
            if k in low:
                return ans_fa if fa else ans_en
    return None
