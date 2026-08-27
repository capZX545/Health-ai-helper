"""
Pharma-style english -> persian transliteration for drug names
(Amoxicillin -> آموکسی‌سیلین). Deterministic and fast; used as a fallback
when no human-reviewed persian name exists.
"""

DIGRAPHS = [("ph", "ف"), ("sh", "ش"), ("ch", "چ"), ("th", "ت"), ("kh", "خ"), ("gh", "غ"), ("ck", "ک"), ("wr", "ر"), ("qu", "کو")]
CONS = {
    "b": "ب", "d": "د", "f": "ف", "g": "گ", "h": "ه", "j": "ج", "k": "ک", "l": "ل",
    "m": "م", "n": "ن", "p": "پ", "r": "ر", "s": "س", "t": "ت", "v": "و", "w": "و",
    "x": "کس", "z": "ز", "q": "ق", "y": "ی", "c": "ک", "a": "ا", "e": "", "i": "ی", "o": "و", "u": "ا",
}
KNOWN = {
    "amoxicillin": "آموکسی‌سیلین", "amoxiclav": "آموکسی‌کلاو", "ibuprofen": "ایبوپروفن",
    "acetaminophen": "استامینوفن", "paracetamol": "پاراستامول", "aspirin": "آسپرین",
    "metformin": "متفورمین", "atorvastatin": "آتورواستاتین", "warfarin": "وارفارین",
    "insulin": "انسولین", "omeprazole": "امپرازول", "diclofenac": "دیکلوفناک",
    "diazepam": "دیازپام", "metoprolol": "متوپرولول", "losartan": "لوزارتان",
    "amlodipine": "آملودیپین", "glibenclamide": "گلی‌بنکلامید", "levothyroxine": "لووتیروکسین",
    "prednisolone": "پردنیزولون", "ciprofloxacin": "سیپروفلوکساسین", "azithromycin": "آزیترومایسین",
    "sertraline": "سرترالین", "fluoxetine": "فلوکستین", "tramadol": "ترامادول",
    "morphine": "مورفین", "furosemide": "فوروزماید", "enalapril": "انالاپریل",
    "pantoprazole": "پانتوپرازول", "vitamin": "ویتامین", "iron": "آهن",
}


def translit(name: str) -> str:
    n = (name or "").strip().lower()
    if not n:
        return ""
    if n in KNOWN:
        return KNOWN[n]
    out = []
    i = 0
    prev_cons = True
    while i < len(n):
        if not n[i].isalpha():
            out.append(n[i]); i += 1; continue
        hit = False
        for d, fa in DIGRAPHS:
            if n.startswith(d, i):
                out.append(fa); i += len(d); prev_cons = True; hit = True; break
        if hit:
            continue
        ch = n[i]
        if ch == "c":
            fa = "س" if (i + 1 < len(n) and n[i + 1] in "eiy") else "ک"
            out.append(fa); prev_cons = True
        elif ch in "aeiou":
            if i == 0:
                out.append("آ" if ch in "ao" else ("ای" if ch == "i" else ("ا" if ch == "a" else "او")))
            elif not prev_cons:
                pass
            prev_cons = False
        elif ch == "e" and i == len(n) - 1:
            pass
        else:
            fa = CONS.get(ch, ch)
            out.append(fa)
            prev_cons = True
        i += 1
    s = "".join(out)
    import re
    s = re.sub(r"(.)\1+", r"\1", s) if s else s
    for suf, fa_suf in (("cillin", "سیلین"), ("mycin", "مایسین"), ("dipine", "دیپین"), ("pril", "پریل"), ("olol", "ولول"), ("statin", "استاتین"), ("azole", "ازول")):
        if n.endswith(suf) and not s.endswith(fa_suf):
            s = s
    return s.strip(" ‌")


if __name__ == "__main__":
    for w in ("Amoxicillin", "Ibuprofen", "Metformin", "Atorvastatin", "Amlodipine",
              "Ceftriaxone", "Omeprazole", "Sertraline", "Albuterol", "Levonorgestrel"):
        print(w, "->", translit(w))
