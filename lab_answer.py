"""
lab_answer.py — answers lab-value and lifestyle questions GPT-style.
Uses lab_full for interpretation and a small food/exercise knowledge base.
"""
from __future__ import annotations


def _is_fa() -> bool:
    from i18n import is_fa
    return is_fa()


_LAB_PATTERNS = [
    (["قند ناشتا", "قند خون ناشتا", "فس", "fbs", "fasting glucose", "fasting blood sugar"], "fbs"),
    (["قند خون", "قند", "گلوکز", "glucose", "blood sugar"], "fbs"),
    (["ایوانک", "هموگلوبین گلیکوزیله", "hba1c", "a1c", "glycated"], "hba1c"),
    (["کلسترول", "chol", "cholesterol", "tc"], "tchol"),
    (["ال دی ال", "ldl", "کلسترول بد"], "ldl"),
    (["ای دی ال", "hdl", "کلسترول خوب"], "hdl"),
    (["تری گلیسرید", "تریگلیسیرید", "tg", "triglyceride"], "tg"),
    (["هموگلوبین", "همو گلوبین", "hb", "hgb", "hemoglobin"], "hb"),
    (["فریتین", "ferritin"], "ferritin"),
    (["ویتامین دی", "ویتامین د", "vitamin d", "25-oh"], "vitd"),
    (["ویتامین ب ۱۲", "ویتامین ب12", "b12", "کوبالامین"], "b12"),
    (["تiroئید", "تی اس اچ", "tsh", "هورمون تیروئید"], "tsh"),
    (["کراتینین", "creatinine", "cr"], "cr"),
    (["اوره", "یوره", "bun", "azot"], "bun"),
    (["اسید اوریک", "uric acid", "ua"], "ua"),
    (["آهن", "iron", "fe"], "fe"),
    (["سدیم", "sodium", "na"], "na"),
    (["پتاسیم", "potassium", "k"], "k"),
    (["کلسیم", "calcium", "ca"], "ca"),
    (["سفید", "wbc", "لکوسیت"], "wbc"),
    (["پلاکت", "plt", "platelet"], "plt"),
    ([" CRP", "سی آر پی", "crp"], "crp"),
    (["ESR", "سرعت ته‌نشینی", "sed rate"], "esr"),
    (["آلتی", "alt", "sgpt", "آلانین"], "alt"),
    (["آست", "ast", "sgot", "آسپارتات"], "ast"),
    (["آلکالن", "alp", "فسفاتاز"], "alp"),
    (["پروتئین تام", "total protein"], "tpr"),
    (["آلبومین", "albumin", "alb"], "alb"),
    (["PSA", "پی اس ای"], "psa"),
]


def extract_lab_value(message: str):
    """Extract (test_key, value) from a message like 'قند خون ناشتا ۱۱۰ یعنی چی'."""
    import re
    from common_2077 import normalize
    low = message.lower()
    norm = normalize(message)
    persian = "۰۱۲۳۴۵۶۷۸۹"
    m = re.search(r"[\d.,]+", message.translate(str.maketrans(persian, "0123456789")))
    if not m:
        return None
    val = m.group(0).replace(",", ".")
    try:
        val = float(val)
    except ValueError:
        return None
    if not (0.01 <= val <= 100000):
        return None
    for keys, tk in _LAB_PATTERNS:
        for k in keys:
            if k in low or k in norm or k.lower() in low:
                return tk, val
    return None


def answer_lab_question(message: str) -> str | None:
    """Answer 'my fasting sugar is 110, what does it mean' style questions."""
    fa = _is_fa()
    r = extract_lab_value(message)
    if not r:
        return None
    key, val = r
    from lab_full import evaluate, TESTS
    ev = evaluate(key, val, fa)
    if not ev.get("ok") or ev.get("qual"):
        return None
    t = TESTS.get(key, {})
    name = t.get("fa", "") if fa else t.get("en", "")
    lines = []
    lines.append(f" {name}: {ev['value']} {ev.get('unit','')}")
    lines.append("")
    status_fa = {"normal": "نرمال ", "low": "پایین‌تر از حد ", "high": "بالاتر از حد ",
                 "very_low": "خیلی پایین ", "very_high": "خیلی بالا ",
                 "crit_low": "خطرناک پایین ", "crit_high": "خطرناک بالا "}
    status_en = {"normal": "normal ", "low": "below range ", "high": "above range ",
                 "very_low": "far below ", "very_high": "far above ",
                 "crit_low": "CRITICAL LOW ", "crit_high": "CRITICAL HIGH "}
    st = (status_fa if fa else status_en).get(ev["status"], ev["status"])
    lines.append(f"  {st}")
    lines.append(f"  {'بازه‌ی مرجع' if fa else 'Reference'}: {ev['range']}")
    if ev.get("deviation_pct"):
        lines.append(f"  {'انحراف' if fa else 'Deviation'}: {ev['deviation_pct']}%")
    if ev.get("note"):
        lines.append("")
        lines.append(f"  {ev['note'][:200]}")
    lines.append("")
    lines.append((" این تفسیر عمومی است — ملاک، بازه‌ی روی برگه‌ی آزمایش خودت و نظر پزشک است." if fa
                 else "General info — your own lab sheet's range and your doctor's judgment apply."))
    return "\n".join(lines)


