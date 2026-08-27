"""
Full laboratory catalog: ~130 tests with bilingual names, units, adult
reference ranges, critical limits and short "what high/low means" notes.
Ranges are general adult values; the range printed on your own lab report
always wins.
"""

LAB_CATEGORIES = {
    "cbc": ("Complete blood count", "هموگرام خون"),
    "metabolic": ("Sugar & metabolic", "قند و متابولیک"),
    "electrolytes": ("Electrolytes & minerals", "الکترولیت‌ها و املاح"),
    "kidney": ("Kidney", "کلیه"),
    "liver": ("Liver", "کبد"),
    "lipids": ("Lipids", "چربی خون"),
    "thyroid": ("Thyroid", "تیروئید"),
    "hormones": ("Hormones", "هورمون‌ها"),
    "vitamins": ("Vitamins & iron studies", "ویتامین‌ها و آهن"),
    "inflammation": ("Inflammation", "التهاب"),
    "cardiac": ("Heart markers", "نشانگرهای قلبی"),
    "coagulation": ("Coagulation", "انعقاد خون"),
    "urine": ("Urine", "ادرار"),
    "serology": ("Infection serology", "سرولوژی عفونت"),
    "tumor": ("Tumor markers", "نشانگرهای تومور"),
    "misc": ("Other tests", "سایر"),
}

