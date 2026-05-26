import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import warnings
warnings.filterwarnings('ignore')

class BansosPreprocessor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.minmax_scaler = MinMaxScaler()
    
    def load_data(self, data_dir='data/raw'):
        """Load data dari file CSV"""
        basic_data = pd.read_csv(f'{data_dir}/bansos_jatim_basic.csv')
        external_data = pd.read_csv(f'{data_dir}/bansos_jatim_external.csv')
        return basic_data, external_data
    
    def create_pivot_table(self, df):
        """Ubah format data dari long ke wide"""
        pivot_df = df.pivot_table(
            index=['nama_kabupaten_kota', 'kode_kabupaten_kota'],
            columns='tahun',
            values='jumlah_penerima_bantuan_sosial',
            aggfunc='sum'
        ).reset_index()
        
        # Pastikan kolom tahun ada
        for year in [2024, 2025]:
            if year not in pivot_df.columns:
                pivot_df[year] = 0
        
        return pivot_df
    
    def calculate_change_metrics(self, df):
        """Hitung metrik perubahan antar tahun"""
        df_changes = df.copy()
        
        # Perubahan absolut
        df_changes['change_abs'] = df_changes[2025] - df_changes[2024]
        
        # Perubahan persentase (handle division by zero)
        df_changes['change_pct'] = np.where(
            df_changes[2024] == 0,
            np.where(df_changes[2025] > 0, 999.99, 0),
            (df_changes['change_abs'] / df_changes[2024]) * 100
        )
        
        # Limit outliers
        df_changes['change_pct'] = df_changes['change_pct'].clip(-500, 500)
        
        return df_changes
    
    def extract_fraud_signatures(self, df):
        """Ekstrak signature fraud berdasarkan pola"""
        df_signatures = df.copy()
        
        # Signature A: Sudden Appearance (dari 0 menjadi >1000)
        df_signatures['pattern_sudden_appearance'] = (
            (df_signatures[2024] == 0) & (df_signatures[2025] > 1000)
        ).astype(int)
        
        # Signature B: Sudden Disappearance (dari >1000 menjadi <500)
        df_signatures['pattern_sudden_disappearance'] = (
            (df_signatures[2024] > 1000) & (df_signatures[2025] < 500)
        ).astype(int)
        
        # Signature C: Extreme Increase (>200%)
        df_signatures['pattern_extreme_increase'] = (
            df_signatures['change_pct'] > 200
        ).astype(int)
        
        # Signature D: Extreme Decrease (<-50%)
        df_signatures['pattern_extreme_decrease'] = (
            df_signatures['change_pct'] < -50
        ).astype(int)
        
        # Flag anomali umum
        df_signatures['anomaly_flag'] = (
            df_signatures['pattern_sudden_appearance'] |
            df_signatures['pattern_sudden_disappearance'] |
            df_signatures['pattern_extreme_increase'] |
            df_signatures['pattern_extreme_decrease']
        ).astype(int)
        
        # Label signature type
        def assign_signature(row):
            if row['pattern_sudden_appearance']:
                return 'A: Sudden Appearance'
            elif row['pattern_sudden_disappearance']:
                return 'B: Sudden Disappearance'
            elif row['pattern_extreme_increase']:
                return 'C: Extreme Increase'
            elif row['pattern_extreme_decrease']:
                return 'D: Extreme Decrease'
            else:
                return 'Normal'
        
        df_signatures['signature_type'] = df_signatures.apply(assign_signature, axis=1)
        
        return df_signatures
    
    def merge_with_external_data(self, df_signatures, external_data):
        """Gabungkan dengan data eksternal"""
        df_merged = df_signatures.merge(
            external_data,
            on='nama_kabupaten_kota',
            how='left'
        )
        
        return df_merged
    
    def create_additional_features(self, df):
        """Buat fitur tambahan untuk modeling"""
        df_features = df.copy()
        
        # Recipients per capita
        df_features['recipients_per_capita'] = (
            df_features[2025] / (df_features['population'] + 1)
        )
        
        # Coverage ratio
        df_features['coverage_ratio'] = (
            df_features[2025] / 
            (df_features['population'] * df_features['poverty_rate'] + 1)
        )
        
        # Mismatch indicator
        df_features['mismatch_indicator'] = (
            (df_features['poverty_rate'] < 0.10) & (df_features[2025] > 2000)
        ).astype(int)
        
        # Volatility score
        df_features['volatility_score'] = np.abs(df_features['change_pct']) / 100
        
        # Risk indicators
        df_features['high_risk_population'] = (
            df_features['population'] > df_features['population'].median()
        ).astype(int)
        
        df_features['low_hdi'] = (
            df_features['hdi'] < df_features['hdi'].median()
        ).astype(int)
        
        return df_features
    
    def preprocess_all(self, output_dir='data/processed'):
        """Jalankan semua preprocessing steps"""
        print("🔄 Loading data...")
        basic_data, external_data = self.load_data()
        
        print("🔄 Creating pivot table...")
        pivot_df = self.create_pivot_table(basic_data)
        
        print("🔄 Calculating change metrics...")
        df_changes = self.calculate_change_metrics(pivot_df)
        
        print(" Extracting fraud signatures...")
        df_signatures = self.extract_fraud_signatures(df_changes)
        
        print("🔄 Merging with external data...")
        df_merged = self.merge_with_external_data(df_signatures, external_data)
        
        print("🔄 Creating additional features...")
        df_features = self.create_additional_features(df_merged)
        
        # Simpan hasil
        os.makedirs(output_dir, exist_ok=True)
        df_features.to_csv(f'{output_dir}/bansos_features.csv', index=False)
        df_signatures.to_csv(f'{output_dir}/bansos_signatures.csv', index=False)
        
        print("✅ Preprocessing selesai!")
        return df_features

if __name__ == "__main__":
    preprocessor = BansosPreprocessor()
    df_features = preprocessor.preprocess_all()
    
    print(f"\n📊 Fitur yang dihasilkan:")
    print(f"Total kolom: {len(df_features.columns)}")
    print(f"Kolom: {list(df_features.columns)}")
    print(f"\n📈 Distribusi Anomali:")
    print(df_features['anomaly_flag'].value_counts())