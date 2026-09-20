"""
calendar_export.py — exports medication reminders (and checkup reminders)
as a standard .ics calendar file, importable into Google Calendar, Apple
Calendar and Outlook.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from i18n import is_fa

_DAYS_MAP = {"daily": list(range(7)), "weekdays": [0, 1, 2, 3, 4], "weekends": [5, 6]}


def _fold(line: str) -> str:
    out = []
    while len(line.encode("utf-8")) > 73:
        cut = 72
        while cut > 1 and len(line[:cut].encode("utf-8")) > 73:
            cut -= 1
        out.append(line[:cut])
        line = " " + line[cut:]
    out.append(line)
    return "\r\n".join(out)


def _esc(s: str) -> str:
    return str(s or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _dt(d: date, hhmm: str) -> str:
    try:
        h, m = str(hhmm).strip().split(":")[:2]
        return f"{d.strftime('%Y%m%d')}T{int(h):02d}{int(m):02d}00"
    except Exception:
        return f"{d.strftime('%Y%m%d')}T080000"


def _parse_when(when: str) -> date | None:
    s = str(when or "").strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def build_ics(days_ahead: int = 90) -> str:
    fa = is_fa()
    now = datetime.now().strftime("%Y%m%dT%H%M%S")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//NexusMed 2077//Reminders//FA",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    events = 0
    try:
        from med_reminder_service import list_all
        today = date.today()
        horizon = today + timedelta(days=max(7, min(days_ahead, 365)))
        d = today
        while d <= horizon and events < 400:
            for r in list_all():
                if not r.get("active", True):
                    continue
                days = _DAYS_MAP.get(str(r.get("days") or "daily").lower(), list(range(7)))
                if d.weekday() not in days:
                    continue
                for hhmm in (r.get("times") or []):
                    drug = str(r.get("drug") or "").strip()
                    if not drug:
                        continue
                    title = (f"دارو: {drug}" if fa else f"Medication: {drug}")
                    lines += [
                        "BEGIN:VEVENT",
                        f"UID:nexusmed-{r.get('id')}-{d.isoformat()}-{hhmm}@nexusmed2077",
                        f"DTSTAMP:{now}",
                        f"DTSTART:{_dt(d, hhmm)}",
                        f"DTEND:{_dt(d, hhmm)}",
                        _fold(f"SUMMARY:{_esc(title)}"),
                        _fold("DESCRIPTION:" + _esc("یادآور NexusMed 2077" if fa else "NexusMed 2077 reminder")),
                        "BEGIN:VALARM",
                        "TRIGGER:-PT10M",
                        "ACTION:DISPLAY",
                        _fold(f"DESCRIPTION:{_esc(title)}"),
                        "END:VALARM",
                        "END:VEVENT",
                    ]
                    events += 1
            d += timedelta(days=1)
    except Exception:
        pass
    try:
        from checkup_calendar import list_reminders
        for c in (list_reminders() or []):
            d2 = _parse_when(str(c.get("when") or ""))
            if not d2 or d2 < date.today():
                continue
            title = str(c.get("title") or "Checkup")
            lines += [
                "BEGIN:VEVENT",
                f"UID:nexusmed-checkup-{c.get('id') or title}@nexusmed2077",
                f"DTSTAMP:{now}",
                f"DTSTART;VALUE=DATE:{d2.strftime('%Y%m%d')}",
                f"DTEND;VALUE=DATE:{(d2 + timedelta(days=1)).strftime('%Y%m%d')}",
                _fold(f"SUMMARY:{_esc(title)}"),
                "END:VEVENT",
            ]
            events += 1
    except Exception:
        pass
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def stats() -> dict[str, Any]:
    fa = is_fa()
    try:
        from med_reminder_service import list_all
        meds = [r for r in list_all() if r.get("active", True)]
    except Exception:
        meds = []
    n_times = sum(len(r.get("times") or []) for r in meds)
    return {"ok": True, "reminders": len(meds), "times": n_times,
            "message_fa": ((f"{len(meds)} یادآور فعال با {n_times} نوبت در روز."
                            if meds else "یادآور فعالی ثبت نشده — اول از ماژول یادآورها اضافه کن.")
                           if fa else
                           (f"{len(meds)} active reminder(s), {n_times} daily time slot(s)."
                            if meds else "No active reminders yet - add them in the reminders module first."))}
