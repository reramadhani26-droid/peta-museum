import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Peta Museum Global", page_icon="🌍", layout="wide")

st.title("🌍 Peta Museum Seluruh Dunia")
st.markdown("Peta sekarang menggunakan **Mode Ringan (Anti-Lag)**. Geser dan klik di pusat kota mana saja!")
st.divider()

# Fungsi untuk mencari artikel geografi terdekat via Wikipedia API
@st.cache_data(ttl=3600)
def cari_museum_sekitar(lat, lon):
    daftar_museum = []
    try:
        url_geo = f"https://en.wikipedia.org/w/api.php?action=query&list=geosearch&gsradius=10000&gscoord={lat}|{lon}&format=json"
        header = {'User-Agent': 'TugasInforApp/1.1'}
        
        # Waktu tunggu dipercepat agar tidak loading terlalu lama
        respon_geo = requests.get(url_geo, headers=header, timeout=5) 
        
        if respon_geo.status_code == 200:
            data_geo = respon_geo.json()
            hasil_pencarian = data_geo.get("query", {}).get("geosearch", [])
            
            # BATAS PINTAR: Hanya memproses maksimal 5 museum agar HP tidak lag
            batas_hasil = 0
            for item in hasil_pencarian:
                judul = item["title"]
                if any(kata in judul.lower() for kata in ["museum", "gallery", "art"]):
                    if batas_hasil >= 5: # Jika sudah 5 museum, hentikan pencarian
                        break
                        
                    url_detail = f"https://en.wikipedia.org/api/rest_v1/page/summary/{judul}"
                    respon_detail = requests.get(url_detail, headers=header, timeout=3)
                    
                    if respon_detail.status_code == 200:
                        data_detail = respon_detail.json()
                        daftar_museum.append({
                            'Nama_Museum': judul,
                            'lat': item["lat"],
                            'lon': item["lon"],
                            'deskripsi': data_detail.get("extract", "Deskripsi tidak tersedia."),
                            'gambar': data_detail.get("thumbnail", {}).get("source", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/300px-No_image_available.svg.png"),
                            'url_wiki': data_detail.get("content_urls", {}).get("desktop", {}).get("page", "")
                        })
                        batas_hasil += 1
                        
        return pd.DataFrame(daftar_museum)
    except Exception as e:
        return pd.DataFrame()

if 'pusat_peta' not in st.session_state:
    st.session_state.pusat_peta = [51.5074, -0.1278] # Default London
if 'data_museum' not in st.session_state:
    st.session_state.data_museum = pd.DataFrame()

# Peta menggunakan "CartoDB positron" yang sangat ringan dibanding versi standar
m = folium.Map(location=st.session_state.pusat_peta, zoom_start=5, tiles="CartoDB positron")

# Menambahkan titik merah jika data ditemukan
if not st.session_state.data_museum.empty:
    for index, row in st.session_state.data_museum.iterrows():
        folium.Marker(
            [row['lat'], row['lon']],
            popup=row['Nama_Museum'],
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)

# Ukuran peta diperkecil (height=400) agar lebih nyaman disentuh (touch-friendly) di HP
hasil_klik = st_folium(m, height=400, use_container_width=True, returned_objects=["last_clicked"])

st.divider()

# Mencegah peta memproses titik yang sama berulang kali (menghemat memori)
if hasil_klik and hasil_klik.get("last_clicked"):
    lat_klik = hasil_klik["last_clicked"]["lat"]
    lon_klik = hasil_klik["last_clicked"]["lng"]
    
    if lat_klik != st.session_state.pusat_peta[0]:
        st.session_state.pusat_peta = [lat_klik, lon_klik]
        with st.spinner("Mencari museum di area ini... (Mode Cepat)"):
            st.session_state.data_museum = cari_museum_sekitar(lat_klik, lon_klik)
            st.rerun()

# Tampilan akhir Galeri
if not st.session_state.data_museum.empty:
    st.success(f"Ditemukan {len(st.session_state.data_museum)} museum populer di sekitar area ini!")
    
    pilihan = st.selectbox("Pilih museum untuk melihat detail:", st.session_state.data_museum['Nama_Museum'])
    
    if pilihan:
        data_pilihan = st.session_state.data_museum[st.session_state.data_museum['Nama_Museum'] == pilihan].iloc[0]
        
        st.image(data_pilihan['gambar'], use_container_width=True)
        st.subheader(data_pilihan['Nama_Museum'])
        st.write(data_pilihan['deskripsi'])
        st.link_button("📖 Baca Artikel Wikipedia", data_pilihan['url_wiki'])
        
elif hasil_klik and hasil_klik.get("last_clicked"):
    st.warning("Tidak ada museum besar di sekitar titik klik. Coba klik di area pusat ibu kota negara!")
else:
    st.info("👆 Silakan geser peta dan sentuh/klik di area kota mana saja.")
