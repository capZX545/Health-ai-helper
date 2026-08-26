# synthesize a real, informative description for every disease entry
# (bilingual, built from the entry's own name/code/chapter — never "not recorded")
import re

BODY = {
    "heart": ("قلب", "the heart"), "cardiac": ("قلبی", "heart"), "coronary": ("عروق کرونر قلب", "the coronary arteries"),
    "lung": ("ریه", "the lungs"), "pulmonary": ("ریه‌ای", "the lungs"), "bronch": ("نایژه", "the airways"),
    "kidney": ("کلیه", "the kidneys"), "renal": ("کلیوی", "the kidneys"), "bladder": ("مثانه", "the bladder"),
    "liver": ("کبد", "the liver"), "hepatic": ("کبدی", "the liver"), "gallbladder": ("کیسه‌ی صفرا", "the gallbladder"),
    "pancrea": ("پانکراس", "the pancreas"), "stomach": ("معده", "the stomach"), "gastric": ("معده‌ای", "the stomach"),
    "esophag": ("مری", "the esophagus"), "intestin": ("روده", "the intestines"), "colon": ("روده‌ی بزرگ", "the colon"),
    "rectum": ("راست‌روده", "the rectum"), "anal": ("مقعد", "the anus"), "brain": ("مغز", "the brain"),
    "cerebr": ("مخ/مخچه", "the brain"), "spinal": ("نخاع/ستون فقرات", "the spinal cord"),
    "nerve": ("عصب", "nerves"), "neuro": ("عصبی", "nervous"), "eye": ("چشم", "the eye"), "ocular": ("چشمی", "the eye"),
    "retina": ("شبکیه", "the retina"), "ear": ("گوش", "the ear"), "otitis": ("گوش", "the ear"),
    "nose": ("بینی", "the nose"), "nasal": ("بینی", "the nose"), "sinus": ("سینوس", "the sinuses"),
    "throat": ("گلو", "the throat"), "pharynx": ("حلق", "the pharynx"), "larynx": ("حنجره", "the larynx"),
    "mouth": ("دهان", "the mouth"), "oral": ("دهانی", "the mouth"), "tongue": ("زبان", "the tongue"),
    "tooth": ("دندان", "the teeth"), "dental": ("دندانی", "the teeth"), "gum": ("لثه", "the gums"),
    "skin": ("پوست", "the skin"), "derma": ("پوستی", "the skin"), "breast": ("پستان", "the breast"),
    "prostate": ("پروستات", "the prostate"), "uterus": ("رحم", "the uterus"), "cervix": ("دهانه‌ی رحم", "the cervix"),
    "ovary": ("تخمدان", "the ovaries"), "testis": ("بیضه", "the testicles"), "vagina": ("واژن", "the vagina"),
    "penis": ("آلت تناسلی", "the penis"), "bone": ("استخوان", "bone"), "joint": ("مفصل", "the joints"),
    "arthr": ("مفصلی", "the joints"), "muscle": ("عضله", "the muscles"), "tendon": ("تاندون", "the tendons"),
    "blood": ("خون", "the blood"), "anemi": ("کم‌خونی", "red blood cells"), "leuk": ("گویچه‌های سفید", "white blood cells"),
    "thyroid": ("تیروئید", "the thyroid gland"), "adrenal": ("غده‌ی فوق کلیوی", "the adrenal glands"),
    "pituitary": ("هیپوفیز", "the pituitary gland"), "lymph": ("لنفاوی", "the lymphatic system"),
    "vessel": ("عروق", "blood vessels"), "arter": ("سرخرگ", "arteries"), "vein": ("ورید", "veins"),
    "urin": ("ادراری", "the urinary tract"), "ureter": ("حالب", "the ureters"), "urethr": ("مجرای ادرار", "the urethra"),
    "femur": ("استخوان ران", "the femur"), "tibia": ("درشت‌نی", "the shin bone"), "fibula": ("نازک‌نی", "the calf bone"),
    "humerus": ("استخوان بازو", "the upper arm bone"), "radius": ("زند زیرین", "the forearm"), "ulna": ("زند بالایی", "the forearm"),
    "vertebra": ("مهره‌های ستون فقرات", "the vertebrae"), "spine": ("ستون فقرات", "the spine"), "skull": ("جمجمه", "the skull"),
    "rib": ("دنده", "the ribs"), "clavicle": ("ترقوه", "the collarbone"), "pelvis": ("لگن", "the pelvis"),
    "hip": ("لگن/ران", "the hip"), "knee": ("زانو", "the knee"), "shoulder": ("شانه", "the shoulder"),
    "elbow": ("آرنج", "the elbow"), "wrist": ("مچ دست", "the wrist"), "ankle": ("مچ پا", "the ankle"),
    "finger": ("انگشت دست", "the fingers"), "toe": ("انگشت پا", "the toes"), "hand": ("دست", "the hand"),
    "foot": ("پا", "the foot"), "arm": ("بازو", "the arm"), "leg": ("پا", "the leg"),
    "chest": ("قفسه‌ی سینه", "the chest"), "abdomen": ("شکم", "the abdomen"), "abdominal": ("شکمی", "the abdomen"),
    "pelvic": ("لگنی", "the pelvis"), "head": ("سر", "the head"), "neck": ("گردن", "the neck"),
    "face": ("صورت", "the face"), "scalp": ("پوست سر", "the scalp"), "trunk": ("تنه", "the trunk"),
    "perine": ("ناحیه‌ی تناسلی/مقعد", "the perineum"), "genital": ("اندام تناسلی", "the genitals"),
    "placenta": ("جفت", "the placenta"), "fetus": ("جنین", "the fetus"), "umbilical": ("ناف", "umbilical"),
    "appendi": ("زائده‌ی آپاندیس", "the appendix"), "hernia": ("فتق/کمردردی", "hernia"), "periton": ("پرده‌ی صفاق", "the peritoneum"),
    "appendix": ("زائده‌ی آپاندیس", "the appendix"), "intestine": ("روده", "the intestines"),
    "cholecyst": ("کیسه‌ی صفرا", "the gallbladder"), "bile": ("صفرا", "bile ducts"), "pancreatitis": ("پانکراس", "the pancreas"),
}

