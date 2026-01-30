import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap, Fullscreen
import altair as alt
from geopy.distance import geodesic
from streamlit_geolocation import streamlit_geolocation

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Analisis Zonasi PPDB Jabar",
    page_icon="🎓",
    layout="wide"
)

# --- CSS CUSTOM UNTUK TAMPILAN PROFESIONAL ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #000;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI LOAD DATA ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data_sekolah_jabar_final.csv")
        return df
    except FileNotFoundError:
        return None

# --- UTILS VISUAL ---
def get_color(akreditasi):
    if akreditasi == 'A': return 'green'
    elif akreditasi == 'B': return 'blue'
    elif akreditasi == 'C': return 'orange'
    else: return 'red'

# --- FUNGSI REKOMENDASI ---
def get_recommendations(user_lat, user_lon, df, radius_km=2.0):
    df_rec = df.copy()
    df_rec['JARAK_KM'] = df_rec.apply(
        lambda row: geodesic((user_lat, user_lon), (row['LINTANG'], row['BUJUR'])).km, axis=1
    )
    
    df_zonasi = df_rec[df_rec['JARAK_KM'] <= radius_km].copy()
    
    if df_zonasi.empty:
        return None
    
    df_zonasi['SCORE_FINAL'] = (
        ((1 - (df_zonasi['JARAK_KM'] / radius_km)) * 60) + 
        ((df_zonasi['QUALITY_SCORE'] / 100) * 40)
    )
    
    return df_zonasi.sort_values(by='SCORE_FINAL', ascending=False).head(3)

