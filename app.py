import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import json
import os
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Sistem Rekomendasi Prioritas Audit Bansos",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1f77b4; text-align: center; margin-bottom: 2rem; }
    .stExpander { border: 1px solid #333; border-radius: 8px; margin-bottom: 10px; background-color: #1a1a1a; }
    .search-result-card { background-color: #262730; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🎯 Sistem Rekomendasi Prioritas Audit Penyaluran Bantuan Sosial")
st.markdown("**Jawa Timur 2024-2025** | Hybrid Machine Learning & Signature Analysis")
st.markdown("---")

# Helper function untuk parse angka
def parse_number(value):
    if pd.isna(value) or value == '' or value is None: return 0.0
    try: return float(value)
    except:
        try: return float(str(value).replace('.', '').replace(',', '.'))
        except: return 0.0

# Helper function untuk format persentase yang rapi
def format_percentage(value):
    if pd.isna(value): return "0.0%"
    val = float(value)
    if val > 1000: return "> +1000%"
    if val < -1000: return "< -1000%"
    return f"{val:.1f}%"

# Load data CSV
@st.cache_data
def load_data():
    try:
        df_scored = pd.read_csv('data/processed/bansos_scored.csv')
        try: df_priority = pd.read_csv('data/processed/recommendation_report.csv', sep=';')
        except: 
            try: df_priority = pd.read_csv('data/processed/recommendation_report.csv')
            except: df_priority = df_scored.copy()
        return df_scored, df_priority
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return None, None

# Load GeoJSON dengan nama file spesifik
@st.cache_data
def load_geojson():
    # Nama file sesuai permintaan: Jawa Timur.geojson
    geojson_path = 'Jawa Timur.geojson'
    
    if os.path.exists(geojson_path):
        with open(geojson_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Coba alternatif tanpa spasi jika user salah save
        alt_path = 'JawaTimur.geojson'
        if os.path.exists(alt_path):
            with open(alt_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

df_scored, df_priority = load_data()
geojson_jatim = load_geojson()

if df_scored is None: st.stop()

# Helper function untuk mencari kolom
def get_col(df, names):
    for name in names:
        if name in df.columns: return name
    return None

# Mapping kolom CSV
col_nama = get_col(df_priority, ['nama_kabupaten_kota', 'Nama Kabupaten/Kota', 'kabupaten', 'region'])
col_score = get_col(df_priority, ['hybrid_risk_score', 'risk_score', 'score'])
col_category = get_col(df_priority, ['risk_category', 'kategori', 'Risk Category'])
col_signature = get_col(df_priority, ['signature_type', 'signature', 'Signature Type'])
col_justification = get_col(df_priority, ['justification', 'justifikasi', 'Justification'])
col_2024 = get_col(df_priority, ['2024'])
col_2025 = get_col(df_priority, ['2025'])
col_change = get_col(df_priority, ['change_pct', 'change_percentage'])

# Sidebar Filters
st.sidebar.header("⚙️ Filter Global")
if col_category:
    unique_cats = sorted(df_scored[col_category].dropna().unique().tolist())
    filters_cat = st.sidebar.multiselect("Risk Category:", unique_cats, default=unique_cats)
else: filters_cat = []

if col_signature:
    unique_sigs = sorted(df_scored[col_signature].dropna().unique().tolist())
    filters_sig = st.sidebar.multiselect("Signature Type:", unique_sigs, default=unique_sigs)
else: filters_sig = []

# Apply filters
df_filtered = df_scored.copy()
if filters_cat and col_category: df_filtered = df_filtered[df_filtered[col_category].isin(filters_cat)]
if filters_sig and col_signature: df_filtered = df_filtered[df_filtered[col_signature].isin(filters_sig)]

# Metrics Utama
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Total Wilayah", len(df_filtered))
with c2: 
    anomaly_count = (df_filtered[col_signature] != 'Normal').sum() if col_signature else 0
    st.metric("Wilayah Anomali", int(anomaly_count))
with c3: 
    high_risk = (df_filtered[col_category] == 'HIGH').sum() if col_category else 0
    st.metric("High Risk", int(high_risk))
with c4: 
    medium_risk = (df_filtered[col_category] == 'MEDIUM').sum() if col_category else 0
    st.metric("Medium Risk", int(medium_risk))

st.markdown("---")

# ==============================================================================
# 🔍 FITUR 1: PENCARIAN WILAYAH
# ==============================================================================
st.subheader("🔍 Pencarian Status Wilayah")
search_query = st.text_input("Ketik nama Kabupaten/Kota:", placeholder="Contoh: KABUPATEN MALANG", key="manual_search")

if col_nama and search_query:
    hasil_cari = df_scored[df_scored[col_nama].str.contains(search_query, case=False, na=False)]
    if not hasil_cari.empty:
        row_data = hasil_cari.iloc[0]
        nama_wilayah = str(row_data[col_nama])
        score = parse_number(row_data[col_score]) if col_score else 0.0
        cat = str(row_data[col_category]) if col_category else "N/A"
        sig = str(row_data[col_signature]) if col_signature else "N/A"
        just = str(row_data[col_justification]) if col_justification else "Tidak ada justifikasi spesifik."
        
        v2024 = int(parse_number(row_data[col_2024])) if col_2024 else 0
        v2025 = int(parse_number(row_data[col_2025])) if col_2025 else 0
        chg_raw = parse_number(row_data[col_change]) if col_change else 0.0
        chg_formatted = format_percentage(chg_raw)
            
        badge_color = "#ff4b4b" if cat == 'HIGH' else "#ffa421" if cat == 'MEDIUM' else "#00cc96"
        icon = "🚨" if cat == 'HIGH' else "⚠️" if cat == 'MEDIUM' else "✅"
        
        st.markdown(f"""
        <div class="search-result-card">
            <h2 style="color:white; margin-bottom:0;">{icon} {nama_wilayah}</h2>
            <h4 style="color:{badge_color}; margin-top:5px;">{'RISIKO TINGGI' if cat=='HIGH' else 'RISIKO SEDANG' if cat=='MEDIUM' else 'NORMAL'}</h4>
        </div>
        """, unsafe_allow_html=True)
        
        res_col1, res_col2 = st.columns([1, 1])
        with res_col1:
            st.info(f"**Score:** {score:.4f} | **Sig:** {sig}")
            st.write(f"**Analisis:** {just}")
        with res_col2:
            m1, m2, m3 = st.columns(3)
            m1.metric("2024", f"{v2024:,}")
            m2.metric("2025", f"{v2025:,}")
            m3.metric("Δ%", chg_formatted)
    else: st.warning("Wilayah tidak ditemukan.")

st.markdown("---")

# ==============================================================================
# 🌟 FITUR 2: SIMULASI DAMPAK AUDIT
# ==============================================================================
st.subheader("💰 Simulasi Dampak Audit (Cost-Benefit Analysis)")
col_sim1, col_sim2 = st.columns(2)
with col_sim1:
    avg_fraud_amount = st.number_input("Estimasi Rata-rata Fraud per Wilayah (Rp)", min_value=1000000, value=50000000, step=1000000)
with col_sim2:
    cost_per_audit = st.number_input("Biaya Audit per Wilayah (Rp)", min_value=100000, value=5000000, step=100000)

high_risk_df = df_filtered[df_filtered[col_category] == 'HIGH'] if col_category else pd.DataFrame()
num_high_risk = len(high_risk_df)
total_potential_fraud = num_high_risk * avg_fraud_amount
total_audit_cost = num_high_risk * cost_per_audit
net_savings = total_potential_fraud - total_audit_cost

sim_col1, sim_col2, sim_col3 = st.columns(3)
sim_col1.metric("Potensi Kebocoran Terdeteksi", f"Rp {total_potential_fraud:,.0f}")
sim_col2.metric("Biaya Audit Diperlukan", f"Rp {total_audit_cost:,.0f}")
sim_col3.metric("Estimasi Penghematan Bersih", f"Rp {net_savings:,.0f}", delta=f"{num_high_risk} Wilayah High Risk")

st.markdown("---")

# ==============================================================================
# 🌟 FITUR 3: PETA CHOROPLETH JAWA TIMUR (HIGHLIGHT WILAYAH)
# ==============================================================================
st.subheader("🗺️ Peta Sebaran Risiko Jawa Timur")
st.caption("Merah = High Risk, Kuning = Medium Risk, Hijau = Low Risk")

if geojson_jatim and col_nama and col_category:
    # Siapkan data untuk choropleth
    map_data = df_filtered[[col_nama, col_category]].copy()
    
    # Buat kolom warna numerik untuk choropleth (0: Low, 1: Medium, 2: High)
    color_map_num = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
    map_data['color_val'] = map_data[col_category].map(color_map_num)
    
    # Deteksi otomatis properti nama di GeoJSON
    # Kita cek fitur pertama untuk melihat kunci apa yang menyimpan nama wilayah
    feature_id_key = "properties.name" # Default
    if 'features' in geojson_jatim and len(geojson_jatim['features']) > 0:
        props = geojson_jatim['features'][0]['properties']
        # Cari kunci yang mirip dengan nama
        possible_keys = ['name', 'NAME_2', 'KABKOTA', 'Kabupaten_Kota', 'Nama']
        for key in possible_keys:
            if key in props:
                feature_id_key = f"properties.{key}"
                break
    
    try:
        fig_map = px.choropleth_mapbox(
            map_data,
            geojson=geojson_jatim,
            locations=col_nama,       # Kolom nama di DataFrame
            featureidkey=feature_id_key, # Properti nama di GeoJSON (otomatis terdeteksi)
            color='color_val',
            color_continuous_scale=["#00cc96", "#ffa421", "#ff4b4b"], # Hijau -> Kuning -> Merah
            range_color=(0, 2),
            mapbox_style="carto-positron",
            zoom=7,
            center={"lat": -7.5, "lon": 112.5},
            opacity=0.7,
            labels={'color_val':'Risk Level'}
        )
        
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
        
    except Exception as e:
        st.error(f"⚠️ Gagal menampilkan peta. Pastikan nama kolom '{col_nama}' di CSV cocok dengan properti '{feature_id_key}' di GeoJSON. Error: {e}")

elif not geojson_jatim:
    st.warning("⚠️ File `Jawa Timur.geojson` tidak ditemukan di folder root. Peta tidak dapat ditampilkan.")
else:
    st.info("ℹ️ Data tidak lengkap untuk menampilkan peta.")

st.markdown("---")

# ==============================================================================
# VISUALISASI DATA LAINNYA
# ==============================================================================
st.subheader("📊 Visualisasi Data")
col1, col2 = st.columns(2)
with col1:
    if col_score:
        fig_hist = px.histogram(df_filtered, x=col_score, nbins=20, title="Distribusi Skor Risiko", color_discrete_sequence=['#1f77b4'])
        fig_hist.add_vline(x=0.6, line_dash="dash", line_color="red")
        st.plotly_chart(fig_hist, use_container_width=True)
with col2:
    if col_signature:
        sig_counts = df_filtered[col_signature].value_counts()
        fig_pie = px.pie(values=sig_counts.values, names=sig_counts.index, title="Distribusi Tipe Signature", hole=0.3)
        st.plotly_chart(fig_pie, use_container_width=True)

# Scatter Plot
st.subheader("📈 Perbandingan 2024 vs 2025")
if col_2024 and col_2025:
    fig_scatter = px.scatter(df_filtered, x=col_2024, y=col_2025, color=col_score, hover_data=[col_nama], title="Perubahan Jumlah Penerima Bansos", labels={col_2024: 'Penerima 2024', col_2025: 'Penerima 2025'}, color_continuous_scale='RdYlGn_r')
    max_val = max(parse_number(df_filtered[col_2024].max()), parse_number(df_filtered[col_2025].max()))
    fig_scatter.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val, line=dict(color="red", dash="dash"))
    st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

# ==============================================================================
# TOP 10 PRIORITAS AUDIT
# ==============================================================================
st.subheader("🔴 TOP 10 Prioritas Audit")
if col_score:
    top10 = df_priority.nlargest(10, col_score)
else: top10 = df_priority.head(10)

for i, (_, row) in enumerate(top10.iterrows()):
    nama = str(row[col_nama]).split(';')[0].strip() if col_nama else f"Wilayah {i+1}"
    score = parse_number(row[col_score]) if col_score else 0.0
    cat = str(row[col_category]) if col_category else "N/A"
    sig = str(row[col_signature]) if col_signature else "N/A"
    just = str(row[col_justification]) if col_justification else "N/A"
    
    v2024 = int(parse_number(row[col_2024])) if col_2024 else 0
    v2025 = int(parse_number(row[col_2025])) if col_2025 else 0
    chg_raw = parse_number(row[col_change]) if col_change else 0.0
    chg_formatted = format_percentage(chg_raw)
    
    badge = "🚨 HIGH" if cat == 'HIGH' else "⚠️ MEDIUM" if cat == 'MEDIUM' else "✅ LOW"
    
    with st.expander(f"#{i+1} - {nama} | Score: {score:.2f} | {badge}"):
        c_left, c_right = st.columns(2)
        with c_left:
            st.write(f"**Signature:** {sig}")
            st.info(f"**Justifikasi:** {just}")
        with c_right:
            st.metric("2024", f"{v2024:,}")
            st.metric("2025", f"{v2025:,}")
            st.metric("Δ%", chg_formatted)

st.markdown("---")
st.markdown("**Research Project | Data Science - Telkom University**")
st.markdown("**Student:** Athaya Alfarabi Asmino (1206230018)")