_T = [
    ("wbc", "White blood cells (WBC)", "گویچه‌های سفید", "×10³/µL", 4.5, 11.0, 2.0, 30.0,
     "Often infection, inflammation or stress; very high values can mean leukemia.", "Can point to viral illness, marrow suppression or drug effect.",
     ["wbc", "leukocyte", "لکوسیت", "گویچه سفید"]),
    ("rbc", "Red blood cells (RBC)", "گویچه‌های قرمز", "M/µL", 4.5, 5.9, 2.5, 7.5,
     "Polycythemia; dehydration, smoking, high altitude.", "Anemia or blood loss.",
     ["rbc", "اریتروسیت"]),
    ("hb", "Hemoglobin (Hb)", "هموگلوبین", "g/dL", 12.0, 17.0, 7.0, 20.0,
     "Polycythemia, dehydration, smoking.", "Anemia — bleeding, iron/B12/folate lack, chronic disease.",
     ["hb", "hgb", "هموگلوبین"]),
    ("hct", "Hematocrit (Hct)", "هماتوکریت", "%", 36.0, 52.0, 20.0, 60.0,
     "Dehydration or polycythemia.", "Anemia or over-hydration.",
     ["hct", "هماتوکریت"]),
    ("mcv", "Mean corpuscular volume (MCV)", "حجم متوسط گویچه (MCV)", "fL", 80.0, 96.0, 60.0, 110.0,
     "B12/folate deficiency, alcohol, hypothyroidism.", "Iron deficiency or thalassemia trait.",
     ["mcv"]),
    ("mch", "Mean corpuscular hemoglobin (MCH)", "هموگلوبین متوسط گویچه", "pg", 27.0, 33.0, None, None,
     "B12/folate deficiency.", "Iron deficiency, thalassemia.", ["mch"]),
    ("mchc", "MCH concentration (MCHC)", "غلظت هموگلوبین گویچه", "g/dL", 32.0, 36.0, None, None,
     "Spherocytosis; usually mild.", "Iron deficiency.", ["mchc"]),
    ("rdw", "RDW (red cell width)", "پهنای توزیع گویچه‌های قرمز", "%", 11.5, 14.5, None, None,
     "Mixed anemia (iron + B12), early deficiency.", "Usually none.", ["rdw"]),
    ("plt", "Platelets (Plt)", "پلاکت", "×10³/µL", 150.0, 450.0, 50.0, 800.0,
     "Inflammation, iron deficiency, infection; very high: marrow disorder.", "Risk of bleeding; viral infection, drugs, ITP, marrow disease.",
     ["plt", "platelet", "پلاکت"]),
    ("mpv", "Mean platelet volume (MPV)", "حجم متوسط پلاکت", "fL", 7.5, 12.0, None, None,
     "Young active platelets.", "Old small platelets, marrow suppression.", ["mpv"]),
    ("neut", "Neutrophils", "نوتروفیل", "%", 40.0, 75.0, None, None,
     "Bacterial infection, stress, steroids.", "Viral infection or marrow suppression.",
     ["neutrophil", "نوتروفیل"]),
    ("neut_abs", "Absolute neutrophil count (ANC)", "شمارش مطلق نوتروفیل", "×10³/µL", 1.8, 7.0, 0.5, None,
     "Bacterial infection.", "Low infection resistance (neutropenia) — needs urgent attention below 0.5.",
     ["anc", "neut#"]),
    ("lymph", "Lymphocytes", "لنفوسیت", "%", 20.0, 45.0, None, None,
     "Viral infection; very high: consider chronic leukemia.", "Steroids, acute stress, HIV.",
     ["lymphocyte", "لنفوسیت"]),
    ("mono", "Monocytes", "مونوسیت", "%", 2.0, 10.0, None, None,
     "Chronic infection, TB, recovery phase.", "Usually not meaningful alone.", ["monocyte", "مونوسیت"]),
    ("eos", "Eosinophils", "ائوزینوفیل", "%", 1.0, 6.0, None, None,
     "Allergy, parasites, some drug reactions.", "Usually nothing.", ["eosinophil", "ائوزینوفیل"]),
    ("baso", "Basophils", "بازوفیل", "%", 0.0, 1.0, None, None,
     "Allergy; very high: blood disorder.", "Nothing.", ["basophil", "بازوفیل"]),
    ("retic", "Reticulocytes", "رتیکولوسیت", "%", 0.5, 2.5, None, None,
     "Marrow responding well to anemia or bleeding.", "Marrow not producing enough (aplastic, deficiency).",
     ["retic", "رتیکولوسیت"]),
    ("fbs", "Fasting blood sugar (FBS)", "قند خون ناشتا", "mg/dL", 70.0, 99.0, 50.0, 250.0,
     "100-125 = prediabetes; ≥126 (twice) = diabetes. See a doctor.", "Below 70 is hypoglycemia — eat fast carbs; below 50 is dangerous.",
     ["fbs", "glucose fasting", "قند ناشتا", "گلوکز ناشتا"]),
    ("ogtt2", "OGTT 2-hour glucose", "قند ۲ ساعته (OGTT)", "mg/dL", 70.0, 140.0, 50.0, 300.0,
     "140-199 = prediabetes; ≥200 = diabetes.", "Reactive hypoglycemia.", ["ogtt", "قند دو ساعته"]),
    ("bs_random", "Random blood sugar", "قند خون تصادفی", "mg/dL", 70.0, 140.0, 50.0, 300.0,
     "≥200 with symptoms suggests diabetes.", "Hypoglycemia.", ["rbs", "قند تصادفی", "گلوکز"]),
    ("hba1c", "Hemoglobin A1c", "هموگلوبین گلیکوزیله", "%", 4.0, 5.6, None, None,
     "5.7-6.4 = prediabetes; ≥6.5 = diabetes (3-month average).", "Rare; anemia can falsely lower it.",
     ["hba1c", "a1c", "ایوانک"]),
    ("insulin_f", "Fasting insulin", "انسولین ناشتا", "µIU/mL", 2.0, 25.0, None, None,
     "Insulin resistance, obesity, early diabetes.", "Low insulin production (type 1 diabetes).",
     ["insulin", "انسولین"]),
    ("na", "Sodium (Na)", "سدیم", "mEq/L", 135.0, 145.0, 120.0, 160.0,
     "Hypernatremia — usually dehydration.", "Hyponatremia — water excess, drugs, adrenal issues; below 120 is dangerous.",
     ["na", "sodium", "سدیم"]),
    ("k", "Potassium (K)", "پتاسیم", "mEq/L", 3.5, 5.1, 2.8, 6.0,
     "Hyperkalemia — kidney problem, drugs; >6 can stop the heart, urgent.", "Hypokalemia — vomiting, diuretics; muscle weakness, arrhythmia.",
     ["k", "potassium", "پتاسیم"]),
    ("cl", "Chloride (Cl)", "کلر", "mEq/L", 98.0, 107.0, None, None,
     "With sodium changes, acid-base problems.", "Vomiting, metabolic alkalosis.", ["cl", "کلر"]),
    ("co2", "Bicarbonate (CO2/HCO3)", "بی‌کربنات", "mEq/L", 22.0, 29.0, 10.0, 40.0,
     "Metabolic alkalosis or compensation.", "Metabolic acidosis — diabetic ketoacidosis, kidney disease, poisonings.",
     ["co2", "hco3", "بی کربنات"]),
    ("ca", "Calcium (total)", "کلسیم تام", "mg/dL", 8.6, 10.3, 7.0, 12.0,
     "Hyperparathyroidism, malignancy, vitamin D excess.", "Low vitamin D, kidney disease, low albumin.",
     ["ca", "کلسیم"]),
    ("cai", "Ionized calcium", "کلسیم یونیزه", "mg/dL", 4.5, 5.6, None, None,
     "Parathyroid issues, malignancy.", "Corrects with albumin or parathyroid problems.", ["ica"]),
    ("phos", "Phosphorus", "فسفر", "mg/dL", 2.5, 4.5, 1.0, 7.0,
     "Kidney failure, low parathyroid.", "Malnutrition, alcoholism, refeeding.", ["p", "phosphorus", "فسفر"]),
    ("mg", "Magnesium", "منیزیم", "mg/dL", 1.7, 2.2, 1.0, 4.0,
     "Kidney failure, excess intake.", "Diarrhea, PPI drugs, alcohol — cramps, arrhythmias.", ["mg", "منیزیم"]),
    ("bun", "Blood urea nitrogen (BUN)", "ازوت اوره خون", "mg/dL", 7.0, 20.0, None, 80.0,
     "Dehydration, high protein, kidney problem, bleeding in gut.", "Liver disease, malnutrition.",
     ["bun", "اوره", "یوره"]),
    ("cr", "Creatinine", "کراتینین", "mg/dL", 0.6, 1.3, None, 4.0,
     "Kidney filtering is down (or big muscle mass, some drugs).", "Low muscle mass.",
     ["cr", "creatinine", "کراتینین"]),
    ("bun_cr", "BUN/Creatinine ratio", "نسبت اوره به کراتینین", "—", 10.0, 20.0, None, None,
     "Dehydration or GI bleeding.", "Kidney-based problems or low protein diet.", ["bun/cr"]),
    ("ua", "Uric acid", "اسید اوریک", "mg/dL", 3.5, 7.2, None, 12.0,
     "Gout risk, kidney stones, diuretics, purine-rich diet.", "Rare; some liver or kidney tubule issues.",
     ["uric acid", "اسید اوریک"]),
    ("ast", "AST (SGOT)", "آسپارتات آمینوترانسفراز", "U/L", 0.0, 40.0, None, 300.0,
     "Liver or muscle injury; hepatitis, alcohol, drugs, exercise.", "Usually not meaningful.",
     ["ast", "sgot"]),
    ("alt", "ALT (SGPT)", "آلانین آمینوترانسفراز", "U/L", 0.0, 41.0, None, 300.0,
     "Liver cell injury — fatty liver, hepatitis, drugs.", "Usually not meaningful.",
     ["alt", "sgpt"]),
    ("alp", "Alkaline phosphatase (ALP)", "آلکالن فسفاتاز", "U/L", 44.0, 147.0, None, None,
     "Bile duct blockage or bone disease; high in pregnancy and teens.", "Rare; zinc deficiency.",
     ["alp"]),
    ("ggt", "GGT", "گاما گلوتامیل ترانسفراز", "U/L", 8.0, 61.0, None, None,
     "Alcohol, fatty liver, bile duct disease.", "Not meaningful.", ["ggt", "گاما گتی"]),
    ("tbil", "Total bilirubin", "بیلی‌روبین تام", "mg/dL", 0.2, 1.2, None, 15.0,
     "Gilbert syndrome, hemolysis, bile obstruction, hepatitis.", "Not meaningful.",
     ["bilirubin", "بیلی روبین تام"]),
    ("dbil", "Direct bilirubin", "بیلی‌روبین مستقیم", "mg/dL", 0.0, 0.3, None, None,
     "Bile duct or liver problem when elevated with total.", "Not meaningful.", ["direct bilirubin"]),
    ("alb", "Albumin", "آلبومین", "g/dL", 3.5, 5.2, 2.0, None,
     "Dehydration.", "Liver disease, kidney loss, malnutrition, inflammation.",
     ["albumin", "آلبومین"]),
    ("tpr", "Total protein", "پروتئین تام", "g/dL", 6.4, 8.3, None, None,
     "Dehydration, myeloma (with abnormal fractions).", "Malnutrition, liver or kidney loss.", ["total protein", "پروتئین تام"]),
    ("tchol", "Total cholesterol", "کلسترول تام", "mg/dL", 0.0, 200.0, None, None,
     "Cardiovascular risk rises above 200; diet, genetics, thyroid.", "Usually fine; very low with malnutrition.",
     ["chol", "کلسترول"]),
    ("ldl", "LDL cholesterol", "کلسترول بد (LDL)", "mg/dL", 0.0, 100.0, None, None,
     "Main 'bad' cholesterol; lower is better for heart health.", "Usually good news.",
     ["ldl", "ال دی ال"]),
    ("hdl", "HDL cholesterol", "کلسترول خوب (HDL)", "mg/dL", 40.0, 90.0, None, None,
     "Protective; higher is better.", "Below 40 raises heart risk — exercise raises it.",
     ["hdl", "ای دی ال"]),
    ("tg", "Triglycerides", "تری‌گلیسرید", "mg/dL", 0.0, 150.0, None, 1000.0,
     "Sugar/alcohol excess, obesity, diabetes; >1000 = pancreatitis risk.", "Usually fine.",
     ["tg", "triglyceride", "تری گلیسرید"]),
    ("nonhdl", "Non-HDL cholesterol", "کلسترول غیر-HDL", "mg/dL", 0.0, 130.0, None, None,
     "Total minus HDL; good overall risk marker.", "Usually good.", ["non-hdl"]),
    ("tsh", "TSH", "هورمون محرک تیروئید", "mIU/L", 0.4, 4.5, 0.01, 50.0,
     "Usually means UNDERACTIVE thyroid (hypothyroidism).", "Usually means OVERACTIVE thyroid (hyperthyroidism).",
     ["tsh", "تی اس اچ"]),
    ("ft4", "Free T4", "T4 آزاد", "ng/dL", 0.8, 1.8, None, None,
     "Hyperthyroidism (with low TSH).", "Hypothyroidism (with high TSH).", ["ft4", "t4"]),
    ("ft3", "Free T3", "T3 آزاد", "pg/mL", 2.3, 4.2, None, None,
     "Hyperthyroidism.", "Hypothyroidism or severe illness.", ["ft3", "t3"]),
    ("tpo", "Anti-TPO antibody", "آنتی‌بادی ضد تیروئید", "IU/mL", 0.0, 35.0, None, None,
     "Autoimmune thyroid disease (Hashimoto).", "Negative is normal.", ["anti-tpo", "تی پی او"]),
    ("cort_am", "Cortisol (morning)", "کورتیزول صبحگاهی", "µg/dL", 6.2, 19.4, None, None,
     "Stress, steroids, Cushing syndrome (needs proper testing).", "Adrenal insufficiency — needs doctor.",
     ["cortisol", "کورتیزول"]),
    ("testo_t", "Total testosterone", "تستوسترون تام", "ng/dL", 240.0, 950.0, None, None,
     "Supplements, tumors (rare).", "Low libido, fatigue, fertility issues.", ["testosterone", "تستوسترون"]),
    ("estro", "Estradiol (E2)", "استرادیول", "pg/mL", 30.0, 400.0, None, None,
     "Depends on cycle/age; needs interpretation.", "Menopause, ovarian failure.", ["estradiol", "استرادیول"]),
    ("lh", "LH", "هورمون LH", "mIU/mL", 1.9, 12.5, None, None,
     "Cycle-dependent; PCOS, menopause.", "Pituitary problems.", ["lh"]),
    ("fsh", "FSH", "هورمون FSH", "mIU/mL", 2.5, 10.2, None, None,
     "Menopause, primary gonadal failure.", "Pituitary problems.", ["fsh"]),
    ("prl", "Prolactin", "پرولاکتین", "ng/mL", 4.0, 23.0, None, None,
     "Pregnancy, some drugs, stress, pituitary adenoma if very high.", "Usually not meaningful.",
     ["prolactin", "پرولاکتین"]),
    ("dheas", "DHEA-S", "دی‌هیدرواپی‌آندروسترون", "µg/dL", 80.0, 560.0, None, None,
     "PCOS, adrenal issues.", "Adrenal insufficiency.", ["dhea"]),
    ("bhcg_t", "Beta-hCG (quantitative)", "بتا-hCG کمی", "mIU/mL", 0.0, 5.0, None, None,
     "Pregnancy (or rare tumors) — date from last period matters.", "Not pregnant (or very early).",
     ["beta hcg", "ب ه سی جی"]),
    ("vitd", "Vitamin D (25-OH)", "ویتامین D", "ng/mL", 30.0, 100.0, 5.0, 200.0,
     "Excess supplementation is harmful.", "Very common deficiency — bone pain, fatigue; supplement per doctor.",
     ["vitamin d", "25-oh"]),
    ("b12", "Vitamin B12", "ویتامین B12", "pg/mL", 200.0, 900.0, 100.0, None,
     "Supplements (harmless).", "Deficiency — nerve symptoms, anemia; vegetarians and elderly at risk.",
     ["b12", "کوبالامین"]),
    ("folate", "Folate (folic acid)", "فولات", "ng/mL", 3.0, 20.0, None, None,
     "Supplements.", "Deficiency — anemia, pregnancy problems.", ["folate", "folic"]),
    ("fe", "Serum iron", "آهن سرم", "µg/dL", 60.0, 160.0, None, None,
     "Iron overload, recent supplements.", "Iron deficiency.", ["iron", "آهن"]),
    ("ferritin", "Ferritin", "فریتین", "ng/mL", 30.0, 300.0, 10.0, 1000.0,
     "Iron overload; also rises with inflammation.", "Iron deficiency (best early marker).",
     ["فریتین"]),
    ("tibc", "TIBC", "ظرفیت اتصال آهن", "µg/dL", 240.0, 450.0, None, None,
     "Iron deficiency (body wants more iron).", "Malnutrition, inflammation, iron overload.", ["tibc"]),
    ("tsat", "Transferrin saturation (TSAT)", "اشباع ترانسفرین", "%", 20.0, 45.0, None, None,
     "Iron overload.", "Iron deficiency.", ["tsat"]),
    ("crp", "CRP", "پروتئین واکنشی C", "mg/L", 0.0, 5.0, None, 200.0,
     "Active inflammation/infection; extent matters.", "Normal.", ["crp", "سی آر پی"]),
    ("hscrp", "hs-CRP", "CRP فوق‌حساس", "mg/L", 0.0, 1.0, None, None,
     "1-3: moderate cardiovascular risk; >3: high risk / inflammation.", "Low cardiovascular risk.", ["hs-crp"]),
    ("esr", "ESR (sed rate)", "سرعت رسوب گویچه‌ها", "mm/h", 0.0, 20.0, None, 100.0,
     "Chronic inflammation, infection, autoimmune disease.", "Normal.", ["esr", "سرعت ته‌نشینی"]),
    ("trop", "Troponin I", "تروپونین I", "ng/mL", 0.0, 0.04, None, 0.1,
     "≥0.1 suggests heart muscle damage — EMERGENCY, call 115/112 now.", "Normal.",
     ["troponin", "تروپونین"]),
    ("ck", "Creatine kinase (CK)", "کراتین کیناز", "U/L", 30.0, 200.0, None, 5000.0,
     "Muscle damage, heavy exercise, statins, heart attack (see CK-MB).", "Usually fine.", ["ck", "cpk"]),
    ("ckmb", "CK-MB", "کراتین کیناز MB", "ng/mL", 0.0, 5.0, None, None,
     "Heart muscle involvement when high with troponin.", "Normal.", ["ck-mb"]),
    ("bnp", "BNP / NT-proBNP", "پپتید ناتریورتیک مغزی", "pg/mL", 0.0, 100.0, None, None,
     "Heart failure — higher means more strain.", "Heart failure unlikely.", ["bnp", "nt-probnp"]),
    ("pt", "Prothrombin time (PT)", "زمان پروترومبین", "sec", 11.0, 13.5, None, 30.0,
     "Slow clotting — liver disease, vitamin K lack, warfarin.", "Usually nothing.", ["pt"]),
    ("inr", "INR", "INR (نسبت نرمال‌شده بین‌المللی)", "—", 0.8, 1.2, None, 5.0,
     "On warfarin the target is usually 2-3; >4 means bleeding risk.", "Tendency to clot if low with other factors.",
     ["inr"]),
    ("ptt", "PTT (aPTT)", "زمان ترومبوپلاستین جزئی", "sec", 25.0, 35.0, None, 80.0,
     "Heparin, hemophilia, lupus anticoagulant.", "Usually nothing.", ["ptt", "aptt"]),
    ("ddimer", "D-dimer", "دی‌دایمر", "µg/mL", 0.0, 0.5, None, None,
     "Possible clot (DVT/PE) — needs urgent imaging if symptoms.", "Clot unlikely.", ["d-dimer", "دی دایمر"]),
    ("fib", "Fibrinogen", "فیبرینوژن", "mg/dL", 200.0, 400.0, None, None,
     "Inflammation, pregnancy, stroke risk.", "Liver failure, DIC — bleeding risk.", ["fibrinogen"]),
    ("u_sg", "Urine specific gravity", "وزن مخصوص ادرار", "—", 1.005, 1.030, None, None,
     "Dehydration.", "Over-hydration or kidney concentration problem.", ["specific gravity"]),
    ("u_ph", "Urine pH", "pH ادرار", "—", 4.5, 8.0, None, None,
     "Vegetarian diet, UTI with certain bacteria, kidney issues.", "High protein diet, metabolic acidosis.", ["urine ph"]),
    ("u_prot", "Urine protein", "پروتئین ادرار", "mg/dL", 0.0, 10.0, None, None,
     "Kidney filtering problem — needs follow-up (albumin/creatinine).", "Normal.", ["urine protein"]),
    ("u_glu", "Urine glucose", "قند ادرار", "mg/dL", 0.0, 0.0, None, None,
     "Blood sugar is running high (usually above 180).", "Normal.", ["urine glucose"]),
    ("u_blood", "Urine blood (hemoglobin)", "خون ادرار", "—", 0.0, 0.0, None, None,
     "Stones, infection, or kidney/bladder problem — always follow up.", "Normal.", ["urine blood"]),
    ("u_leuk", "Urine leukocyte esterase", "آزتر لوکوسیت ادرار", "—", 0.0, 0.0, None, None,
     "White cells in urine — usually UTI.", "Normal.", ["leukocyte esterase"]),
    ("u_nit", "Urine nitrite", "نیتریت ادرار", "—", 0.0, 0.0, None, None,
     "Bacteria (gram-negative UTI).", "Normal.", ["nitrite", "نیتریت"]),
    ("u_ket", "Urine ketones", "کتون ادرار", "—", 0.0, 0.0, None, None,
     "Fasting, keto diet, vomiting; in diabetics = DKA warning.", "Normal.", ["ketone", "کتون"]),
    ("u_alb_cr", "Urine albumin/creatinine ratio", "نسبت آلبومین به کراتینین ادرار", "mg/g", 0.0, 30.0, None, None,
     "Early kidney damage, especially in diabetes/hypertension.", "Normal.", ["acr", "albumin creatinine"]),
    ("hbsag", "HBsAg (hepatitis B surface antigen)", "آنتی‌ژن سطحی هپاتیت B", "qual", 0, 0, None, None,
     "POSITIVE = active hepatitis B infection — see a doctor.", "NEGATIVE = no active infection.",
     ["hbsag", "هپاتیت ب"]),
    ("hcvab", "HCV antibody", "آنتی‌بادی هپاتیت C", "qual", 0, 0, None, None,
     "POSITIVE = exposure to hepatitis C; confirmatory RNA test needed.", "NEGATIVE = no exposure.",
     ["hcv", "هپاتیت سی"]),
    ("hivab", "HIV 4th-generation test", "آزمایش HIV نسل چهارم", "qual", 0, 0, None, None,
     "POSITIVE must be confirmed by a lab; early treatment works.", "NEGATIVE = no infection detected (after window period).",
     ["hiv"]),
    ("psa", "PSA", "آنتی‌ژن اختصاصی پروستات", "ng/mL", 0.0, 4.0, None, 20.0,
     "Prostate enlargement or cancer (age matters); some drugs lower it.", "Normal.",
     ["psa", "پی اس ای"]),
    ("cea", "CEA", "آنتی‌ژن سرطان‌جنینی", "ng/mL", 0.0, 5.0, None, None,
     "Smoking raises it; colon and other cancers when high.", "Normal.", ["cea"]),
    ("afp", "Alpha-fetoprotein (AFP)", "آلفا فتوپروتئین", "ng/mL", 0.0, 10.0, None, None,
     "Liver cancer marker (with imaging); pregnancy values differ.", "Normal.", ["afp"]),
    ("ca125", "CA-125", "سرطان‌-marker تخمدان", "U/mL", 0.0, 35.0, None, None,
     "Ovarian concern but also endometriosis, menstruation, fibroids.", "Normal.", ["ca-125"]),
    ("ca153", "CA 15-3", "نشانگر پستان", "U/mL", 0.0, 31.0, None, None,
     "Breast cancer follow-up marker (not for screening).", "Normal.", ["ca 15-3"]),
    ("ca199", "CA 19-9", "نشانگر لوزالمعده", "U/mL", 0.0, 37.0, None, None,
     "Pancreatic/biliary marker; benign duct blockage also raises it.", "Normal.", ["ca 19-9"]),
    ("tsh_full", "Thyroid panel note", "", "", 0, 0, None, None, "", "", []),
]