# --- MAIN APPLICATION ---
def main():
    st.title("🗺️ Dashboard Pemetaan & Kualitas Sekolah Jabar")
    st.markdown("**Penunjang Analisis Zonasi PPDB** | Data Source: Dapodik/Verval SP (Scraped)")
    
    df = load_data()
    
    if df is None:
        st.error("⚠️ File 'data_sekolah_jabar_final.csv' belum ditemukan!")
        st.stop()

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("🎛️ Filter Konfigurasi")
    filter_jenjang = st.sidebar.multiselect("Pilih Jenjang:", options=df['JENJANG'].unique(), default=df['JENJANG'].unique())
    opsi_akreditasi = sorted(df['AKREDITASI_CLEAN'].unique())
    filter_akreditasi = st.sidebar.multiselect("Pilih Akreditasi:", options=opsi_akreditasi, default=opsi_akreditasi)
    filter_kota = st.sidebar.multiselect("Pilih Kab/Kota:", options=sorted(df['KABUPATEN'].unique().astype(str)), default=[])
    
    # --- LOGIKA FILTERING ---
    df_filtered = df[df['JENJANG'].isin(filter_jenjang)]
    df_filtered = df_filtered[df_filtered['AKREDITASI_CLEAN'].isin(filter_akreditasi)]
    if filter_kota:
        df_filtered = df_filtered[df_filtered['KABUPATEN'].isin(filter_kota)]

    # --- KPI METRICS ---
    st.markdown("### 📊 Ringkasan Statistik Area Terpilih")
    col1, col2, col3, col4 = st.columns(4)
    total_sekolah = len(df_filtered)
    sekolah_a = len(df_filtered[df_filtered['AKREDITASI_CLEAN'] == 'A'])
    persen_a = (sekolah_a / total_sekolah * 100) if total_sekolah > 0 else 0
    avg_quality = df_filtered['QUALITY_SCORE'].mean() if total_sekolah > 0 else 0
    
    col1.metric("Total Sekolah", f"{total_sekolah:,}")
    col2.metric("Akreditasi A", f"{sekolah_a} ({persen_a:.1f}%)")
    col3.metric("Rata-rata Kualitas", f"{avg_quality:.1f}/100")
    if 'STATUS' in df_filtered.columns:
        negeri = len(df_filtered[df_filtered['STATUS'] == 'NEGERI'])
        col4.metric("Status Sekolah", f"{negeri} Negeri | {total_sekolah-negeri} Swasta")

    st.divider()

    # --- LAYOUT UTAMA ---
    col_map, col_chart = st.columns([2, 1])

    with col_map:
        st.subheader("📍 Penentuan Lokasi Rumah")
        
        # Penentuan Center dan Zoom (DI SINI AGAR TIDAK ERROR)
        if not df_filtered.empty:
            center_lat, center_lon = df_filtered['LINTANG'].mean(), df_filtered['BUJUR'].mean()
            zoom = 11 if filter_kota else 9
        else:
            center_lat, center_lon, zoom = -6.9175, 107.6191, 9

        # Opsi Lokasi
        mode_lokasi = st.radio("Pilih Cara Penentuan Lokasi:", ["Klik Manual di Peta", "Gunakan GPS Perangkat"], horizontal=True)
        lat_final, lon_final = None, None

        if mode_lokasi == "Gunakan GPS Perangkat":
            st.caption("Klik tombol di bawah untuk melacak lokasi GPS Anda.")
            loc = streamlit_geolocation()
            if loc['latitude']:
                lat_final, lon_final = loc['latitude'], loc['longitude']
                st.success(f"GPS Terdeteksi: `{lat_final:.5f}, {lon_final:.5f}`")
        else:
            st.info("Silakan **klik pada peta** untuk menentukan lokasi rumah Anda.")

        # Inisialisasi Peta
        m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles="CartoDB positron")
        Fullscreen().add_to(m)

        # Mode Tampilan Peta
        view_mode = st.radio("Layer Visualisasi:", ["Cluster", "Heatmap", "Radius Zonasi"], horizontal=True)
        if not df_filtered.empty:
            if view_mode == "Cluster":
                cluster = MarkerCluster().add_to(m)
                for _, r in df_filtered.iterrows():
                    folium.Marker([r['LINTANG'], r['BUJUR']], tooltip=r['NAMA SEKOLAH'], 
                                  icon=folium.Icon(color=get_color(r['AKREDITASI_CLEAN']), icon="graduation-cap", prefix="fa")).add_to(cluster)
            elif view_mode == "Heatmap":
                HeatMap([[r['LINTANG'], r['BUJUR']] for _, r in df_filtered.iterrows()]).add_to(m)
            else:
                for _, r in df_filtered.head(500).iterrows(): # Limit 500 untuk performa
                    folium.Circle([r['LINTANG'], r['BUJUR']], radius=2000, color=get_color(r['AKREDITASI_CLEAN']), fill=True, opacity=0.1).add_to(m)

        # Render Peta & Tangkap Klik
        output = st_folium(m, height=500, use_container_width=True, key="map_jabar")

        if mode_lokasi == "Klik Manual di Peta" and output.get('last_clicked'):
            lat_final, lon_final = output['last_clicked']['lat'], output['last_clicked']['lng']

        # LOGIKA REKOMENDASI
        if lat_final and lon_final:
            rec = get_recommendations(lat_final, lon_final, df_filtered)
            if rec is not None:
                st.markdown("### 🏆 Top 3 Rekomendasi Sekolah")
                c = st.columns(3)
                for i, (_, r) in enumerate(rec.iterrows()):
                    with c[i]:
                        st.markdown(f"""<div style="background-color:white; padding:15px; border-radius:10px; border-left:5px solid {get_color(r['AKREDITASI_CLEAN'])}; box-shadow: 2px 2px 5px rgba(0,0,0,0.1)">
                            <h4 style="margin:0; font-size:14px;">{r['NAMA SEKOLAH']}</h4>
                            <p style="margin:5px 0; font-size:12px;">📏 <b>{r['JARAK_KM']:.2f} km</b> | ⭐ <b>{r['SCORE_FINAL']:.1f}/100</b></p>
                        </div>""", unsafe_allow_html=True)
            else:
                st.warning("Tidak ada sekolah dalam radius 2KM.")

    with col_chart:
        st.subheader("📈 Analisis Data")
        if not df_filtered.empty:
            chart = alt.Chart(df_filtered).mark_arc(innerRadius=50).encode(
                theta="count()", color=alt.Color('AKREDITASI_CLEAN', scale=alt.Scale(domain=['A', 'B', 'C', 'TT'], range=['green', 'blue', 'orange', 'red'])),
                tooltip=['AKREDITASI_CLEAN', 'count()']
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)
            
            if 'KECAMATAN' in df_filtered.columns:
                top_kec = df_filtered['KECAMATAN'].value_counts().head(10).reset_index()
                top_kec.columns = ['Kecamatan', 'Jumlah']
                st.altair_chart(alt.Chart(top_kec).mark_bar().encode(x='Jumlah', y=alt.Y('Kecamatan', sort='-x')), use_container_width=True)

    with st.expander("📂 Lihat Data Mentah"):
        df_tampil = df_filtered.drop(columns=['Unnamed: 0', 'BENTUK PENDIDIKAN', 'BENTUK'], errors='ignore')
        st.dataframe(df_tampil, use_container_width=True)

if __name__ == "__main__":
    main()
    
