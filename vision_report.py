"""
vision_report.py — turns the internal vision engine's structured findings
into a clear bilingual explanation: what the image shows, WHERE the damage
is, where things look healthy, what it may mean in plain language and how
urgent it looks. No external AI involved.
"""
from __future__ import annotations

from typing import Any

INFO: dict[str, dict[str, Any]] = {
    "lesion": {
        "n": ("a skin lesion", "ضایعه‌ی پوستی"),
        "x": ("a spot or bump that looks distinct from the surrounding skin; it can be a mole, inflammatory or infectious.",
              "لکه یا برجستگی‌ای که از پوست اطرافش متمایز دیده می‌شود؛ می‌تواند خال، التهابی یا عفونی باشد."),
        "a": ("if its border is irregular, its color uneven, it is larger than 6 mm, or it has changed recently, a dermatologist should evaluate it.",
              "اگر حاشیه‌اش نامنظم، رنگش ناهمگون یا قطرش بیشتر از ۶ میلی‌متر است یا اخیراً تغییر کرده، ارزیابی متخصص پوست لازم است."),
        "lvl": "routine"},
    "bruise": {
        "n": ("a bruise", "کبودی"),
        "x": ("blood leaked under the skin, usually after a bump; it typically fades over 1-2 weeks.",
              "خونریزی زیر پوست؛ معمولاً بعد از ضربه و طی ۱ تا ۲ هفته خودش جذب می‌شود."),
        "a": ("if it grows without a clear injury, or you are on blood thinners, check with a doctor.",
              "اگر بدون ضربه‌ی واضح بزرگ می‌شود یا داروی رقیق‌کننده مصرف می‌کنی، با پزشک مشورت کن."),
        "lvl": "routine"},
    "burn": {
        "n": ("a burn-like red area", "ناحیه‌ی قرمز سوختگی‌مانند"),
        "x": ("focal redness consistent with a superficial burn.",
              "قرمزی موضعی که با سوختگی سطحی سازگار است."),
        "a": ("20 minutes of cool running water; do not pop blisters; aloe or burn ointment and a clean cover. Larger than a palm, or on hand/face/genitals - see a doctor.",
              "۲۰ دقیقه آب خنک جاری؛ تاول را نترکان؛ ژل آلوئه یا پماد سوختگی و پوشش تمیز. بزرگ‌تر از کف دست یا در دست/صورت/اندام تناسلی → پزشک."),
        "lvl": "urgent"},
    "granulation": {
        "n": ("red granulation tissue (healing)", "بافت قرمز گرانوله (در حال ترمیم)"),
        "x": ("this beefy red tissue is a good sign: the wound is healing.",
              "این بافت قرمز حبه‌ای، علامت خوب است: زخم در حال ترمیم است."),
        "a": ("keep the wound clean and moist; a proper dressing speeds healing.",
              "زخم را تمیز و مرطوب نگه دار؛ پانسمان مناسب سرعت ترمیم را بالا می‌برد."),
        "lvl": "routine"},
    "slough": {
        "n": ("yellow slough tissue", "بافت زرد (اسلاف)"),
        "x": ("soft yellow/cream tissue on the wound bed that slows healing.",
              "بافت زرد/کرم روی بستر زخم که ترمیم را کند می‌کند."),
        "a": ("this layer should be removed with proper wound cleansing; a wound-care nurse decides the route.",
              "این لایه باید با پاک‌سازی مناسب برداشته شود؛ تیم زخم/پرستار مسیرش را مشخص می‌کند."),
        "lvl": "routine"},
    "eschar": {
        "n": ("black eschar", "بافت سیاه‌رنگ (اسکار)"),
        "x": ("dead black tissue on a wound; seen in burns and pressure ulcers.",
              "بافت مرده‌ی سیاه روی زخم؛ در سوختگی‌ها و زخم‌های فشاری دیده می‌شود."),
        "a": ("do not debride it yourself; the wound needs assessment because infection can hide underneath.",
              "خودت جدا نکن؛ ارزیابی زخم لازم است چون زیر آن عفونت می‌تواند پنهان باشد."),
        "lvl": "urgent"},
    "opacity": {
        "n": ("an area brighter than expected (opacity)", "ناحیه‌ی روشن‌تر از طبیعت (اپیسیتی)"),
        "x": ("on a radiograph, an area looking whiter can represent fluid, secretions, tissue thickening or inflammation.",
              "در تصویر رادیولوژی، سفیدتر دیده شدن یک ناحیه می‌تواند معنای مایع، ترشح، ضخامت بافت یا التهاب داشته باشد."),
        "a": ("the final read belongs to a radiologist and your doctor; this is a machine-vision finding, not a diagnosis.",
              "تفسیر نهایی تصویر با رادیولوژیست و پزشکت است؛ این یافته‌ی ماشین‌بین است، نه تشخیص."),
        "lvl": "urgent"},
    "exudate": {
        "n": ("bright exudates", "رسوبات روشن (اگزودیت)"),
        "x": ("bright yellow-white dots in a retina photo; often linked to diabetes or high lipids.",
              "نقاط روشن-زرد در عکس شبکیه؛ اغلب با دیابت یا بالا بودن چربی خون مرتبط‌اند."),
        "a": ("an ophthalmologist evaluation plus glucose/lipid control is advised.",
              "ارزیابی چشم‌پزشک و کنترل قند/چربی خون توصیه می‌شود."),
        "lvl": "urgent"},
    "density_abnormality": {
        "n": ("an area of abnormal density", "ناحیه‌ای با چگالی غیرطبیعی"),
        "x": ("a region whose brightness clearly differs from the surrounding tissue of the same image.",
              "ناحیه‌ای که روشنایی‌اش به‌وضوح از بافت اطراف در همان تصویر متفاوت است."),
        "a": ("the engine located the area but could not name the cause with confidence - fluid, bleeding, inflammation, scar or mass can all look like this; a doctor must read the original images.",
              "موتور ناحیه را پیدا کرد اما علت را با اطمینان نام‌گذاری نکرد — مایع، خونریزی، التهاب، اسکار یا توده همگی می‌توانند این‌طور دیده شوند؛ پزشک باید تصاویر اصلی را ببیند."),
        "lvl": "urgent"},
    "nevus": {
        "n": ("a mole (nevus)", "خال (نووس)"),
        "x": ("a pigmented mole; most are benign, but they deserve watching for change.",
              "خال رنگدانه‌دار؛ اکثراً خوش‌خیم‌اند اما باید تغییرشان را زیر نظر گرفت."),
        "a": ("photograph it next to a ruler today and re-shoot monthly; if it grows, changes color or develops an irregular border, show it to a dermatologist.",
              "امروز کنار خط‌کش ازش عکس بگیر و ماهانه تکرار کن؛ اگر بزرگ شد، رنگش تغییر کرد یا حاشیه‌اش نامنظم شد، به متخصص پوست نشان بده."),
        "lvl": "routine"},
    "melanoma_susp": {
        "n": ("a pigmented lesion with concerning features", "ضایعه‌ی رنگدانه‌دار با ویژگی‌های نگران‌کننده"),
        "x": ("the pattern (asymmetry, irregular border, uneven color, size) overlaps with what skin-cancer screening looks for.",
              "الگوی آن (عدم تقارن، حاشیه‌ی نامنظم، رنگ ناهمگون، اندازه) با چیزی که غربالگری سرطان پوست دنبالش است هم‌پوشانی دارد."),
        "a": ("this is a machine-vision flag, NOT a diagnosis - but a lesion like this should be shown to a dermatologist soon; do not delay.",
              "این پرچم ماشین‌بین است، نه تشخیص — اما چنین ضایعه‌ای باید به‌زودی به متخصص پوست نشان داده شود؛ به تعویق نینداز."),
        "lvl": "urgent"},
    "mass_tumor": {
        "n": ("a mass / tumor-like area", "توده / ناحیه‌ی توموری"),
        "x": ("a discrete bright or dark region with mass effect, standing out from the surrounding tissue.",
              "ناحیه‌ی مجزا و برجسته‌ی روشن یا تیره که از بافت اطرافش متمایز است."),
        "a": ("a mass on any imaging needs a doctor's review with the original files; bring the CD/images to a specialist promptly.",
              "توده در هر تصویربرداری نیازمند بررسی پزشک با فایل‌های اصلی است؛ سی‌دی یا تصاویر را به‌سرعت به متخصص ببر."),
        "lvl": "urgent"},
    "pneumonia": {
        "n": ("a lung opacity consistent with consolidation", "اپیسیتی ریه سازگار با تصلب"),
        "x": ("a whiter patch inside the lung field - the pattern pneumonia, edema or bleeding can produce.",
              "لکه‌ی سفیدتر داخل میدان ریه — الگویی که پنومونی، ادم یا خونریزی می‌تواند بسازد."),
        "a": ("with fever, cough or breathlessness this combination needs same-day medical evaluation; chest imaging is always interpreted together with the exam.",
              "با تب، سرفه یا تنگی نفس، این ترکیب همان روز نیاز به بررسی پزشکی دارد؛ تصویر قفسه سینه همیشه همراه معاینه تفسیر می‌شود."),
        "lvl": "urgent"},
    "fracture": {
        "n": ("a suspected fracture line", "خط شکستگی مشکوک"),
        "x": ("a discontinuity in the bone contour with a dense rim around it.",
              "وقفه در خط استخوان با حاشیه‌ی متراکم اطرافش."),
        "a": ("immobilize, do not bear weight, and get an in-person X-ray review; machine vision can miss or overcall subtle fractures.",
              "بی‌حرکت کن، وزن نینداز و نظر حضوری روی رادیولوژی بگیر؛ ماشین‌بین ممکن است شکستگی‌های ظریف را از دست بدهد یا بیشتر از حد نشان دهد."),
        "lvl": "urgent"},
    "infarct": {
        "n": ("a region compatible with infarct (stroke territory)", "ناحیه‌ای سازگار با سکته (قلمرو انفارکت)"),
        "x": ("a wedge-shaped area with density change in a vascular territory.",
              "ناحیه‌ی گُوه‌ای با تغییر چگالی در قلمروی عروقی."),
        "a": ("if this is acute (sudden weakness, speech or vision problem), it is an EMERGENCY - call 115/112 immediately; time determines the treatment window.",
              "اگر حاد است (ضعف ناگهانی، اختلال تکلم یا بینایی) اورژانسی است — فوراً ۱۱۵/۱۱۲ زنگ بزن؛ زمان، پنجره‌ی درمان را تعیین می‌کند."),
        "lvl": "urgent"},
    "hemorrhage": {
        "n": ("hemorrhage", "خونریزی"),
        "x": ("dark blood patches in the image; in the retina they can signal serious vascular problems.",
              "لکه‌های تیره‌ی خونی در تصویر؛ در شبکیه می‌تواند نشانه‌ی مشکلات جدی عروقی باشد."),
        "a": ("retinal hemorrhage needs a prompt eye exam - especially with any vision loss.",
              "در خونریزی شبکیه، معاینه‌ی فوری چشم لازم است — به‌خصوص با کاهش دید."),
        "lvl": "urgent"},
}