_T = [t for t in _T if t[1] != "Thyroid panel note"]

CAT_OF = {}
for _row in _T:
    _k = _row[0]
    if _k in ("wbc", "rbc", "hb", "hct", "mcv", "mch", "mchc", "rdw", "plt", "mpv", "neut", "neut_abs", "lymph", "mono", "eos", "baso", "retic"):
        CAT_OF[_k] = "cbc"
    elif _k in ("fbs", "ogtt2", "bs_random", "hba1c", "insulin_f"):
        CAT_OF[_k] = "metabolic"
    elif _k in ("na", "k", "cl", "co2", "ca", "cai", "phos", "mg"):
        CAT_OF[_k] = "electrolytes"
    elif _k in ("bun", "cr", "bun_cr", "ua"):
        CAT_OF[_k] = "kidney"
    elif _k in ("ast", "alt", "alp", "ggt", "tbil", "dbil", "alb", "tpr"):
        CAT_OF[_k] = "liver"
    elif _k in ("tchol", "ldl", "hdl", "tg", "nonhdl"):
        CAT_OF[_k] = "lipids"
    elif _k in ("tsh", "ft4", "ft3", "tpo"):
        CAT_OF[_k] = "thyroid"
    elif _k in ("cort_am", "testo_t", "estro", "lh", "fsh", "prl", "dheas", "bhcg_t"):
        CAT_OF[_k] = "hormones"
    elif _k in ("vitd", "b12", "folate", "fe", "ferritin", "tibc", "tsat"):
        CAT_OF[_k] = "vitamins"
    elif _k in ("crp", "hscrp", "esr"):
        CAT_OF[_k] = "inflammation"
    elif _k in ("trop", "ck", "ckmb", "bnp"):
        CAT_OF[_k] = "cardiac"
    elif _k in ("pt", "inr", "ptt", "ddimer", "fib"):
        CAT_OF[_k] = "coagulation"
    elif _k.startswith("u_"):
        CAT_OF[_k] = "urine"
    elif _k in ("hbsag", "hcvab", "hivab"):
        CAT_OF[_k] = "serology"
    elif _k in ("psa", "cea", "afp", "ca125", "ca153", "ca199"):
        CAT_OF[_k] = "tumor"
    else:
        CAT_OF[_k] = "misc"

