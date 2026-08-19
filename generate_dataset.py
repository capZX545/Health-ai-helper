# -*- coding: utf-8 -*-
"""
generate_dataset.py — ساخت دیتاست مصنوعی medical_ml_test_dataset.csv (۱۰۰۰ ردیف). فقط برای تست روش‌های ماشین لرنینگ — نه برای استفاده‌ی پزشکی واقعی.
اجرا: python generate_dataset.py
"""
from __future__ import annotations

import csv
import os
import random

random.seed(2077)

ROWS = 1000
NOTE = "synthetic_for_ml_testing_not_clinical"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medical_ml_test_dataset.csv")

LABELS = {
    "سرماخوردگی": {"fever": 0.35, "cough": 0.85, "sore_throat": 0.65, "runny_nose": 0.9, "sneezing": 0.75, "body_ache": 0.3, "headache": 0.3, "red": 0.0},
    "آنفلوآنزا": {"fever": 0.9, "cough": 0.7, "sore_throat": 0.35, "runny_nose": 0.4, "sneezing": 0.2, "body_ache": 0.9, "headache": 0.7, "red": 0.01},
    "آلرژی فصلی": {"fever": 0.02, "cough": 0.25, "sore_throat": 0.15, "runny_nose": 0.95, "sneezing": 0.95, "body_ache": 0.05, "headache": 0.1, "red": 0.0},
    "میگرن احتمالی": {"fever": 0.01, "cough": 0.05, "sore_throat": 0.02, "runny_nose": 0.05, "sneezing": 0.02, "body_ache": 0.2, "headache": 1.0, "nausea": 0.6, "red": 0.0},
    "گاستروانتریت": {"fever": 0.35, "cough": 0.05, "sore_throat": 0.05, "runny_nose": 0.05, "sneezing": 0.02, "body_ache": 0.2, "headache": 0.1, "nausea": 0.8, "vomiting": 0.65, "diarrhea": 0.95, "abdominal_pain": 0.8, "red": 0.0},
    "عفونت ادراری احتمالی": {"fever": 0.25, "cough": 0.02, "sore_throat": 0.02, "runny_nose": 0.02, "sneezing": 0.0, "body_ache": 0.15, "headache": 0.1, "dysuria": 0.95, "urinary_frequency": 0.85, "red": 0.0},
    "اضطراب/استرس": {"fever": 0.01, "cough": 0.05, "sore_throat": 0.02, "runny_nose": 0.02, "sneezing": 0.02, "body_ache": 0.15, "headache": 0.3, "anxiety": 1.0, "red": 0.0},
    "فشار خون بالا احتمالی": {"fever": 0.02, "cough": 0.05, "sore_throat": 0.02, "runny_nose": 0.02, "sneezing": 0.0, "body_ache": 0.1, "headache": 0.55, "chest_pain": 0.1, "red": 0.0, "bp_high": True},
    "قند خون بالا احتمالی": {"fever": 0.02, "cough": 0.05, "sore_throat": 0.02, "runny_nose": 0.02, "sneezing": 0.0, "body_ache": 0.15, "headache": 0.2, "thirst": 0.9, "gluc_high": True, "red": 0.0},
    "نیاز به بررسی فوری": {"fever": 0.4, "cough": 0.2, "sore_throat": 0.05, "runny_nose": 0.05, "sneezing": 0.02, "body_ache": 0.3, "headache": 0.4, "chest_pain": 0.85, "shortness_of_breath": 0.7, "red": 1.0},
}

BIN_COLS = ["cough", "fever", "sore_throat", "runny_nose", "body_ache", "headache", "nausea", "vomiting",
            "diarrhea", "abdominal_pain", "dysuria", "urinary_frequency", "skin_itch", "rash", "sneezing",
            "anxiety", "chest_pain", "shortness_of_breath"]