CH_DESC = {
    "A00-B99": ("بیماری‌های عفونی ناشی از باکتری‌ها، ویروس‌ها، قارچ‌ها و انگل‌ها", "infections caused by bacteria, viruses, fungi and parasites"),
    "C00-D49": ("بدخیمی‌ها (سرطان‌ها) و تومورها", "cancers and tumors"),
    "D50-D89": ("بیماری‌های خون، کم‌خونی‌ها و اختلالات سیستم ایمنی", "blood disorders, anemias and immune system problems"),
    "E00-E89": ("بیماری‌های غدد، تغذیه و متابولیسم مثل دیابت و تیروئید", "endocrine, nutritional and metabolic conditions such as diabetes and thyroid disease"),
    "F01-F99": ("اختلالات روانی و رفتاری مثل افسردگی، اضطراب و اسکیزوفرنی", "mental and behavioral disorders such as depression, anxiety and schizophrenia"),
    "G00-G99": ("بیماری‌های مغز، نخاع و اعصاب محیطی", "diseases of the brain, spinal cord and peripheral nerves"),
    "H00-H59": ("بیماری‌های چشم و دید", "eye disorders"),
    "H60-H95": ("بیماری‌های گوش و شنوایی", "ear disorders"),
    "I00-I99": ("بیماری‌های قلب و عروق مثل فشار خون، سکته و نارسایی قلبی", "cardiovascular diseases like hypertension, heart attack and heart failure"),
    "J00-J99": ("بیماری‌های سیستم تنفسی مثل آنفلوآنزا، آسم و COPD", "respiratory diseases like flu, asthma and COPD"),
    "K00-K95": ("بیماری‌های دستگاه گوارش مثل زخم معده، هپاتیت و یبوست", "digestive diseases like ulcers, hepatitis and constipation"),
    "L00-L99": ("بیماری‌های پوست مثل اگزما، پسوریازیس و عفونت‌های پوستی", "skin diseases like eczema, psoriasis and skin infections"),
    "M00-M99": ("بیماری‌های عضلات، استخوان‌ها و مفاصل مثل آرتروز و آرتریت", "musculoskeletal diseases like osteoarthritis and arthritis"),
    "N00-N99": ("بیماری‌های کلیه و دستگاه ادراری/تناسلی", "kidney and genitourinary diseases"),
    "O00-O9A": ("وضعیت‌های مرتبط با بارداری، زایمان و دوره‌ی بعد از زایمان", "pregnancy, childbirth and postpartum conditions"),
    "P00-P96": ("وضعیت‌های نوزادان در هفته‌های اول زندگی", "newborn conditions in the first weeks of life"),
    "Q00-Q99": ("ناهنجاری‌های مادرزادی ساختاری یا ژنتیکی", "congenital and genetic structural anomalies"),
    "R00-R99": ("علائم و یافته‌های غیرطبیعی آزمایش‌ها و معاینه‌ها", "symptoms and abnormal findings from tests and exams"),
    "S00-T88": ("آسیب‌ها، شکستگی‌ها، زخم‌ها و مسمومیت‌ها", "injuries, fractures, wounds and poisonings"),
    "V00-Y99": ("علل خارجی مثل تصادف و سایه‌ها", "external causes such as accidents"),
    "Z00-Z99": ("عوامل وضعیت سلامت مثل غربالگری، واکسیناسیون و سابقه‌ها", "health status factors like screening, vaccination and histories"),
    "U00-U85": ("کدهای خاص مثل بیماری‌های نوپدید", "special codes including emerging diseases"),
}


