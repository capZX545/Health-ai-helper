"""
first_aid.py — bilingual first aid guides: CPR with a 110 bpm metronome,
stroke (FAST), choking, burns, heart attack, seizure, bleeding.
Educational guidance based on general first aid principles; it never replaces
the emergency services.
"""
from __future__ import annotations

from typing import Any

from i18n import pick

CPR_BPM = 110
EMERGENCY_LINE = {"fa": "ایران: ۱۱۵ | اروپا/فنلاند: ۱۱۲", "en": "Iran: 115 | Europe/Finland: 112"}

TOPICS: dict[str, dict[str, Any]] = {
    "cpr": {
        "title": {"fa": "CPR — احیای قلبی‌ریوی بزرگسال", "en": "CPR - adult cardiopulmonary resuscitation"},
        "steps": {
            "fa": [
                "۱) ایمنی صحنه را چک کن؛ اگر واکنشی نبود، فریاد کمک و از اطرافیان بخواه اورژانس (۱۱۵/۱۱۲) را زنگ بزند.",
                "۲) راه هوایی: سر را به عقب، چانه را بالا؛ تنفس را حداکثر ۱۰ ثانیه ببین/شنو/حس کن.",
                "۳) اگر تنفس نیست یا فقط گس‌گس می‌زند: CPR را شروع کن.",
                "۴) مرکز قفسه سینه (بین نوک پستان‌ها)، عمق ۵–۶ سانتی‌متر، سرعت حدود ۱۱۰ در دقیقه.",
                "۵) نسبت ۳۰ فشار به ۲ نفس دهانی (اگر آموزش دیده‌ای؛ وگرنه فقط فشار بدون وقفه).",
                "۶) تا رسیدن اورژانس یا برگشت تنفس ادامه بده؛ هر ۲ دقیقه نوبت را با دیگری عوض کن.",
                "۷) اگر AED (دفیبریلاتور) موجود است، هرچه سریع‌تر متصل کن و از صدای دستگاه پیروی کن.",
            ],
            "en": [
                "1) Make sure the scene is safe. If the person is unresponsive, shout for help and have someone call emergency services (115/112).",
                "2) Airway: tilt the head back, lift the chin; look, listen and feel for breathing for up to 10 seconds.",
                "3) If there is no breathing, or only gasping: start CPR.",
                "4) Push the centre of the chest (between the nipples), 5-6 cm deep, at about 110 per minute.",
                "5) 30 compressions to 2 rescue breaths (if trained; otherwise continuous compressions).",
                "6) Continue until help arrives or breathing returns; swap with another rescuer every 2 minutes.",
                "7) If an AED is available, attach it as soon as possible and follow its voice prompts.",
            ],
        },
        "metronome_bpm": CPR_BPM,
        "warnings": {
            "fa": ["پس از برگشت تنفس: POSITION RECOVERY (پهلو) و پایش تنفس."],
            "en": ["After breathing returns: recovery position (on the side) and keep monitoring."],
        },
    },
    "heart_attack": {
        "title": {"fa": "حمله‌ی قلبی مشکوک", "en": "Suspected heart attack"},
        "steps": {
            "fa": [
                "۱) فوراً اورژانس (۱۱۵/۱۱۲)؛ در فنلاند ۱۱۲.",
                "۲) بیمار را بنشان/بخوابان، فعالیت صفر، لب گشاد.",
                "۳) اگر بیمار خودش آسپرین جویدنی دارد و حساسیت/خونریزی فعال ندارد، اورژانس تلفنی ممکن است جویدن آسپرین معمولی (نه انتریک) بگوید — فقط با تایید اورژانس.",
                "۴) نیترات قطره/اسپری فقط اگر قبلاً برای بیمار تجویز شده.",
                "۵) اگر بیهوش شد و نفس نمی‌زند: CPR + AED.",
            ],
            "en": [
                "1) Call emergency services immediately (115/112; Finland 112).",
                "2) Sit or lay the person down, zero exertion, loosen clothing.",
                "3) If the person has regular chewable aspirin and no allergy or active bleeding, the dispatcher may advise chewing it - only with their approval.",
                "4) Nitroglycerin spray/drops only if previously prescribed for this person.",
                "5) If they become unconscious and stop breathing: CPR + AED.",
            ],
        },
        "warnings": {
            "fa": ["در خانم‌ها/دیابتی‌ها ممکن است فقط تهوع، خستگی شدید یا درد فک باشد.", "هر دقیقه تأخیر، عضله‌ی قلب را بیشتر آسیب می‌زند."],
            "en": ["In women and diabetics the only signs may be nausea, severe fatigue or jaw pain.", "Every minute of delay costs heart muscle."],
        },
    },
    "stroke": {
        "title": {"fa": "سکته‌ی مغزی — FAST", "en": "Stroke - FAST"},
        "steps": {
            "fa": [
                "۱) F (Face): از بیمار بخند؛ آیا یک طرف صورت افتاده است؟",
                "۲) A (Arm): هر دو دست را بالا بیاورد؛ آیا یک طرف می‌افتد؟",
                "۳) S (Speech): جمله بگوید؛ آیا نامفهوم است؟",
                "۴) T (Time): اگر هر مورد مثابت است → همین حالا اورژانس؛ زمان شروع علائم را دقیق یادداشت کن (برای داروهای لخته‌بازکن).",
                "۵) به بیمار آب/غذا/داروی خوراکی نده؛ اگر بیهوش شد، به پهلو بخوابان.",
            ],
            "en": [
                "1) F (Face): ask them to smile; is one side drooping?",
                "2) A (Arms): raise both arms; does one drift down?",
                "3) S (Speech): ask for a sentence; is it slurred or strange?",
                "4) T (Time): if any sign is positive, call emergency services now and note the exact onset time (it decides clot-busting treatment).",
                "5) Give no food, water or oral medication; if unconscious, roll them on their side.",
            ],
        },
        "warnings": {
            "fa": ["پنجره‌ی طلایی درمان معمولاً کمتر از ۴٫۵ ساعت است.", "علائم گذرا (TIA) هم اورژانس است."],
            "en": ["The golden treatment window is usually under 4.5 hours.", "Temporary symptoms (TIA) are also an emergency."],
        },
    },
    "choking": {
        "title": {"fa": "خفگی — مانور هایملیخ", "en": "Choking - Heimlich maneuver"},
        "steps": {
            "fa": [
                "۱) آیا می‌تواند سرفه بزند؟ اگر بله: تشویق به سرفه‌ی قوی؛ دخالت نکن.",
                "۲) اگر سرفه نمی‌کند و نفس‌گیر است: ۵ ضربه‌ی پشتی بین کتف‌ها با پنجه‌ی دست.",
                "۳) سپس ۵ فشار شکمی (هایملیخ): مشت بالای ناف، به داخل و بالا.",
                "۴) چرخه‌ی ۵ ضربه / ۵ فشار را تکرار کن تا خروج جسم یا افت هوشیاری.",
                "۵) اگر بیهوش شد: CPR شروع کن و اورژانس.",
                "۶) نوزاد زیر ۱ سال: ۵ ضربه‌ی پشتی با پنجه + ۵ فشار سینه با دو انگشت؛ هرگز مانور شکمی نزن.",
            ],
            "en": [
                "1) Can they cough? If yes: encourage strong coughs; do not interfere.",
                "2) If they cannot cough and cannot breathe: 5 back blows between the shoulder blades with the heel of your hand.",
                "3) Then 5 abdominal thrusts (Heimlich): fist above the navel, in and up.",
                "4) Alternate 5 blows / 5 thrusts until the object comes out or they collapse.",
                "5) If they become unconscious: start CPR and call emergency services.",
                "6) Infants under 1 year: 5 back blows + 5 chest thrusts with two fingers; never abdominal thrusts.",
            ],
        },
        "warnings": {
            "fa": ["بعد از مانور موفق، حتی بدون علامت هم معاینه در بیمارستان توصیه می‌شود."],
            "en": ["Even after a successful maneuver, a medical check is recommended."],
        },
    },
    "burn": {
        "title": {"fa": "سوختگی حرارتی", "en": "Thermal burn"},
        "steps": {
            "fa": [
                "۱) منبع حرارت را قطع کن؛ لباس سوخته/باز را جدا کن (مگر چسبیده به پوست).",
                "۲) آب خنک جاری (نه یخ) به مدت ۱۰ تا ۲۰ دقیقه.",
                "۳) ضماد استریل یا پارچه‌ی تمیز غیرپرزدار؛ بدون پنبه، بدون خمیردندان، بدون یخ.",
                "۴) تاول را نترکان.",
                "۵) مسکن ساده مثل استامینوفن در صورت نیاز.",
                "۶) اورژانس اگر: سوختگی صورت/دست/اندام تناسلی، سطح وسیع، عمق درجه ۳، سوختگی الکتریکی/شیمیایی یا مشکل تنفسی.",
            ],
            "en": [
                "1) Stop the heat source; remove loose or burnt clothing (unless stuck to the skin).",
                "2) Cool running water (not ice) for 10 to 20 minutes.",
                "3) Sterile dressing or clean non-fluffy cloth; no cotton, no toothpaste, no ice.",
                "4) Do not pop blisters.",
                "5) Simple pain relief such as paracetamol if needed.",
                "6) Emergency if: burns to face/hands/genitals, large area, full thickness, electrical/chemical burn, or breathing problems.",
            ],
        },
        "warnings": {
            "fa": ["سوختگی شیمیایی: اول شست‌وشوی فراوان با آب (۲۰ دقیقه+) سپس اورژانس."],
            "en": ["Chemical burns: flush generously with water first (20+ minutes), then emergency care."],
        },
    },
    "seizure": {
        "title": {"fa": "تشنج", "en": "Seizure"},
        "steps": {
            "fa": [
                "۱) زمان‌سنجی شروع کن؛ اشیای خطرناک را دور کن.",
                "۲) زیر سر چیزی نرم بگذار؛ بعد از تشنج به پهلو (POSITION RECOVERY).",
                "۳) هیچ‌چیز در دهان نگذار؛ حرکت‌دادن شدید ممنوع.",
                "۴) بیش از ۵ دقیقه، تکرار حمله، آسیب، بارداری، یا اولین تجربه → اورژانس.",
                "۵) پس از تشنج: خواب‌آلودگی طبیعی است؛ پایش تنفس تا هوشیاری کامل.",
            ],
            "en": [
                "1) Time the seizure; move dangerous objects away.",
                "2) Put something soft under the head; after it ends, roll to the recovery position.",
                "3) Never put anything in the mouth; do not restrain movements.",
                "4) Over 5 minutes, repeated seizures, injury, pregnancy, or a first-ever seizure - emergency.",
                "5) Afterward sleepiness is normal; monitor breathing until fully alert.",
            ],
        },
        "warnings": {"fa": [], "en": []},
    },
    "bleeding": {
        "title": {"fa": "خونریزی شدید", "en": "Severe bleeding"},
        "steps": {
            "fa": [
                "۱) فشار مستقیم با پارچه‌ی تمیز؛ دست‌ها را در صورت امکان محافظت کن.",
                "۲) اندام را بالاتر از سطح قلب نگه دار (در صورت نبود شکستگی مشکوک).",
                "۳) اگر پارچه خیس شد، رویش اضافه کن؛ جایگزین نکن.",
                "۴) تورنیکه فقط در خونریزی غیرقابل کنترل اندام و با آموزش؛ زمان بستن را یادداشت کن.",
                "۵) اورژانس + پایش علائم شوک (سردی، رنگ‌پریدگی، تنگی نفس، گیجی).",
            ],
            "en": [
                "1) Direct pressure with a clean cloth; protect your hands if possible.",
                "2) Raise the limb above heart level (if no suspected fracture).",
                "3) If the cloth soaks through, add more on top; do not remove it.",
                "4) A tourniquet only for uncontrollable limb bleeding and only if trained; note the time.",
                "5) Emergency services + watch for shock (cold, pale, breathless, confused).",
            ],
        },
        "warnings": {"fa": [], "en": []},
    },
}


