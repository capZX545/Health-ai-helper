# -*- coding: utf-8 -*-
t = open("clinic_2077.html", encoding="utf-8").read()

# تغییر type=password به type=text برای Paste آسان
old = 'type=\\"password\\" id=\\"key-'
new = 'type=\\"text\\" autocomplete=\\"off\\" spellcheck=\\"false\\" id=\\"key-'
assert old in t, "password input not found"
t = t.replace(old, new)
open("clinic_2077.html", "w", encoding="utf-8").write(t)
print("input type changed to text (paste-friendly)")
