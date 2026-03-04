import pandas as pd
import numpy as np

def clean_coordinates(val):
    try:
        if pd.isna(val) or val == '' or val == '-':
            return None
        val = str(val).replace(',', '.')
        return float(val)
    except:
        return None

def clean_text(text):
    if pd.isna(text):
        return ""
    return str(text).replace("`", "").replace("'", "").strip()

def process_data():
    print("⏳ Sedang mengambil data dari Google Sheets...")
    
    # Config Sources
    sources = [
        {
            "jenjang": "SMA",
            "id": "1GiovYqUBP7egoVW9kRzJvrovNRrBI-ad",
            "rename": {} 
        },
        {
            "jenjang": "SMK",
            "id": "1jKbrmaRNoSzkRHyUj6p_td5xXahRAK2H",
            "rename": {'NAMA': 'NAMA SEKOLAH', 'STATUS SEKOLAH': 'STATUS', 'DESA KELURAHAN': 'DESA/KELURAHAN'}
        }
    ]

    all_data = []

    for source in sources:
        url = f"https://docs.google.com/spreadsheets/d/{source['id']}/export?format=csv"
        try:
            df = pd.read_csv(url, header=3)
            
            # Rename columns if needed
            if source['rename']:
                df = df.rename(columns=source['rename'])
            
            df['JENJANG'] = source['jenjang']
            all_data.append(df)
            print(f"✅ Data {source['jenjang']} berhasil diambil.")
        except Exception as e:
            print(f"❌ Gagal mengambil data {source['jenjang']}: {e}")

    if not all_data:
        return

    # Gabung Data
    df_final = pd.concat(all_data, ignore_index=True)

    # 1. Cleaning Kolom Penting
    print("⚙️ Sedang membersihkan data...")
    df_final['NAMA SEKOLAH'] = df_final['NAMA SEKOLAH'].apply(clean_text)
    
    # Koordinat
    df_final['LINTANG'] = df_final['LINTANG'].apply(clean_coordinates)
    df_final['BUJUR'] = df_final['BUJUR'].apply(clean_coordinates)
    
    # Hapus koordinat invalid (0 atau NaN)
    df_final = df_final.dropna(subset=['LINTANG', 'BUJUR'])
    df_final = df_final[(df_final['LINTANG'] != 0) & (df_final['BUJUR'] != 0)]
    
    # Filter Jabar (Koordinat Geografis Kasar) -> Opsional untuk membuang data nyasar
    # Jabar kira-kira di Lat -5 s.d -8, Long 106 s.d 109
    df_final = df_final[
        (df_final['LINTANG'] < -5) & (df_final['LINTANG'] > -8.5) & 
        (df_final['BUJUR'] > 106) & (df_final['BUJUR'] < 109)
    ]

    # 2. Standardisasi Akreditasi & Quality Scoring
    # Ini PENTING untuk judul "Kualitas"
    df_final['AKREDITASI'] = df_final['AKREDITASI'].astype(str).str.upper().str.strip()
    mapping_akreditasi = {
        'A': 'A', 'B': 'B', 'C': 'C'
    }
    # Semua yang aneh-aneh jadi "TT" (Tidak Terakreditasi)
    df_final['AKREDITASI_CLEAN'] = df_final['AKREDITASI'].map(mapping_akreditasi).fillna('TT')
    
    # Bobot Skor (Feature Engineering sederhana untuk Heatmap Kualitas)
    # A=100, B=75, C=50, TT=20
    score_map = {'A': 100, 'B': 75, 'C': 50, 'TT': 20}
    df_final['QUALITY_SCORE'] = df_final['AKREDITASI_CLEAN'].map(score_map)

    # 3. Export
    output_file = "data_sekolah_jabar_final.csv"
    df_final.to_csv(output_file, index=False)
    print(f"🎉 Selesai! File tersimpan: {output_file} ({len(df_final)} baris data)")

if __name__ == "__main__":
    process_data()