def _body_of(name_low: str):
    for k, (fa, en) in BODY.items():
        if k in name_low:
            return fa, en
    return "", ""


def synthesize_description(name: str, code: str = "", ch_key: str = ""):
    """Return (fa, en) — always an informative description for the entry itself."""
    n = (name or "").strip()
    low = n.lower()
    ch_fa_d, ch_en_d = CH_DESC.get(ch_key, ("", ""))
    bfa, ben = _body_of(low)

    def fa_body(x): return x or "بدن"
    def en_body(x): return x or "the body"

    # ---------- بدخیمی ----------
    if re.search(r"\b(malignant neoplasm|carcinoma|cancer|lymphoma|leukemia|melanoma|sarcoma|myeloma)\b", low):
        fa = f"سرطان مربوط به {fa_body(bfa)}. سرطان یعنی رشد کنترل‌نشده‌ی سلول‌ها که اگر درمان نشد می‌تواند به بافت‌های اطراف و سایر اندام‌ها سرایت کند."
        if bfa:
            fa += f" محل اصلی آن {bfa} است."
        en = f"A cancer related to {en_body(ben)}. Cancer means uncontrolled cell growth that can spread to nearby tissue and other organs if untreated."
        return fa, en
    if "benign neoplasm" in low or "adenoma" in low or "lipoma" in low or "polyp" in low:
        fa = f"توده‌ی خوش‌خیم در {fa_body(bfa)}؛ غیرسرطانی است، به سایر نقاط بدن سرایت نمی‌کند اما بسته به اندازه و محلش ممکن است علائم ایجاد کند یا نیاز به پیگیری داشته باشد."
        en = f"A benign (non-cancerous) growth in {en_body(ben)}; it does not spread but may cause symptoms or need follow-up depending on size and location."
        return fa, en
    # ---------- شکستگی/آسیب ----------
    if "fracture" in low:
        fa = f"شکستگی استخوان در ناحیه‌ی {fa_body(bfa)}. معمولاً بر اثر ضربه یا زمین‌خوردن رخ می‌دهد؛ درد، تورم و ناتوانی حرکتی می‌آورد و نیاز به تصویربرداری و مراقبت ارتوپدی دارد."
        en = f"A bone fracture in the area of {en_body(ben)}, usually from trauma or a fall; it causes pain, swelling and loss of function and needs imaging and orthopedic care."
        return fa, en
    if re.search(r"\b(injury|laceration|wound|contusion|sprain|strain|dislocation)\b", low):
        fa = f"آسیب فیزیکی به {fa_body(bfa)} ناشی از ضربه یا حادثه؛ درد، تورم، کبودی یا محدودیت حرکت ایجاد می‌کند و شدت آن به نوع ضربه بستگی دارد."
        en = f"Physical injury to {en_body(ben)} from trauma; it causes pain, swelling, bruising or limited movement, with severity depending on the force involved."
        return fa, en
    if re.search(r"burn|corrosion", low):
        fa = "آسیب سوختگی/اسیدی پوست یا بافت زیر آن؛ عمق و وسعت سوختگی شدت آن را تعیین می‌کند و سوختگی‌های وسیع یا عمیق نیاز به مراقبت فوری پزشکی دارند."
        en = "A burn or corrosive injury to skin or deeper tissue; depth and size determine severity, and large or deep burns need urgent medical care."
        return fa, en
    if re.search(r"poisoning|toxic effect|overdose", low):
        fa = "مسمومیت با دارو یا ماده‌ی شیمیایی؛ بسته به ماده می‌تواند تهوع، استفراغ، گیجی یا اختلال تنفس بدهد و در موارد شدید اورژانسی است (۱۱۵/۱۱۲)."
        en = "Poisoning by a drug or chemical; depending on the substance it can cause nausea, vomiting, confusion or breathing problems and may be an emergency."
        return fa, en
    # ---------- سابقه/غربالگری/ویزیت ----------
    if "family history of" in low:
        x = re.split(r"family history of", n, flags=re.I)[-1].strip() or "این وضعیت"
        fa = f"یعنی یکی از بستگان نزدیک «{x}» را داشته است. شما این بیماری را ندارید؛ فقط احتمال بروز آن کمی بالاتر است و پزشک ممکن است غربالگری زودتر توصیه کند."
        en = f"Means a close relative had '{x}'. You do not have the condition yourself; the risk of developing it is somewhat higher and earlier screening may be advised."
        return fa, en
    if "personal history of" in low:
        x = n.split("personal history of")[-1].strip() or "این وضعیت"
        fa = f"یعنی در گذشته «{x}» را داشته‌اید و اکنون ثبت شده تا پزشک در پیگیری‌ها و انتخاب درمان‌های بعدی لحاظش کند؛ لزوماً بیماری فعال نیست."
        en = f"Means you had '{x}' in the past; it is recorded so doctors can plan follow-ups and treatments accordingly. It is not necessarily an active illness now."
        return fa, en
    if re.search(r"encounter for.*(screening|examination)", low) or low.startswith("screening for"):
        fa = "یک ویزیت پیشگیرانه برای بررسی زودهنگام یک بیماری قبل از بروز علائم است؛ خودِ کد بیماری نیست و نتیجه‌ی غربالگری قدم بعدی را مشخص می‌کند."
        en = "A preventive visit to detect a disease before symptoms appear; the code itself is not an illness, and the screening result decides the next step."
        return fa, en
    if "encounter for" in low:
        fa = "کدی برای ثبت دلیل مراجعه به مراکز درمانی (ویزیت، واکسیناسیون، پیگیری یا مشاوره)؛ خودش بیماری نیست."
        en = "A code recording the reason for a healthcare visit (consultation, vaccination, follow-up or counseling); not a disease itself."
        return fa, en
    # ---------- یافته‌ها ----------
    if re.search(r"abnormal (cytological|histological)", low):
        fa = "یافته‌ی آزمایشگاهی: در نمونه‌ی گرفته‌شده (سیتولوژی/بافت) سلول‌های غیرطبیعی دیده شده. خودش بیماری نیست؛ پزشک با تکرار آزمایش یا بیوپسی علت آن (التهاب، عفونت، توده) را مشخص می‌کند."
        en = "A laboratory finding: abnormal cells were seen in the taken sample (cytology/tissue). Not a disease by itself; a doctor clarifies the cause (inflammation, infection, growth) with repeat tests or biopsy."
        return fa, en
    if re.search(r"abnormal.*(finding|result)", low):
        fa = "یافته‌ی غیرطبیعی در آزمایش یا معاینه؛ یک «نتیجه» است نه تشخیص. معنایش کاملاً به نوع آزمایش بستگی دارد و پزشک آن را همراه علائم شما تفسیر می‌کند."
        en = "An abnormal finding on a test or exam; it is a result, not a diagnosis. Its meaning depends on which test, and a doctor interprets it together with your symptoms."
        return fa, en
    # ---------- نام‌های توصیفی ----------
    m = re.search(r"^(.*?),?\s*type\s*(i{1,3}|\d+|[12]b|a|b)\b", low)
    if "unspecified" in low or ", unspecified" in low:
        core = re.sub(r",?\s*unspecified", "", n)
        fa = f"«{core}» به‌صورت مشخص‌نشده؛ یعنی تشخیص تا جزئیات دقیق‌تر مشخص نشده. علائم و درمان همان بیماری اصلی را دنبال می‌کند."
        en = f"'{core}', unspecified variant; the diagnosis was not narrowed further. Symptoms and care follow the parent condition."
        return fa, en
    if low.startswith("other specified") or "other specified" in low:
        core = re.sub(r"^other specified\s*", "", n, flags=re.I)
        fa = f"یک شکل خاص از «{core}» که در دسته‌ی خودش جزئیات بیشتری دارد؛ جزئیات دقیق در پرونده‌ی پزشکی شما ثبت شده است."
        en = f"A specific form of '{core}' with additional detail recorded in your medical record."
        return fa, en
    if "sequela" in low or "late effect" in low:
        fa = "عارضه‌ی دیررس یک بیماری یا آسیب قبلی؛ یعنی اثری که پس از گذشتن فاز حاصل باقی مانده (مثل ضعف بعد از سکته)."
        en = "A late effect of a previous disease or injury; something that remains after the acute phase has passed (e.g., weakness after a stroke)."
        return fa, en
    if re.search(r"congenital|malformation", low):
        fa = f"یک ناهنجاری مادرزادی مربوط به {fa_body(bfa)} که از بدو تولد وجود دارد؛ برخی با سونوگرافی یا غربالگری نوزادی پیدا می‌شوند و اغلب نیاز به پیگیری تخصصی دارند."
        en = f"A congenital anomaly involving {en_body(ben)} present from birth; some are found on ultrasound or newborn screening and often need specialist follow-up."
        return fa, en

    # ---------- پیش‌فرض هوشمند: نام + فصل ----------
    core = re.sub(r"^(other|unspecified)\s+", "", n, flags=re.I).strip(" ,;") or n
    if ch_fa_d:
        fa = f"«{core}» یک وضعیت پزشکی در حوزه‌ی {ch_fa_d} است"
        en = f"'{core}' is a medical condition in the area of {ch_en_d}"
        if bfa:
            fa += f" که مربوط به {bfa} می‌شود"
            en += f" involving {ben}"
        fa += ". برای ارزیابی دقیق، علائم خود را در ماژول «علائم» وارد کنید تا احتمالات رتبه‌بندی شود."
        en += ". For a closer look, enter your symptoms in the Symptoms module to rank possibilities."
        return fa, en
    return (f"«{core}» یک وضعیت پزشکی ثبت‌شده است.", f"'{core}' is a recorded medical condition.")