def get_topic(key: str) -> dict[str, Any] | None:
    t = TOPICS.get(key)
    if not t:
        return None
    from common_2077 import MEDICAL_DISCLAIMER
    out = {
        "key": key,
        "title": pick(t["title"]),
        "steps": pick(t["steps"]),
        "warnings": pick(t.get("warnings", {"fa": [], "en": []})),
        "emergency_line": pick(EMERGENCY_LINE),
        "disclaimer": pick({
            "fa": "آموزش عمومی اولیا؛ در همه‌ی موارد با اورژانس هماهنگ باش. " + EMERGENCY_LINE["fa"],
            "en": "General first-aid guidance; coordinate with emergency services in every case. " + EMERGENCY_LINE["en"],
        }) + " | " + MEDICAL_DISCLAIMER(),
    }
    if t.get("metronome_bpm"):
        out["metronome_bpm"] = t["metronome_bpm"]
    return out


def list_topics() -> list[dict[str, str]]:
    return [{"key": k, "title": pick(v["title"])} for k, v in TOPICS.items()]


def cpr_timing() -> dict[str, Any]:
    from i18n import is_fa
    interval = 60.0 / CPR_BPM
    return {"bpm": CPR_BPM, "interval_sec": round(interval, 3),
            "depth_cm": "۵–۶ سانتی‌متر" if is_fa() else "5-6 cm",
            "ratio": "30:2", "emergency_line": pick(EMERGENCY_LINE)}
