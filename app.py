import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, Fullscreen
import altair as alt
from math import radians, cos, sin, asin, sqrt
from streamlit_js_eval import streamlit_js_eval
from geopy.geocoders import Nominatim
import data_loader

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="West Java PPDB Zoning Analysis",
    page_icon="",
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
    [data-testid="stMetricLabel"] {
        font-size: 14px;
        color: #495057 !important; 
    }
    [data-testid="stMetricValue"] {
        font-size: 20px;
        font-weight: bold;
        color: #000000 !important;
    }
    [data-testid="stMetricDelta"] {
        color: #495057 !important;
    }
    .stStatusWidget {
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    </style>
""", unsafe_allow_html=True)

# --- DISTANCE FUNCTION (HAVERSINE) ---
def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 
    return c * r

# --- LOAD DATA FUNCTION ---
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
        try:
            data_loader.process_data()
            df = pd.read_csv("data_sekolah_jabar_final.csv")
            return df
        except Exception as e:
            st.error(f"Failed to load data: {e}")
            return None

# --- GEOCODING FUNCTION ---
def geocode_address(address):
    try:
        geolocator = Nominatim(user_agent="west_java_ppdb_app")
        location = geolocator.geocode(address + ", West Java, Indonesia")
        if location:
            return location.latitude, location.longitude
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        return None, None
    except Exception as e:
        st.error(f"Geocoding error: {e}")
        return None, None

# --- VISUAL UTILS ---
def get_color(akreditasi):
    if akreditasi == 'A': return 'green'
    elif akreditasi == 'B': return 'blue'
    elif akreditasi == 'C': return 'orange'
    else: return 'red'

# --- MAIN APPLICATION ---
def main():
    st.title("West Java Education Insight - Interactive GIS Dashboard")
    st.markdown("**School Distance & Quality Simulation** | Data Source: Dapodik/Verval SP")
    
    with st.status("Loading zoning system...", expanded=False) as status:
        df = load_data() 
        if df is not None:
            status.update(label="System Ready!", state="complete")
    
    if df is None:
        st.error("Data file not found.")
        st.stop()

    if 'lokasi_rumah' not in st.session_state:
        st.session_state['lokasi_rumah'] = None
    
    if 'selected_school' not in st.session_state:
        st.session_state['selected_school'] = None

    # ==================== SIDEBAR ====================
    st.sidebar.header("Control Panel")
    st.sidebar.subheader("Location & Zoning")
    
    if st.session_state.get('lokasi_rumah'):
        lat_curr, lon_curr = st.session_state['lokasi_rumah']
        st.sidebar.success(f"Active Location: {lat_curr:.5f}, {lon_curr:.5f}")
    else:
        st.sidebar.info("No location selected yet")
    
    # GPS Button
    if st.sidebar.button("Use My GPS", use_container_width=True):
        with st.spinner("Getting location..."):
            try:
                loc = streamlit_js_eval(
                    js_expressions="new Promise((resolve, reject) => { navigator.geolocation.getCurrentPosition(pos => resolve({latitude: pos.coords.latitude, longitude: pos.coords.longitude, accuracy: pos.coords.accuracy}), err => resolve(null), {enableHighAccuracy: true, timeout: 10000}) })", 
                    key="get_location_gps"
                )
                if loc and loc.get('latitude'):
                    st.session_state['lokasi_rumah'] = [loc['latitude'], loc['longitude']]
                    st.toast(f"Location obtained! (Accuracy: +/-{loc.get('accuracy', '?')}m)")
                    st.rerun()
                else:
                    st.toast("Failed. Make sure GPS is enabled and permission is granted.")
            except Exception as e:
                st.toast(f"Error: {str(e)}")
    
    # Manual Address Input - NEW!
    with st.sidebar.expander("Manual Address Input"):
        address_input = st.text_input(
            "Enter Address:",
            placeholder="e.g., Bandung, Cimahi, Cianjur",
            help="Enter a city, district, or street address in West Java",
            key="address_input"
        )
        
        if st.button("Search Address", key="search_address_btn", use_container_width=True):
            if address_input.strip():
                with st.spinner(f"Searching for '{address_input}'..."):
                    lat, lon = geocode_address(address_input)
                    if lat and lon:
                        st.session_state['lokasi_rumah'] = [lat, lon]
                        st.toast(f"Address found! {lat:.5f}, {lon:.5f}")
                        st.rerun()
                    else:
                        st.error("Address not found. Try a more specific address.")
            else:
                st.warning("Please enter an address.")
        
        st.caption("Examples: 'Bandung', 'Cimahi', 'Cianjur', 'Jalan Braga Bandung'")
    
    # Manual Coordinate Input (fallback)
    with st.sidebar.expander("Manual Coordinate Input"):
        col_lat, col_lon = st.columns(2)
        with col_lat:
            manual_lat = st.number_input("Latitude", value=st.session_state.get('lokasi_rumah', [-6.9175])[0] if st.session_state.get('lokasi_rumah') else -6.9175, format="%.6f", min_value=-8.5, max_value=-5.0)
        with col_lon:
            manual_lon = st.number_input("Longitude", value=st.session_state.get('lokasi_rumah', [107.6191])[1] if st.session_state.get('lokasi_rumah') else 107.6191, format="%.6f", min_value=106.0, max_value=109.0)
        if st.button("Set Coordinates", key="set_coords_btn", use_container_width=True):
            if -8.5 <= manual_lat <= -5.0 and 106.0 <= manual_lon <= 109.0:
                st.session_state['lokasi_rumah'] = [manual_lat, manual_lon]
                st.toast(f"Manual coordinates set! {manual_lat:.5f}, {manual_lon:.5f}")
                st.rerun()
            else:
                st.error("Coordinates outside West Java region!")
    
    st.sidebar.divider()
    
    # Zoning Settings
    aktifkan_zonasi = st.sidebar.checkbox("Enable Zoning Mode", value=False)
    radius_km = st.sidebar.slider("Zoning Radius (KM):", 1, 15, 3, disabled=not aktifkan_zonasi)
    
    if aktifkan_zonasi and not st.session_state.get('lokasi_rumah'):
        st.sidebar.warning("Please select a location first!")
    
    st.sidebar.divider()
    
    # Filter Data
    st.sidebar.subheader("Filter Data")
    filter_jenjang = st.sidebar.multiselect("Education Level:", df['JENJANG'].unique(), default=df['JENJANG'].unique())
    filter_akreditasi = st.sidebar.multiselect("Accreditation:", sorted(df['AKREDITASI_CLEAN'].unique()), default=df['AKREDITASI_CLEAN'].unique())
    filter_kota = st.sidebar.multiselect("City/Regency:", sorted(df['KABUPATEN'].unique().astype(str)), default=[])
    
    st.sidebar.divider()
    
    # Actions
    col_reset1, col_reset2 = st.sidebar.columns(2)
    with col_reset1:
        if st.button("Reset Filter", use_container_width=True):
            st.rerun()
    with col_reset2:
        if st.button("Reset All", use_container_width=True):
            st.session_state['lokasi_rumah'] = None
            st.rerun()
    
    if st.sidebar.button("Apply & Display", use_container_width=True):
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.caption("Tips: Click on the map to set home location")
    st.sidebar.caption("Developed by Davin")

    # Filtering Logic
    df_filtered = df[df['JENJANG'].isin(filter_jenjang)]
    df_filtered = df_filtered[df_filtered['AKREDITASI_CLEAN'].isin(filter_akreditasi)]
    if filter_kota:
        df_filtered = df_filtered[df_filtered['KABUPATEN'].isin(filter_kota)]

    # Distance Logic
    jarak_msg = ""
    if aktifkan_zonasi and st.session_state['lokasi_rumah']:
        user_lat, user_lon = st.session_state['lokasi_rumah']
        df_filtered['JARAK_KM'] = df_filtered.apply(
            lambda row: haversine(user_lon, user_lat, row['BUJUR'], row['LINTANG']), axis=1
        )
        df_filtered = df_filtered[df_filtered['JARAK_KM'] <= radius_km].copy()
        df_filtered = df_filtered.sort_values('JARAK_KM')
        jarak_msg = f"Radius {radius_km} KM from home."

    # KPI Metrics
    st.markdown("### Statistical Summary")
    if jarak_msg:
        st.toast(jarak_msg) 
        st.success(jarak_msg) 
        
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1.5])
    
    total = len(df_filtered)
    jml_a = len(df_filtered[df_filtered['AKREDITASI_CLEAN'] == 'A'])
    persen_a = (jml_a / total * 100) if total > 0 else 0
    avg_q = df_filtered['SKOR_KUALITAS'].mean() if total > 0 else 0 
    
    col1.metric("Total Schools", f"{total:,}")
    col2.metric("Accreditation A", f"{jml_a} ({persen_a:.1f}%)")
    col3.metric("Average Score", f"{avg_q:.1f}")
    
    if 'STATUS' in df_filtered.columns:
        negeri = len(df_filtered[df_filtered['STATUS'] == 'NEGERI'])
        swasta = total - negeri
        col4.metric("Status", f"{negeri} Public | {swasta} Private")

    st.divider()
    col_map, col_chart = st.columns([2, 1])

    # Map & Chart
    with col_map:
        st.subheader("Interactive Map")
        
        if not df_filtered.empty:
            school_options = ["-- Select School --"] + sorted(df_filtered['NAMA SEKOLAH'].unique().tolist())
            selected_school = st.selectbox(
                "Search School:",
                options=school_options,
                index=0,
                key="school_search",
                help="Select a school name to view its location on the map"
            )
            
            if selected_school != "-- Select School --":
                school_data = df_filtered[df_filtered['NAMA SEKOLAH'] == selected_school]
                if not school_data.empty:
                    center_lat = school_data.iloc[0]['LINTANG']
                    center_lon = school_data.iloc[0]['BUJUR']
                    zoom = 16
                    st.session_state['selected_school'] = selected_school
            else:
                st.session_state['selected_school'] = None
                if aktifkan_zonasi and st.session_state['lokasi_rumah']:
                    center_lat, center_lon = st.session_state['lokasi_rumah']
                    zoom = 13 
                elif not df_filtered.empty:
                    center_lat, center_lon = df_filtered['LINTANG'].mean(), df_filtered['BUJUR'].mean()
                    zoom = 10 if filter_kota else 9
                else:
                    center_lat, center_lon = -6.9175, 107.6191
                    zoom = 9
        else:
            center_lat, center_lon = -6.9175, 107.6191
            zoom = 9

        m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles="CartoDB positron")
        Fullscreen().add_to(m)

        if aktifkan_zonasi and st.session_state['lokasi_rumah']:
            folium.Marker(
                location=st.session_state['lokasi_rumah'],
                tooltip="Your Home Location",
                icon=folium.Icon(color="black", icon="home", prefix="fa")
            ).add_to(m)
            
            folium.Circle(
                location=st.session_state['lokasi_rumah'],
                radius=radius_km * 1000, 
                color="blue", fill=True, fill_opacity=0.1
            ).add_to(m)

        marker_cluster = MarkerCluster().add_to(m)
        for _, row in df_filtered.iterrows():
            info_jarak = f"<br><b>Distance:</b> {row['JARAK_KM']:.2f} KM" if 'JARAK_KM' in row else ""
            
            html = f"""
            <div style="font-family:sans-serif; width:200px">
                <h4 style="margin-bottom:0;">{row['NAMA SEKOLAH']}</h4>
                <span style="font-size:12px; color:gray;">{row['JENJANG']} | {row.get('STATUS','-')}</span>
                <hr style="margin:5px 0;">
                <b>Accreditation:</b> {row['AKREDITASI_CLEAN']}<br>
                <b>Score:</b> {row['SKOR_KUALITAS']}{info_jarak}
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
        st.subheader("Data Analysis")
        if not df_filtered.empty:
            chart_akreditasi = alt.Chart(df_filtered).mark_arc(innerRadius=50).encode(
                theta=alt.Theta("count()", stack=True),
                color=alt.Color('AKREDITASI_CLEAN', legend=alt.Legend(title="Accreditation"),
                                scale=alt.Scale(domain=['A', 'B', 'C', 'TT'], range=['green', 'blue', 'orange', 'red'])),
                tooltip=[
                    alt.Tooltip('AKREDITASI_CLEAN', title='Accreditation'),
                    alt.Tooltip('count()', title='Number of Schools') 
                ],
                order=alt.Order("AKREDITASI_CLEAN", sort="ascending")
            ).properties(title="School Proportion (Selected Area)")
            
            st.altair_chart(chart_akreditasi, use_container_width=True)

            if 'KECAMATAN' in df_filtered.columns:
                top_kec = df_filtered['KECAMATAN'].value_counts().head(10).reset_index()
                top_kec.columns = ['Subdistrict', 'Count']
                
                chart_kec = alt.Chart(top_kec).mark_bar().encode(
                    x=alt.X('Count', title='Number of Schools'), 
                    y=alt.Y('Subdistrict', sort='-x', title=''),
                    tooltip=['Subdistrict', alt.Tooltip('Count', title='Number of Schools')]
                ).properties(title="Top 10 Subdistricts")
                st.altair_chart(chart_kec, use_container_width=True)
        else:
            st.info("No schools in this radius. Try moving the map or increasing the radius.")

    # Data Table
    with st.expander("View Data Details"):
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