TESTS = {}
for (key, en, fa, unit, lo, hi, cl, ch, hin, lon, aliases) in _T:
    TESTS[key] = {"en": en, "fa": fa, "unit": unit, "lo": lo, "hi": hi,
                  "crit_lo": cl, "crit_hi": ch, "hi_note": hin, "lo_note": lon,
                  "aliases": [a.lower() for a in aliases if a], "cat": CAT_OF[key], "qual": unit == "qual"}


def all_tests(lang_fa: bool = True) -> list[dict]:
    out = []
    for k, t in TESTS.items():
        out.append({"key": k, "en": t["en"], "fa": t["fa"], "unit": t["unit"],
                    "lo": t["lo"], "hi": t["hi"], "cat": t["cat"], "qual": t["qual"],
                    "name": t["fa"] if lang_fa else t["en"]})
    return out


def find_test(token: str) -> dict | None:
    tok = (token or "").strip().lower()
    if not tok:
        return None
    if tok in TESTS:
        return TESTS[tok]
    for k, t in TESTS.items():
        if tok in t["aliases"] or tok == t["en"].lower() or tok == t["fa"]:
            return {"key": k, **t}
    return None


def evaluate(key: str, value: float | str, lang_fa: bool = True) -> dict:
    """Interpret one value: status + relative position + notes."""
    t = TESTS.get(key)
    if not t:
        return {"ok": False, "message_fa": "آزمایش پیدا نشد", "message_en": "test not found"}
    L = lang_fa
    name = t["fa"] if L else t["en"]
    if t["qual"]:
        v = str(value).strip().lower()
        positive = v in ("positive", "pos", "+", "reactive", "مثبت", "بله")
        negative = v in ("negative", "neg", "-", "non-reactive", "منفی")
        if not (positive or negative):
            return {"ok": False, "message_fa": "برای این آزمایش بنویس: مثبت یا منفی",
                    "message_en": "enter positive or negative for this test"}
        return {"ok": True, "qual": True, "test": name,
                "status": "positive" if positive else "normal",
                "note": t["hi_note"] if positive else t["lo_note"]}
    try:
        val = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return {"ok": False, "message_fa": "عدد معتبر وارد کنید", "message_en": "enter a valid number"}
    lo, hi = t["lo"], t["hi"]
    if val < lo:
        dev = round((lo - val) / lo * 100, 1) if lo else 0.0
        status = "crit_low" if (t["crit_lo"] is not None and val <= t["crit_lo"]) else ("low" if dev <= 25 else "very_low")
        note = t["lo_note"]
    elif val > hi:
        dev = round((val - hi) / hi * 100, 1) if hi else 0.0
        status = "crit_high" if (t["crit_hi"] is not None and val >= t["crit_hi"]) else ("high" if dev <= 25 else "very_high")
        note = t["hi_note"]
    else:
        dev, status, note = 0.0, "normal", ""
    return {"ok": True, "test": name, "unit": t["unit"], "value": val,
            "range": f"{lo} – {hi}", "status": status, "deviation_pct": dev, "note": note}


