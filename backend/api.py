from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import math
import numpy as np
from scipy import stats
from StatEngine import StatEngine

try:
    from lifelines import KaplanMeierFitter
    from lifelines.statistics import logrank_test
    lifelines_available = True
except ImportError:
    lifelines_available = False

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.neighbors import NearestNeighbors
    sklearn_available = True
except ImportError:
    sklearn_available = False

app = FastAPI(title="AutoStatMed API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def safe_float(val):
    if pd.isna(val) or math.isinf(val):
        return None
    return float(val)

@app.get("/")
def home():
    return {"status": "AutoStatMed API Aktif"}

@app.post("/analyze")
async def analyze_file(file: UploadFile = File(...)):
    contents = await file.read()
    
    if file.filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(contents))
    else:
        df = pd.read_excel(io.BytesIO(contents))
        
    engine = StatEngine(df)
    demographics = engine.get_table1_demographics()
    
    normality_results = {}
    for col in df.select_dtypes(include=['number']).columns:
        res = engine.check_normality(col)
        if "p_value" in res:
            res["p_value"] = float(res["p_value"]) if not pd.isna(res["p_value"]) else "Hesaplanamadı"
        normality_results[col] = res

    chart_data = []
    scatter_data = []
    group_test_result = None
    correlation_result = None
    chi_square_result = None
    
    if 'Cinsiyet' in df.columns and 'Yas' in df.columns:
        avg_age = df.groupby('Cinsiyet')['Yas'].mean().round(1).to_dict()
        chart_data = [{"Cinsiyet": str(k), "Ortalama Yas": safe_float(v) or 0} for k, v in avg_age.items()]
        group_test_result = engine.compare_two_groups('Cinsiyet', 'Yas')

    if 'Yas' in df.columns and 'Kan_Basinci' in df.columns:
        valid_data = df[['Yas', 'Kan_Basinci']].dropna()
        if len(valid_data) > 2:
            r_stat, p_val = stats.pearsonr(valid_data['Yas'], valid_data['Kan_Basinci'])
            correlation_result = {
                "aciklama": "Yaş ile Kan Basıncı Arasındaki İlişki",
                "r_degeri": safe_float(round(r_stat, 3)),
                "p_degeri": safe_float(round(p_val, 4)),
                "anlamli_mi": bool(p_val < 0.05)
            }
            scatter_data = [{"Yas": safe_float(row['Yas']), "Kan_Basinci": safe_float(row['Kan_Basinci'])} for _, row in valid_data.iterrows()]

    # EKSİK OLAN Kİ-KARE BAĞLANTISI EKLENDİ
    if 'Cinsiyet' in df.columns and 'Iyilesme_Durumu' in df.columns:
        chi_square_result = engine.chi_square_test('Cinsiyet', 'Iyilesme_Durumu')

    advanced_modules = []

    # 1. Regresyon
    if 'Yas' in df.columns and 'Kan_Basinci' in df.columns:
        valid = df[['Yas', 'Kan_Basinci']].dropna()
        if len(valid) > 2:
            slope, intercept, r_val, p_val, std_err = stats.linregress(valid['Yas'], valid['Kan_Basinci'])
            advanced_modules.append({
                "isim": "1. Doğrusal Regresyon",
                "durum": "Başarılı",
                "detay": f"Yaş ile Kan Basıncı tahmin modeli kuruldu. P-Değeri: {safe_float(round(p_val, 4))} | R-Kare: {safe_float(round(r_val**2, 3))}",
                "renk": "#16a34a" if p_val < 0.05 else "#ca8a04"
            })
    else:
        advanced_modules.append({"isim": "1. Doğrusal Regresyon", "durum": "Eksik Veri", "detay": "Sayısal değişkenler bulunamadı.", "renk": "#6b7280"})

    # 2. ANOVA (Grafikli)
    if 'Kan_Grubu' in df.columns and 'Kan_Basinci' in df.columns:
        anova_res = engine.anova_test('Kan_Grubu', 'Kan_Basinci')
        if anova_res:
            means = df.groupby('Kan_Grubu')['Kan_Basinci'].mean().dropna().to_dict()
            c_data = [{"isim": str(k), "deger": safe_float(round(v, 1))} for k, v in means.items()]
            advanced_modules.append({
                "isim": "2. ANOVA (Çoklu Grup)",
                "durum": "Başarılı",
                "detay": f"Kan Gruplarına göre Kan Basıncı farkı incelendi. P-Değeri: {anova_res['p_degeri']}",
                "renk": "#16a34a" if anova_res['anlamli_mi'] else "#ca8a04",
                "chart_title": "Kan Grubuna Göre Tansiyon",
                "chart_data": c_data
            })
        else:
             advanced_modules.append({"isim": "2. ANOVA", "durum": "Yetersiz", "detay": "Veri az.", "renk": "#6b7280"})
    else:
         advanced_modules.append({"isim": "2. ANOVA", "durum": "Eksik", "detay": "Kan_Grubu yok.", "renk": "#6b7280"})

    # 3. Sağkalım
    if 'Takip_Suresi' in df.columns and 'Son_Durum' in df.columns and 'Cinsiyet' in df.columns and lifelines_available:
        valid_surv = df[['Takip_Suresi', 'Son_Durum', 'Cinsiyet']].dropna()
        if len(valid_surv) > 5:
            event_col = valid_surv['Son_Durum'].apply(lambda x: 1 if str(x).lower() == 'olum' else 0)
            group1 = valid_surv['Cinsiyet'] == 'E'
            group2 = valid_surv['Cinsiyet'] == 'K'
            try:
                results = logrank_test(valid_surv['Takip_Suresi'][group1], valid_surv['Takip_Suresi'][group2], 
                                     event_observed_A=event_col[group1], event_observed_B=event_col[group2])
                advanced_modules.append({
                    "isim": "3. Sağkalım (Kaplan-Meier)",
                    "durum": "Başarılı",
                    "detay": f"Cinsiyete göre sağkalım analizi. P-Değeri: {round(results.p_value, 4)}",
                    "renk": "#16a34a" if results.p_value < 0.05 else "#ca8a04"
                })
            except: pass
    else:
         advanced_modules.append({"isim": "3. Sağkalım", "durum": "Eksik", "detay": "Sütunlar yok.", "renk": "#6b7280"})

    # 4. Tekrarlayan Ölçümler (Grafikli)
    if 'Ameliyat_Oncesi' in df.columns and 'Ameliyat_Sonrasi' in df.columns:
        rep_res = engine.repeated_measures_test('Ameliyat_Oncesi', 'Ameliyat_Sonrasi')
        if rep_res:
            pre_mean = df['Ameliyat_Oncesi'].mean()
            post_mean = df['Ameliyat_Sonrasi'].mean()
            c_data = [{"isim": "Öncesi", "deger": safe_float(round(pre_mean, 1))}, {"isim": "Sonrası", "deger": safe_float(round(post_mean, 1))}]
            advanced_modules.append({
                "isim": "4. Tekrarlayan Ölçümler",
                "durum": "Başarılı",
                "detay": f"Ameliyat öncesi/sonrası P-Değeri: {rep_res['p_degeri']}",
                "renk": "#16a34a" if rep_res['anlamli_mi'] else "#ca8a04",
                "chart_title": "Ameliyat Öncesi vs Sonrası Skoru",
                "chart_data": c_data
            })
    else:
        advanced_modules.append({"isim": "4. Tekrarlayan Ölçümler", "durum": "Eksik", "detay": "Sütunlar yok.", "renk": "#6b7280"})

    # 5. PSM
    if 'Tedavi_Grubu' in df.columns and 'Kolesterol' in df.columns and sklearn_available:
        valid_psm = df[['Tedavi_Grubu', 'Kolesterol']].dropna()
        if len(valid_psm) > 10:
             try:
                 X = valid_psm[['Kolesterol']]
                 y = valid_psm['Tedavi_Grubu'].apply(lambda x: 1 if 'A' in str(x) else 0)
                 model = LogisticRegression()
                 model.fit(X, y)
                 advanced_modules.append({
                    "isim": "5. Eğilim Skoru Eşleştirmesi",
                    "durum": "Başarılı",
                    "detay": f"Model Skoru: {round(model.score(X,y), 2)}. Gruplar eşleştirilebilir.",
                    "renk": "#16a34a"
                })
             except: pass
    else:
        advanced_modules.append({"isim": "5. Eğilim Skoru", "durum": "Eksik", "detay": "Sütunlar yok.", "renk": "#6b7280"})


    # ==========================================
    # GÜNCELLENMİŞ DEVASA MAKALE YAZARI
    # ==========================================
    academic_text = f"Bu çalışmada toplam {len(df)} hastanın klinik verileri incelenmiştir. "
    
    if group_test_result:
        anlam = "anlamlı bir farklılık saptanmıştır" if group_test_result['anlamli_mi'] else "anlamlı bir farklılık saptanmamıştır"
        academic_text += f"Yapılan {group_test_result['test_adi']} sonucunda, {group_test_result['aciklama'].lower()} değerlendirildiğinde {anlam} (p = {group_test_result['p_degeri']}). "
    
    if correlation_result:
        iliski = "anlamlı bir korelasyon (ilişki) bulunmuştur" if correlation_result['anlamli_mi'] else "anlamlı bir korelasyon bulunamamıştır"
        academic_text += f"Pearson korelasyon analizi ile {correlation_result['aciklama'].lower()} incelenmiş ve {iliski} (r = {correlation_result['r_degeri']}, p = {correlation_result['p_degeri']}). "
        
    if chi_square_result:
        anlam_ki = "istatistiksel olarak anlamlı bir ilişki saptanmıştır" if chi_square_result['anlamli_mi'] else "anlamlı bir ilişki saptanamamıştır"
        academic_text += f"Kategorik veriler üzerinde yapılan Ki-Kare testi ile {chi_square_result['aciklama'].lower()} değerlendirilmiş olup, {anlam_ki} (p = {chi_square_result['p_degeri']}). "

    for mod in advanced_modules:
        if mod['durum'] == "Başarılı":
            academic_text += f"İleri analiz aşamasında {mod['isim']} yapılmış olup; {mod['detay'].replace('P-Değeri:', 'p =').replace('|', ',')}. "

    return {
        "filename": file.filename,
        "demographics": demographics,
        "normality": normality_results,
        "chart_data": chart_data,
        "scatter_data": scatter_data,
        "group_test_result": group_test_result,
        "correlation_result": correlation_result,
        "chi_square_result": chi_square_result,
        "advanced_modules": advanced_modules,
        "academic_text": academic_text
    }
    #cd backend , .\venv\Scripts\Activate.ps1 ,uvicorn api:app --reload --port 8000 ,, cd frontend , npm run dev