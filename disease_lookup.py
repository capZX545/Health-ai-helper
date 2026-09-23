"""
disease_lookup.py — turns a bare disease name (Farsi or English) typed in
the chat into a full answer: what it is, common signs, the related
medications and treatment. Exact-match resolver over a curated top-disease
table, the 104-condition engine bank, the 27k ICD-10 catalog, the 15k
Persian name bank and the Wikidata bank. Known symptom names are never
hijacked away from the symptom-analysis flow.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

from common_2077 import normalize

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

_WRAPPERS = [
    "what is", "what s", "whats", "what's", "tell me about", "tell me",
    "explain", "define", "definition of", "meaning of", "info on",
    "information on", "about", "i want to know", "what is it", "what is this",
    "whats it", "what s it", "what does it mean", "what it is", "mean", "means",
    "درباره", "در مورد",
    "اطلاعاتی درباره", "اطلاعاتی در مورد", "میخوام بدوم", "میخواهم بدانم",
    "بگو برام", "توضیح بده", "توضیح میدهی", "چی هست", "چیه هست", "چیه",
    "چیست", "یعنی چی", "یعنی چیست", "چی باشه", "بگو", "من",
]

_CURATED: list[dict[str, Any]] = [
    {"icd": "E11", "en": "type 2 diabetes mellitus", "fa": "دیابت نوع ۲",
     "alias": ["دیابت", "قند", "قند خون", "قند بالا", "دیابت نوع دو", "دیابت شیرین", "دیابت بزرگسالان", "diabetes", "diabetes mellitus", "type 2 diabetes", "t2dm", "dm2"],
     "drugs": ("متفورمین (خط اول)، انسولین در موارد پیشرفته؛ داروهای جدیدتر: GLP-1 (لیراگلوتاید)، SGLT2 (داپاگلیفلوزین)، سیتاگلیپتین",
               "metformin (first line), insulin in advanced cases; newer agents: GLP-1 (liraglutide), SGLT2 (dapagliflozin), sitagliptin")},
    {"icd": "E10", "en": "type 1 diabetes mellitus", "fa": "دیابت نوع ۱",
     "alias": ["دیابت نوع یک", "دیابت کودکان", "type 1 diabetes", "t1dm", "juvenile diabetes"],
     "drugs": ("انسولین تزریقی مادام‌العمر (سریع‌اثر + میان‌اثر یا طولانی‌اثر)، شمارش کربوهیدرات",
               "lifelong injected insulin (rapid + intermediate or long-acting), carbohydrate counting")},
    {"icd": "I10", "en": "essential hypertension", "fa": "فشار خون بالا",
     "alias": ["فشار خون", "فشار بالا", "پرفشاری خون", "hypertension", "high blood pressure", "htn"],
     "drugs": ("آملودیپین، لوزارتان یا مهارکننده‌های ACE (لیزینوپریل)، هیدروکلروتیازید؛ ترکیبی در صورت نیاز",
               "amlodipine, losartan or ACE inhibitors (lisinopril), hydrochlorothiazide; combinations if needed")},
    {"icd": "J45", "en": "asthma", "fa": "آسم",
     "alias": ["آسم ریوی", "asthma bronchiale", "bronchial asthma"],
     "drugs": ("اسپری نجات سالبوتامول، اسپری کورتیکواستروئید استنشاقی (بودزوناید) به‌عنوان کنترلر، لِوکوترین آنتاگونیست (مونته‌لوکاست)",
               "salbutamol reliever inhaler, inhaled corticosteroid controller (budesonide), leukotriene antagonist (montelukast)")},
    {"icd": "L40", "en": "psoriasis", "fa": "پسوریازیس",
     "alias": ["صورتیز", "پسوریاز", "psoriasis vulgaris"],
     "drugs": ("کرم‌های کورتونی + آنالوگ ویتامین D (کالسی‌پوتریول)، فوتوتراپی، متوترکسات یا بیولوژیک‌ها (آدالیموماب) در موارد شدید",
               "steroid creams + vitamin D analogs (calcipotriol), phototherapy, methotrexate or biologics (adalimumab) if severe")},
    {"icd": "L30", "en": "atopic dermatitis", "fa": "اگزما (درماتیت آتوپیک)",
     "alias": ["اگزما", "درماتیت", "خشکی پوست التهابی", "eczema", "dermatitis"],
     "drugs": ("مرطوب‌کننده‌ی مکرر، کرم کورتونی حمله‌ای، مهارکننده‌های کالسینئورین (پیمکرولیموس)، آنتی‌هیستامین برای خارش",
               "frequent moisturizers, steroid creams for flares, calcineurin inhibitors (pimecrolimus), antihistamines for itch")},
    {"icd": "L70", "en": "acne vulgaris", "fa": "آکنه (جوش)",
     "alias": ["جوش", "جوش صورت", "آکنه روزاسه", "acne", "pimples"],
     "drugs": ("بنزوئیل پراکساید، آداپالن، آنتی‌بیوتیک موضعی (کلیندامایسین)، ایزوترتینوئین خوراکی در موارد شدید",
               "benzoyl peroxide, adapalene, topical antibiotic (clindamycin), oral isotretinoin for severe cases")},
    {"icd": "G43", "en": "migraine", "fa": "میگرن",
     "alias": ["میگرن", "سردرد میگرنی", "migraine headache"],
     "drugs": ("سوماتریپتان یا ارگوتامین در حمله، NSAID (ناپروکسن)؛ پیشگیری: پروپرانولول یا توپیرامات",
               "sumatriptan or ergotamine for attacks, NSAIDs (naproxen); prevention: propranolol or topiramate")},
    {"icd": "G40", "en": "epilepsy", "fa": "صرع",
     "alias": ["ماریزی", "بیماری تشنج", "seizure disorder"],
     "drugs": ("ضدتشنج‌ها بسته به نوع: کاربامازپین، لِوِتیراستام، والپروات سدیم — تنظیم دوز فقط با نورولوژیست",
               "antiepileptics per type: carbamazepine, levetiracetam, sodium valproate - dosing only with a neurologist")},
    {"icd": "G35", "en": "multiple sclerosis", "fa": "مالتیپل اسکلروزیس (ام اس)",
     "alias": ["ام اس", "ام‌اس", "ال‌تی‌اس", "ms disease", "ms"],
     "drugs": ("کورتون در حملات، داروهای تعدیل‌کننده‌ی بیماری (اینترفرون، فینگولیمود، اوکرلیزوماب)",
               "steroids for relapses, disease-modifying drugs (interferons, fingolimod, ocrelizumab)")},
    {"icd": "G20", "en": "Parkinson disease", "fa": "پارکینسون",
     "alias": ["بیماری پارکینسون", "لرزش پارکینسون", "parkinsons", "parkinson disease"],
     "drugs": ("لوودوپا/کاربیدوپا، آگونیست‌های دوپامین (پرامی‌پکسول)، مهارکننده‌ی MAO-B (راساژیلین)",
               "levodopa/carbidopa, dopamine agonists (pramipexole), MAO-B inhibitor (rasagiline)")},
    {"icd": "G30", "en": "Alzheimer disease", "fa": "آلزایمر",
     "alias": ["فراموشی سالمندی", "alzheimers", "alzheimer disease"],
     "drugs": ("دونپزیل، مِمانتین؛ همراه با ساخت ایمنی محیط و روتین ثابت",
               "donepezil, memantine; plus a safe environment and fixed routines")},
    {"icd": "F32", "en": "major depressive disorder", "fa": "افسردگی",
     "alias": ["افسردگی_major", "دپرشن", "depression", "major depression", "mdd"],
     "drugs": ("سرترالین، فلوکستین یا اس‌سیتالوپرام + روان‌درمانی؛ اثر دارو از ۲ تا ۴ هفته شروع می‌شود",
               "sertraline, fluoxetine or escitalopram plus psychotherapy; drugs take 2-4 weeks to work")},
    {"icd": "F41", "en": "anxiety disorder", "fa": "اضطراب",
     "alias": ["استرس مزمن", "anxiety", "gad", "generalized anxiety"],
     "drugs": ("SSRI (سرترالین) خط اول، بنزودیازپین فقط کوتاه‌مدت، تمرین تنفس و CBT",
               "SSRIs (sertraline) first line, benzodiazepines only short-term, breathing practice and CBT")},
    {"icd": "F42", "en": "obsessive compulsive disorder", "fa": "وسواس (OCD)",
     "alias": ["وسواس", "بیماری وسواس", "ocd", "obsessive compulsive"],
     "drugs": ("فلوکستین یا سرترالین در دوز بالا + درمان مواجهه و پیشگیری از پاسخ (ERP)",
               "high-dose fluoxetine or sertraline plus exposure and response prevention (ERP)")},
    {"icd": "G47", "en": "insomnia", "fa": "بی‌خوابی",
     "alias": ["بیدار ماندن", "نمی توانم بخوابم", "insomnia", "sleeplessness"],
     "drugs": ("بهبود خواب اول؛ در صورت نیاز ملاتونین یا زولپیدم کوتاه‌مدت با تجویز",
               "sleep hygiene first; if needed melatonin or short-term zolpidem by prescription")},
    {"icd": "F90", "en": "attention deficit hyperactivity disorder", "fa": "اختلال بیش‌فعالی-کم‌توجهی (ADHD)",
     "alias": ["بیش فعالی", "کم توجهی", "adhd", "add", "attention deficit"],
     "drugs": ("متیل‌فنیدات یا اتموکستین با نظارت دقیق؛ در کنار ساختار و رفتاردرمانی",
               "methylphenidate or atomoxetine with close monitoring; alongside structure and behavioral therapy")},
    {"icd": "F84", "en": "autism spectrum disorder", "fa": "اوتیسم",
     "alias": ["طیف اوتیسم", "autism", "asd", "autism spectrum"],
     "drugs": ("داروی مشخصی اوتیسم را درمان نمی‌کند؛ رفتاردرمانی و گفتاردرمانی محورند، دارو فقط برای علائم همراه",
               "no drug treats autism itself; behavioral and speech therapy are the core, medication only for co-occurring symptoms")},
    {"icd": "E03", "en": "hypothyroidism", "fa": "کم‌کاری تیروئید",
     "alias": ["کم کاری تیروئید", "تیروئید کم کار", "hypothyroid", "hypothyroidism", "low thyroid"],
     "drugs": ("لووتیروکسین خوراکی روزانه ناشتا؛ تنظیم دوز با TSH هر ۶ تا ۸ هفته",
               "daily oral levothyroxine on an empty stomach; dose tuned by TSH every 6-8 weeks")},
    {"icd": "E05", "en": "hyperthyroidism", "fa": "پرکاری تیروئید",
     "alias": ["پر کاری تیروئید", "تیروئید پر کار", "hyperthyroid", "hyperthyroidism", "overactive thyroid", "graves"],
     "drugs": ("متیمازول یا پروپیل‌تیواوراسیل؛ بتابلاکر (پروپرانولول) برای علائم؛ رادیوید یا جراحی در موارد مقاوم",
               "methimazole or propylthiouracil; beta-blocker (propranolol) for symptoms; radioiodine or surgery if resistant")},
    {"icd": "E66", "en": "obesity", "fa": "چاقی",
     "alias": ["اضافه وزن", "obesity", "overweight"],
     "drugs": ("اورلیستات یا آگونیست‌های GLP-1 (لیراگلوتاید، سماگلوتاید) فقط همراه رژیم و ورزش و زیر نظر پزشک",
               "orlistat or GLP-1 agonists (liraglutide, semaglutide) only with diet, exercise and medical supervision")},
    {"icd": "K76", "en": "non-alcoholic fatty liver disease", "fa": "کبد چرب",
     "alias": ["چربی کبد", "fatty liver", "nafld", "nash"],
     "drugs": ("داروی اختصاصی ندارد؛ کاهش ۷ تا ۱۰ درصد وزن مؤثرترین درمان + ورزش و حذف نوشیدنی‌های شیرین؛ ویتامین E در موارد منتخب",
               "no dedicated drug; 7-10% weight loss is the most effective treatment plus exercise and cutting sugary drinks; vitamin E in selected cases")},
    {"icd": "K25", "en": "gastric ulcer", "fa": "زخم معده",
     "alias": ["زخم معده و دوازدهه", "ulcer", "stomach ulcer", "peptic ulcer", "gastric ulcer"],
     "drugs": ("مهارکننده‌ی پمپ پروتون (امپرازول) ۴ تا ۸ هفته + آزمایش و درمان هلیکوباکتر (آموکسی‌سیلین + کلاریترومایسین)",
               "PPI (omeprazole) for 4-8 weeks plus testing and treating H. pylori (amoxicillin + clarithromycin)")},
    {"icd": "K21", "en": "gastroesophageal reflux disease", "fa": "رفلاکس معده به مری",
     "alias": ["رفلاکس", "سوزش سر دل مزمن", "gerd", "reflux", "acid reflux"],
     "drugs": ("امپرازول یا پانتوپرازول + کاهش وزن، شام زودهنگام و بالا بردن سر تخت",
               "omeprazole or pantoprazole plus weight loss, early dinner and raising the head of the bed")},
    {"icd": "K58", "en": "irritable bowel syndrome", "fa": "سندرم روده‌ی تحریک‌پذیر",
     "alias": ["روده تحریک پذیر", "ibs", "irritable bowel"],
     "drugs": ("انفه‌کننده‌ی پنبه‌رینه، اسپاسمولیت (مِبِوِرین)، پروبیوتیک؛ رژیم کم FODMAP",
               "psyllium fiber, antispasmodics (mebeverine), probiotics; low-FODMAP diet")},
    {"icd": "C95", "en": "leukemia", "fa": "سرطان خون (لوسمی)",
     "alias": ["لوسمی", "سرطان خون", "leukaemia", "blood cancer"],
     "drugs": ("شیمی‌درمانی بسته به نوع (AML/ALL/CML/CLL)، تارگت‌تراپی (ایماتینیب در CML)، پیوند مغز استخوان — کاملاً تخصصی",
               "chemotherapy per type (AML/ALL/CML/CLL), targeted therapy (imatinib in CML), bone-marrow transplant - fully specialized")},
    {"icd": "C50", "en": "breast cancer", "fa": "سرطان سینه (پستان)",
     "alias": ["سرطان پستان", "سرطان سینه", "breast cancer"],
     "drugs": ("جراحی + شیمی‌درمانی؛ هورمون‌درمانی (تاموکسیفن)، هرسپتین در HER2 مثبت، پرتودرمانی",
               "surgery plus chemotherapy; hormone therapy (tamoxifen), trastuzumab for HER2+, radiotherapy")},
    {"icd": "C61", "en": "prostate cancer", "fa": "سرطان پروستات",
     "alias": ["سرطان پروستات", "prostate cancer"],
     "drugs": ("جراحی یا پرتودرمانی؛ هورمون‌درمانی (توقف آندروژن) در بیماری پیشرفته",
               "surgery or radiotherapy; androgen-deprivation hormone therapy in advanced disease")},
    {"icd": "C18", "en": "colon cancer", "fa": "سرطان کولون (روده‌ی بزرگ)",
     "alias": ["سرطان روده بزرگ", "سرطان کولون", "سرطان روده", "colon cancer", "colorectal cancer", "bowel cancer"],
     "drugs": ("جراحی + شیمی‌درمانی (FOLFOX)، آنتی‌بادی‌ها (بواسیزوماب) در موارد متاستاتیک",
               "surgery plus chemotherapy (FOLFOX), antibodies (bevacizumab) in metastatic cases")},
    {"icd": "C34", "en": "lung cancer", "fa": "سرطان ریه",
     "alias": ["سرطان ریه", "lung cancer"],
     "drugs": ("جراحی در مراحل اولیه، شیمی + ایمونوتراپی (پمبرولیزوماب) یا داروهای هدفمند بر اساس نوع بافت",
               "surgery in early stages, chemo plus immunotherapy (pembrolizumab) or targeted drugs by histology")},
    {"icd": "C43", "en": "melanoma", "fa": "ملانوما (سرطان پوست بدخیم)",
     "alias": ["ملانوما", "سرطان پوست", "melanoma", "skin cancer"],
     "drugs": ("جراحی برداشت وسیع؛ ایمونوتراپی (نیوولوماب) و هدفمند (وِمورافنیب) در موارد پیشرفته",
               "wide surgical excision; immunotherapy (nivolumab) and targeted therapy (vemurafenib) if advanced")},
    {"icd": "C16", "en": "stomach cancer", "fa": "سرطان معده",
     "alias": ["سرطان معده", "stomach cancer", "gastric cancer"],
     "drugs": ("جراحی + شیمی‌درمانی (CF یا FOLFOX)؛ هرسپتین در HER2 مثبت",
               "surgery plus chemotherapy (CF or FOLFOX); trastuzumab for HER2+")},
    {"icd": "M10", "en": "gout", "fa": "نقرس",
     "alias": ["نقرس", "gout"],
     "drugs": ("در حمله: NSAID یا کولشیسین؛ کاهش طولانی‌مدت اسید اوریک: آلوپورینول — شروعش وسط حمله ممنوع",
               "for attacks: NSAIDs or colchicine; long-term urate lowering: allopurinol - never started mid-attack")},
    {"icd": "M15", "en": "osteoarthritis", "fa": "آرتروز (استئوآرتریت)",
     "alias": ["آرتروز", "ساییدگی مفاصل", "استئو آرتریت", "arthrosis", "degenerative joint disease"],
     "drugs": ("استامینوفن خط اول، NSAID موضعی/خوراکی کوتاه‌مدت، تزریق داخل‌مفصلی در موارد منتخب + ورزش و کاهش وزن",
               "paracetamol first line, short-course topical/oral NSAIDs, intra-articular injection in selected cases, plus exercise and weight loss")},
    {"icd": "M06", "en": "rheumatoid arthritis", "fa": "آرتریت روماتوئید",
     "alias": ["روماتوید", "آرتریت روماتوئید", "روماتیسم مفصلی", "rheumatoid", "ra", "rheumatoid arthritis"],
     "drugs": ("متنکسات خط اول، سولفاسالازین، بیولوژیک‌ها (آدالیموماب)؛ هدف: درمان زودهنگام برای جلوگیری از خرابی مفصل",
               "methotrexate first line, sulfasalazine, biologics (adalimumab); the goal is early treatment to prevent joint damage")},
    {"icd": "M81", "en": "osteoporosis", "fa": "پوکی استخوان",
     "alias": ["پوکی استخوان", "استئوپروز", "osteoporosis"],
     "drugs": ("کلسیم + ویتامین D پایه؛ بیس‌فسفونات‌ها (آلندرونات) یا دنوسوماب در موارد تأییدشده",
               "calcium plus vitamin D as the base; bisphosphonates (alendronate) or denosumab when confirmed")},
    {"icd": "D50", "en": "iron deficiency anemia", "fa": "کم‌خونی کم‌آهن",
     "alias": ["کم خونی", "کم خونی آهنی", "anemia", "iron deficiency", "ida"],
     "drugs": ("آهن خوراکی با ویتامین C روی معده‌ی خالی + یافتن و درمان منبع خونریزی",
               "oral iron with vitamin C on an empty stomach plus finding and treating the bleeding source")},
    {"icd": "D56", "en": "thalassemia", "fa": "تالاسمی",
     "alias": ["تالاسمی مینور", "تالاسمی ماژور", "thalassemia"],
     "drugs": ("خون‌تزریسی منظم + داروهای کاهنده آهن (دِفِراسیروکس) در تالاسمی ماژور؛ مینور معمولاً فقط پایش",
               "regular transfusions plus iron chelation (deferasirox) in major; minor usually just monitoring")},
    {"icd": "D67", "en": "hemophilia", "fa": "هموفیلی",
     "alias": ["هموفیلی", "haemophilia", "hemophilia"],
     "drugs": ("تزریق فاکتور انعقادی جایگزین (۸ یا ۹) هنگام خونریزی یا پیش از جراحی — تخصص هماتولوژی",
               "replacement clotting factor (VIII or IX) during bleeding or before surgery - hematology specialty")},
    {"icd": "M32", "en": "systemic lupus erythematosus", "fa": "لوپوس اریتماتوز سیستمیک",
     "alias": ["لوپوس", "lupus", "sle"],
     "drugs": ("هیدروکسی‌کلروکین پایه، کورتون دوز پایین، ایمونوساپرسورها (آزاتیوپرین) در درگیری اندام",
               "hydroxychloroquine as the base, low-dose steroids, immunosuppressants (azathioprine) for organ involvement")},
    {"icd": "B16", "en": "hepatitis B", "fa": "هپاتیت ب",
     "alias": ["هپاتیت ب", "hepatitis b", "hbv"],
     "drugs": ("آنالوگ‌های خوراکی (تنوفوویر، ان‌تکاویر) در بیماری فعال؛ پایش منفی شدن HBsAg",
               "oral analogs (tenofovir, entecavir) in active disease; regular monitoring toward HBsAg clearance")},
    {"icd": "B18", "en": "hepatitis C", "fa": "هپاتیت سی",
     "alias": ["هپاتیت سی", "هپاتیت ث", "hepatitis c", "hcv"],
     "drugs": ("داروهای ضدویروس مستقیم (سوفوسبوویر + ولپاتاسویر) — درمان ۸ تا ۱۲ هفته با شانس درمان بالای ۹۵٪",
               "direct-acting antivirals (sofosbuvir + velpatasvir) - 8-12 week cure with >95% success")},
    {"icd": "U07", "en": "COVID-19", "fa": "کووید-۱۹ (کرونا)",
     "alias": ["کرونا", "کووید", "کرونا ویروس", "covid", "covid19", "covid 19", "corona"],
     "drugs": ("در موارد خفیف استراحت و مایعات؛ در بیماران پرخطر پاکس‌لویید؛ شدید: دکسمتازون و اکسیژن در بیمارستان",
               "mild cases: rest and fluids; Paxlovid for high-risk patients; severe: dexamethasone and hospital oxygen")},
    {"icd": "B50", "en": "malaria", "fa": "مالاریا",
     "alias": ["مالاریا", "malaria"],
     "drugs": ("کلروکین یا آرت‌میشین ترکیبی (آرت‌متر-لومفانترین) بسته به نوع و منطقه — فوری درمان می‌خواهد",
               "chloroquine or artemisinin combination (artemether-lumefantrine) by species and region - needs urgent treatment")},
    {"icd": "A15", "en": "pulmonary tuberculosis", "fa": "سل ریوی",
     "alias": ["سل", "توبرکولوز", "tb", "tuberculosis"],
     "drugs": ("رژیم چهار‌دارویی ۶ ماهه: ایزونیازید، ریفامپین، پیرازینامید، اتامبوتول — کامل کردن دوره حیاتی است",
               "6-month four-drug regimen: isoniazid, rifampin, pyrazinamide, ethambutol - completing the course is critical")},
    {"icd": "J11", "en": "influenza", "fa": "آنفولانزا",
     "alias": ["انفولانزا", "flu", "influenza"],
     "drugs": ("استراحت و مایعات؛ اسملتامایویر فقط در ۴۸ ساعت اول و برای پرخطرها",
               "rest and fluids; oseltamivir only within the first 48 hours and for high-risk patients")},
    {"icd": "J06", "en": "common cold", "fa": "سرماخوردگی",
     "alias": ["سرماخوردگی", "زکام", "cold", "common cold"],
     "drugs": ("درمان علامتی: استامینوفن، آنتی‌هیستامین، شربت سرفه؛ آنتی‌بیوتیک بی‌اثر است",
               "symptomatic care: paracetamol, antihistamines, cough syrup; antibiotics do nothing")},
    {"icd": "J32", "en": "sinusitis", "fa": "سینوزیت",
     "alias": ["سینوزیت", "التهاب سینوس ها", "sinusitis"],
     "drugs": ("شست‌وشوی بینی با سالین، اسپری کورتونی بینی؛ آنتی‌بیوتیک فقط در موارد باکتریایی (آموکسی‌سیلین)",
               "saline nasal rinse, steroid nasal spray; antibiotics only for bacterial cases (amoxicillin)")},
    {"icd": "N39", "en": "urinary tract infection", "fa": "عفونت ادراری",
     "alias": ["عفونت ادرار", "عفونت مثانه", "uti", "urinary tract infection", "bladder infection", "cystitis"],
     "drugs": ("نیتروفورانتوئین یا فوسفومایسین در عفونت ساده؛ آب فراوان — تشخیص با آزمایش ادرار",
               "nitrofurantoin or fosfomycin for simple cases; plenty of water - diagnosis by urine test")},
    {"icd": "N20", "en": "kidney stone", "fa": "سنگ کلیه",
     "alias": ["سنگ کلیه", "سنگ مثانه", "kidney stone", "renal stone", "nephrolithiasis"],
     "drugs": ("مسکن (ایبوپروفن)، آب ۲٫۵ تا ۳ لیتر؛ در سنگ‌های بزرگ: لیتوتریپسی یا اورولوژی",
               "pain relief (ibuprofen), 2.5-3 L water daily; larger stones: lithotripsy or urology")},
    {"icd": "N40", "en": "benign prostatic hyperplasia", "fa": "بزرگی خوش‌خیم پروستات",
     "alias": ["بزرگی پروستات", "پروستات", "bph", "enlarged prostate", "prostate enlargement"],
     "drugs": ("تامسولوزین (آلفابلاکر)، فیناستراید برای کوچک‌کردن؛ جراحی در موارد مقاوم",
               "tamsulosin (alpha-blocker), finasteride to shrink; surgery if refractory")},
    {"icd": "I83", "en": "varicose veins", "fa": "واریس",
     "alias": ["واریس", "varicose", "varicose veins"],
     "drugs": ("جوراب واریس، ورزش، بالا نگه‌داشتن پا؛ اسکلروتراپی یا جراحی برای موارد پیشرفته",
               "compression stockings, exercise, leg elevation; sclerotherapy or surgery for advanced cases")},
    {"icd": "K64", "en": "hemorrhoids", "fa": "بواسیر (هموروئید)",
     "alias": ["بواسیر", "هموروئید", "hemorrhoids", "piles"],
     "drugs": ("فیبر + آب، حمام نشسته، پماد موضعی؛ بندگذاری لاستیکی یا جراحی در درجات بالا",
               "fiber plus water, sitz baths, topical ointments; rubber-band ligation or surgery for higher grades")},
    {"icd": "H40", "en": "glaucoma", "fa": "گلوکوم (آب سیاه چشم)",
     "alias": ["گلوکوم", "آب سیاه", "glaucoma"],
     "drugs": ("قطره‌های کاهنده‌ی فشار چشم (لاتانوپراست، تیمولول) — درمان قطعی با لیزر یا جراحی",
               "pressure-lowering drops (latanoprost, timolol) - definitive treatment by laser or surgery")},
    {"icd": "H25", "en": "cataract", "fa": "آب‌مرواراد (کاتاراکت)",
     "alias": ["آب مرواراد", "کاتاراکت", "cataract"],
     "drugs": ("دارویی ندارد؛ جراحی تعویض عدسی درمان قطعی و بسیار موفق است",
               "no medication; lens-replacement surgery is the definitive and highly successful treatment")},
    {"icd": "I50", "en": "heart failure", "fa": "نارسایی قلبی",
     "alias": ["نارسایی قلب", "ضعف قلب", "heart failure", "chf"],
     "drugs": ("مهارکننده ACE/ARNI، بتابلاکر، داباگاتران-گروه SGLT2، دیورتیک — تنظیم تخصصی کاردیولوژی",
               "ACE inhibitors/ARNI, beta-blockers, SGLT2 inhibitors, diuretics - specialized cardiology management")},
    {"icd": "I20", "en": "angina pectoris", "fa": "آنژین صدری",
     "alias": ["آنژین", "بیماری عروق کرونر", "angina", "coronary artery disease", "cad"],
     "drugs": ("آسپرین، استاتین، بتابلاکر، نیترات زیرزبان در درد — ارزیابی فوری قلب لازم است",
               "aspirin, statins, beta-blockers, sublingual nitrate for pain - urgent cardiac workup needed")},
    {"icd": "I63", "en": "stroke", "fa": "سکته‌ی مغزی",
     "alias": ["سکته مغزی", "stroke", "cerebrovascular accident", "cva"],
     "drugs": ("در پنجره‌ی طلایی tPA یا بازسازی عروق؛ پیشگیری ثانویه: آسپرین/کلوپیدوگرل + استاتین + کنترل فشار",
               "tPA or mechanical thrombectomy in the golden window; secondary prevention: aspirin/clopidogrel, statins, BP control")},
    {"icd": "G47", "en": "obstructive sleep apnea", "fa": "آپنه‌ی خواب انسدادی",
     "alias": ["آپنه خواب", "قطع تنفس خواب", "sleep apnea", "osa"],
     "drugs": ("دارو ندارد؛ دستگاه CPAP شبانه + کاهش وزن درمان اصلی‌اند",
               "no drug; nightly CPAP plus weight loss are the main treatments")},
    {"icd": "J30", "en": "allergic rhinitis", "fa": "رینیت آلرژیک (حساسیت فصلی)",
     "alias": ["آلرژی فصلی", "حساسیت", "آلرژی", "allergic rhinitis", "hay fever", "allergy"],
     "drugs": ("اسپری کورتونی بینی (فلوتیکازون) خط اول، آنتی‌هیستامین (سیتریزین)، اجتناب از محرک",
               "steroid nasal spray (fluticasone) first line, antihistamines (cetirizine), trigger avoidance")},
]

_engine_by_key: dict[str, dict] = {}
_icd_by_key: dict[str, tuple[str, str]] = {}
_fa2en: dict[str, str] = {}
_wiki_by_key: dict[str, dict] = {}
_curated_by_key: dict[str, dict] = {}
_symptom_keys: set[str] = set()
_loaded = False


def _nk(s: str) -> str:
    return "".join(ch for ch in str(s or "").lower() if ch.isalnum())


def _load_all() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    for c in _CURATED:
        keys = {_nk(x) for x in c["alias"]} | {_nk(c["en"]), _nk(c["fa"])}
        for k in keys:
            if k and k not in _curated_by_key:
                _curated_by_key[k] = c
    try:
        from medical_engine import DISEASES, SYMPTOM_NAMES_FA, SYMPTOM_NAMES_EN
        for d in DISEASES:
            for nm in (d.get("fa", ""), d.get("en", "")):
                k = _nk(nm)
                if k and k not in _engine_by_key:
                    _engine_by_key[k] = d
        def _sym_names(d):
            out = list(d)
            if isinstance(d, dict):
                out += [str(v) for v in d.values()]
            return out
        for nm in _sym_names(SYMPTOM_NAMES_FA) + _sym_names(SYMPTOM_NAMES_EN):
            for part in str(nm).replace("/", " ").split():
                k = _nk(part)
                if k:
                    _symptom_keys.add(k)
    except Exception:
        pass
    try:
        nlm = json.load(open(os.path.join(DATA_DIR, "nlm_conditions.json"), encoding="utf-8"))
        for it in nlm:
            k = _nk(it.get("name", ""))
            if not k:
                continue
            cur = _icd_by_key.get(k)
            if cur is None or len(it["name"]) < len(cur[0]):
                _icd_by_key[k] = (it["name"], it.get("icd10", "") or "")
    except Exception:
        pass
    try:
        fa = json.load(open(os.path.join(DATA_DIR, "fa_names.json"), encoding="utf-8"))
        for en, fa_name in (fa.get("disease_en_fa") or {}).items():
            k = _nk(fa_name)
            if k and k not in _fa2en:
                _fa2en[k] = en
    except Exception:
        pass
    try:
        wk = json.load(open(os.path.join(DATA_DIR, "wiki_diseases.json"), encoding="utf-8"))
        for e in wk.values():
            k = _nk(e.get("en", ""))
            if not k:
                continue
            cur = _wiki_by_key.get(k)
            if cur is None or (e.get("icd") and not cur.get("icd")):
                _wiki_by_key[k] = {"en": e.get("en", ""), "fa": e.get("fa", ""), "icd": e.get("icd", "")}
    except Exception:
        pass


_STRIP_RE = None


def _core_of(message: str) -> str:
    global _STRIP_RE
    if _STRIP_RE is None:
        parts = sorted(_WRAPPERS, key=len, reverse=True)
        _STRIP_RE = re.compile(r"^(?:" + "|".join(re.escape(p) for p in parts) + r")[\s:،,]+|[\s:،,]+(?:" +
                               "|".join(re.escape(p) for p in parts) + r")$", re.I)
    t = str(message or "").strip().strip("؟?!.:،, ")
    for _ in range(3):
        t2 = _STRIP_RE.sub(" ", t).strip()
        if t2 == t:
            break
        t = t2
    return t.strip()


def resolve(core: str) -> dict[str, Any] | None:
    _load_all()
    if not core or len(core) < 2:
        return None
    k = _nk(core)
    if not k:
        return None
    code_m = re.match(r"^([A-TV-Z][0-9]{2}(?:\.[0-9]{1,2})?)$", core.strip().upper())
    if code_m:
        code = code_m.group(1)
        name = ""
        for nm, ic in _icd_by_key.items():
            if ic[1] == code:
                name = ic[0]
                break
        if not name:
            name = code
        return {"en": name, "fa": "", "icd": code, "engine": None, "drugs": None, "source": "code"}
    if len(k) <= 4 and k not in _curated_by_key and k not in _engine_by_key:
        return None
    c = _curated_by_key.get(k)
    if c:
        return {"en": c["en"], "fa": c["fa"], "icd": c["icd"], "engine": None,
                "drugs": c["drugs"], "source": "curated"}
    eng = _engine_by_key.get(k)
    if eng:
        cur_drugs = None
        for cc in _CURATED:
            if _nk(cc["en"]) == k or _nk(cc["fa"]) == k or k in {_nk(a) for a in cc["alias"]}:
                cur_drugs = cc["drugs"]
                break
        return {"en": eng.get("en", ""), "fa": eng.get("fa", ""), "icd": "",
                "engine": eng, "drugs": cur_drugs, "source": "engine"}
    en = _fa2en.get(k)
    if en:
        ek = _nk(en)
        c = _curated_by_key.get(ek)
        if c:
            return {"en": c["en"], "fa": c["fa"], "icd": c["icd"], "engine": None,
                    "drugs": c["drugs"], "source": "curated"}
        hit = _icd_by_key.get(ek)
        if hit:
            return {"en": hit[0], "fa": core, "icd": hit[1], "engine": None,
                    "drugs": None, "source": "fa_bank"}
    hit = _icd_by_key.get(k)
    if hit:
        return {"en": hit[0], "fa": "", "icd": hit[1], "engine": None,
                "drugs": None, "source": "icd"}
    wk = _wiki_by_key.get(k)
    if wk:
        return {"en": wk["en"], "fa": wk.get("fa", ""), "icd": wk.get("icd", ""),
                "engine": None, "drugs": None, "source": "wiki"}
    return None


def answer_if_disease(message: str) -> str | None:
    from i18n import is_fa
    fa = is_fa()
    core = _core_of(message or "")
    r = resolve(core)
    if r is None:
        return None
    _load_all()
    k = _nk(core)
    rk = _nk(r.get("en", "")) + "|" + _nk(r.get("fa", ""))
    if (k in _symptom_keys or _nk(r.get("en", "")) in _symptom_keys) and r.get("source") != "curated":
        return None
    from knowledge_browser import full_profile, fa_disease_name
    name_en = r["en"]
    icd = r.get("icd", "")
    fa_name = r.get("fa") or fa_disease_name(icd, name_en)
    p = full_profile(name_en, icd, "", "", [], [])
    about = p["about_fa"] if fa else p["about_en"]
    if "ثبت‌شده" in about or "recorded medical" in about:
        from synth_desc import synthesize_description
        about = (synthesize_description(name_en, icd, ""))[0 if fa else 1]
    meds = r.get("drugs")
    med_txt = (meds[0] if fa else meds[1]) if meds else (p["drug_fb_fa"] if fa else p["drug_fb_en"])
    sym_txt = p["sym_fb_fa"] if fa else p["sym_fb_en"]
    L = (lambda a, b: b) if fa else (lambda a, b: a)
    lines = []
    if fa:
        title = f"{fa_name} ({name_en})" if fa_name else name_en
    else:
        title = f"{name_en} ({fa_name})" if fa_name else name_en
    lines.append(title + (f"  [ICD-10: {icd}]" if icd else ""))
    lines.append("")
    lines.append(L("What it is", "درباره") + ":")
    lines.append(about[:380])
    lines.append("")
    lines.append(L("Common signs", "علائم شایع") + ": " + sym_txt)
    lines.append("")
    lines.append(L("Common medications", "داروهای رایج") + ":")
    lines.append(med_txt)
    lines.append("")
    lines.append(L("Treatment", "درمان") + ": " + (p["treat_fa"] if fa else p["treat_en"]))
    eng = r.get("engine")
    if eng:
        advice = eng.get("advice") if fa else (eng.get("advice_en") or eng.get("advice"))
        if advice:
            lines.append("")
            lines.append(L("Self-care", "مراقبت خانگی") + ": " + "؛ ".join(advice[:3]))
        dw = eng.get("doctor_when") if fa else (eng.get("doctor_when_en") or eng.get("doctor_when"))
        if dw:
            lines.append(L("See a doctor if", "چه زمانی پزشک") + ": " + dw)
    lines.append("")
    lines.append(L("Dose and final drug choice are decided by a doctor.",
                   "دوز و انتخاب نهایی دارو را پزشک تعیین می‌کند."))
    return "\n".join(lines)
