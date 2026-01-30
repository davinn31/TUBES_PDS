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
        # Pastikan file ini adalah hasil generate dari data_loader.py
        df = pd.read_csv("data_sekolah_jabar_final.csv")
        return df
    except FileNotFoundError:
        return None

# --- UTILS VISUAL ---
def get_color(akreditasi):
    if akreditasi == 'A': return 'green'
    elif akreditasi == 'B': return 'blue'
    elif akreditasi == 'C': return 'orange'
    else: return 'red' # Tidak terakreditasi/TT

# --- FUNGSI REKOMENDASI CERDAS ---
def get_recommendations(user_lat, user_lon, df, radius_km=2.0):
    df_rec = df.copy()
    # Hitung jarak lurus presisi
    df_rec['JARAK_KM'] = df_rec.apply(
        lambda row: geodesic((user_lat, user_lon), (row['LINTANG'], row['BUJUR'])).km, axis=1
    )
    
    # Filter hanya yang masuk radius 2KM
    df_zonasi = df_rec[df_rec['JARAK_KM'] <= radius_km].copy()
    if df_zonasi.empty:
        return None
    
    # Inovasi Skor: Jarak (60%) + Kualitas (40%)
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
        st.error("⚠️ File 'data_sekolah_jabar_final.csv' belum ditemukan. Jalankan script 'data_loader.py' terlebih dahulu!")
        st.stop()

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("🎛️ Filter Konfigurasi")
    
    # 1. Filter Jenjang
    filter_jenjang = st.sidebar.multiselect(
        "Pilih Jenjang:", 
        options=df['JENJANG'].unique(), 
        default=df['JENJANG'].unique()
    )

    # 2. Filter Akreditasi
    opsi_akreditasi = sorted(df['AKREDITASI_CLEAN'].unique())
    filter_akreditasi = st.sidebar.multiselect(
        "Pilih Akreditasi:",
        options=opsi_akreditasi,
        default=opsi_akreditasi 
    )
    
    # 3. Filter Kab/Kota
    filter_kota = st.sidebar.multiselect(
        "Pilih Kab/Kota:", 
        options=sorted(df['KABUPATEN'].unique().astype(str)), 
        default=[] 
    )
    
    # --- LOGIKA FILTERING ---
    df_filtered = df[df['JENJANG'].isin(filter_jenjang)]
    df_filtered = df_filtered[df_filtered['AKREDITASI_CLEAN'].isin(filter_akreditasi)]
    
    if filter_kota:
        df_filtered = df_filtered[df_filtered['KABUPATEN'].isin(filter_kota)]

    # --- KPI METRICS (BARIS ATAS) ---
    st.markdown("### 📊 Ringkasan Statistik Area Terpilih")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_sekolah = len(df_filtered)
    sekolah_a = len(df_filtered[df_filtered['AKREDITASI_CLEAN'] == 'A'])
    persen_a = (sekolah_a / total_sekolah * 100) if total_sekolah > 0 else 0
    avg_quality = df_filtered['QUALITY_SCORE'].mean() if total_sekolah > 0 else 0
    
    col1.metric("Total Sekolah Terpilih", f"{total_sekolah:,}")
    col2.metric("Jumlah Akreditasi A", f"{sekolah_a} ({persen_a:.1f}%)")
    col3.metric("Skor Kualitas Rata-rata", f"{avg_quality:.1f}/100")
    
    if 'STATUS' in df_filtered.columns:
        negeri = len(df_filtered[df_filtered['STATUS'] == 'NEGERI'])
        swasta = total_sekolah - negeri
        col4.metric("Status Sekolah", f"{negeri} Negeri | {swasta} Swasta")

    st.divider()

    # --- LAYOUT UTAMA: PETA & CHART ---
    col_map, col_chart = st.columns([2, 1])

    with col_map:
        st.subheader("📍 Penentuan Lokasi & Zonasi")
        
        # --- A. PILIHAN MODE LOKASI ---
        mode_lokasi = st.radio(
            "Metode Penentuan Lokasi Rumah:",
            ["Klik Manual di Peta", "GPS Perangkat (Otomatis)"],
            horizontal=True
        )

        home_lat, home_lon = None, None

        if mode_lokasi == "GPS Perangkat (Otomatis)":
            st.caption("Izinkan akses lokasi di browser untuk menggunakan fitur ini.")
            loc = streamlit_geolocation()
            if loc['latitude']:
                home_lat, home_lon = loc['latitude'], loc['longitude']
                st.success(f"Lokasi GPS Terdeteksi: `{home_lat:.5f}, {home_lon:.5f}`")
        else:
            st.info("Silakan **Klik pada peta** untuk menentukan lokasi rumah Anda.")

        # --- B. SETTING CENTER & ZOOM ---
        if not df_filtered.empty:
            center_lat, center_lon = df_filtered['LINTANG'].mean(), df_filtered['BUJUR'].mean()
            zoom = 11 if filter_kota else 9
        else:
            center_lat, center_lon, zoom = -6.9175, 107.6191, 9

        # --- C. INISIALISASI PETA ---
        m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles="CartoDB positron")
        Fullscreen().add_to(m)

        # Logika View Mode (Cluster/Heatmap/Radius) tetap sama seperti kodemu...
        # [Bagian view_mode kodemu ditaruh di sini]

        # --- D. TAMBAHKAN MARKER RUMAH JIKA ADA ---
        if home_lat and home_lon:
            folium.Marker(
                [home_lat, home_lon], 
                tooltip="Lokasi Rumah Anda", 
                icon=folium.Icon(color='red', icon='home', prefix='fa')
            ).add_to(m)
            folium.Circle([home_lat, home_lon], radius=2000, color='red', fill=True, opacity=0.1).add_to(m)

        # --- E. RENDER PETA & TANGKAP KLIK ---
        # Ganti baris st_folium(m) lamamu dengan ini:
        output = st_folium(m, height=500, use_container_width=True, key="peta_jabar_utama")

        if mode_lokasi == "Klik Manual di Peta" and output.get('last_clicked'):
            home_lat, home_lon = output['last_clicked']['lat'], output['last_clicked']['lng']
            
       
        

        # --- F. TAMPILKAN HASIL REKOMENDASI ---
        if home_lat and home_lon:
            st.markdown("---")
            rekomendasi = get_recommendations(home_lat, home_lon, df_filtered)
            
            if rekomendasi is not None:
                st.subheader("🏆 Top 3 Rekomendasi Sekolah (Radius 2KM)")
                cols_rec = st.columns(3)
                for i, (_, row) in enumerate(rekomendasi.iterrows()):
                    with cols_rec[i]:
                        color = get_color(row['AKREDITASI_CLEAN'])
                        st.markdown(f"""
                        <div style="background-color:white; padding:15px; border-radius:10px; border-left:5px solid {color}; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); height:160px;">
                            <h4 style="margin:0; font-size:14px;">{row['NAMA SEKOLAH']}</h4>
                            <p style="margin:5px 0; font-size:12px; color:gray;">📏 Jarak: <b>{row['JARAK_KM']:.2f} km</b></p>
                            <p style="margin:0; font-size:12px;">⭐ Skor Keunggulan: <b>{row['SCORE_FINAL']:.1f}/100</b></p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("Tidak ditemukan sekolah dalam radius zonasi 2KM dari lokasi Anda.")

    with col_chart:
        st.subheader("📈 Analisis Data")
        
        if not df_filtered.empty:
            chart_akreditasi = alt.Chart(df_filtered).mark_arc(innerRadius=50).encode(
                theta=alt.Theta("count()", stack=True),
                color=alt.Color('AKREDITASI_CLEAN', scale=alt.Scale(domain=['A', 'B', 'C', 'TT'], range=['green', 'blue', 'orange', 'red']), legend=alt.Legend(title="Akreditasi")),
                tooltip=['AKREDITASI_CLEAN', 'count()'],
                order=alt.Order("AKREDITASI_CLEAN", sort="ascending")
            ).properties(title="Proporsi Akreditasi (Data Terfilter)")
            
            st.altair_chart(chart_akreditasi, use_container_width=True)

            if 'KECAMATAN' in df_filtered.columns:
                top_kec = df_filtered['KECAMATAN'].value_counts().head(10).reset_index()
                top_kec.columns = ['Kecamatan', 'Jumlah']
                
                chart_kec = alt.Chart(top_kec).mark_bar().encode(
                    x=alt.X('Jumlah', title='Jumlah Sekolah'),
                    y=alt.Y('Kecamatan', sort='-x', title=''),
                    color=alt.value('#3182bd'),
                    tooltip=['Kecamatan', 'Jumlah']
                ).properties(title="Top 10 Kecamatan (Data Terfilter)")
                
                st.altair_chart(chart_kec, use_container_width=True)
        else:
            st.info("Data kosong. Silakan atur filter kembali.")

    # --- TABEL DATA RAW (FINAL CLEANING & REORDERING) ---
    with st.expander("📂 Lihat Data Mentah"):
        # 1. Hapus kolom yang tidak diinginkan (DITAMBAH: 'BENTUK' dan 'AKREDITASI_CLEAN')
        kolom_dibuang = [
            'Unnamed: 0', 
            'BENTUK PENDIDIKAN', 
            'WAKTU PENYELENGGARAAN', 
            'AKREDITASI_CLEAN',
            'BENTUK'  # <-- Kolom BENTUK dihapus sesuai request
        ]
        
        # Buat copy data & buang kolom sampah
        df_tampil = df_filtered.drop(columns=kolom_dibuang, errors='ignore').copy()

        # 2. PINDAHKAN POSISI KOLOM 'JENJANG' (Reordering)
        # Logika: Kita ingin urutannya -> NAMA SEKOLAH, NPSN, JENJANG, ... sisanya
        cols = list(df_tampil.columns)
        
        if 'JENJANG' in cols:
            cols.remove('JENJANG') # Cabut dulu kolom JENJANG dari belakang
            
            # Cari posisi 'NPSN' untuk patokan
            if 'NPSN' in cols:
                idx_npsn = cols.index('NPSN')
                cols.insert(idx_npsn + 1, 'JENJANG') # Masukkan JENJANG setelah NPSN
            else:
                # Kalau gak ada NPSN, taruh setelah NAMA SEKOLAH
                if 'NAMA SEKOLAH' in cols:
                     idx_nama = cols.index('NAMA SEKOLAH')
                     cols.insert(idx_nama + 1, 'JENJANG')
                else:
                    cols.insert(0, 'JENJANG') # Fallback: taruh paling depan
            
            # Terapkan urutan kolom baru
            df_tampil = df_tampil[cols]

        # 3. Fix Format KODE POS (Menghilangkan .0 dan nan)
        if 'KODE POS' in df_tampil.columns:
            df_tampil['KODE POS'] = df_tampil['KODE POS'].astype(str)
            df_tampil['KODE POS'] = df_tampil['KODE POS'].str.replace(r'\.0$', '', regex=True)
            df_tampil['KODE POS'] = df_tampil['KODE POS'].replace({'nan': '-', 'NaN': '-'})

        # 4. Reset Index agar mulai dari 1
        df_tampil = df_tampil.reset_index(drop=True)
        df_tampil.index = df_tampil.index + 1
        
        # 5. Tampilkan Tabel
        st.dataframe(df_tampil, use_container_width=True)

if __name__ == "__main__":
    main()
