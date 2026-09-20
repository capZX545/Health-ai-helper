"""
medical_qa.py — hard-coded GPT-quality answers for common medical questions
that banks alone can't answer well. Concise, structured, bilingual.
"""
from __future__ import annotations


def _fa() -> bool:
    from i18n import is_fa
    return is_fa()


_QA: list[tuple[tuple, str, str]] = [
    (("فرق دیابت نوع ۱ و ۲", "فرق دیابت ۱ و ۲", "تفاوت دیابت"),
     ("difference between type 1 and type 2", "type 1 vs type 2"),
     """ **فرق دیابت نوع ۱ و ۲:**

**نوع ۱:**
• بیماری خودایمنی — بدن سلول‌های انسولین‌ساز پانکراس را تخریب می‌کند
• معمولاً از کودکی یا نوجوانی شروع می‌شود
• بدن انسولین **نمی‌سازد**
• درمان: تزریق انسولین مادام‌العمر (اجباری)
• ~۵-۱۰٪ کل دیابت‌ها

**نوع ۲:**
• مقاومت به انسولین — بدن انسولین می‌سازد ولی استفاده نمی‌تواند بکند
• معمولاً بعد از ۳۰-۴۰ سالگی (در حال افزایش در جوان‌ترها)
• بدن انسولین **می‌سازد ولی کافی نیست**
• درمان: رژیم + ورزش → قرص (متفورمین) → گاهی انسولین
• ~۹۰-۹۵٪ کل دیابت‌ها

**خلاصه:** نوع ۱ = کمبود انسولین؛ نوع ۲ = مقاومت به انسولین""",

     """ **Type 1 vs Type 2 Diabetes:**

**Type 1:**
• Autoimmune — body destroys insulin-producing cells
• Usually starts in childhood/teens
• Body makes **no insulin**
• Treatment: lifelong insulin injections (mandatory)
• ~5-10% of all diabetes

**Type 2:**
• Insulin resistance — body makes insulin but can't use it
• Usually after age 30-40
• Body makes insulin **but not enough**
• Treatment: diet + exercise → tablets (metformin) → sometimes insulin
• ~90-95% of all diabetes"""),

    (("ویتامین د چقدر", "ویتامین دی چقدر", "دوز ویتامین د", "ویتامین d چقدر", "ویتامین d بخورم"),
     ("vitamin d dose", "vitamin d how much", "vitamin d"),
     """ **دوز ویتامین D:**

• **بزرگسالان:** ۶۰۰-۸۰۰ واحد بین‌المللی (IU) در روز
• **بالای ۷۰ سال:** ۸۰۰ IU در روز
• **کمبود شدید (فقط با آزمایش و نظر پزشک):** ۵۰,۰۰۰ واحد هفته‌ای برای ۸ هفته
• **بارداری:** ۶۰۰ IU در روز

**منابع طبیعی:**
• نور خورشید: ۱۰-۱۵ دقیقه، ۲-۳ بار در هفته (بدید ضدآفتاب)
• ماهی چرب (سالمون، تن): ~۳۶۰-۶۰۰ IU در ۱۰۰ گرم
• زرده تخم‌مرغ: ~۴۰ IU

 دوز بالای ۴,۰۰۰ IU در روز بدون نظر پزشک **مسمومیت** ایجاد می‌کند (کلسیم بالا، سنگ کلیه).""",

     """ **Vitamin D dosage:**

• **Adults:** 600-800 IU/day
• **Over 70:** 800 IU/day
• **Severe deficiency (lab + doctor only):** 50,000 IU weekly for 8 weeks
• **Pregnancy:** 600 IU/day

**Sources:** sunlight 10-15 min 2-3×/week; fatty fish 360-600 IU/100g; egg yolk ~40 IU

 Over 4,000 IU/day without medical supervision can cause toxicity."""),

    (("چرا همیشه خسته", "همیشه خسته‌ام", "دلیل خستگی"),
     ("why am i always tired", "always fatigued"),
     """ **دلایل شایع خستگی مداوم:**

**سبک زندگی (شایع‌ترین):**
• کم‌خوابی (زیر ۷ ساعت) یا بی‌کیفیت بودن خواب
• کم‌تحرکی — پارادوکس‌طورانه ورزش انرژی می‌دهد
• تغذیه‌ی ضعیف (قند زیاد → افت انرژی)
• کم‌آبی
• استرس مزمن

**پزشکی (نیاز به آزمایش):**
• کم‌خونی (فقر آهن) → آزمایش CBC + فریتین
• کم‌کاری تیروئید → آزمایش TSH
• کمبود ویتامین D یا B12
• آپنه خواب (خروپف + خواب‌آلودگی روزانه)
• دیابت کنترل‌نشده

**چه کنم؟**
۱. خواب منظم ۷-۹ ساعت
۲. ورزش روزانه ۳۰ دقیقه پیاده‌روی
۳. آب کافی (۸ لیوان)
۴. اگر بعد از ۲-۳ هفته بهتر نشدی → آزمایش CBC، TSH، فریتین، ویتامین D""",

     """ **Common causes of persistent fatigue:**

**Lifestyle:** poor sleep (<7h), inactivity, poor diet, dehydration, chronic stress
**Medical (need labs):** anemia (CBC+ferritin), hypothyroidism (TSH), vitamin D/B12 deficiency, sleep apnea, diabetes

**Do:** 7-9h regular sleep, 30 min daily walk, adequate water
**If not better in 2-3 weeks → get CBC, TSH, ferritin, vitamin D checked**"""),
    (("فشار خون نرمال", "فشار خون چقدر نرمال", "فشار خون چنده", "فشار خون چقدر باشه", "فشار خون سالم"),
     ("normal blood pressure", "blood pressure normal", "blood pressure chart", "bp normal"),
     """**مقادیر فشار خون (mmHg):**
• طبیعی: زیر ۱۲۰ / زیر ۸۰
• بالاتر از حد نرمال: ۱۲۰-۱۲۹ / زیر ۸۰
• مرحله ۱: ۱۳۰-۱۳۹ یا ۸۰-۸۹
• مرحله ۲: ۱۴۰ به بالا یا ۹۰ به بالا
• بحران: ۱۸۰ به بالا یا ۱۲۰ به بالا

اندازه‌گیری درست: ۵ دقیقه بنشین، پشت تکیه‌گاه، کف پا روی زمین، دست در سطح قلب؛ دو بار با فاصله بگیر و میانگین بزن. قهوه و سیگار تا ۳۰ دقیقه قبل عدد را بالا می‌برد.

۱۸۰/۱۲۰ یا بالاتر همراه با سردرد، تاری دید یا درد سینه = اورژانس ۱۱۵.""",

     """**Blood pressure ranges (mmHg):**
• Normal: <120/<80 • Elevated: 120-129/<80 • Stage 1: 130-139 or 80-89
• Stage 2: >=140 or >=90 • Crisis: >=180/120

Measure right: sit 5 min, back supported, arm at heart level, average two readings; coffee/smoking 30 min before raises it.

>=180/120 with headache, vision change or chest pain = call emergency services."""),

    (("قند ناشتا چقدر", "قند خون نرمال چنده", "قند ناشتا نرمال", "قند خون نرمال چیه", "قند چقدر باشه"),
     ("fasting glucose normal", "normal blood sugar", "fasting blood sugar range"),
     """**قند خون (mg/dL):**
• ناشتا طبیعی: ۷۰-۹۹
• پیش‌دیابت: ۱۰۰-۱۲۵
• دیابت: ۱۲۶ یا بالاتر (در دو آزمایش تکرارشده)
• دو ساعت بعد از غذا، طبیعی: زیر ۱۴۰
• تصادفی بالای ۲۰۰ با تشنگی و تکرر ادرار: احتمال دیابت

ناشتا یعنی ۸ ساعت بدون کالری؛ آب آزاد است.

زیر ۷۰ با تعریق، لرز یا ضعف = افت قند: ۱۵ گرم قند سریع (خرما یا آب‌قند) و بعد از ۱۵ دقیقه دوباره بررسی.""",

     """**Blood glucose (mg/dL):**
• Fasting normal 70-99 • Prediabetes 100-125 • Diabetes >=126 twice
• 2h after meal normal <140 • Random >=200 with thirst/urination = likely diabetes

Fasting = 8 hours, no calories (water fine).

Below 70 with sweating/tremor = hypoglycemia: 15 g fast carbs, recheck in 15 minutes."""),

    (("هموگلوبین a1c", "a1c چقدر", "hba1c چقدر", "a1c نرمال", "آ۱سی"),
     ("hba1c normal", "a1c normal", "a1c how much"),
     """**HbA1c — ناشتا لازم ندارد:**
• طبیعی: زیر ۵٫۷ درصد
• پیش‌دیابت: ۵٫۷ تا ۶٫۴
• دیابت: ۶٫۵ یا بالاتر
• هدف درمان در بیشتر دیابتی‌ها: زیر ۷ (در سالمند یا بیماری پیشرفته هدف شل‌تر)

مزیتش: میانگین قند ۲ تا ۳ ماه اخیر را نشان می‌دهد، نه لحظه را.

بالای ۸ یعنی قند کنترل‌نشده و خطر بیشتر عوارض چشم، کلیه و عصب.""",

     """**HbA1c - no fasting needed:**
• Normal <5.7% • Prediabetes 5.7-6.4% • Diabetes >=6.5%
• Target for most diabetics <7% (looser for frail elderly)

It shows the 2-3 month average glucose, not the moment.

Above 8% = uncontrolled sugar and rising eye/kidney/nerve risk."""),

    (("کلسترول نرمال", "کلسترول چقدر", "ldl چقدر باشه", "ldl نرمال", "کلسترول خوب"),
     ("normal cholesterol", "ldl normal", "cholesterol chart", "ldl how much"),
     """**چربی خون (mg/dL):**
• کلسترول کل: مطلوب زیر ۲۰۰
• LDL (بد): بهینه زیر ۱۰۰؛ با دیابت یا بیماری قلبی هدف زیر ۷۰
• HDL (خوب): مردان بالای ۴۰، زنان بالای ۵۰
• تری‌گلیسیرید: زیر ۱۵۰ (ناشتا بگیر)

اثرگذارترین تغییرها: حذف چربی ترانس، فیبر بیشتر (جو دوسر، حبوبات)، ۱۵۰ دقیقه ورزش در هفته، ترک سیگار.

لازم بودن استاتین را پزشک تعیین می‌کند؛ خودسرانه شروع یا قطع نکن.""",

     """**Lipids (mg/dL):**
• Total desirable <200 • LDL optimal <100 (<70 with diabetes/heart disease)
• HDL men >40, women >50 • Triglycerides <150 (fasting)

Biggest levers: cut trans fat, more fiber (oats, legumes), 150 min/week exercise, quit smoking.

Whether a statin is needed is a doctor's decision."""),

    (("tsh چقدر", "تیروئید نرمال", "tsh نرمال", "کم‌کاری تیروئید چیه", "پرکاری تیروئید چیه"),
     ("tsh normal", "thyroid normal range", "hypothyroid vs hyperthyroid", "tsh how much"),
     """**TSH (mIU/L):** طبیعی حدود ۰٫۴ تا ۴
• بالا = کم‌کاری تیروئید: خستگی، افزایش وزن، تحمل نکردن سرما، یبوست، خشکی پوست، ریزش مو
• پایین = پرکاری: تپش قلب، لرز دست، کاهش وزن، عرق کردن، بی‌قراری

TSH بالا یعنی غده کم‌کار است و مغز هورمون تحریک‌کننده‌ی بیشتری می‌فرستد — برعکسِ حدس اول.

تشخیص و دوز دارو با پزشک است؛ تا تنظیم دوز، هر ۶ تا ۸ هفته TSH تکرار می‌شود.""",

     """**TSH (mIU/L):** normal about 0.4-4.
• High = hypothyroid: fatigue, weight gain, cold intolerance, constipation, hair loss
• Low = hyperthyroid: palpitations, tremor, weight loss, sweating, restlessness

High TSH means the gland is underactive - opposite of the first guess.

Diagnosis and dosing belong to a doctor; TSH is rechecked every 6-8 weeks until stable."""),

    (("ویتامین ب۱۲ چقدر", "b12 چقدر", "ویتامین b12 کمبود"),
     ("vitamin b12 normal", "b12 deficiency", "b12 how much"),
     """**ویتامین B12 (pg/mL):**
• طبیعی: ۲۰۰ تا ۹۰۰
• زیر ۲۰۰ = کمبود؛ ۲۰۰ تا ۳۰۰ مرزی است

در معرض کمبود: گیاه‌خواران، بالای ۶۰ سال، مصرف طولانی متفورمین یا امپرازول، بعد از جراحی معده.

علائم: خستگی، گزگز دست و پا، اختلال حافظه، زبان قرمز و دردناک، کم‌خونی.

کمبود درمان‌نشده به عصب آسیب دائمی می‌زند؛ با پزشک مشورت کن.""",

     """**Vitamin B12 (pg/mL):** normal 200-900; <200 deficient; 200-300 borderline.

At risk: vegetarians, age >60, long-term metformin or PPI use, gastric surgery.

Symptoms: fatigue, tingling hands/feet, memory problems, sore red tongue, anemia.

Untreated deficiency can permanently damage nerves."""),

    (("هموگلوبین چقدر", "هموگلوبین نرمال", "کم خونی چقدر", "hb نرمال"),
     ("normal hemoglobin", "low hemoglobin", "hemoglobin how much"),
     """**هموگلوبین (g/dL):**
• مرد: ۱۳٫۵ تا ۱۷٫۵ — زیر ۱۳ کم‌خونی
• زن: ۱۲ تا ۱۵٫۵ — زیر ۱۲ کم‌خونی
• بارداری: زیر ۱۱ چشم‌گیر است

شایع‌ترین علت در زنان جوان کمبود آهن است (قاعدگی سنگین یا رژیم فقیر)؛ آزمایش فریتین را همزمان بگیر که ذخیره‌ی آهن را نشان می‌دهد.

کم‌خونی همراه با درد قفسه سینه، تنگی نفس شدید یا خونریزی فعال = همان روز پزشک.""",

     """**Hemoglobin (g/dL):** men 13.5-17.5 (<13 = anemia); women 12-15.5 (<12 = anemia); pregnancy <11 significant.

Most common cause in young women is iron deficiency; order ferritin alongside to see iron stores.

Anemia with chest pain, severe breathlessness or active bleeding = same-day doctor."""),

    (("فریتین چقدر", "فریتین نرمال", "ذخیره آهن"),
     ("ferritin normal", "ferritin how much"),
     """**فریتین (ng/mL) — ذخیره‌ی آهن بدن:**
• مرد: حدود ۳۰ تا ۴۰۰
• زن: حدود ۱۵ تا ۲۰۰
• زیر ۳۰ = ذخیره‌ی آهن خالی، حتی وقتی هموگلوبین هنوز نرمال است

فریتین با التهاب هم بالا می‌رود؛ در عفونت فعال ممکن است با وجود کمبود، نرمال دیده شود (همزمان CRP ببین).

فریتین پایین با خستگی و ریزش مو، قبل از افت هموگلوبین خودش را نشان می‌دهد.""",

     """**Ferritin (ng/mL) - iron stores:** men ~30-400, women ~15-200. Below 30 = empty stores even with normal hemoglobin.

Ferritin rises with inflammation, so it can look normal despite deficiency (check CRP alongside).

Low ferritin causes fatigue and hair loss before anemia appears."""),

    (("گویچه سفید", "wbc نرمال", "سفید خون چقدر", "wbc بالا یعنی"),
     ("normal wbc", "wbc high means", "white blood cell count"),
     """**WBC — گویچه‌های سفید (در میکرولیتر):**
• طبیعی: ۴۵۰۰ تا ۱۱۰۰۰
• بالا: عفونت باکتریایی (شایع‌ترین)، التهاب، استرس، سیگار، کورتون
• پایین: سرماخوردگی و آنفولانزا (افت موقت)، برخی داروها

راهنمای تقریبی: نوتروفیل بالا به باکتری و لنفوسیت بالا به ویروس اشاره می‌کند — تقریبی است، نه قطعی.

WBC بالای ۲۵ هزار، زیر ۲ هزار، یا همراه با تب بالا و بدحالی شدید = فوری پزشک.""",

     """**WBC (per microliter):** normal 4,500-11,000.
• High: bacterial infection (most common), inflammation, stress, smoking, steroids
• Low: cold/flu viruses (temporary), some drugs

High neutrophils hint bacterial; high lymphocytes hint viral - a rough guide, not a verdict.

WBC >25k, <2k, or with high fever and severe illness = urgent care."""),

    (("پلاکت چقدر", "پلاکت نرمال"),
     ("normal platelet", "platelet count"),
     """**پلاکت (هزار در میکرولیتر):**
• طبیعی: ۱۵۰ تا ۴۵۰
• پایین (زیر ۱۰۰): کبودی و خونریزی آسان‌تر
• بالا (بالای ۵۰۰): التهاب، کمبود آهن، بعد از عفونت

پلاکت پایین همراه با تب و لکه‌های ریز پوستی = همان روز پزشک.

پلاکت بالای یک میلیون یا لخته‌های تکرارشونده = بررسی تخصصی.""",

     """**Platelets (thousand per microliter):** normal 150-450.
• Low (<100): easier bruising and bleeding • High (>500): inflammation, iron deficiency, post-infection

Low platelets with fever and tiny skin spots = same-day doctor.

Platelets above one million or repeated clots = specialist workup."""),

    (("کراتینین چقدر", "کراتینین نرمال", "کرئاتینین بالا"),
     ("normal creatinine", "creatinine how much", "high creatinine"),
     """**کراتینین خون (mg/dL):**
• مرد: حدود ۰٫۷ تا ۱٫۳
• زن: حدود ۰٫۶ تا ۱٫۱

نکته‌ها:
• به عضله وابسته است؛ ورزشکار عضلانی عدد بالاتر و سالمند لاغر عدد پایین‌تری دارد حتی با کلیه‌ی ضعیف
• یک عدد تکی تشخیص نمی‌دهد؛ روند و کلیرانس مهم‌ترند (ماژول دوز کلیوی همین برنامه کلیرانس را حساب می‌کند)
• ایبوپروفن و بعضی آنتی‌بیوتیک‌ها عدد را بالا می‌برند

افزایش جدید کراتینین، مخصوصاً با تورم یا کاهش ادرار = پزشک.""",

     """**Creatinine (mg/dL):** men ~0.7-1.3, women ~0.6-1.1.

It depends on muscle mass; one number alone doesn't decide - the trend and clearance matter more (the Renal dosing module here computes clearance). NSAIDs and some antibiotics raise it.

A new rise, especially with swelling or low urine output = doctor."""),

    (("اسید اوریک", "اوره خون", "نقرس چیه"),
     ("uric acid normal", "gout what is", "high uric acid"),
     """**اسید اوریک (mg/dL):**
• مطلوب: زیر ۷ (در برخی آزمایشگاه‌ها محدوده‌ی نرمال تا ۸ هم گزارش می‌شود)
• بالای ۷ با حمله‌ی درد مفصلی = نقرس

حمله‌ی نقرس: درد ناگهانی و شدید پای شست (قرمز، گرم، متورم) اغلب نیمه‌شب.

کارهایی که کمک می‌کند: آب فراوان (۲ تا ۳ لیتر)، کاهش وزن آرام، پرهیز از الکل و گوشت اندام‌ها (جگر، کله‌پاچه)، شربت‌های شیرین.

در حمله‌ی حاد، شروع یا قطع آلوپورینول بدون پزشک ممنوع است؛ مسکن ضدالتهاب با پزشک.""",

     """**Uric acid (mg/dL):** desirable below 7; above 7 with joint pain attacks = gout.

A gout attack: sudden severe pain of the big toe (red, hot, swollen), often at night.

Helps: 2-3 L water daily, gradual weight loss, avoiding alcohol and organ meats, sugary drinks.

Do not start or stop allopurinol during an acute attack without a doctor."""),

    (("پتاسیم چقدر", "سدیم چقدر", "پتاسیم نرمال", "سدیم نرمال"),
     ("normal potassium", "normal sodium", "potassium how much"),
     """**الکترولیت‌های خون:**
• پتاسیم (mEq/L): ۳٫۵ تا ۵ — خارج از این بازه، از خطر ریتم قلب است
• سدیم (mEq/L): ۱۳۵ تا ۱۴۵

پتاسیم بالا: علائمش ضعف و گزگز است؛ در نارسایی کلیه یا بعضی داروهای فشار (لوزارتان، اسپیرونولاکتون، ACE) دیده می‌شود.
سدیم پایین: در مسکن‌های قوی، آب زیاد، نارسایی قلبی؛ علائمش گیجی و ضعف است.

هر دو انحراف قابل‌توجه نیاز به بررسی فوری پزشک دارد؛ خودت عدد را تفسیر و درمان نکن.""",

     """**Blood electrolytes:**
• Potassium (mEq/L): 3.5-5.0 - outside this range is a heart-rhythm risk
• Sodium (mEq/L): 135-145

High potassium appears in kidney failure and with some BP drugs (losartan, spironolactone, ACE inhibitors).
Low sodium appears with strong painkillers, excess water and heart failure; symptoms are confusion and weakness.

Both significant deviations need prompt medical review - don't interpret or treat them yourself."""),

    (("alt ast بالا", "کبد چرب", "انزیم کبد", "alt نرمال", "sgpt بالا"),
     ("fatty liver", "high alt ast", "alt normal", "liver enzymes high"),
     """**ALT/AST (واحد در لیتر):**
• طبیعی: تا حدود ۴۰ (مرد) و ۳۲ (زن)؛ بعضی آزمایشگاه‌ها تا ۵۰ می‌گیرند

شایع‌ترین علت افزایش خفیف امروز: **کبد چرب غیرالکلی** — چاقی، قند بالا، چربی خون، کم‌تحرکی.

کارهایی که ALT را پایین می‌آورد: کاهش ۷ تا ۱۰ درصد وزن، حذف نوشیدنی‌های شیرین، ورزش منظم، قطع الکل.

ALT بالای ۱۰۰، زردی پوست یا چشم، ادرار خیلی تیره، یا استفراغ خونی = فوری پزشک.""",

     """**ALT/AST (U/L):** normal up to ~40 (men) and ~32 (women); some labs use 50.

The most common cause of mild elevation today: **non-alcoholic fatty liver** - obesity, high sugar, dyslipidemia, inactivity.

Lowers ALT: 7-10% weight loss, cutting sugary drinks, regular exercise, stopping alcohol.

ALT >100, yellow skin/eyes, very dark urine, or bloody vomit = urgent care."""),

    (("crp بالا", "سرعت رسوب", "esr بالا", "crp چیه"),
     ("high crp", "crp means", "esr high"),
     """**CRP و ESR — نشانگرهای التهاب:**
• CRP بالا (مثلاً بالای ۱۰ mg/L) یعنی در بدن التهاب فعال است
• عفونت باکتریایی معمولاً CRP را خیلی بالاتر می‌برد (اغلب بالای ۵۰)
• ویروس‌ها و التهاب‌های مزمن بالا رفتن خفیف‌تری می‌دهند
• ESR کندتر است و روند بیماری‌های مزمن را نشان می‌دهد

این دو نمی‌گویند التهاب کجاست؛ فقط می‌گویند هست — تفسیرش با علائم و پزشک است.

CRP خیلی بالا با تب و بدحالی = همان روز پزشک.""",

     """**CRP and ESR - inflammation markers:**
• High CRP (e.g. >10 mg/L) = active inflammation somewhere
• Bacterial infections usually push CRP much higher (often >50)
• Viruses and chronic inflammation cause milder rises
• ESR is slower and tracks chronic disease better

They don't say where the inflammation is - only that it exists; interpretation belongs with symptoms and a doctor.

Very high CRP with fever and feeling very ill = same-day doctor."""),

    (("تست بارداری کی", "تست بارداری چند روزگی", "تست بارداری چه زمانی", "آزمایش بارداری چه زمانی", "کی بفهمم باردارم"),
     ("when to take pregnancy test", "pregnancy test timing", "how early pregnancy test"),
     """**تست بارداری چه زمانی معتبر است:**
• بهترین زمان: از روزِ جاماندن پریود (حدود ۱۴ روز بعد از تخمک‌گذاری)
• تست خانگی ادرار: صبحگاهی با ادرار غلیظ دقیق‌ترین است
• خون (beta-hCG): حدود ۱۰ تا ۱۱ روز بعد از تخمک‌گذاری، زودتر از ادرار جواب می‌دهد

منفی ولی پریود نشده: بعد از ۴۸ ساعت دوباره تست کن (احتمال بارداری دیر لانه‌گزین‌شده).

خونریزی یا درد یک‌طرفه‌ی شدید شکم با تست مثبت = احتمال حاملگی خارج رحم؛ فوراً اورژانس.""",

     """**Pregnancy test timing:**
• Best: from the day of the missed period (~14 days after ovulation)
• Urine home test: most accurate with concentrated morning urine
• Blood beta-hCG: works earlier, ~10-11 days after ovulation

Negative but no period: retest after 48 hours.

Bleeding or severe one-sided abdominal pain with a positive test = possible ectopic pregnancy - emergency now."""),

    (("اسید فولیک بارداری", "فولیک اسید بارداری", "فولیک اسید چقدر", "فولات بارداری", "ویتامین بارداری"),
     ("folic acid pregnancy", "folic acid dose pregnancy"),
     """**اسید فولیک در بارداری:**
• دوز استاندارد: ۴۰۰ میکروگرم در روز
• شروع: از ۱ تا ۳ ماه قبل از بارداری تا پایان سه‌ماهه‌ی اول
• سابقه‌ی نقص لوله‌ی عصبی در خانواده: ۴ تا ۵ میلی‌گرم در روز فقط با نظر پزشک

چرا مهم: از نقص لوله‌ی عصبی (اسپینا بیفیدا) در جنین جلوگیری می‌کند و باید قبل از بسته شدن لوله‌ی عصبی (هفته‌ی ۴) در بدن باشد — یعنی قبل از اینکه بفهمی باردار هستی.

منابع غذایی: سبزیجات برگ‌سبز، حبوبات، نان غنی‌شده.""",

     """**Folic acid in pregnancy:**
• Standard dose: 400 micrograms daily
• Start 1-3 months before conception through the first trimester
• Previous family history of neural tube defects: 4-5 mg/day, doctor's decision only

Why it matters: it prevents neural tube defects and must be in the body before week 4 - before you know you are pregnant.

Food sources: leafy greens, legumes, fortified bread."""),

    (("تب چند درجه", "تب چقدر", "تب کی دکتر", "تب بزرگسال", "کاهش تب"),
     ("fever when to see doctor", "adult fever", "reduce fever"),
     """**تب = دمای ۳۸ درجه یا بالاتر (زیر بغل حدود ۰٫۵ درجه کمتر نشان می‌دهد).**

مدیریت در بزرگسال:
• استامینوفن ۵۰۰ تا ۱۰۰۰ میلی‌گرم هر ۶ ساعت (حداکثر ۳ گرم در روز)
• مایعات فراوان، لباس سبک، اتاق خنک
• تب تا ۳۸٫۵ بدون علامت خطر نیازی به سرکوب فوری ندارد

همین روز پزشک: تب بالای ۳۹٫۵، بیش از ۳ روز، همراه با سفتی گردن، تنگی نفس، درد شدید، کاهش ادرار، گیجی یا بعد از سفر به منطقه‌ی مالاریایی.""",

     """**Fever = 38 C or higher.**

Adult management:
• Paracetamol 500-1000 mg every 6 hours (max 3 g/day)
• Plenty of fluids, light clothing, cool room
• Fever under 38.5 without danger signs doesn't need immediate suppression

Same-day doctor: fever >39.5, lasting >3 days, or with stiff neck, breathlessness, severe pain, low urine, confusion, or after travel to a malaria area."""),

    (("تب کودک", "تب نوزاد", "تب بچه چیکار کنم"),
     ("fever in children", "baby fever", "child fever when doctor"),
     """**تب کودک — قاعده‌ی طلایی بر اساس سن:**
• زیر ۳ ماه با تب ۳۸ یا بالاتر: فوراً پزشک، بدون استامینوفن خانگی
• ۳ تا ۶ ماه: پزشک همان روز اگر تب بالای ۳۹ یا بدحالی دارد
• بالای ۶ ماه: اگر می‌خورد، می‌نوشد و بازی می‌کند، معمولاً نگرانی فوری نیست

دوز استامینوفن کودک: ۱۰ تا ۱۵ میلی‌گرم به ازای هر کیلو وزن، هر ۴ تا ۶ ساعت.
ایبوپروفن: از ۶ ماهگی، ۵ تا ۱۰ میلی‌گرم بر کیلو هر ۸ ساعت، همراه غذا.

همین حالا اورژانس: بی‌حالی شدید، لکه‌های بنفش که با فشار نمی‌روی، سفتی گردن، تشنج، تنفس سخت، استفراغ مکرر، کمی ادرار.""",

     """**Child fever - the golden rule by age:**
• Under 3 months with fever >=38 C: doctor immediately, no home paracetamol
• 3-6 months: same-day doctor if fever >39 or the child looks unwell
• Over 6 months: if drinking, playing and alert, usually not an emergency

Paracetamol dose: 10-15 mg per kg, every 4-6 hours. Ibuprofen: from 6 months, 5-10 mg/kg every 8 hours, with food.

Emergency now: severe limpness, purple spots that don't fade under pressure, stiff neck, seizure, hard breathing, repeated vomiting, very little urine."""),

    (("استامینوفن دوز", "دوز استامینوفن", "استامینوفن چقدر", "استامینوفن چند تا", "استامینوفن چقدر بخورم", "پاراستامول دوز"),
     ("paracetamol dose", "acetaminophen dose", "how much paracetamol"),
     """**استامینوفن — دوز ایمن بزرگسال:**
• هر نوبت: ۵۰۰ تا ۱۰۰۰ میلی‌گرم
• فاصله: حداقل ۴ تا ۶ ساعت
• سقف روزانه: ۳ گرم (در مسن‌ها یا بیماری کبدی ۲ گرم)

نکته‌های مهم:
• بیش‌مصرفیت علامت فوری ندارد ولی به کبد آسیب جدی می‌زند
• در بسیاری از داروهای سرماخوردگی ترکیبی هم استامینوفن هست — جمعش نکن (دوز تکراری)
• با الکل مصرفش را محدود کن

مصرف همزمان ناخواسته بالای ۷٫۵ گرم = مسمومیت کبدی؛ همان روز اورژانس.""",

     """**Paracetamol - safe adult dose:**
• 500-1000 mg per dose, at least 4-6 hours apart, max 3 g/day (2 g in elderly or liver disease)

Notes: overdose has no early warning but seriously damages the liver; many combination cold medicines also contain paracetamol - don't double up; limit with alcohol.

Accidental intake above 7.5 g in a day = liver toxicity - emergency the same day."""),

    (("ایبوپروفن عوارض", "عوارض ایبوپروفن", "ایبوپروفن چقدر", "nsaid عوارض", "ژلوفن ضرر", "ایبوپروفن چند تا"),
     ("ibuprofen side effects", "ibuprofen safe dose", "nsaid risks"),
     """**ایبوپروفن (ژلوفن) — با احتیاط:**
• دوز بزرگسال: ۲۰۰ تا ۴۰۰ میلی‌گرم هر ۶ تا ۸ ساعت، همراه غذا، کوتاه‌مدت (۲ تا ۳ روز)

خطرها:
• معده: درد و زخم — با معده‌ی خالی نگیر
• کلیه: در کم‌آبی و سالمندان خطرناک
• فشار خون را بالا می‌برد و با وارفارین/آسپرین تداخل دارد
• در بیماری کرونا، دنگی و بعد از جراحی، طبق نظر پزشک

در بیماری کلیوی، زخم معده، بارداری سه‌ماهه‌ی سوم = بدون نظر پزشک ممنوع.

درد شکم با استفراغ خونی یا مدفوع سیاه در مصرف NSAID = اورژانس.""",

     """**Ibuprofen - handle with care:**
• Adults: 200-400 mg every 6-8 hours, with food, short courses only (2-3 days)

Risks: stomach pain and ulcers (never on an empty stomach); kidneys (dangerous with dehydration and in the elderly); raises blood pressure; interacts with warfarin/aspirin.

Avoid without a doctor in kidney disease, ulcer history, or third-trimester pregnancy.

Abdominal pain with bloody vomit or black stools while on NSAIDs = emergency."""),

    (("آسپرین روزانه", "آسپرین پیشگیری", "aspirin daily"),
     ("daily aspirin", "aspirin prevention", "baby aspirin"),
     """**آسپرین روزانه برای پیشگیری — نه برای همه:**
• فقط کسانی که قبلاً سکته‌ی قلبی/مغزی یا استنت داشته‌اند، با تجویز پزشک مصرف می‌کنند (پیشگیری ثانویه)
• در افراد سالم، خطر خونریزی معده و مغز معمولاً از سودش بیشتر است

اگر آسپرین روزانه می‌خوری، قبل از هر عمل جراحی یا دندان‌پزشکی به پزشک بگویی.

خودسرانه شروع نکن؛ تصمیرم با پزشک بر اساس ریسک شخصی توست.""",

     """**Daily aspirin for prevention - not for everyone:**
• Only people with a prior heart attack, stroke or stent take it, prescribed by a doctor (secondary prevention)
• In healthy people the bleeding risk (stomach, brain) usually outweighs the benefit

If you take daily aspirin, tell your doctor before any surgery or dental work.

Don't start it on your own - the decision is based on your personal risk."""),

    (("آنتی بیوتیک سرماخوردگی", "آنتی بیوتیک برای سرماخوردگی", "آنتی بیوتیک لازمه", "سرماخوردگی آنتی بیوتیک", "antibiotic for cold", "do i need antibiotics"),
     ("antibiotic for cold", "do i need antibiotics", "antibiotics cold flu"),
     """**سرماخوردگی و آنفولانزا ویروسی‌اند — آنتی‌بیوتیک هیچ اثری رویشان ندارد:**
• آنتی‌بیوتیک باکتری را می‌کشد، نه ویروس را
• مصرف بی‌مورد: مقاومت باکتریایی می‌سازد، فلور روده را خراب می‌کند، حساسیت دارویی می‌آورد
• سرماخوردگی معمولی ۷ تا ۱۰ روز خودش خوب می‌شود؛ استراحت، مایعات، استامینوفن کافی است

چه زمانی شک باکتریایی منطق است: گلودرد با تب بالا و بدون سرفه، درد گوش شدید، ترشح چرکی صورت بیش از ۱۰ روز بدون بهبود، بدتر شدن بعد از بهبود اولیه — باز هم تشخیص با پزشک.

اگر آنتی‌بیوتیک تجویز شد، دوره را کامل کن؛ نصفه رها کردن مقاومت می‌سازد.""",

     """**Colds and flu are viral - antibiotics do nothing:**
• Antibiotics kill bacteria, not viruses
• Unnecessary use builds resistance, damages gut flora, causes allergy
• A common cold resolves in 7-10 days; rest, fluids and paracetamol are enough

When a bacterial cause is plausible: severe sore throat with fever and no cough, severe ear pain, pus-like facial discharge >10 days without improvement, or worsening after initial improvement - still a doctor's call.

If prescribed, finish the course; stopping halfway breeds resistance."""),

    (("فرق آنفولانزا و سرماخوردگی", "فرق آنفولانزا سرماخوردگی", "آنفولانزا یا سرماخوردگی", "آنفولانزا سرماخوردگی فرق"),
     ("flu vs cold", "flu or cold difference"),
     """**سرماخوردگی یا آنفولانزا؟**
• شروع: سرماخوردگی آرام، آنفولانزا ناگهانی (چند ساعت)
• تب: سرماخوردگی کم یا هیچ، آنفولانزا ۳۸ تا ۴۰ و ۳ تا ۵ روز
• درد بدن: خفیف در سرماخوردگی، شدید در آنفولانزا
• ضعف: خفیف در برابر خواب‌آلود و بستری‌کننده
• علائم بینی و عطسه: شایع‌تر در سرماخوردگی

در آنفولانزا، داروی ضدهرب (اسمولتامایویر) فقط در ۴۸ ساعت اول اثر واقعی دارد — افراد پرخطر (بارداری، سالمند، بیماری مزمن) همان روز پزشک.

تنگی نفس، درد قفسه سینه، گیجی یا برگشت تب بعد از بهبود = پزشک فوری.""",

     """**Cold or flu?**
• Onset: cold gradual, flu sudden (hours)
• Fever: cold none/mild, flu 38-40 C for 3-5 days
• Body aches: mild vs severe; weakness: mild vs exhausting
• Sneezing and runny nose: more typical of colds

In flu, antivirals (oseltamivir) only really work within the first 48 hours - high-risk people (pregnant, elderly, chronic disease) should see a doctor the same day.

Breathlessness, chest pain, confusion, or fever returning after improvement = urgent care."""),

    (("آب چقدر بخورم", "چقدر آب بخورم", "چقدر آب", "آب روزانه", "مایعات چقدر"),
     ("how much water", "water intake daily"),
     """**آب روزانه:**
• بزرگسال: حدود ۲ تا ۲٫۵ لیتر کل مایعات (خوراکی‌ها هم حساب می‌شوند)
• گرما، ورزش، تب، شیردهی: ۵۰۰ میلی تا یک لیتر بیشتر
• سنجه‌ی ساده‌تر: ادرار باید روشن زرد باشد؛ تیره یعنی کم‌آبی

موارد خطرناک کم‌آبی: سرگیجه هنگام بلند شدن، خشکی دهان، ادرار خیلی کم.

نکته: نوشیدن دفعی چند لیتر آب فایده اضافه ندارد؛ زیاده‌روی شدید هم سدیم خون را می‌آورد پایین.

مردم با نارسایی قلبی یا کلیه ممکن است محدودیت مایعات داشته باشند — با پزشکشان.""",

     """**Daily water:**
• Adults: about 2-2.5 L of total fluids (food counts)
• Add 0.5-1 L in heat, exercise, fever, breastfeeding
• Simplest gauge: urine should be pale yellow; dark = dehydration

Warning signs of dehydration: dizziness on standing, dry mouth, very little urine.

Drinking several liters at once has no extra benefit; extreme over-drinking lowers blood sodium.

People with heart or kidney failure may have fluid limits - per their doctor."""),

    (("خواب چقدر", "ساعت خواب", "بی‌خوابی چیکار"),
     ("how much sleep", "sleep hours"),
     """**ساعت خواب مورد نیاز:**
• بزرگسال: ۷ تا ۹ ساعت
• نوجوان: ۸ تا ۱۰
• بالای ۶۵ سال: ۷ تا ۸

کیفیت مهم‌تر از ساعت است: خواب پیوسته، اتاق تاریک و خنک، بدون صفحه‌ی موبایل یک ساعت قبل.

قواعد خواب خوب: ساعت خواب و بیداری ثابت حتی تعطیلات، کافئین بعد از ساعت ۲ بعدازظهر نه، چرت روزانه زیر ۳۰ دقیقه.

خروپف بلند با قطع نفس روزانه + سردرد صبحگاهی = احتمال آپنه‌ی خواب؛ آزمون STOP-BANG در ماژول خواب همین برنامه را بزن.""",

     """**How much sleep:**
• Adults 7-9 hours • teenagers 8-10 • over 65: 7-8

Quality beats quantity: continuous sleep, dark cool room, no screens an hour before.

Sleep hygiene: fixed sleep/wake times even on weekends, no caffeine after 2 pm, naps under 30 minutes.

Loud snoring with daytime pauses + morning headache = possible sleep apnea; run the STOP-BANG test in the Sleep module here."""),

    (("ورزش چقدر", "ورزش در هفته", "ورزش روزانه چقدر", "فعالیت بدنی چقدر", "فعالیت بدنی"),
     ("how much exercise", "exercise per week"),
     """**توصیه‌ی سازمان جهانی بهداشت برای بزرگسالان:**
• هفته‌ای ۱۵۰ تا ۳۰۰ دقیقه ورزش متوسط (پیاده‌روی تند، دوچرخه)
• یا ۷۵ تا ۱۵۰ دقیقه ورزش شدید (دویدن)
• به‌علاوه ۲ جلسه تمرین قدرتی در هفته
• کم‌تحرکی مطلق مضر است؛ هر حرکتی بهتر از هیچ است

شروع از صفر: روزی ۱۰ دقیقه پیاده‌روی، هر هفته ۵ دقیقه اضافه کن.

هدف واقع‌بینانه‌ی قدم: حدود ۷ تا ۸ هزار قدم در روز (۱۰ هزار قدم عدد جادویی نیست).

درد قفسه سینه یا سرگیجه حین ورزش = توقف و بررسی پزشکی.""",

     """**WHO recommendation for adults:**
• 150-300 minutes of moderate activity per week (brisk walking, cycling), or 75-150 min vigorous
• Plus 2 strength sessions per week
• Any movement beats none

Starting from zero: 10 minutes of walking a day, add 5 minutes weekly.

A realistic step goal: about 7-8 thousand steps a day (10k is not magic).

Chest pain or dizziness during exercise = stop and get checked."""),

    (("bmi چنده", "شاخص توده بدنی", "bmi چقدر"),
     ("normal bmi", "bmi chart", "what is bmi"),
     """**BMI = وزن (کیلوگرم) تقسیم بر مربع قد (متر):**
• زیر ۱۸٫۵ = کمبود وزن
• ۱۸٫۵ تا ۲۴٫۹ = طبیعی
• ۲۵ تا ۲۹٫۹ = اضافه‌وزن
• ۳۰ به بالا = چاقی

نکته‌ها:
• در آسیایی‌ها خطر متابولیک از BMI حدود ۲۳ شروع می‌شود و چاقی از ۲۷٫۵
• BMI عضله و چربی را تشخیص نمی‌دهد؛ ورزشکار عضلانی عدد بالای «سالم» می‌گیرد
• همراهش دور کمر را ببین: مرد زیر ۹۴ و زن زیر ۸۰ سانتی‌متر

ماژول علائم حیاتی همین برنامه BMI و دسته‌بندی را حساب می‌کند.""",

     """**BMI = weight (kg) / height (m) squared:**
• <18.5 underweight • 18.5-24.9 normal • 25-29.9 overweight • >=30 obese

Notes: in Asians metabolic risk starts around BMI 23 and obesity at 27.5; BMI can't tell muscle from fat; check waist alongside (men <94 cm, women <80 cm).

The Vitals module of this app computes BMI and the category."""),

    (("دور کمر چقدر", "دور کمر نرمال", "شکم چربی"),
     ("waist circumference", "normal waist size"),
     """**دور کمر — متر ساده‌تر از هر آزمایشی:**
• مرد: نرمال زیر ۹۴؛ ریسک بالا ۹۴ تا ۱۰۲؛ خیلی بالا بالای ۱۰۲
• زن: نرمال زیر ۸۰؛ ریسک بالا ۸۰ تا ۸۸؛ خیلی بالا بالای ۸۸

اندازه‌گیری: متر را افقی روی ناف بگذار، در پایان بازدم، بدون فشار دادن پوست.

چرا مهم: چربی شکمی (احشایی) مستقیماً با دیابت، فشار و چربی خون مرتبط است؛ حتی با BMI نرمال، کمر بزرگ خطر است.

هفته‌ای یک بار صبح ناشتا اندازه بگیر و در ماژول علائم حیاتی ثبت کن تا روندش دیده شود.""",

     """**Waist circumference - a tape measure beats many labs:**
• Men: normal <94 cm; high risk 94-102; very high >102
• Women: normal <80 cm; high risk 80-88; very high >88

Measure: tape horizontal at the navel, at the end of an exhale, without squeezing.

Why it matters: belly (visceral) fat drives diabetes, blood pressure and lipids - even with a normal BMI.

Measure weekly, fasting, in the morning and log it in the Vitals module to see the trend."""),

    (("نمک چقدر", "نمک روزانه", "سدیم محدود"),
     ("how much salt", "salt intake daily"),
     """**نمک روزانه: زیر ۵ گرم (یک قاشق چای‌خوری پر) — توصیه‌ی سازمان جهانی بهداشت**

نکته‌ها:
• بیشتر نمک ما از نان، پنیر، سوسیس، رب، غذای آماده و فست‌فود می‌آید، نه نمدان
• چاشنی‌های پنهان: سس سویا، چیپس، آجیل شور، ترشی
• کاهش نمک در فشارخونی‌ها تا ۵ تا ۶ میل فشار را پایین می‌آورد

جایگزین‌های طعم: لیمو، سرکه، سیر، آویشن، زردچوبه؛ حواس به نمک‌های رژیمی پتاسیم‌دار باشد — در نارسایی کلیه ممنوع‌اند.""",

     """**Daily salt: under 5 g (one heaped teaspoon) - WHO advice.**

Most of our salt hides in bread, cheese, sausages, tomato paste and fast food, not the salt shaker. Hidden sources: soy sauce, chips, salted nuts, pickles.

Cutting salt lowers blood pressure by 5-6 mmHg in hypertensives.

Flavor swaps: lemon, vinegar, garlic, thyme, turmeric. Potassium-based salt substitutes are dangerous in kidney failure."""),

    (("کافئین چقدر", "قهوه چقدر", "قهوه در روز", "چند فنجان قهوه", "چای چقدر"),
     ("how much caffeine", "coffee per day"),
     """**کافئین روزانه بزرگسال: تا حدود ۴۰۰ میلی‌گرم (۳ تا ۴ فنجان قهوه)**
• یک فنجان قهوه دم‌کرده: حدود ۸۰ تا ۱۰۰
• چای: حدود ۳۰ تا ۵۰
• نوشابه‌ی کولا: حدود ۳۰ تا ۴۰
• انرژی‌زا: تا ۱۶۰ در قوطی

بارداری: سقف حدود ۲۰۰ در روز. اضطراب، بی‌خوابی، تپش و رفلاکس با کافئین بدتر می‌شوند.

نیمه‌عمر کافئین ۵ تا ۶ ساعت است؛ قهوه‌ی ساعت ۶ عصر، نیمه‌اش ساعت نیمه‌شب در بدنت است.

تپش قلب بعد از قهوه‌ی زیاد معمولاً بی‌خطر است ولی اگر طولانی شد یا با غش آمد، بررسی کن.""",

     """**Daily caffeine for adults: up to ~400 mg (3-4 cups of coffee)**
• Brewed coffee ~80-100 mg • tea ~30-50 • cola ~30-40 • energy drinks up to 160 per can

Pregnancy cap: about 200 mg/day. Caffeine worsens anxiety, insomnia, palpitations and reflux.

Its half-life is 5-6 hours - half of your 6 pm coffee is still in you at midnight.

Palpitations after too much coffee are usually harmless, but if prolonged or with fainting, get checked."""),

    (("ترک سیگار", "سیگار ترک", "سیگار رو ترک", "سیگار را ترک", "فواید ترک سیگار"),
     ("quit smoking benefits", "stop smoking timeline"),
     """**ترک سیگار — جدول زمانی بازگشت سلامت:**
• ۲۰ دقیقه: ضربان و فشار پایین می‌آید
• ۱۲ ساعت: کربن‌مونوکسید خون نرمال می‌شود
• ۲ هفته تا ۳ ماه: گردش خون و عملکرد ریه بهتر
• ۱ سال: خطر سکته‌ی قلبی نصف سیگاری‌ها
• ۵ تا ۱۵ سال: خطر سکته به سطح غیرسیگاری
• ۱۰ سال: خطر سرطان ریه نصف

مؤثرترین روش: مشاوره + دارودرمانی (نیکوتین جایگزین، وارنی‌کلاین یا بروپروپیون) خیلی بهتر از اراده‌ی تنهاست؛ خط ترک سیگار ایران: ۱۹۰۴.

لجاظه‌ی اضطراب چند روز اول طبیعی و موقتی است؛ اوج وسوسه‌ها ۳ تا ۵ دقیقه طول می‌کشد.""",

     """**Quitting - the recovery timeline:**
• 20 min: heart rate and BP drop • 12 h: carbon monoxide normalizes
• 2 weeks-3 months: circulation and lung function improve
• 1 year: heart attack risk halves • 5-15 years: stroke risk near non-smoker
• 10 years: lung cancer risk halves

Best results come from counseling plus medication (nicotine replacement, varenicline, bupropion) - far better than willpower alone; Iran's quit line: 1904.

The first-days anxiety is normal and temporary; cravings peak for only 3-5 minutes."""),

    (("سردرد خطرناک", "سردرد چه زمانی خطر", "سردرد علائم خطر"),
     ("headache red flags", "dangerous headache", "when headache dangerous"),
     """**سردرد — علائم خطر که باید همان روز دیده شوند:**
• بدترین سردرد زندگی در کمتر از یک دقیقه (رعدآسا) = اورژانس
• سردرد + تب + سفتی گردن (چانه به سینه نمی‌رسد)
• سردرد + ضعف یک طرفه، اشکال تکلم، doppio بینایی، گیجی
• سردرد بعد از ضربه به سر
• شروع جدید سردرد بعد از ۵۰ سالگی یا بدترشونده‌ی هفته‌ها
• سردرد با استفراغ صبحگاهی بدون تهوع قبلی

میگرن و سردرد تنشی شایع و خطرناک نیستند؛ این فهرست استثناهاست.

هر مورد از بالا = پزشک فوری، نه فردا.""",

     """**Headache danger signs - same-day care:**
• Worst headache of your life peaking within a minute (thunderclap) = emergency
• Headache + fever + stiff neck
• Headache + one-sided weakness, slurred speech, double vision, confusion
• Headache after a head injury
• New headache after age 50, or steadily worsening over weeks
• Morning vomiting without nausea beforehand

Migraine and tension headaches are common and not dangerous - this list is the exception.

Any item above = urgent care now, not tomorrow."""),

    (("سرگیجه دلایل", "سرگیجه چرا میشه", "سرگیجه ایستادن"),
     ("dizziness causes", "why am i dizzy", "lightheaded causes"),
     """**سرگیجه — شایع‌ترین علت‌ها:**
• کم‌آبی یا گرسنگی، ایستادن ناگهانی (افت فشار وضعیتی)
• داروها: فشار، مسکن قوی، خواب‌آور، آنتی‌هیستامین
• کم‌خونی
• سرگیجه‌ی وضعیتی خوش‌خیم (BPPV): چرخش چند ثانیه‌ای با حرکت سر، به‌خصوص هنگام بلند شدن از تخت
• اضطراب و هیپرونتیلاسیون
• قند پایین در دیابتی‌ها

کار فوری: بنشین، آب بخور، قند بزن اگر دیابت داری.

اتاق می‌چرخد با استفراغ مداوم، اختلال تکلم یا ضعف اندام = اورژانس. سرگیجه‌ی تکرارشونده = آزمایش CBC + فشار خوابیده و ایستاده با پزشک.""",

     """**Dizziness - the common causes:**
• Dehydration, hunger, standing up too fast (orthostatic)
• Medications: BP drugs, strong painkillers, sedatives, antihistamines
• Anemia • benign positional vertigo (BPPV): seconds of spinning with head movement, especially rolling out of bed
• Anxiety and over-breathing • low sugar in diabetics

Do now: sit down, drink water, check sugar if diabetic.

Room spinning with persistent vomiting, slurred speech or limb weakness = emergency. Recurring dizziness = CBC plus lying/standing BP with a doctor."""),

    (("تورم پا", "پاها متورم", "پاهام متورم", "پاهای متورم", "پاهاش متورم", "پا متورم", "متورم پا", "تورم ساق", "تورم یک طرف پا"),
     ("leg swelling causes", "swollen legs", "one leg swollen"),
     """**تورم پا — تفکیک مهم:**
• دو طرف و آخر روز: ایستادن طولانی، نمک زیاد، اضافه‌وزن، داروها (آملودیپین، ضدالتهاب‌ها) — خطرناک نیست
• یک طرف، به‌خصوص با درد و گرمی و قرمزی: احتمال لخته در ورید عمقی (DVT) → همان روز اورژانس، ماساژ ممنوع
• دو طرف با تنگی شبانه‌ی نفس یا افزایش وزن سریع: احتمال نارسایی قلبی → پزشک
• حول مچ ساق با فشار جای انگشت می‌ماند؟ درست است که به آن توجه کنی

سفر طولانی نشسته + تورم یک پا = لخته تا وقتی خلافش ثابت شود.

DVT درمان‌نشده می‌تواند لخته به ریه بفرستد (تنگی نفس ناگهانی = ۱۱۵).""",

     """**Leg swelling - the key distinction:**
• Both legs, end of day: prolonged standing, salt, excess weight, drugs (amlodipine, NSAIDs) - usually not dangerous
• One leg, especially with pain, warmth and redness: possible deep vein clot (DVT) → same-day emergency, no massage
• Both legs with night-time breathlessness or rapid weight gain: possible heart failure → doctor
• Pitting (fingerprint stays)? take it seriously

Long seated travel + one swollen leg = a clot until proven otherwise.

Untreated DVT can send a clot to the lungs (sudden breathlessness = call emergency)."""),

    (("خونریزی بینی", "داخل بینی خون", "بینیم خون میاد"),
     ("nosebleed what to do", "nose bleeding", "how to stop nosebleed"),
     """**خونریزی بینی — کار درست:**
۱. سر را جلو خم کن (نه عقب؛ خون را قورت نده)
۲. بالای سوراخ‌های بینی (استخوان نرم) را ۱۰ دقیقه کامل بفشار
۳. تنفس از دهان، آرام
۴. کمپرس سرد روی پل بینی کمک می‌کند
۵. تا ۲۴ ساعت دستکش نکن، فین نزن، شیپور نزن

تکرارش در هوای خشک طبیعی است؛ ژل رطوبت‌دهنده یا اسپری آب نمک راه‌حل روزمره است.

خونریزی بیش از ۲۰ دقیقه با فشار، همراه با داروی رقیق‌کننده (وارفارین/آسپرین)، یا کبودی‌های خودبه‌خود دیگر جاها = اورژانس.""",

     """**Nosebleed - the right steps:**
1. Lean the head forward (never back; don't swallow blood)
2. Pinch the soft part of the nose for a full 10 minutes
3. Breathe through the mouth, stay calm
4. A cold pack over the bridge helps
5. For 24 hours: no nose blowing, picking or straining

Recurrent bleeds in dry air are common; a moisturizing gel or saline spray is the daily fix.

Bleeding beyond 20 minutes of pressure, while on blood thinners, or with spontaneous bruises elsewhere = emergency."""),

    (("اسهال چیکار", "اسهال درمان", "اسهال خون"),
     ("diarrhea what to do", "diarrhea treatment"),
     """**اسهال — قانون طلایی: جایگزینی مایعات مهم‌تر از هر قرصی است**
• ORS (پودر سایرورت به ازای هر دفعه): طبق دستور با آب
• در دسترس نبود: ۱ لیتر آب + نصف قاشق چای‌خوری نمک + ۶ قاشق چای‌خوری شکر
• غذا: برز و مرغ، سوپ، موز، ماست؛ چای و کافئین کمتر
• در بزرگسال غیرخطرناک، لوپرامید فقط برای موارد غیرعفونی و کوتاه، با احتیاط

همین روز پزشک: خون در مدفوع، تب بالای ۳۸٫۵، بیش از ۲ روز، اسهال آبکی شدید با کم‌ادراری، مسافرت اخیر، مسن یا بیمار زمینه‌ای.

اسهال بعد از آنتی‌بیوتیک با تب و درد شکم = احتمال کولیت؛ پزشک.""",

     """**Diarrhea - golden rule: fluid replacement beats any pill**
• ORS packets after every loose stool
• No ORS at hand: 1 L water + half a teaspoon of salt + 6 teaspoons of sugar
• Food: rice and chicken, soup, banana, yogurt; less tea/caffeine
• Loperamide only for short, non-infective cases in adults, with care

Same-day doctor: blood in stool, fever >38.5, lasting >2 days, severe watery diarrhea with low urine, recent travel, elderly or chronically ill.

Diarrhea after antibiotics with fever and abdominal pain = possible colitis; see a doctor."""),

    (("یبوست چیکار", "یبوست درمان", "یبوست مزمن"),
     ("constipation what to do", "constipation remedy"),
     """**یبوست — پله‌پله بالا برو:**
۱. آب: ۸ لیوان در روز؛ صبح ناشتا یک لیوان ولرم
۲. فیبر: آلو، انجیر، سبزی، نان سبوس‌دار، حبوبات — ناگهانی زیاد نکن (نفخ)
۳. حرکت: ۳۰ دقیقه پیاده‌روی روزانه؛ حرکت روده با تحرک شروع می‌شود
۴. عادت: بعد از صبحانه ۱۰ دقیقه دستشویی؛ صبر کردن را تمرین کن
۵. شربت لاکتولوز (بدون نسخه) برای دوره‌ی کوتاه

مخرب‌ها: مسکن‌های opioid، آهن، بعضی آنتی‌افسردگی‌ها، کم‌تحرکی.

پرش به پزشک: یبوست جدید بالای ۵۰ سال، خون در مدفوع، کاهش وزن بی‌دلیل، یا مسدود شدن کامل گاز و مدفوع + استفراغ (انسداد = اورژانس).""",

     """**Constipation - climb the ladder:**
1. Water: 8 glasses a day; one lukewarm glass on waking
2. Fiber: prunes, figs, vegetables, wholegrain bread, legumes - increase slowly
3. Movement: 30 min walking daily; the bowel starts with motion
4. Habit: 10 minutes on the toilet after breakfast
5. Lactulose syrup (OTC) for short courses

Culprits: opioid painkillers, iron, some antidepressants, inactivity.

See a doctor promptly: new constipation after 50, blood in stool, unexplained weight loss, or complete blockage of gas and stool with vomiting (obstruction = emergency)."""),

    (("سوزش سر دل", "ریفلاکس درمان", "ترش کردن"),
     ("heartburn remedy", "acid reflux what to do", "gerd"),
     """**سوزش سر دل و ریفلاکس:**
• وعده‌های کوچک؛ ۳ ساعت قبل خواب هیچ‌چیز نخور
• سر تخت را ۱۰ تا ۱۵ سانتی‌متر بالا بیاور (بالش زیر سر کافی نیست)
• محرک‌ها را کم کن: چربی، شکلات، نعناع، قهوه، ادویه تند، الکل، سیگار
• اضافه‌وزن را کم کن؛ حتی ۵ کیلو اثر دارد
• آنتی‌اسید (بدون نسخه) برای حملات گاه‌بی‌گاه

۳ روز پشت‌سرهم یا هفته‌ای ۲ بار بیش از ۲ هفته = پزشک؛ گاهی اندوسکوپی لازم است.

سوزش با درد قفسه سینه‌ی فشارنده‌ی همراه با تنگی نفس و عرق = مشکل قلبی تا خلافش ثابت شود؛ ۱۱۵.""",

     """**Heartburn and reflux:**
• Smaller meals; nothing 3 hours before bed
• Raise the head of the bed 10-15 cm (extra pillows alone don't work)
• Cut triggers: fat, chocolate, mint, coffee, spicy food, alcohol, smoking
• Lose weight - even 5 kg helps • OTC antacids for occasional attacks

More than 3 days in a row, or twice a week for over 2 weeks = doctor; sometimes endoscopy is needed.

Burning chest pain that feels like pressure with breathlessness and sweating = cardiac until proven otherwise; call emergency."""),

    (("عفونت ادرار", "سوزش ادرار", "uti چیکار"),
     ("uti what to do", "urinary tract infection", "burning urination"),
     """**عفونت ادراری — علائم:** سوزش هنگام ادرار، تکرر فوری، بوی تند، گاهی خون مایل؛ زنان شایع‌تر.

کارها:
• آب زیاد (۲ تا ۳ لیتر) و ادرار نکردن با تحمل
• ادرار بعد از رابطه برای زنان مستعد
• آزمایش ادرار قبل از شروع آنتی‌بیوتیک بهتر است
• آنتی‌بیوتیک فقط با نسخه؛ دوره کوتاه در عفونت ساده معمولاً کافی است

خطرناک — همان روز پزشک: درد پهلو یا کمر + تب و لرز (عفونت کلیه)، بارداری، مرد بودن (بررسی لازم دارد)، سنگ اخیر.

تب بالا با گیجی و افت فشار در بستر عفونت ادراری = اورژانس.""",

     """**Urinary tract infection - symptoms:** burning on urination, urgency, foul smell, sometimes blood-tinged; more common in women.

Do: 2-3 L water daily, don't hold urine, for prone women urinate after intercourse; a urine test before antibiotics is better; antibiotics by prescription only - a short course usually suffices for simple cases.

Same-day doctor: flank/back pain with fever and chills (kidney infection), pregnancy, men (needs workup), recent stones.

High fever with confusion and low blood pressure = emergency."""),

    (("سنگ کلیه", "درد کلیه", "درد پهلو سنگ"),
     ("kidney stone what to do", "kidney stone pain", "renal colic"),
     """**سنگ کلیه — درد قولنجی:** موج‌دار، از پهلو به کشاله‌ی ران و بیضه/لابیا می‌زند؛ همراه با تهوع و بی‌قراری؛ بیمار آرام نمی‌گیرد (برخلاف پریتونیت).

کارها:
• درد را با مسکن (ایبوپروفن یا کتورولاک با پزشک) کنترل کن — سنگ زیر ۵ میلی اغلب با آب زیاد (۲٫۵ تا ۳ لیتر) خودش خارج می‌شود
• ادرار را از صافی بگذر و سنگ را نگه دار برای آزمایش
• پرش یا راه رفتن، خروج را سریع‌تر می‌کند

اورژانس: تب همراه درد پهلو، استفراغ بی‌وقفه، ادرار نکردن، یک کلیه‌ی تنها، درد بیش از ۴۸ ساعت.

بعد از سنگ اولین، نصف بیماران دوباره سنگ می‌سازند؛ آب کافی + بررسی متابولیک با پزشک.""",

     """**Kidney stone - colicky pain:** comes in waves from the flank to the groin; with nausea and restlessness - the patient cannot lie still (unlike peritonitis).

Do: control pain (ibuprofen or ketorolac per doctor); stones under 5 mm mostly pass with 2.5-3 L water daily; strain the urine and keep the stone for analysis; jumping or walking speeds passage.

Emergency: fever with flank pain, relentless vomiting, no urine output, a solitary kidney, pain beyond 48 hours.

After a first stone, half of patients form another: enough water plus a metabolic workup with a doctor."""),

    (("درد کمر", "کمردرد چیکار", "درد کمر علائم خطر"),
     ("back pain what to do", "low back pain", "back pain red flags"),
     """**کمردرد — ۹۰٪ بدون علت جدی و خودمحدودشونده:**
• بهترین دارو حرکت است؛ چند روز رخت خواب مطلقاً توصیه نمی‌شود
• ادامه‌ی فعالیت روزانه در حد قابل‌تحمل + پیاده‌روی
• گرما یا سرما هر کدام که راحت‌تر کرد
• مسکن ساده + کشش آرام

علائم خطر — بررسی فوری:
• ضعف پاها یا مشکلات مثانه/روده (بی‌اختیاری)
• بی‌حسی ناحیه‌ی سمی (زین اسب)
• تب یا کاهش وزن بی‌دلیل یا سابقه‌ی سرطان
• بعد از ضربه شدید؛ مصرف کورتون طولانی
• شب‌ها بی‌قرارکننده و با استراحت خوب نمی‌شود

بی‌اختیاری ادرار/مدفوع با کمردرد = اورژانس مغز و اعصاب.""",

     """**Low back pain - 90% is non-specific and self-limiting:**
• The best medicine is movement; days of strict bed rest are not advised
• Stay active within tolerance plus walking
• Heat or cold, whichever eases it • simple painkillers plus gentle stretching

Red flags - prompt evaluation: leg weakness, bladder/bowel problems, saddle numbness, fever or unexplained weight loss, cancer history, major trauma, long-term steroid use, relentless night pain.

Urinary/fecal incontinence with back pain = neurological emergency."""),

    (("کزاز واکسن", "زخم کزاز", "تزریک کزاز"),
     ("tetanus booster", "tetanus shot after wound"),
     """**کزاز — بعد از زخم:**
• واکسن کزاز هر ۱۰ سال یک بار (یادآور)
• زخم تمیز و سطحی: اگر ۱۰ سال از آخرین دوز گذشته، یادآور بزن
• زخم کثیف/عمقی/خاک‌گرفته/گاز انسانی یا حیوانی: اگر ۵ سال گذشته، یادآور بزن

کزاز از خاک و گرد و غبار می‌آید؛ زخم‌های سوراخ‌کننده‌ی عمیق خطرناک‌ترین‌اند.

زخم را ۱۵ دقیقه با آب و صابون بشور؛ نکند داخلش را با الکل بسوزان؛ زخم‌های گازگرفته به همان اندازه که واکسن، پایش عفونت می‌خواهند.

تب، قرمزی گسترده یا خارج شدن چرک بعد از چند روز = عفونت زخم؛ پزشک.""",

     """**Tetanus - after a wound:**
• Booster every 10 years
• Clean minor wound: booster if >10 years since the last dose
• Dirty/deep/soil-contaminated/human or animal bite: booster if >5 years

Tetanus comes from soil; deep puncture wounds are the most dangerous.

Wash the wound 15 minutes with soap and water; don't pour alcohol into it; bite wounds need infection monitoring as much as the vaccine.

Fever, spreading redness or pus after a few days = wound infection; see a doctor."""),

    (("گزش سگ", "گزش حیوان", "هاری چه کنم", "گاز سگ", "سگ گاز", "هاری بعد از گزش"),
     ("dog bite what to do", "animal bite rabies", "rabies exposure"),
     """**گزش سگ/گربه — هاری جدی است، ایران اندیمی است:**
۱. فوراً زخم را ۱۵ دقیقه با آب و صابون فراوان بشور (ساده‌ترین و مؤثرترین کار)
۲. الکل یا بتادین روی زخم
۳**. همان روز** سری واکسن هاری و تزریق ایمونوگلوبولین طبق پروتکل — در ایران مراکز بهداشتی رایگان است
۴. اگر حیوان اهلی و واکسینه است، ۱۰ روز زیر نظر بماند

گاز عمقی سر و صورت و دست = بیشترین ریسک.

هاری وقتی علائم بدهد درمان ندارد؛ ولی تا پیش از علائم، واکسیناسیون کامل محافظت می‌کند — پس هیچ‌وقت دیر نیست، فقط همین امروز.

چاقوکشی زخم، بخیه در گازگرفتگی، و آنتی‌بیوتیک پیشگیرانه = تصمیم پزشک.""",

     """**Dog/cat bite - rabies is real, Iran is endemic:**
1. Wash the wound 15 minutes with plenty of soap and water (simplest, most effective step)
2. Antiseptic on the wound
3. Rabies vaccine series and immunoglobulin per protocol the same day - free at Iranian health centers
4. If the animal is owned and vaccinated, observe it 10 days

Deep bites to the head, face and hands carry the highest risk.

Rabies is untreatable once symptomatic, but post-exposure vaccination fully protects before symptoms - so it is never too late, just do it today.

Wound exploration, suturing a bite, and preventive antibiotics are a clinician's decisions."""),

    (("عسل نوزاد", "عسل به نوزاد", "عسل به بچه", "عسل شیرخوار", "عسل کودک زیر یک سال", "honey for baby"),
     ("honey for baby", "honey infant botulism"),
     """**عسل برای نوزاد زیر ۱ سال مطلقاً ممنوع است.**

دلیل: هاگ بوتولیسم در عسل می‌تواند در روده‌ی نابالغ نوزاد سم بسازد.

علائم مسمومیت نوزادی: یبوست، ضعف مکیدن، افتاب پلک، بی‌صدایی گریه، شلی صورت — در صورت مشاهده فوراً اورژانس.

برای شیرینی دهان نوزاد هیچ دلیلی نیست؛ شیر مادر یا فرمول کافی است.

قند و شیرین‌کننده‌های خانگی دیگر (مالتوز، شیره) هم قبل از یک سال لازم نیستند.""",

     """**Honey is absolutely forbidden under 12 months of age.**

Reason: botulism spores in honey can make toxin in a newborn's immature gut.

Symptoms of infant botulism: constipation, weak sucking, droopy eyelids, weak cry, floppy face - emergency immediately.

No newborn needs added sweetness; breast milk or formula is enough. Other home sweeteners are also unnecessary before age one."""),

    (("کاهش وزن چقدر", "چقدر وزن کم", "وزن کم کنم", "وزن کم کن", "لاغری سریع", "رژیم چقدر وزن", "سرعت کاهش وزن"),
     ("how fast lose weight", "safe weight loss rate"),
     """**سرعت سالم کاهش وزن: نیم تا یک کیلو در هفته**

• سریع‌تر از این = آب و عضله می‌رود، نه چربی؛ و برگشت وزن تقریباً قطعی است
• کمبود ۵۰۰ کالری در روز = حدود نیم کیلو در هفته
• پروتئین کافی (حدود ۱٫۲ تا ۱٫۶ گرم بر کیلو وزن) عضله را حفظ می‌کند
• ورزش قدرتی ۲ بار در هفته همراه رژیم، ترکیب بدن را بهتر می‌کند
• خواب کم و استرس، لاغری را سخت‌تر می‌کند (هورمون‌های اشتها)

خطر رژیم‌های خیلی کم‌کالری بدون پزشک: سنگ صفرا، ریزش مو، اختلال ریتم قلب، اختلال خوردن.

کاهش وزن با دارو (اورلیستات، GLP-1ها) فقط تحت نظارت پزشک و همراه تغییر رفتار معنا دارد.""",

     """**Safe weight-loss rate: 0.5-1 kg per week.**

Faster than that loses water and muscle, not fat, and rebound is almost certain. A 500 kcal daily deficit = about half a kilo a week. Adequate protein (~1.2-1.6 g/kg) preserves muscle; strength training twice a week improves body composition; poor sleep and stress make fat loss harder.

Risks of unsupervised very-low-calorie diets: gallstones, hair loss, heart-rhythm problems, eating disorders.

Weight-loss medication (orlistat, GLP-1 drugs) only makes sense under a doctor and with behavior change."""),

    (("کولونوسکوپی چند", "کولونوسکوپی چه سنی", "سرطان روده چه سنی", "سرطان روده غربالگری"),
     ("colonoscopy age", "when to get colonoscopy", "colon cancer screening age"),
     """**کولونوسکوپی — سن شروع:**
• ریسک متوسط: از ۴۵ سالگی (برنامه‌ی جدید) تا ۵۰؛ تکرار هر ۱۰ سال اگر نرمال باشد
• یک بستگان درجه‌یک (پدر، مادر، خواهر، برادر) با سرطان کولون: از ۴۰ سالگی یا ۱۰ سال قبل از سن تشخیص او، هر کدام زودتر؛ تکرار هر ۵ سال
• دو بستگان درجه‌یک یا یک نسب زیر ۶۰ سال: احتمالاً زودتر و مکرر‌تر

جایگزین‌های کمتر تهاجمی: آزمایش خون مخفی مدفوع سالانه یا کولونوسکوپی مجازی — با پزشک.

علائم زنگ‌خطر در هر سنی: خون در مدفوع، تغییر عادت روده بیش از چند هفته، کاهش وزن بی‌دلیل، کم‌خونی آهنی.

ماژول ریسک خانوادگی همین برنامه سابقه‌ی خانواده‌ی تو را به برنامه‌ی شخصی تبدیل می‌کند.""",

     """**Colonoscopy - when to start:**
• Average risk: at 45 (new guidance) to 50; repeat every 10 years if normal
• One first-degree relative with colon cancer: at 40 or 10 years before their age at diagnosis, whichever first; every 5 years
• Two first-degree relatives, or one diagnosed under 60: earlier and more often

Less invasive alternatives: yearly stool occult blood or virtual colonoscopy - with a doctor.

Alarm symptoms at any age: blood in stool, change of bowel habit over weeks, unexplained weight loss, iron-deficiency anemia.

The Family risk module of this app turns your family history into a personal plan."""),
]


def answer_from_qa(message: str) -> str | None:
    """Match a question against the QA knowledge base."""
    from common_2077 import normalize
    fa = _fa()
    low = message.lower().strip()
    n = normalize(message)
    for fa_keys, en_keys, ans_fa, ans_en in _QA:
        keys = fa_keys if fa else (en_keys + fa_keys)
        for k in keys:
            if k in low:
                return ans_fa if fa else ans_en
            kn = normalize(k)
            if kn and kn in n:
                return ans_fa if fa else ans_en
    return None
