import streamlit as st
import pandas as pd
import requests

# Konfigurasi Halaman
st.set_page_config(page_title="World Museum Explorer", page_icon="🌍", layout="wide")

st.title("🌍 Peta Live Museum Dunia")
st.markdown("Cari kota mana saja di dunia, dan biarkan sistem kami menarik data seluruh museum di sekitarnya secara otomatis! (Menggunakan Overpass & Wikipedia API)")
st.divider()

# 1. FITUR PENCARIAN KOTA
nama_kota = st.text_input("🔍 Ketik nama kota (Misal: Yogyakarta, Paris, London, Tokyo):", "Yogyakarta")

# Fungsi untuk mencari koordinat kota
def cari_koordinat_kota(kota):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={kota}&format=json&limit=1"
        header = {'User-Agent': 'TugasInforApp/1.0'}
        respon_mentah = requests.get(url, headers=header, timeout=10)
        
        # Cek apakah server merespon dengan baik (Status 200 = OK)
        if respon_mentah.status_code == 200:
            respon_json = respon_mentah.json()
            if respon_json:
                return float(respon_json[0]['lat']), float(respon_json[0]['lon'])
    except Exception as e:
        pass
    return None, None

# Fungsi untuk menarik data museum di sekitar koordinat (Radius 15km)
@st.cache_data # Fitur pintar Streamlit agar web tidak loading terus menerus
def tarik_data_museum(lat, lon):
    url_overpass = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    node(around:15000,{lat},{lon})["tourism"="museum"];
    out center;
    """
    try:
        respon_mentah = requests.get(url_overpass, params={'data': query}, timeout=15)
        
        # Mencegah JSONDecodeError: Hanya ubah ke JSON jika server membalas dengan OK (200)
        if respon_mentah.status_code == 200:
            respon_json = respon_mentah.json()
            daftar_museum = []
            
            for item in respon_json.get('elements', []):
                if 'tags' in item and 'name' in item['tags']:
                    daftar_museum.append({
                        'Nama_Museum': item['tags']['name'],
                        'lat': item['lat'],
                        'lon': item['lon']
                    })
            return pd.DataFrame(daftar_museum)
        else:
            return pd.DataFrame() # Kembalikan data kosong jika server API sedang sibuk
    except Exception as e:
        return pd.DataFrame() # Kembalikan data kosong jika terjadi error internet

# Fungsi untuk mencari info di Wikipedia
def cari_info_wikipedia(nama_museum):
    try:
        url = f"https://id.wikipedia.org/api/rest_v1/page/summary/{nama_museum}"
        respon_mentah = requests.get(url, timeout=10)
        
        if respon_mentah.status_code == 200:
            respon_json = respon_mentah.json()
            if 'title' in respon_json:
                deskripsi = respon_json.get('extract', 'Deskripsi tidak ditemukan di Wikipedia.')
                gambar = respon_json.get('thumbnail', {}).get('source', 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/300px-No_image_available.svg.png')
                return deskripsi, gambar
    except Exception as e:
        pass
    return "Belum ada artikel Wikipedia bahasa Indonesia yang spesifik untuk museum ini.", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/300px-No_image_available.svg.png"


# --- EKSEKUSI PROGRAM UTAMA ---
if nama_kota:
    with st.spinner("Sedang mencari koordinat kota..."):
        lat_kota, lon_kota = cari_koordinat_kota(nama_kota)
    
    if lat_kota and lon_kota:
        st.success(f"Lokasi '{nama_kota}' ditemukan! Menarik data museum dari server satelit...")
        
        # Mengambil database live
        with st.spinner("Tunggu sebentar ya, sedang menyedot data dari OpenStreetMap..."):
            df_museum = tarik_data_museum(lat_kota, lon_kota)
        
        if not df_museum.empty:
            st.write(f"Menemukan **{len(df_museum)}** museum di sekitar {nama_kota}.")
            
            # BAGIAN 2: Menampilkan Peta
            st.map(df_museum, zoom=11)
            st.divider()
            
            # BAGIAN 3: Menampilkan Info Valid dari Wikipedia
            st.subheader("🏛️ Eksplorasi Detail Museum")
            pilihan = st.selectbox("Pilih museum yang ingin dilihat detailnya:", df_museum['Nama_Museum'].sort_values())
            
            if pilihan:
                st.info("Sedang mencari data sejarah valid dari Wikipedia...")
                deskripsi, link_gambar = cari_info_wikipedia(pilihan)
                
                kolom1, kolom2 = st.columns([1, 1.5])
                with kolom1:
                    st.image(link_gambar, use_container_width=True)
                with kolom2:
                    st.header(pilihan)
                    st.write(deskripsi)
                    kata_kunci = pilihan.replace(" ", "+")
                    st.link_button(f"🔍 Telusuri '{pilihan}' di Google", f"https://www.google.com/search?q={kata_kunci}")
        else:
            st.warning("Data museum kosong atau Server Peta sedang sibuk. Coba cari kota lain atau coba lagi dalam beberapa detik.")
    else:
        st.error("Kota tidak ditemukan. Coba ketik nama kota yang lebih spesifik (Misal: 'Jakarta, Indonesia' atau 'Tokyo, Japan').")
