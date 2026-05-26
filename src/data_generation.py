import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

class BansosDataGenerator:
    def __init__(self, seed=42):
        self.seed = seed
        np.random.seed(seed)
        
        # Data wilayah Jawa Timur
        self.regions = [
            'KABUPATEN PACITAN', 'KABUPATEN PONOROGO', 'KABUPATEN TRENGGALEK',
            'KABUPATEN TULUNGAGUNG', 'KABUPATEN BLITAR', 'KABUPATEN KEDIRI',
            'KABUPATEN MALANG', 'KABUPATEN LUMAJANG', 'KABUPATEN JEMBER',
            'KABUPATEN BANYUWANGI', 'KABUPATEN BONDOWOSO', 'KABUPATEN SITUBONDO',
            'KABUPATEN PROBOLINGGO', 'KABUPATEN PASURUAN', 'KABUPATEN SIDOARJO',
            'KABUPATEN MOJOKERTO', 'KABUPATEN JOMBANG', 'KABUPATEN NGANJUK',
            'KABUPATEN MADIUN', 'KABUPATEN MAGETAN', 'KABUPATEN NGAWI',
            'KABUPATEN BOJONEGORO', 'KABUPATEN TUBAN', 'KABUPATEN LAMONGAN',
            'KABUPATEN GRESIK', 'KABUPATEN BANGKALAN', 'KABUPATEN SAMPANG',
            'KABUPATEN PAMEKASAN', 'KABUPATEN SUMENEP', 'KOTA KEDIRI',
            'KOTA BLITAR', 'KOTA MALANG', 'KOTA PROBOLINGGO', 'KOTA PASURUAN',
            'KOTA MOJOKERTO', 'KOTA MADIUN', 'KOTA SURABAYA', 'KOTA BATU'
        ]
        
        self.region_codes = [
            '3501', '3502', '3503', '3504', '3505', '3506', '3507', '3508', '3509',
            '3510', '3511', '3512', '3513', '3514', '3515', '3516', '3517', '3518',
            '3519', '3520', '3521', '3522', '3523', '3524', '3525', '3526', '3527',
            '3528', '3529', '3571', '3572', '3573', '3574', '3575', '3576', '3577',
            '3578', '3579'
        ]
    
    def generate_basic_data(self, years=[2024, 2025]):
        """Generate data dasar penerima bansos"""
        data = []
        id_counter = 1
        
        for year in years:
            for i, region in enumerate(self.regions):
                # Base recipients dengan distribusi normal
                base_recipients = int(np.random.normal(1000, 300))
                base_recipients = max(0, base_recipients)
                
                # Inject anomalies untuk tahun 2025
                if year == 2025:
                    # Pattern A: Sudden Appearance
                    if region in ['KABUPATEN SUMENEP', 'KABUPATEN BONDOWOSO']:
                        base_recipients = np.random.randint(5000, 10000)
                    
                    # Pattern B: Sudden Disappearance  
                    elif region in ['KABUPATEN NGANJUK', 'KABUPATEN LAMONGAN']:
                        base_recipients = int(base_recipients * 0.2)
                    
                    # Pattern C: Extreme Increase
                    elif region in ['KABUPATEN BANYUWANGI', 'KABUPATEN PAMEKASAN']:
                        base_recipients = int(base_recipients * np.random.uniform(3, 5))
                    
                    # Pattern D: Extreme Decrease
                    elif region in ['KOTA KEDIRI', 'KABUPATEN JEMBER']:
                        base_recipients = int(base_recipients * np.random.uniform(0.3, 0.5))
                
                record = {
                    'id': id_counter,
                    'kode_provinsi': '35',
                    'nama_provinsi': 'JAWA TIMUR',
                    'kode_kabupaten_kota': self.region_codes[i],
                    'nama_kabupaten_kota': region,
                    'jumlah_penerima_bantuan_sosial': base_recipients,
                    'tahun': year,
                    'periode_update': f"{year}-12",
                    'satuan': 'PENERIMA MANFAAT'
                }
                data.append(record)
                id_counter += 1
        
        return pd.DataFrame(data)
    
    def generate_external_data(self):
        """Generate data eksternal pendukung"""
        n_regions = len(self.regions)
        
        external_data = {
            'nama_kabupaten_kota': self.regions,
            'kode_kabupaten_kota': self.region_codes,
            'poverty_rate': np.random.uniform(0.05, 0.25, n_regions),
            'population': np.random.uniform(500000, 3000000, n_regions),
            'hdi': np.random.uniform(60, 80, n_regions),
            'unemployment_rate': np.random.uniform(0.03, 0.15, n_regions),
            'avg_income': np.random.uniform(2000000, 5000000, n_regions),
            'latitude': np.random.uniform(-8.5, -7.0, n_regions),
            'longitude': np.random.uniform(111.0, 114.5, n_regions)
        }
        
        return pd.DataFrame(external_data)
    
    def save_data(self, output_dir='data'):
        """Simpan data ke file CSV"""
        os.makedirs(f'{output_dir}/raw', exist_ok=True)
        os.makedirs(f'{output_dir}/processed', exist_ok=True)
        
        # Generate dan simpan data dasar
        basic_data = self.generate_basic_data()
        basic_data.to_csv(f'{output_dir}/raw/bansos_jatim_basic.csv', index=False)
        
        # Generate dan simpan data eksternal
        external_data = self.generate_external_data()
        external_data.to_csv(f'{output_dir}/raw/bansos_jatim_external.csv', index=False)
        
        print("✅ Data berhasil di-generate dan disimpan!")
        return basic_data, external_data

if __name__ == "__main__":
    generator = BansosDataGenerator()
    basic_data, external_data = generator.save_data()
    
    print(f"\n Statistik Data:")
    print(f"Total records: {len(basic_data)}")
    print(f"Tahun: {basic_data['tahun'].unique()}")
    print(f"Wilayah: {basic_data['nama_kabupaten_kota'].nunique()}")