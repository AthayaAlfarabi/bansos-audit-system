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
        # Jika sudah float/int
        return float(value)
    except (ValueError, TypeError):
        try:
            # Jika string dengan format Indonesia (titik sebagai pemisah ribuan)
            clean_value = str(value).replace('.', '')
            # Handle jika ada koma sebagai desimal
            clean_value = clean_value.replace(',', '.')
            return float(clean_value)
        except:
            return 0.0

# Load data dengan error handling
@st.cache_data
def load_data():
    try:
        # Load scored data
        df_scored = pd.read_csv('data/processed/bansos_scored.csv')
        
        # Load recommendation data dengan delimiter yang tepat
        try:
            df_priority = pd.read_csv('data/processed/recommendation_report.csv', sep=';')
        except:
            try:
                df_priority = pd.read_csv('data/processed/recommendation_report.csv')
            except:
                df_priority = df_scored.copy()
                st.warning("⚠️ Menggunakan data scored sebagai fallback")
        
        return df_scored, df_priority
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return None, None

df_scored, df_priority = load_data()

if df_scored is None:
    st.error("❌ Data tidak ditemukan. Pastikan file CSV ada di folder data/processed/")
    st.info("💡 Jalankan semua script preprocessing dan modeling terlebih dahulu!")
    st.stop()

# Helper function untuk mencari kolom
def get_col(df, names):
    """Mencari kolom dengan mencoba beberapa kemungkinan nama"""
    for name in names:
        if name in df.columns:
            return name
    return None

# Mapping kolom
col_nama = get_col(df_priority, ['nama_kabupaten_kota', 'Nama Kabupaten/Kota', 'kabupaten', 'region'])
col_score = get_col(df_priority, ['hybrid_risk_score', 'risk_score', 'score', 'Hybrid Risk Score'])
col_category = get_col(df_priority, ['risk_category', 'kategori', 'Risk Category', 'Kategori'])
col_signature = get_col(df_priority, ['signature_type', 'signature', 'Signature Type', 'Signature'])
col_justification = get_col(df_priority, ['justification', 'justifikasi', 'Justification', 'Justifikasi'])
col_2024 = get_col(df_priority, ['2024'])
col_2025 = get_col(df_priority, ['2025'])
col_change = get_col(df_priority, ['change_pct', 'change_percentage', 'Change %'])

# Sidebar
st.sidebar.header("⚙️ Filter")

# Risk Category filter
if col_category:
    unique_cats = sorted(df_scored[col_category].dropna().unique().tolist())
    filters_cat = st.sidebar.multiselect(
        "Risk Category:", 
        unique_cats,
        default=unique_cats
    )
else:
    filters_cat = []

# Signature Type filter
if col_signature:
    unique_sigs = sorted(df_scored[col_signature].dropna().unique().tolist())
    filters_sig = st.sidebar.multiselect(
        "Signature Type:",
        unique_sigs,
        default=unique_sigs
    )
else:
    filters_sig = []

# Apply filters
df_filtered = df_scored.copy()
if filters_cat and col_category:
    df_filtered = df_filtered[df_filtered[col_category].isin(filters_cat)]
if filters_sig and col_signature:
    df_filtered = df_filtered[df_filtered[col_signature].isin(filters_sig)]

# Metrics
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Total Wilayah", len(df_filtered))

with c2:
    if col_signature:
        anomaly_count = (df_filtered[col_signature] != 'Normal').sum()
    else:
        anomaly_count = 0
    st.metric("Wilayah Anomali", int(anomaly_count))

with c3:
    if col_category:
        high_risk = (df_filtered[col_category] == 'HIGH').sum()
    else:
        high_risk = 0
    st.metric("High Risk", int(high_risk))

with c4:
    if col_category:
        medium_risk = (df_filtered[col_category] == 'MEDIUM').sum()
    else:
        medium_risk = 0
    st.metric("Medium Risk", int(medium_risk))

st.markdown("---")

# TOP 10 Prioritas Audit
st.subheader("🔴 TOP 10 Prioritas Audit")

if col_score:
    top10 = df_priority.nlargest(10, col_score)
else:
    top10 = df_priority.head(10)

