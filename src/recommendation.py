import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')

class AuditRecommender:
    def __init__(self, cost_fn=1000000, cost_fp=10000):
        self.cost_fn = cost_fn  # Cost False Negative
        self.cost_fp = cost_fp  # Cost False Positive
    
    def calculate_expected_cost(self, df, threshold):
        """Hitung expected cost untuk threshold tertentu"""
        if 'anomaly_flag' not in df.columns:
            return float('inf'), 0, 0
        
        y_true = df['anomaly_flag']
        y_pred = (df['hybrid_risk_score'] >= threshold).astype(int)
        
        fn = ((y_true == 1) & (y_pred == 0)).sum()
        fp = ((y_true == 0) & (y_pred == 1)).sum()
        
        expected_cost = (fn * self.cost_fn) + (fp * self.cost_fp)
        
        return expected_cost, fn, fp
    
    def optimize_threshold(self, df):
        """Optimasi threshold berdasarkan expected cost"""
        thresholds = np.arange(0.1, 0.9, 0.05)
        costs = []
        
        for threshold in thresholds:
            cost, fn, fp = self.calculate_expected_cost(df, threshold)
            costs.append({
                'threshold': threshold,
                'cost': cost,
                'fn': fn,
                'fp': fp
            })
        
        # Cari threshold dengan cost minimum
        optimal = min(costs, key=lambda x: x['cost'])
        
        print(f"\n🎯 Optimal Threshold Analysis:")
        print("=" * 50)
        print(f"Optimal Threshold: {optimal['threshold']:.2f}")
        print(f"Minimum Expected Cost: Rp {optimal['cost']:,.0f}")
        print(f"False Negatives: {optimal['fn']}")
        print(f"False Positives: {optimal['fp']}")
        
        return optimal
    
    def generate_priority_list(self, df, top_n=15):
        """Generate daftar prioritas audit"""
        priority_df = df.sort_values('hybrid_risk_score', ascending=False).head(top_n).copy()
        
        # Generate justifications
        def generate_justification(row):
            justifications = []
            
            if row.get('rule_score', 0) >= 0.5:
                justifications.append("⚠️ Pelanggaran aturan eligibility")
            
            if row.get('stat_score', 0) >= 0.5:
                justifications.append("📊 Anomali statistik signifikan")
            
            if row.get('spatial_score', 0) >= 0.5:
                justifications.append("🗺️ Deviasi dari wilayah tetangga")
            
            if row.get('pattern_sudden_appearance', 0) == 1:
                justifications.append("🔴 Muncul tiba-tiba (0→High)")
            
            if row.get('pattern_sudden_disappearance', 0) == 1:
                justifications.append(" Hilang tiba-tiba (High→0)")
            
            if row.get('pattern_extreme_increase', 0) == 1:
                justifications.append(f"📈 Kenaikan ekstrem ({row.get('change_pct', 0):.0f}%)")
            
            if row.get('pattern_extreme_decrease', 0) == 1:
                justifications.append(f"📉 Penurunan ekstrem ({row.get('change_pct', 0):.0f}%)")
            
            return "; ".join(justifications) if justifications else "✅ Pola normal"
        
        priority_df['justification'] = priority_df.apply(generate_justification, axis=1)
        priority_df['audit_priority'] = range(1, len(priority_df) + 1)
        
        return priority_df
    
    def calculate_similarity_matrix(self, df):
        """Hitung similarity matrix antar wilayah"""
        features = ['rule_score', 'stat_score', 'spatial_score', 
                   'volatility_score', 'coverage_ratio']
        
        available_features = [f for f in features if f in df.columns]
        X = df[available_features].fillna(0)
        
        similarity_matrix = cosine_similarity(X)
        
        return similarity_matrix
    
    def find_similar_regions(self, df, target_region, top_n=5):
        """Cari wilayah dengan profil risiko serupa"""
        if target_region not in df['nama_kabupaten_kota'].values:
            return None
        
        similarity_matrix = self.calculate_similarity_matrix(df)
        region_idx = df[df['nama_kabupaten_kota'] == target_region].index[0]
        
        similarities = similarity_matrix[region_idx]
        similar_indices = np.argsort(similarities)[::-1][1:top_n+1]
        
        similar_regions = df.iloc[similar_indices][['nama_kabupaten_kota', 'hybrid_risk_score']]
        
        return similar_regions
    
    def generate_recommendation_report(self, df, output_file='recommendation_report.csv'):
        """Generate laporan rekomendasi lengkap"""
        print("🔄 Generating recommendation report...")
        
        # Optimasi threshold
        optimal = self.optimize_threshold(df)
        
        # Generate priority list
        priority_list = self.generate_priority_list(df)
        
        # Simpan hasil
        priority_list.to_csv(output_file, index=False)
        
        print(f"\n✅ Recommendation report saved to {output_file}")
        print(f"\n Top 10 Audit Priorities:")
        print("=" * 80)
        
        for idx, row in priority_list.head(10).iterrows():
            print(f"{row['audit_priority']}. {row['nama_kabupaten_kota']}")
            print(f"   Risk Score: {row['hybrid_risk_score']:.3f}")
            print(f"   Justification: {row['justification']}")
            print("-" * 60)
        
        return priority_list, optimal

if __name__ == "__main__":
    # Load scored data
    df = pd.read_csv('data/processed/bansos_scored.csv')
    
    # Initialize recommender
    recommender = AuditRecommender()
    
    # Generate recommendations
    priority_list, optimal = recommender.generate_recommendation_report(df)
    
    print("\n✅ Recommendation system complete!")