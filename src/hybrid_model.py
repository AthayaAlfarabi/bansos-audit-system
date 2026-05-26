import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

class HybridFraudDetector:
    def __init__(self, rule_weight=0.3, stat_weight=0.4, spatial_weight=0.3):
        self.rule_weight = rule_weight
        self.stat_weight = stat_weight
        self.spatial_weight = spatial_weight
        
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        
        self.scaler = MinMaxScaler()
        
    def calculate_rule_based_score(self, df):
        """Hitung skor berbasis aturan"""
        scores = np.zeros(len(df))
        
        # Bobot untuk setiap pattern
        pattern_weights = {
            'pattern_sudden_appearance': 0.4,
            'pattern_sudden_disappearance': 0.3,
            'pattern_extreme_increase': 0.2,
            'pattern_extreme_decrease': 0.1,
            'mismatch_indicator': 0.3
        }
        
        for pattern, weight in pattern_weights.items():
            if pattern in df.columns:
                scores += df[pattern].values * weight
        
        return np.clip(scores, 0, 1)
    
    def calculate_statistical_score(self, df):
        """Hitung skor statistik menggunakan Isolation Forest"""
        # Pilih fitur untuk statistical analysis
        stat_features = [
            'change_abs', 'change_pct', 'volatility_score',
            'recipients_per_capita', 'coverage_ratio',
            'poverty_rate', 'unemployment_rate'
        ]
        
        available_features = [f for f in stat_features if f in df.columns]
        X_stat = df[available_features].fillna(0)
        
        # Fit Isolation Forest
        self.isolation_forest.fit(X_stat)
        
        # Dapatkan anomaly scores
        if_scores = -self.isolation_forest.score_samples(X_stat)
        
        # Normalisasi ke range 0-1
        stat_scores = self.scaler.fit_transform(
            if_scores.reshape(-1, 1)
        ).flatten()
        
        return stat_scores
    
    def calculate_spatial_score(self, df):
        """Hitung skor spasial/kontekstual"""
        if '2025' in df.columns:
            median_recipients = df['2025'].median()
            
            # Hitung deviasi dari median
            spatial_deviation = np.abs(
                df['2025'].values - median_recipients
            ) / (median_recipients + 1)
            
            # Normalisasi
            spatial_scores = self.scaler.fit_transform(
                spatial_deviation.reshape(-1, 1)
            ).flatten()
        else:
            spatial_scores = np.zeros(len(df))
        
        return spatial_scores
    
    def calculate_hybrid_score(self, df):
        """Gabungkan ketiga skor menjadi hybrid score"""
        df_scored = df.copy()
        
        # Hitung ketiga komponen skor
        rule_scores = self.calculate_rule_based_score(df_scored)
        stat_scores = self.calculate_statistical_score(df_scored)
        spatial_scores = self.calculate_spatial_score(df_scored)
        
        # Gabungkan dengan weighting
        hybrid_scores = (
            rule_scores * self.rule_weight +
            stat_scores * self.stat_weight +
            spatial_scores * self.spatial_weight
        )
        
        # Tambahkan ke dataframe
        df_scored['rule_score'] = rule_scores
        df_scored['stat_score'] = stat_scores
        df_scored['spatial_score'] = spatial_scores
        df_scored['hybrid_risk_score'] = hybrid_scores
        
        # Kategorisasi risiko
        def categorize_risk(score):
            if score >= 0.6:
                return 'HIGH'
            elif score >= 0.3:
                return 'MEDIUM'
            else:
                return 'LOW'
        
        df_scored['risk_category'] = df_scored['hybrid_risk_score'].apply(categorize_risk)
        
        return df_scored
    
    def evaluate_model(self, df_scored):
        """Evaluasi performa model"""
        if 'anomaly_flag' not in df_scored.columns:
            print("⚠️ Tidak ada label ground truth untuk evaluasi")
            return None
        
        y_true = df_scored['anomaly_flag']
        y_pred = (df_scored['hybrid_risk_score'] >= 0.3).astype(int)
        
        print("\n📊 Model Evaluation:")
        print("=" * 50)
        print(classification_report(y_true, y_pred))
        
        cm = confusion_matrix(y_true, y_pred)
        print("\nConfusion Matrix:")
        print(cm)
        
        return {
            'confusion_matrix': cm,
            'classification_report': classification_report(y_true, y_pred, output_dict=True)
        }
    
    def get_top_risky_regions(self, df_scored, top_n=10):
        """Dapatkan wilayah dengan risiko tertinggi"""
        top_risky = df_scored.nlargest(top_n, 'hybrid_risk_score')
        
        print(f"\n🔴 Top {top_n} Wilayah Berisiko Tinggi:")
        print("=" * 60)
        
        for idx, row in top_risky.iterrows():
            print(f"{row['nama_kabupaten_kota']}")
            print(f"  Score: {row['hybrid_risk_score']:.3f}")
            print(f"  Category: {row['risk_category']}")
            print(f"  Signature: {row['signature_type']}")
            print(f"  Change: {row.get('change_pct', 0):.1f}%")
            print("-" * 40)
        
        return top_risky

if __name__ == "__main__":
    # Load data
    df = pd.read_csv('data/processed/bansos_features.csv')
    
    # Initialize dan train model
    detector = HybridFraudDetector()
    df_scored = detector.calculate_hybrid_score(df)
    
    # Evaluasi
    evaluation = detector.evaluate_model(df_scored)
    
    # Get top risky regions
    top_risky = detector.get_top_risky_regions(df_scored)
    
    # Simpan hasil
    df_scored.to_csv('data/processed/bansos_scored.csv', index=False)
    
    print("\n✅ Hybrid model training complete!")