def build(vision: dict, type_key: str, fa: bool) -> list[str] | None:
    if not vision or not vision.get("ok"):
        return None
    regions = vision.get("regions") or []
    healthy = vision.get("healthy_pct", 100.0)
    L = (lambda a, b: b) if fa else (lambda a, b: a)
    out: list[str] = []
    head = L("Internal vision analysis (offline, no external AI)",
             "تحلیل بینایی داخلی (آفلاین — بدون AI خارجی)")
    out.append(head)
    if regions:
        out.append("")
        out.append(L("Where the damage is:", "کجا آسیب دیده:"))
        for r in regions:
            info = INFO.get(r["label"], {})
            name = info.get("n", (r["label"], r["label"]))[1 if fa else 0]
            where = r["where_fa" if fa else "where_en"]
            out.append(f"• {name} — {where}"
                       + L(f" (~{r['area_pct']}% of the image, confidence {int(r['conf'] * 100)}%)",
                           f" (حدود {r['area_pct']}٪ تصویر، اطمینان {int(r['conf'] * 100)}٪)"))
        out.append("")
        out.append(L("What it looks like, in plain language:", "به زبان ساده چه دیده می‌شود:"))
        for r in regions:
            info = INFO.get(r["label"], {})
            expl = info.get("x")
            adv = info.get("a")
            if expl:
                out.append("• " + (expl[1] if fa else expl[0]))
            if adv:
                out.append("  " + (adv[1] if fa else adv[0]))
    else:
        out.append(L("No clearly abnormal region was found by the internal vision model.",
                     "موتور بینایی داخلی ناحیه‌ی غیرطبیعی واضحی پیدا نکرد."))
    out.append("")
    out.append(L("Where it looks healthy:", "کجا سالم است:"))
    out.append(L(f"About {healthy}% of the analyzed area appears normal for this kind of image.",
                 f"حدود {healthy}٪ ناحیه‌ی تحلیل‌شده برای این نوع تصویر طبیعی به نظر می‌رسد."))
    urgent = [r for r in regions if INFO.get(r["label"], {}).get("lvl") == "urgent"]
    if urgent:
        out.append("")
        out.append(L("Urgency note: at least one finding looks like it deserves a prompt professional look - read the advice lines above.",
                     "یادداشت فوریت: حداقل یکی از یافته‌ها ارزش بررسی سریع توسط متخصص را دارد — توصیه‌های بالا را بخوان."))
    return out
