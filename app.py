import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap, Fullscreen
import altair as alt
from math import radians, cos, sin, asin, sqrt
import time

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Analisis Zonasi PPDB Jabar",
    page_icon="🎓",
    layout="wide"
)

# --- CSS CUSTOM ---
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        color: #000000;
    }
    [data-testid="stMetricValue"] {
        font-size: 20px;
        font-weight: bold;
        color: #212529 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI JARAK (HAVERSINE) ---
def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 
    return c * r

# --- FUNGSI LOAD DATA ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data_sekolah_jabar_final.csv")
        if 'NAMA DUSUN' in df.columns:
            df = df.drop(columns=['NAMA DUSUN'])
        if 'QUALITY_SCORE' in df.columns:
            df = df.rename(columns={'QUALITY_SCORE': 'SKOR_KUALITAS'})
        return df
    except FileNotFoundError:
        return None

# --- UTILS VISUAL ---
def get_color(akreditasi):
    if akreditasi == 'A': return 'green'
    elif akreditasi == 'B': return 'blue'
    elif akreditasi == 'C': return 'orange'
    else: return 'red' 

# --- MAIN APPLICATION ---
def main():
    st.title("West java Education Insight - Interactive GIS Dashboard")
    st.markdown("**Simulasi Jarak & Kualitas Sekolah** | Data Source: Dapodik/Verval SP")
    
    with st.status("🚀 Sedang memuat sistem zonasi...", expanded=False) as status:
        df = load_data() 
        if df is not None:
            status.update(label="Sistem Siap!", state="complete")
    
    if df is None:
        st.error("⚠️ File data tidak ditemukan.")
        st.stop()

    if 'lokasi_rumah' not in st.session_state:
        st.session_state['lokasi_rumah'] = None

    # --- SIDEBAR (THE FIX) ---
    st.sidebar.header("🎛️ Panel Kontrol")

    # Tombol Reset ditaruh di luar FORM karena aturan Streamlit
    if st.sidebar.button("Reset Lokasi Rumah"):
        st.session_state['lokasi_rumah'] = None
        st.rerun()

    with st.sidebar.form("filter_form"):
        st.subheader("🏠 Mode Zonasi")
        aktifkan_zonasi = st.checkbox("Aktifkan Pilih Lokasi Rumah", value=False)
        radius_km = st.slider("Radius Zonasi (KM):", 1, 15, 3)
        
        st.divider()
        
        st.subheader("Filter Data")
        filter_jenjang = st.multiselect("Jenjang:", df['JENJANG'].unique(), default=df['JENJANG'].unique())
        filter_akreditasi = st.multiselect("Akreditasi:", sorted(df['AKREDITASI_CLEAN'].unique()), default=df['AKREDITASI_CLEAN'].unique())
        filter_kota = st.multiselect("Kab/Kota:", sorted(df['KABUPATEN'].unique().astype(str)), default=[])

        # TOMBOL SUBMIT (Wajib menjorok di dalam form)
        submitted = st.form_submit_button("Terapkan Filter")

    # --- INFO TAMBAHAN ---
    st.sidebar.markdown("---")
    st.sidebar.caption("Developed by Kelompok 5 PDS IF 6")

    # --- LOGIKA FILTERING ---
    df_filtered = df[df['JENJANG'].isin(filter_jenjang)]
    df_filtered = df_filtered[df_filtered['AKREDITASI_CLEAN'].isin(filter_akreditasi)]
    if filter_kota:
        df_filtered = df_filtered[df_filtered['KABUPATEN'].isin(filter_kota)]

    # --- LOGIKA JARAK ---
    jarak_msg = ""
    if aktifkan_zonasi and st.session_state['lokasi_rumah']:
        user_lat, user_lon = st.session_state['lokasi_rumah']
        df_filtered['JARAK_KM'] = df_filtered.apply(
            lambda row: haversine(user_lon, user_lat, row['BUJUR'], row['LINTANG']), axis=1
        )
        df_filtered = df_filtered[df_filtered['JARAK_KM'] <= radius_km].copy()
        df_filtered = df_filtered.sort_values('JARAK_KM')
        jarak_msg = f
