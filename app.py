import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Sistem Rekomendasi Prioritas Audit Bansos",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stExpander {
        border: 1px solid #333;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    /* Style untuk Card Hasil Pencarian */
    .search-result-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #444;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🎯 Sistem Rekomendasi Prioritas Audit Penyaluran Bantuan Sosial")
st.markdown("**Jawa Timur 2024-2025** | Hybrid Machine Learning & Signature Analysis")
st.markdown("---")

# Helper function untuk parse angka (handle format Indonesia)
def parse_number(value):
    """Convert string dengan thousand separator ke float"""
    if pd.isna(value) or value == '' or value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        try:
            clean_value = str(value).replace('.', '')
            clean_value = clean_value.replace(',', '.')
            return float(clean_value)
        except:
            return 0.0

# Load data
@st.cache_data
def load_data():
    try:
        df_scored = pd.read_csv('data/processed/bansos_scored.csv')
        try:
            df_priority = pd.read_csv('data/processed/recommendation_report.csv', sep=';')
        except:
            try:
                df_priority = pd.read_csv('data/processed/recommendation_report.csv')
            except:
                df_priority = df_scored.copy()
        return df_scored, df_priority
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return None, None

df_scored, df_priority = load_data()

if df_scored is None:
    st.stop()

# Helper function untuk mencari kolom
def get_col(df, names):
    for name in names:
        if name in df.columns:
            return name
    return None

# Mapping kolom
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
else:
    filters_cat = []

if col_signature:
    unique_sigs = sorted(df_scored[col_signature].dropna().unique().tolist())
    filters_sig = st.sidebar.multiselect("Signature Type:", unique_sigs, default=unique_sigs)
else:
    filters_sig = []

# Apply filters to main dataframe
df_filtered = df_scored.copy()
if filters_cat and col_category:
    df_filtered = df_filtered[df_filtered[col_category].isin(filters_cat)]
if filters_sig and col_signature:
    df_filtered = df_filtered[df_filtered[col_signature].isin(filters_sig)]

# Metrics
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
# 🔍 FITUR BARU: PENCARIAN WILAYAH (DITAMBAHKAN DI SINI)
# ==============================================================================
st.subheader("🔍 Pencarian Status Wilayah")