TEXT_TMPL = {
    "سرماخوردگی": ["سرفه و آبریزش بینی دارم", "گلویم درد می‌کند و عطسه می‌کنم", "دو روز است سرما خورده‌ام"],
    "آنفلوآنزا": ["تب بالا و بدن‌درد شدید دارم", "کل بدنم درد می‌کند و تب دارم", "خسته و تب‌دار هستم"],
    "آلرژی فصلی": ["مدام عطسه می‌کنم و بینیم آب می‌ریزد", "چشمم اشک می‌ریزد و عطسه دارم", "آلرژی فصلی گرفته‌ام"],
    "میگرن احتمالی": ["سردرد یک طرفه با تهوع دارم", "نور چشمم را می‌آذارد و سرم درد می‌کند", "میگرن گرفته‌ام"],
    "گاستروانتریت": ["اسهال و استفراغ دارم", "شکمم درد می‌کند و اسهال کردم", "دل‌درد و اسهال آبکی دارم"],
    "عفونت ادراری احتمالی": ["سوزش ادرار دارم", "تکرر ادرار و سوزش دارم", "موقع ادرار سوزش می‌گیرم"],
    "اضطراب/استرس": ["مضطربم و قلبم تند می‌زند", "استرس دارم و نمی‌توانم بخوابم", "بی‌قرار و نگران هستم"],
    "فشار خون بالا احتمالی": ["سرگیجه و سردرد دارم", "فشارم بالا آمده بود", "پشت گردنم درد می‌گیرد"],
    "قند خون بالا احتمالی": ["مدام تشنه‌ام و زیاد دستشویی می‌روم", "خستگی زیاد و تشنگی دارم", "وزنم کم شده و تشنه‌ام"],
    "نیاز به بررسی فوری": ["درد قفسه سینه دارم", "درد سینه با تنگی نفس", "نفسم بند می‌آید و سینه‌ام درد می‌کند"],
}

LABEL_WEIGHTS = [0.16, 0.12, 0.12, 0.10, 0.10, 0.08, 0.10, 0.07, 0.07, 0.08]
URGENCY = {"سرماخوردگی": "routine", "آنفلوآنزا": "routine", "آلرژی فصلی": "routine", "میگرن احتمالی": "routine",
           "گاستروانتریت": "routine", "عفونت ادراری احتمالی": "routine", "اضطراب/استرس": "routine",
           "فشار خون بالا احتمالی": "urgent", "قند خون بالا احتمالی": "urgent", "نیاز به بررسی فوری": "emergency"}


def pick_binomial(label_cfg: dict, col: str, default_p: float = 0.05) -> int:
    p = label_cfg.get(col, default_p)
    return 1 if random.random() < p else 0


def gen_row(i: int) -> dict:
    label = random.choices(list(LABELS.keys()), weights=LABEL_WEIGHTS, k=1)[0]
    cfg = LABELS[label]
    age = random.randint(8, 85)
    gender = random.choice([0, 1])
    duration = max(1, min(60, int(random.expovariate(1 / 4))))
    fever = pick_binomial(cfg, "fever")
    temp = round(36.6 + (random.uniform(0.9, 3.3) if fever else random.uniform(-0.3, 0.4)), 1)
    hr = int(72 + (18 if fever else 0) + random.gauss(0, 7) + (6 if cfg.get("anxiety") else 0))
    bp_high = bool(cfg.get("bp_high"))
    sys_bp = int(random.uniform(140, 185) if bp_high else random.uniform(95, 135))
    dia_bp = int(random.uniform(90, 115) if bp_high else random.uniform(60, 85))
    gluc_high = bool(cfg.get("gluc_high"))
    glucose = int(random.uniform(130, 260) if gluc_high else random.uniform(75, 115))
    row = {
        "sample_id": f"S{i:04d}", "age": age, "gender": gender, "duration_days": duration,
        "temp_c": temp, "heart_rate": max(50, min(160, hr)),
        "systolic_bp": sys_bp, "diastolic_bp": dia_bp, "glucose_mg_dl": glucose,
    }
    for c in BIN_COLS:
        p = 0.9 if c in cfg and cfg[c] >= 0.9 else None
        if c == "fever":
            row[c] = fever
        elif c in ("chest_pain", "shortness_of_breath"):
            row[c] = pick_binomial(cfg, c, 0.02)
        else:
            row[c] = pick_binomial(cfg, c, 0.03)
    red = 1 if (random.random() < cfg.get("red", 0.0) and row["chest_pain"]) else 0
    if label == "نیاز به بررسی فوری":
        red = 1
    if sys_bp >= 180:
        red = 1
    row["red_flag"] = red
    row["text_fa"] = random.choice(TEXT_TMPL[label]) + (f"؛ حدود {duration} روز است" if random.random() < 0.6 else "")
    row["diagnosis_label"] = label
    row["urgency_level"] = "emergency" if red else URGENCY[label]
    row["dataset_note"] = NOTE
    return row


def main() -> int:
    cols = ["sample_id", "age", "gender", "duration_days", "temp_c", "heart_rate", "systolic_bp",
            "diastolic_bp", "glucose_mg_dl"] + BIN_COLS + ["red_flag", "text_fa", "diagnosis_label",
                                                            "urgency_level", "dataset_note"]
    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for i in range(1, ROWS + 1):
            w.writerow(gen_row(i))
    print(f"ساخته شد: {OUT} ({ROWS} ردیف مصنوعی — {NOTE})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