for i, (_, row) in enumerate(top10.iterrows()):
    # Extract data dengan parse_number untuk handle format angka
    nama = str(row[col_nama]) if col_nama else f"Wilayah {i+1}"
    nama = nama.split(';')[0].strip()
    
    score = parse_number(row[col_score]) if col_score else 0.0
    cat = str(row[col_category]) if col_category else "N/A"
    sig = str(row[col_signature]) if col_signature else "N/A"
    just = str(row[col_justification]) if col_justification else "Tidak ada justifikasi"
    
    # Parse angka untuk 2024 dan 2025
    v2024 = int(parse_number(row[col_2024])) if col_2024 else 0
    v2025 = int(parse_number(row[col_2025])) if col_2025 else 0
    chg = parse_number(row[col_change]) if col_change else 0.0
    
    # Badge
    if cat == 'HIGH':
        badge = "🚨 HIGH"
    elif cat == 'MEDIUM':
        badge = "⚠️ MEDIUM"
    else:
        badge = "✅ LOW"
    
    # Expander
    with st.expander(f"#{i+1} - {nama} | Score: {score:.2f} | {badge}"):
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown(f"**🔍 Signature:** {sig}")
            st.info(f"**💡 Justifikasi:** {just}")
            
            if cat == 'HIGH':
                st.error("🔴 Audit Sangat Disarankan")
            elif cat == 'MEDIUM':
                st.warning("🟡 Perlu Pemantauan")
            else:
                st.success("✅ Risiko Rendah")
        
        with col_right:
            st.metric("Penerima 2024", f"{v2024:,}")
            st.metric("Penerima 2025", f"{v2025:,}")
            
            # Delta untuk perubahan
            if chg > 0:
                delta_text = f"{chg:.1f}%"
                st.metric("Perubahan (%)", delta_text, delta=f"+{chg:.1f}%")
            else:
                delta_text = f"{chg:.1f}%"
                st.metric("Perubahan (%)", delta_text, delta=f"{chg:.1f}%")
            
            st.divider()
            st.write(f"**Risk Score:** {score:.4f}")
            
            # Breakdown skor jika ada
            if 'rule_score' in row.index:
                rule_s = parse_number(row['rule_score'])
                st.caption(f"Rule Score: {rule_s:.2f}")
            if 'stat_score' in row.index:
                stat_s = parse_number(row['stat_score'])
                st.caption(f"Stat Score: {stat_s:.2f}")

st.markdown("---")

# Visualizations
st.subheader("📊 Visualisasi Data")

col1, col2 = st.columns(2)

with col1:
    if col_score:
        fig_hist = px.histogram(
            df_filtered, 
            x=col_score,
            nbins=20,
            title="Distribusi Skor Risiko",
            labels={col_score: 'Hybrid Risk Score', 'count': 'Frekuensi'},
            color_discrete_sequence=['#1f77b4']
        )
        fig_hist.add_vline(x=0.6, line_dash="dash", line_color="red", 
                          annotation_text="High Risk (0.6)")
        fig_hist.add_vline(x=0.3, line_dash="dash", line_color="orange", 
                          annotation_text="Medium Risk (0.3)")
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.warning("⚠️ Kolom skor tidak ditemukan")

with col2:
    if col_signature:
        sig_counts = df_filtered[col_signature].value_counts()
        fig_pie = px.pie(
            values=sig_counts.values,
            names=sig_counts.index,
            title="Distribusi Tipe Signature",
            hole=0.3
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("⚠️ Kolom signature tidak ditemukan")

# Scatter plot - PERBAIKAN DI SINI
st.subheader("📈 Perbandingan 2024 vs 2025")

if col_2024 and col_2025:
    fig_scatter = px.scatter(
        df_filtered,
        x=col_2024,
        y=col_2025,
        color=col_score if col_score else None,
        hover_data=[col_nama] if col_nama else [],
        title="Perubahan Jumlah Penerima Bansos (Garis Merah = Tidak Ada Perubahan)",
        labels={col_2024: 'Penerima 2024', col_2025: 'Penerima 2025'},
        color_continuous_scale='RdYlGn_r' if col_score else None,
        size='population' if 'population' in df_filtered.columns else None
    )
    
    # Hitung max value untuk garis diagonal
    max_2024 = parse_number(df_filtered[col_2024].max())
    max_2025 = parse_number(df_filtered[col_2025].max())
    max_val = max(max_2024, max_2025)
    
    # Tambahkan garis diagonal (TANPA annotation yang menyebabkan error)
    fig_scatter.add_shape(
        type="line",
        x0=0, y0=0, x1=max_val, y1=max_val,
        line=dict(color="red", dash="dash", width=2),
    )
    
    # Tambahkan annotation dengan cara yang BENAR (terpisah dari add_shape)
    fig_scatter.add_annotation(
        x=max_val * 0.95,
        y=max_val * 0.95,
        text="Tidak Ada Perubahan",
        showarrow=False,
        font=dict(color="red", size=12),
        xref="x",
        yref="y"
    )
    
    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.warning("⚠️ Data tahun tidak tersedia")

# Download section
st.markdown("---")
st.subheader("📥 Export Data")

col_d1, col_d2, col_d3 = st.columns(3)

with col_d1:
    st.download_button(
        label="📊 Download Scored Data",
        data=df_scored.to_csv(index=False).encode('utf-8'),
        file_name='bansos_scored_data.csv',
        mime='text/csv'
    )

with col_d2:
    st.download_button(
        label="🎯 Download Priority List",
        data=df_priority.to_csv(index=False).encode('utf-8'),
        file_name='audit_priority_list.csv',
        mime='text/csv'
    )

with col_d3:
    st.download_button(
        label="📋 Download Filtered Data",
        data=df_filtered.to_csv(index=False).encode('utf-8'),
        file_name='filtered_analysis.csv',
        mime='text/csv'
    )

# Footer
st.markdown("---")
st.markdown("**Research Project | Data Science - Telkom University**")
st.markdown("**Supervisors:** Bu Amalia Nur Alifah & Pak Ahmad Wali Satria Bahari Johan")
st.markdown("**Student:** Athaya Alfarabi Asmino (1206230018)")