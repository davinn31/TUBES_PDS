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

# --- CSS CUSTOM (DIPERBAIKI AGAR TEKS TIDAK KEPOTONG) ---
st.markdown("""
    <style>
    /* Metric Cards */
    [data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        color: #000000;
    }
    [data-testid="stMetricLabel"] {
        font-size: 14px;
        color: #495057 !important; 
    }
    
    /* PERBAIKAN DI SINI: Font Value Diperkecil jadi 20px */
    [data-testid="stMetricValue"] {
        font-size: 20px; /* <-- Ukuran pas agar "Negeri | Swasta" tidak kepotong */
        font-weight: bold;
        color: #212529 !important;
    }
    
    [data-testid="stMetricDelta"] {
        color: #495057 !important;
    }
    
    /* Loading Status Container Styling */
    .stStatusWidget {
        border-radius: 10px;
        border: 1px solid #e0e0e0;
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
    
    # --- UI LOADING ---
    with st.status("🚀 Sedang memuat sistem zonasi...", expanded=True) as status:
        st.write("📂 Menghubungkan ke database sekolah...")
        time.sleep(0.8) 
        
        st.write("🧹 Membersihkan data duplikat & normalisasi...")
        df = load_data() 
        
        if df is not None:
            st.write(f"✅ Berhasil memuat {len(df):,} data sekolah aktif.")
        
        time.sleep(0.5) 
        st.write("🗺️ Menyiapkan peta interaktif...")
        status.update(label="Sistem Siap Digunakan!", state="complete", expanded=False)
    
    if df is None:
        st.error("⚠️ File 'data_sekolah_jabar_final.csv' belum ditemukan.")
        st.stop()

    # --- SESSION STATE ---
    if 'lokasi_rumah' not in st.session_state:
        st.session_state['lokasi_rumah'] = None

    # --- SIDEBAR ---
    st.sidebar.header("🎛️ Panel Kontrol")

    with st.sidebar.form("filter_form"):
    st.subheader("🏠 Mode Zonasi")
    aktifkan_zonasi = st.sidebar.checkbox("Aktifkan Pilih Lokasi Rumah", value=False)

    
    radius_km = 0 
    if aktifkan_zonasi:
        st.sidebar.info("👉 Klik di Peta untuk menentukan lokasi rumah Anda.")
        radius_km = st.sidebar.slider("Radius Zonasi (KM):", 1, 15, 3)
        if st.sidebar.button("Reset Lokasi Rumah"):
            st.session_state['lokasi_rumah'] = None
            st.rerun()

    st.sidebar.divider()
    
    st.sidebar.subheader("Filter Data")
    filter_jenjang = st.sidebar.multiselect("Jenjang:", df['JENJANG'].unique(), default=df['JENJANG'].unique())
    opsi_akreditasi = sorted(df['AKREDITASI_CLEAN'].unique())
    filter_akreditasi = st.sidebar.multiselect("Akreditasi:", opsi_akreditasi, default=opsi_akreditasi)
    filter_kota = st.sidebar.multiselect("Kab/Kota:", sorted(df['KABUPATEN'].unique().astype(str)), default=[])

    # TOMBOL Terapkan Filter
    submitted = st.form_submit_button("Terapkan Filter")
    
    # --- INFO TAMBAHAN DI SIDEBAR ---
    st.sidebar.markdown("---")
    with st.sidebar.expander("ℹ️ Tentang Aplikasi"):
        st.markdown("""
        **Panduan Pengguna:**
        1. **Filter:** Gunakan menu di atas untuk memilah jenjang/akreditasi.
        2. **Zonasi:** Centang **'Aktifkan Pilih Lokasi Rumah'**, atur radius, lalu klik lokasi rumah di peta.
        3. **Reset:** Tekan tombol Reset jika ingin menghapus titik rumah.
        
        **Catatan Teknis:**
        - **Skor Kualitas:** Dihitung dari bobot Akreditasi (A=100, B=75, C=50).
        - **Jarak:** Menggunakan rumus *Haversine* (garis lurus/euclidean).
        """)
        st.caption("Developed by Kelompok 5 PDS IF 6")

    # --- LOGIKA FILTERING ---
    df_filtered = df[df['JENJANG'].isin(filter_jenjang)]
    df_filtered = df_filtered[df_filtered['AKREDITASI_CLEAN'].isin(filter_akreditasi)]
    if filter_kota:
        df_filtered = df_filtered[df_filtered['KABUPATEN'].isin(filter_kota)]

    # --- LOGIKA JARAK ---
    jarak_msg = ""
    if aktifkan_zonasi and st.session_state['lokasi_rumah']:
        user_lat = st.session_state['lokasi_rumah'][0]
        user_lon = st.session_state['lokasi_rumah'][1]
        
        df_filtered['JARAK_KM'] = df_filtered.apply(
            lambda row: haversine(user_lon, user_lat, row['BUJUR'], row['LINTANG']), axis=1
        )
        
        df_filtered = df_filtered[df_filtered['JARAK_KM'] <= radius_km].copy()
        df_filtered = df_filtered.sort_values('JARAK_KM')
        
        jarak_msg = f"📍 Menampilkan **{len(df_filtered)}** sekolah dalam radius **{radius_km} KM** dari titik rumah."

    # --- KPI METRICS ---
    st.markdown("### 📊 Ringkasan Statistik")
    if jarak_msg:
        st.toast(jarak_msg, icon='📍') 
        st.success(jarak_msg) 
        
    # PERBAIKAN DI SINI: Kolom ke-4 dibuat lebih lebar (1.5x) agar muat
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1.5])
    
    total = len(df_filtered)
    jml_a = len(df_filtered[df_filtered['AKREDITASI_CLEAN'] == 'A'])
    persen_a = (jml_a / total * 100) if total > 0 else 0
    avg_q = df_filtered['SKOR_KUALITAS'].mean() if total > 0 else 0 
    
    col1.metric("Total Sekolah", f"{total:,}")
    col2.metric("Akreditasi A", f"{jml_a} ({persen_a:.1f}%)")
    col3.metric("Rata-rata Skor", f"{avg_q:.1f}")
    
    if 'STATUS' in df_filtered.columns:
        negeri = len(df_filtered[df_filtered['STATUS'] == 'NEGERI'])
        swasta = total - negeri
        col4.metric("Status", f"{negeri} Negeri | {swasta} Swasta")

    st.divider()

    # --- PETA & CHART ---
    col_map, col_chart = st.columns([2, 1])

    with col_map:
        st.subheader("Interactive Map")
        
        if aktifkan_zonasi and st.session_state['lokasi_rumah']:
             center_lat, center_lon = st.session_state['lokasi_rumah']
             zoom = 13 
        elif not df_filtered.empty:
            center_lat, center_lon = df_filtered['LINTANG'].mean(), df_filtered['BUJUR'].mean()
            zoom = 10 if filter_kota else 9
        else:
            center_lat, center_lon = -6.9175, 107.6191
            zoom = 9

        m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles="CartoDB positron")
        Fullscreen().add_to(m)

        if aktifkan_zonasi and st.session_state['lokasi_rumah']:
            folium.Marker(
                location=st.session_state['lokasi_rumah'],
                tooltip="Lokasi Rumah Anda",
                icon=folium.Icon(color="black", icon="home", prefix="fa")
            ).add_to(m)
            
            folium.Circle(
                location=st.session_state['lokasi_rumah'],
                radius=radius_km * 1000, 
                color="blue", fill=True, fill_opacity=0.1
            ).add_to(m)

        marker_cluster = MarkerCluster().add_to(m)
        for _, row in df_filtered.iterrows():
            info_jarak = f"<br><b>Jarak:</b> {row['JARAK_KM']:.2f} KM" if 'JARAK_KM' in row else ""
            
            html = f"""
            <div style="font-family:sans-serif; width:200px">
                <h4 style="margin-bottom:0;">{row['NAMA SEKOLAH']}</h4>
                <span style="font-size:12px; color:gray;">{row['JENJANG']} | {row.get('STATUS','-')}</span>
                <hr style="margin:5px 0;">
                <b>Akreditasi:</b> {row['AKREDITASI_CLEAN']}<br>
                <b>Skor:</b> {row['SKOR_KUALITAS']}{info_jarak}
            </div>
            """
            folium.Marker(
                [row['LINTANG'], row['BUJUR']],
                popup=folium.Popup(html, max_width=250),
                tooltip=f"{row['NAMA SEKOLAH']}",
                icon=folium.Icon(color=get_color(row['AKREDITASI_CLEAN']), icon="graduation-cap", prefix="fa")
            ).add_to(marker_cluster)

        map_output = st_folium(m, height=550, use_container_width=True)

        if aktifkan_zonasi:
            if map_output['last_clicked']:
                clicked_lat = map_output['last_clicked']['lat']
                clicked_lng = map_output['last_clicked']['lng']
                
                if st.session_state['lokasi_rumah'] != [clicked_lat, clicked_lng]:
                    st.session_state['lokasi_rumah'] = [clicked_lat, clicked_lng]
                    st.rerun() 

    with col_chart:
        st.subheader("📈 Analisis Data")
        if not df_filtered.empty:
            chart_akreditasi = alt.Chart(df_filtered).mark_arc(innerRadius=50).encode(
                theta=alt.Theta("count()", stack=True),
                color=alt.Color('AKREDITASI_CLEAN', legend=alt.Legend(title="Akreditasi"),
                                scale=alt.Scale(domain=['A', 'B', 'C', 'TT'], range=['green', 'blue', 'orange', 'red'])),
                tooltip=[
                    alt.Tooltip('AKREDITASI_CLEAN', title='Akreditasi'),
                    alt.Tooltip('count()', title='Jumlah Sekolah') 
                ],
                order=alt.Order("AKREDITASI_CLEAN", sort="ascending")
            ).properties(title="Proporsi Sekolah (Area Terpilih)")
            
            st.altair_chart(chart_akreditasi, use_container_width=True)

            if 'KECAMATAN' in df_filtered.columns:
                top_kec = df_filtered['KECAMATAN'].value_counts().head(10).reset_index()
                top_kec.columns = ['Kecamatan', 'Jumlah']
                
                chart_kec = alt.Chart(top_kec).mark_bar().encode(
                    x=alt.X('Jumlah', title='Jumlah Sekolah'), 
                    y=alt.Y('Kecamatan', sort='-x', title=''),
                    tooltip=['Kecamatan', alt.Tooltip('Jumlah', title='Jumlah Sekolah')]
                ).properties(title="Top 10 Kecamatan")
                st.altair_chart(chart_kec, use_container_width=True)
        else:
            st.info("Belum ada sekolah dalam radius ini. Coba geser peta atau perbesar radius.")

    # --- TABEL DATA ---
    with st.expander("📂 Lihat Data Detail"):
        kolom_buang = ['Unnamed: 0', 'BENTUK PENDIDIKAN', 'WAKTU PENYELENGGARAAN', 
                       'AKREDITASI_CLEAN', 'BENTUK', 'NAMA DUSUN']
        
        df_tampil = df_filtered.drop(columns=kolom_buang, errors='ignore').copy()
        
        cols = list(df_tampil.columns)
        if 'JENJANG' in cols and 'NPSN' in cols:
            cols.remove('JENJANG')
            idx_npsn = cols.index('NPSN')
            cols.insert(idx_npsn + 1, 'JENJANG')
            df_tampil = df_tampil[cols]

        if 'KODE POS' in df_tampil.columns:
            df_tampil['KODE POS'] = df_tampil['KODE POS'].astype(str).str.replace(r'\.0$', '', regex=True).replace({'nan': '-', 'NaN': '-'})

        df_tampil = df_tampil.reset_index(drop=True)
        df_tampil.index = df_tampil.index + 1
        
        st.dataframe(df_tampil, use_container_width=True)

if __name__ == "__main__":
    main()