# Buat list unik nama wilayah untuk autocomplete
if col_nama:
    list_wilayah = sorted(df_scored[col_nama].unique().tolist())
    
    # Input pencarian
    search_query = st.text_input(
        "Ketik nama Kabupaten/Kota:", 
        placeholder="Contoh: KABUPATEN MALANG",
        help="Masukkan nama wilayah untuk melihat detail status auditnya."
    )
    
    # Jika ada input, cari datanya
    if search_query:
        # Filter case-insensitive
        hasil_cari = df_scored[df_scored[col_nama].str.contains(search_query, case=False, na=False)]
        
        if not hasil_cari.empty:
            # Ambil baris pertama jika ada lebih dari 1 hasil (biasanya karena duplikasi tahun)
            row_data = hasil_cari.iloc[0]
            
            # Ekstrak data
            nama_wilayah = str(row_data[col_nama])
            score = parse_number(row_data[col_score]) if col_score else 0.0
            cat = str(row_data[col_category]) if col_category else "N/A"
            sig = str(row_data[col_signature]) if col_signature else "N/A"
            just = str(row_data[col_justification]) if col_justification else "Tidak ada justifikasi spesifik."
            
            v2024 = int(parse_number(row_data[col_2024])) if col_2024 else 0
            v2025 = int(parse_number(row_data[col_2025])) if col_2025 else 0
            chg = parse_number(row_data[col_change]) if col_change else 0.0
            
            # Tentukan warna badge
            if cat == 'HIGH':
                badge_color = "#ff4b4b" # Merah
                icon = "🚨"
                status_text = "RISIKO TINGGI - PERLU AUDIT SEGERA"
            elif cat == 'MEDIUM':
                badge_color = "#ffa421" # Kuning/Oranye
                icon = "⚠️"
                status_text = "RISIKO SEDANG - PERLU PEMANTAUAN"
            else:
                badge_color = "#00cc96" # Hijau
                icon = "✅"
                status_text = "RISIKO RENDAH - NORMAL"

            # Tampilkan Hasil dalam Card yang Rapi
            st.markdown(f"""
            <div class="search-result-card">
                <h2 style="color:white; margin-bottom:0;">{icon} {nama_wilayah}</h2>
                <h4 style="color:{badge_color}; margin-top:5px;">{status_text}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Layout 2 Kolom untuk Detail
            res_col1, res_col2 = st.columns([1, 1])
            
            with res_col1:
                st.markdown("### 📊 Detail Risiko")
                st.info(f"**Hybrid Risk Score:** {score:.4f}")
                st.write(f"**Kategori:** {cat}")
                st.write(f"**Signature Fraud:** {sig}")
                st.markdown(f"**💡 Analisis AI:**<br>{just}", unsafe_allow_html=True)
                
            with res_col2:
                st.markdown("### 📈 Data Statistik")
                m1, m2, m3 = st.columns(3)
                m1.metric("Penerima 2024", f"{v2024:,}")
                m2.metric("Penerima 2025", f"{v2025:,}")
                m3.metric("Perubahan (%)", f"{chg:.1f}%")
                
                st.divider()
                st.caption("Data terakhir diperbarui: Periode 2024-2025")
                
        else:
            st.warning(f"Wilayah dengan kata kunci '{search_query}' tidak ditemukan.")

st.markdown("---")

# ==============================================================================
# TOP 10 PRIORITAS AUDIT (TIDAK DIUBAH)
# ==============================================================================
st.subheader("🔴 TOP 10 Prioritas Audit")

if col_score:
    top10 = df_priority.nlargest(10, col_score)
else:
    top10 = df_priority.head(10)

for i, (_, row) in enumerate(top10.iterrows()):
    nama = str(row[col_nama]) if col_nama else f"Wilayah {i+1}"
    nama = nama.split(';')[0].strip()
    
    score = parse_number(row[col_score]) if col_score else 0.0
    cat = str(row[col_category]) if col_category else "N/A"
    sig = str(row[col_signature]) if col_signature else "N/A"
    just = str(row[col_justification]) if col_justification else "Tidak ada justifikasi"
    
    v2024 = int(parse_number(row[col_2024])) if col_2024 else 0
    v2025 = int(parse_number(row[col_2025])) if col_2025 else 0
    chg = parse_number(row[col_change]) if col_change else 0.0
    
    badge = "🚨 HIGH" if cat == 'HIGH' else "⚠️ MEDIUM" if cat == 'MEDIUM' else "✅ LOW"
    
    with st.expander(f"#{i+1} - {nama} | Score: {score:.2f} | {badge}"):
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown(f"**🔍 Signature:** {sig}")
            st.info(f"**💡 Justifikasi:** {just}")
            if cat == 'HIGH': st.error("🔴 Audit Sangat Disarankan")
            elif cat == 'MEDIUM': st.warning("🟡 Perlu Pemantauan")
        with col_right:
            st.metric("Penerima 2024", f"{v2024:,}")
            st.metric("Penerima 2025", f"{v2025:,}")
            st.metric("Perubahan (%)", f"{chg:.1f}%")
            st.divider()
            st.write(f"**Risk Score:** {score:.4f}")

st.markdown("---")

# Visualizations (Histogram & Pie Chart) - TIDAK DIUBAH
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

# Scatter Plot - TIDAK DIUBAH
st.subheader("📈 Perbandingan 2024 vs 2025")
if col_2024 and col_2025:
    fig_scatter = px.scatter(df_filtered, x=col_2024, y=col_2025, color=col_score, hover_data=[col_nama], title="Perubahan Jumlah Penerima Bansos", labels={col_2024: 'Penerima 2024', col_2025: 'Penerima 2025'}, color_continuous_scale='RdYlGn_r')
    max_val = max(parse_number(df_filtered[col_2024].max()), parse_number(df_filtered[col_2025].max()))
    fig_scatter.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val, line=dict(color="red", dash="dash"))
    st.plotly_chart(fig_scatter, use_container_width=True)

# Footer - TIDAK DIUBAH
st.markdown("---")
st.markdown("**Research Project | Data Science - Telkom University**")
st.markdown("**Student:** Athaya Alfarabi Asmino (1206230018)")