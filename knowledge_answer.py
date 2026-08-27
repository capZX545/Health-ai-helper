"""
knowledge_answer.py — answers knowledge questions (drug/disease/advice)
using the local banks, GPT-style: concise, structured, bilingual.
"""
from __future__ import annotations

from typing import Any

from common_2077 import normalize


def _is_fa() -> bool:
    from i18n import is_fa
    return is_fa()


def answer_drug_question(message: str) -> str | None:
    """Answer 'what is ibuprofen' style questions from the drug bank."""
    fa = _is_fa()
    from knowledge_browser import search_drugs, get_drug_label, fa_drug_name
    q = message.strip()
    hits = search_drugs(q) or []
    if not hits:
        for w in q.split():
            if len(w) > 3:
                hits = search_drugs(w)
                if hits:
                    break
    if not hits:
        return None
    d = hits[0]
    name = d.get("fa") if fa else (d.get("en") or d.get("fa"))
    lines = []
    lines.append(f" {name}" + (f" ({d['en']})" if fa and d.get("en") else ""))
    if d.get("category") or d.get("category_en"):
        cat = d.get("category") if fa else (d.get("category_en") or d.get("category"))
        lines.append(f"{'دسته' if fa else 'Class'}: {cat}")
    lb = get_drug_label(d.get("en", ""))
    if lb and lb.get("ind"):
        txt = lb["ind"]
        for h in ("INDICATIONS AND USAGE", "Indications and Usage", "Uses", "Uses "):
            txt = txt.replace(h, "").strip(" .:—-")
        txt = txt.split(". ")[0][:150].strip()
        if fa:
            from translit import translit
            lines.append("")
            lines.append(f"موارد مصرف: {txt}")
        else:
            lines.append("")
            lines.append(f"Used for: {txt}")
    inter = d.get("interactions") or []
    if inter:
        sev_fa = {"major": "شدید", "moderate": "متوسط", "minor": "خفیف"}
        lines.append("")
        lines.append(f"{'تداخل‌های مهم' if fa else 'Key interactions'}:")
        for it in inter[:3]:
            sev = it.get("severity", "")
            s = (sev_fa.get(sev, sev) if fa else sev)
            other = it.get("other", "")
            if isinstance(other, list):
                other = other[0] if other else ""
            lines.append(f"  • {str(other).strip('[]\'')} ({s})")
    lines.append("")
    lines.append(" " + ("دوز و مصرف فقط با تجویز پزشک." if fa else "Dosage only as prescribed."))
    return "\n".join(lines)


def answer_disease_question(message: str) -> str | None:
    """Answer 'what is diabetes' style questions from the disease bank."""
    fa = _is_fa()
    from knowledge_browser import full_profile, search_wiki_diseases, search_doid, icd_about
    q = message.strip()
    name = ""
    wiki = search_wiki_diseases(q, 1)
    if wiki:
        name = wiki[0].get("en", "")
    if not name:
        doid = search_doid(q, 1)
        if doid:
            name = doid[0].get("name", "")
    if not name:
        for kw, key in (("دیابت", "E11"), ("فشار", "I10"), ("آسم", "J45"),
                        ("سرطان", "C00"), ("diabet", "E11"), ("hypertens", "I10"), ("asthma", "J45")):
            if kw in q.lower():
                name = kw
                break
    if not name:
        return None
    code = ""
    for kw, icd in (("دیابت", "E11"), ("فشار خون", "I10"), ("آسم", "J45"),
                    ("سرطان", "C00"), ("diabet", "E11"), ("hypertens", "I10"), ("asthma", "J45")):
        if kw in q.lower() or kw in name.lower():
            code = icd
            break
    p = full_profile(name, code, "", "", [], [])
    lines = []
    nm = name if not fa else (p.get("about_fa", "") and name or name)
    lines.append(f" {nm}")
    lines.append("")
    about = p["about_fa"] if fa else p["about_en"]
    if "ثبت‌شده" in about or "recorded medical" in about:
        from synth_desc import synthesize_description
        fa_s, en_s = synthesize_description(name, code, "")
        about = fa_s if fa else en_s
    lines.append(about[:400])
    if p["sym_fb_en"]:
        lines.append("")
        lines.append(f"{'علائم شایع' if fa else 'Common signs'}: {p['sym_fb_fa'] if fa else p['sym_fb_en']}")
    lines.append("")
    lines.append(f"{'درمان' if fa else 'Treatment'}: {p['treat_fa'] if fa else p['treat_en']}")
    return "\n".join(lines)


def answer_advice_question(message: str) -> str | None:
    """Answer 'what should I do for a cold' style questions."""
    fa = _is_fa()
    from medical_engine import detect_symptoms, SYMPTOM_NAMES_FA, SYMPTOM_NAMES_EN
    det = detect_symptoms(message)
    present = [s for s, i in det.get("present", {}).items() if not i.get("denied")]
    if not present:
        from knowledge_browser import search_wiki_diseases, search_doid, get_catalog_diseases
        name = ""
        w = search_wiki_diseases(message, 1)
        if w:
            name = w[0].get("en", "")
        if not name:
            d = search_doid(message, 1)
            if d:
                name = d[0].get("name", "")
        if not name:
            cat = get_catalog_diseases(message, 1).get("results") or []
            if cat:
                name = cat[0].get("name", "")
        if not name:
            from knowledge_browser import _FA_EN_MED
            nq = message.strip()
            for fa_t, en_t in _FA_EN_MED.items():
                if fa_t in nq:
                    w2 = search_wiki_diseases(en_t, 1)
                    if w2:
                        name = w2[0].get("en", "")
                    break
        if not name:
            return None
        from knowledge_browser import full_profile
        p = full_profile(name, "", "", "", [], [])
        lines = [f" {'توصیه برای' if fa else 'Care for'} {name}:", ""]
        lines.append(f"  • {'درمان' if fa else 'Treatment'}: {p['treat_fa'] if fa else p['treat_en']}")
        if p['sym_fb_en']:
            lines.append(f"  • {'علائم' if fa else 'Signs'}: {p['sym_fb_fa'] if fa else p['sym_fb_en']}")
        lines.append("")
        lines.append(("اگر علائم شدید یا بیش از ۳ روز ادامه داشت، به پزشک مراجعه کن." if fa
                     else "See a doctor if symptoms are severe or last over 3 days."))
        return "\n".join(lines)
    lines = []
    lines.append(("برای علائمی که گفتی:" if fa else "For your symptoms:"))
    lines.append("")
    for sid in present[:4]:
        nm = SYMPTOM_NAMES_FA.get(sid, sid) if fa else SYMPTOM_NAMES_EN.get(sid, sid)
        lines.append(f"• {nm}")
    lines.append("")
    lines.append(("توصیه کلی:" if fa else "General care:"))
    lines.append(("  • استراحت و مایعات کافی" if fa else "  • Rest and fluids"))
    lines.append(("  • اگر بدتر شد به پزشک مراجعه کن" if fa else "  • See a doctor if it worsens"))
    return "\n".join(lines)


def answer_greeting(message: str) -> str:
    fa = _is_fa()
    if fa:
        return ("سلام  من نکسوس هستم، دستیار پزشکی دوزبانه.\n\n" "علائمت را بنویس تا احتمالات را بررسی کنم.\n" "یا هر سوال پزشکی داری بپرس.")
    return ("Hi  I'm Nexus, the bilingual medical assistant.\n\n" "Describe your symptoms and I'll check the possibilities.\n" "Or ask me any medical question.")
