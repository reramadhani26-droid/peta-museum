import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Peta Museum Global", page_icon="🌍", layout="wide")

st.title("🌍 Peta Museum Seluruh Dunia")
st.markdown("Geser peta ke negara mana pun, lalu **klik bebas di area peta (kota/daerah)**. Sistem akan otomatis mencari museum terpopuler di sekitar lokasi yang Anda klik!")
st.divider()

# Fungsi untuk mencari artikel geografi terdekat via Wikipedia API berdasarkan Koordinat
@st.cache_data(ttl=3600)
def cari_museum_sekitar(lat, lon):
    daftar_museum = []
    try:
        # Mencari artikel (tempat) dalam radius 10km dari titik yang diklik
        url_geo = f"https://en.wikipedia.org/w/api.php?action=query&list=geosearch&gsradius=10000&gscoord={lat}|{lon}&format=json"
        header = {'User-Agent': 'TugasInforApp/1.0 (Student Project)'}
        
        respon_geo = requests.get(url_geo, headers=header, timeout=10)
        
        if respon_geo.status_code == 200:
            data_geo = respon_geo.json()
            hasil_pencarian = data_geo.get("query", {}).get("geosearch", [])
            
            # Kita filter artikel yang namanya mengandung kata "Museum", "Gallery", atau "Art"
            for item in hasil_pencarian:
                judul = item["title"]
                
                # Cek apakah ini artikel museum
                if any(kata in judul.lower() for kata in ["museum", "gallery", "art"]):
                    # Ambil deskripsi dan gambar via Wikipedia Summary API
                    url_detail = f"https://en.wikipedia.org/api/rest_v1/page/summary/{judul}"
                    respon_detail = requests.get(url_detail, headers=header, timeout=5)
                    
                    if respon_detail.status_code == 200:
                        data_detail = respon_detail.json()
                        daftar_museum.append({
                            'Nama_Museum': judul,
                            'lat': item["lat"],
                            'lon': item["lon"],
                            'deskripsi': data_detail.get("extract", "Deskripsi tidak tersedia di ensiklopedia."),
                            'gambar': data_detail.get("thumbnail", {}).get("source", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/300px-No_image_available.svg.png"),
                            'url_wiki': data_detail.get("content_urls", {}).get("desktop", {}).get("page", "")
                        })
                        
        return pd.DataFrame(daftar_museum)
    except Exception as e:
        return pd.DataFrame()

# Inisialisasi posisi peta awal (Tengah peta) - Kita set di London sebagai contoh awal
if 'pusat_peta' not in st.session_state:
    st.session_state.pusat_peta = [51.5074, -0.1278]
if 'data_museum' not in st.session_state:
    st.session_state.data_museum = pd.DataFrame()

# TAMPILAN PETA MENGGUNAKAN FOLIUM
st.subheader("Pilih Lokasi di Peta 🗺️")
# Membuat base map
m = folium.Map(location=st.session_state.pusat_peta, zoom_start=5)

# Jika ada data museum, tambahkan titik (marker) merah ke peta
if not st.session_state.data_museum.empty:
    for index, row in st.session_state.data_museum.iterrows():
        folium.Marker(
            [row['lat'], row['lon']],
            popup=folium.Popup(row['Nama_Museum'], max_width=300),
            tooltip=row['Nama_Museum'],
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)

# Tampilkan peta di web dan tangkap interaksi klik
hasil_klik = st_folium(m, width=1200, height=500, returned_objects=["last_clicked"])

st.divider()

# MENANGKAP TITIK KOORDINAT YANG DIKLIK PENGGUNA
if hasil_klik and hasil_klik.get("last_clicked"):
    lat_klik = hasil_klik["last_clicked"]["lat"]
    lon_klik = hasil_klik["last_clicked"]["lng"]
    
    st.session_state.pusat_peta = [lat_klik, lon_klik]
    
    with st.spinner("Sedang mencari museum di sekitar lokasi yang Anda klik..."):
        st.session_state.data_museum = cari_museum_sekitar(lat_klik, lon_klik)
        st.rerun() # Refresh halaman agar titik merah langsung muncul di peta

# MENAMPILKAN GALERI MUSEUM DI BAWAH PETA
if not st.session_state.data_museum.empty:
    st.success(f"Berhasil menemukan **{len(st.session_state.data_museum)}** museum di sekitar lokasi yang Anda klik!")
    
    st.subheader("🏛️ Galeri Koleksi & Sejarah")
    
    # Gunakan dropdown untuk memilih museum dari data yang ditemukan
    pilihan = st.selectbox("Pilih museum untuk melihat detailnya:", st.session_state.data_museum['Nama_Museum'].sort_values())
    
    if pilihan:
        data_pilihan = st.session_state.data_museum[st.session_state.data_museum['Nama_Museum'] == pilihan].iloc[0]
        
        kolom1, kolom2 = st.columns([1, 2])
        with kolom1:
            st.image(data_pilihan['gambar'], use_container_width=True)
        with kolom2:
            st.header(data_pilihan['Nama_Museum'])
            st.write(data_pilihan['deskripsi'])
            st.link_button("📖 Baca Sejarah Lengkap (Wikipedia)", data_pilihan['url_wiki'])
            
            kata_kunci = data_pilihan['Nama_Museum'].replace(" ", "+")
            st.link_button("🔍 Cari Gambar Lainnya", f"https://www.google.com/search?q={kata_kunci}&tbm=isch")
elif hasil_klik and hasil_klik.get("last_clicked"):
    st.warning("Tidak ada museum besar/terkenal dalam radius 10 km dari titik yang Anda klik. Coba klik di pusat kota besar!")
else:
    st.info("👈 Silakan klik di area mana saja pada peta di atas untuk memulai pencarian museum.")
