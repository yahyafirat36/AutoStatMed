import pandas as pd
from scipy import stats
import numpy as np

class StatEngine:
    def __init__(self, df):
        self.data = df

    def get_table1_demographics(self):
        summary = {}
        for col in self.data.select_dtypes(include=['number']).columns:
            mean_val = self.data[col].mean()
            std_val = self.data[col].std()
            if not pd.isna(mean_val) and not pd.isna(std_val):
                summary[col] = f"{mean_val:.2f} ± {std_val:.2f}"
        return summary

    def check_normality(self, col_name):
        series = self.data[col_name].dropna()
        if len(series) < 3:
            return {"test_name": "Shapiro-Wilk", "p_value": None, "is_normal": False, "next_step": "Yetersiz Veri"}
        
        stat, p = stats.shapiro(series)
        is_normal = bool(p > 0.05) 
        return {
            "test_name": "Shapiro-Wilk",
            "p_value": float(p),
            "is_normal": is_normal,
            "next_step": "T-Testi veya ANOVA" if is_normal else "Mann-Whitney U veya Kruskal-Wallis"
        }

    def compare_two_groups(self, group_col, value_col):
        groups = self.data[group_col].dropna().unique()
        if len(groups) != 2:
            return None
        
        g1 = self.data[self.data[group_col] == groups[0]][value_col].dropna()
        g2 = self.data[self.data[group_col] == groups[1]][value_col].dropna()
        
        if len(g1) < 2 or len(g2) < 2:
            return None
            
        normality1 = self.check_normality(value_col)['is_normal']
        
        if normality1:
            stat, p = stats.ttest_ind(g1, g2)
            test_name = "Bağımsız Örneklem T-Testi (Parametrik)"
        else:
            stat, p = stats.mannwhitneyu(g1, g2)
            test_name = "Mann-Whitney U Testi (Non-Parametrik)"
            
        return {
            "aciklama": f"{groups[0]} ve {groups[1]} grupları arasında {value_col} karşılaştırması",
            "test_adi": test_name,
            "stat_degeri": round(float(stat), 3),
            "p_degeri": round(float(p), 4),
            "anlamli_mi": bool(p < 0.05)
        }

    # Tekrarlayan Ölçümler (Bağımlı T-Testi)
    def repeated_measures_test(self, pre_col, post_col):
        valid = self.data[[pre_col, post_col]].dropna()
        if len(valid) < 2:
            return None
            
        stat, p = stats.ttest_rel(valid[pre_col], valid[post_col])
        return {
            "test_adi": "Eşleştirilmiş T-Testi (Pre-Post)",
            "p_degeri": round(float(p), 4),
            "anlamli_mi": bool(p < 0.05)
        }

    # ANOVA (Çoklu Grup)
    def anova_test(self, group_col, value_col):
        groups = self.data[group_col].dropna().unique()
        if len(groups) < 3:
            return None
            
        group_data = [self.data[self.data[group_col] == g][value_col].dropna() for g in groups]
        group_data = [g for g in group_data if len(g) > 1]
        
        if len(group_data) < 3:
            return None

        stat, p = stats.f_oneway(*group_data)
        return {
            "test_adi": "Tek Yönlü ANOVA",
            "p_degeri": round(float(p), 4),
            "anlamli_mi": bool(p < 0.05)
        }

    # EKSİK KALAN VE EKLENEN: Kategorik Veriler İçin Ki-Kare Testi
    def chi_square_test(self, col1, col2):
        if col1 not in self.data.columns or col2 not in self.data.columns:
            return None
            
        contingency_table = pd.crosstab(self.data[col1], self.data[col2])
        if contingency_table.empty or contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
            return None
            
        chi2, p, dof, expected = stats.chi2_contingency(contingency_table)
        return {
            "aciklama": f"{col1} ile {col2} Arasındaki İlişki (Ki-Kare Testi)",
            "chi2_degeri": round(float(chi2), 3),
            "p_degeri": round(float(p), 4),
            "anlamli_mi": bool(p < 0.05)
        }