_FOOD_TIPS = {
    "hypertension": (
        ["نمک را کم کن (زیر ۵ گرم در روز)", "سبزیجات و میوه‌ی تازه بیشتر", "ماهی ۲ بار در هفته",
         "غذای فرآوری‌شده و فست‌فود کمتر", "کافئین و الکل محدود", "وزن مناسب و ورزش روزانه ۳۰ دقیقه پیاده‌روی"],
        "food for high blood pressure"),
    "diabetes": (
        ["کربوهیدرات‌های تصفیه‌شده (نان سفید، قند) کم", "نان سبوس‌دار و حبوبات", "سبزیجات فیبردار",
         "۳ وعده‌ی منظم، میان‌وعده‌ی سالم", "نوشیدنی‌های شیرین ممنوع", "پروتئین کم‌چرب (مرغ، ماهی، حبوبات)"],
        "food for diabetes"),
    "anemia": (
        ["غذاهای غنی از آهن: گوشت قرمز کم‌چرب، جگر، عدس، اسفناج", "ویتامین C همراه غذا (آب‌لیمو روی سالاد) جذب آهن را زیاد می‌کند",
         "چای و قهوه همراه غذا نخور (جذب آهن را کم می‌کند)", "مکمل آهن فقط با تجویز پزشک"],
        "food for anemia"),
    "high_cholesterol": (
        ["چربی اشباع (کره، گوشت چرب) کم", "ماهی چرب (سالمون، ساردین) ۲ بار در هفته",
         "آجیل و روغن زیتون", "فیبر محلول: جو دوسر، حبوبات", "تخم‌مرغ زیاده‌روی نشود"],
        "food for high cholesterol"),
}


def answer_lifestyle_question(message: str) -> str | None:
    """Answer food/diet/exercise questions using condition context."""
    fa = _is_fa()
    low = message.lower()
    wants_food = any(k in low for k in ("غذا", "غذایی", "بخوره", "بخورم", "بخور", "رژیم", "diet", "food", "eat"))
    wants_ex = any(k in low for k in ("ورزش", "ورزشی", "exercise", "sport", "workout"))
    if not (wants_food or wants_ex):
        return None
    cond = None
    if any(k in low for k in ("فشار خون", "hypertens", "پرفشاری")):
        cond = "hypertension"
    elif any(k in low for k in ("دیابت", "قند", "diabet", "sugar")):
        cond = "diabetes"
    elif any(k in low for k in ("کم‌خونی", "کم خونی", "آهن", "anemia", "iron")):
        cond = "anemia"
    elif any(k in low for k in ("کلسترول", "چربی خون", "cholesterol", "lipid")):
        cond = "high_cholesterol"
    elif any(k in low for k in ("آسم", "asthma")):
        if wants_ex:
            return (" **ورزش با آسم:**\n\n" "• بله، ورزش مجاز و حتی مفید است — با کنترل درست\n" "• اسپری تسکین‌دهنده را ۱۵ دقیقه قبل از ورزش استفاده کن (اگر پزشک گفته)\n" "• گرم‌کردن طولانی (۱۰-۱۵ دقیقه) انجام بده\n" "• ورزش‌های مناسب: شنا، پیاده‌روی، دوچرخه\n" "• هوای سرد و خشک می‌تواند حملات را تحریک کند — در پاییز/زمستان داخل خانه ورزش کن\n" "• اسپری اضطراری همیشه همراهت باشد\n\n اگر حین ورزش تنگی نفس شدنی، ورزش را قطع کن و اسپری بزن.") if fa else \
                   (" **Exercise with asthma:**\n\n" "• Yes, exercise is fine with proper control\n" "• Use reliever inhaler 15 min before exercise (if prescribed)\n" "• Long warm-up (10-15 min)\n" "• Good options: swimming, walking, cycling\n" "• Cold dry air can trigger attacks\n" "• Always carry your rescue inhaler")
        return None
    if not cond:
        return None
    tips = _FOOD_TIPS.get(cond)
    if not tips:
        return None
    tip_list = tips[0]
    names = {"hypertension": "فشار خون بالا", "diabetes": "دیابت",
             "anemia": "کم‌خونی", "high_cholesterol": "کلسترول بالا"}
    lines = [f" {'تغذیه برای' if fa else 'Diet for'} {names[cond] if fa else cond}:", ""]
    for t in tip_list:
        lines.append(f"  • {t}")
    lines.append("")
    lines.append(" " + ("تغییرات را تدریجی شروع کن و با پزشک یا متخصص تغذیه هماهنگ باش." if fa
                          else "Start changes gradually and coordinate with your doctor."))
    return "\n".join(lines)