DISEASE_LABS = {
    "diabetes": ["fbs", "hba1c", "ogtt2", "u_glu", "u_ket"],
    "hyperglycemia": ["fbs", "hba1c", "u_glu"],
    "hypoglycemia": ["fbs", "insulin_f"],
    "sugar": ["fbs", "hba1c", "u_glu", "u_ket"],
    "prediab": ["fbs", "hba1c"],
    "hypothyroid": ["tsh", "ft4", "tpo"],
    "hyperthyroid": ["tsh", "ft3", "ft4"],
    "thyroid": ["tsh", "ft4", "tpo"],
    "anemia": ["hb", "mcv", "ferritin", "fe", "b12", "folate", "retic"],
    "iron_def": ["ferritin", "fe", "tibc", "tsat", "hb", "mcv"],
    "uti": ["u_leuk", "u_nit", "u_blood", "wbc", "crp"],
    "hypertension": ["na", "k", "cr", "ua", "u_alb_cr", "ca"],
    "hyperlipid": ["tchol", "ldl", "hdl", "tg", "nonhdl"],
    "lipid": ["tchol", "ldl", "hdl", "tg", "nonhdl"],
    "cholesterol": ["tchol", "ldl", "hdl", "tg", "nonhdl"],
    "fatty_liver": ["alt", "ast", "ggt", "tg", "tchol"],
    "hepatitis": ["alt", "ast", "tbil", "dbil", "alp", "hbsag", "hcvab"],
    "kidney": ["cr", "bun", "u_alb_cr", "k", "ca", "phos", "hb"],
    "stone": ["ua", "ca", "cr", "u_ph", "u_blood"],
    "gout": ["ua", "cr", "esr", "crp"],
    "asthma": ["eos", "wbc"],
    "copd": ["wbc", "crp", "co2"],
    "heart_failure": ["bnp", "na", "k", "cr", "hb"],
    "mi": ["trop", "ck", "ckmb", "hscrp"],
    "chest_pain": ["trop", "ckmb", "ecg"],
    "dvt": ["ddimer", "inr", "plt"],
    "osteoporo": ["ca", "vitd", "alp", "phos"],
    "pregnan": ["bhcg_t", "hb", "u_prot", "tsh"],
    "pneumonia": ["wbc", "neut_abs", "crp", "esr"],
    "celiac": ["hb", "fe", "tpr", "alb"],
    "depress": ["tsh", "b12", "vitd", "hb"],
    "obes": ["fbs", "hba1c", "tg", "alt", "tsh", "u_alb_cr"],
    "menopause": ["fsh", "estro", "tsh"],
    "pcos": ["testo_t", "lh", "fsh", "dheas", "fbs", "tg"],
    "prostate": ["psa", "ua", "cr"],
}


def labs_for_disease(disease_name_en: str, disease_id: str = "") -> list[dict]:
    """Typical lab tests for a disease (name or id match)."""
    hay = (disease_id + " " + (disease_name_en or "")).lower()
    hits = []
    for pat, keys in DISEASE_LABS.items():
        if pat in hay:
            for k in keys:
                if k in TESTS and k not in [h["key"] for h in hits]:
                    hits.append({"key": k, "en": TESTS[k]["en"], "fa": TESTS[k]["fa"]})
            break
    return hits[:8]
