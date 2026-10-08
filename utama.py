import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="World Museum Explorer", page_icon="🌍", layout="wide")

st.title("🌍 Peta Live Museum Dunia")
st.markdown("Cari kota mana saja di dunia, dan sistem kami akan menarik data beserta gambar koleksi museum langsung dari ensiklopedia global secara instan!")
st.divider()

nama_kota = st.text_input("🔍 Ketik nama kota di dunia (Misal: Jakarta, Paris, London, Tokyo):", "Jakarta")

@st.cache_data # Fitur ini menyimpan sementara data yang dicari agar web tidak lambat
def cari_museum_wikipedia(kota):
    daftar_museum = []
    try:
        # Langkah 1: Mencari artikel Wikipedia yang mengandung nama kota dan kata "museum"
        # Kita menggunakan Wikipedia bahasa Inggris agar datanya lengkap untuk seluruh dunia
        url_search = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": f"{kota} museum",
            "utf8": "",
            "format": "json",
            "srlimit": 15 # Mengambil maksimal 15 hasil pencarian teratas
        }
        
        header = {'User-Agent': 'TugasInforApp/1.0 (Student Project)'}
        respon_search = requests.get(url_search, params=params, headers=header, timeout=10)
        
        if respon_search.status_code == 200:
            data_search = respon_search.json()
            hasil_pencarian = data_search.get("query", {}).get("search", [])
            
            # Langkah 2: Mengambil detail setiap artikel (Koordinat, Gambar, Deskripsi)
            for item in hasil_pencarian:
                judul = item["title"]
                
                # Mengakses API Summary dari Wikipedia untuk mendapatkan deskripsi singkat dan titik kordinat
                url_detail = f"https://en.wikipedia.org/api/rest_v1/page/summary/{judul}"
                respon_detail = requests.get(url_detail, headers=header, timeout=5)
                
                if respon_detail.status_code == 200:
                    data_detail = respon_detail.json()
                    
                    # Kita hanya memasukkan data ke tabel jika artikel tersebut memiliki titik koordinat (Lokasi valid)
                    if "coordinates" in data_detail:
                        daftar_museum.append({
                            'Nama_Museum': judul,
                            'lat': data_detail["coordinates"]["lat"],
                            'lon': data_detail["coordinates"]["lon"],
                            'deskripsi': data_detail.get("extract", "No description available."),
                            'gambar': data_detail.get("thumbnail", {}).get("source", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/300px-No_image_available.svg.png"),
                            'url_wiki': data_detail.get("content_urls", {}).get("desktop", {}).get("page", "")
                        })
                        
        return pd.DataFrame(daftar_museum)
    except Exception as e:
        return pd.DataFrame() # Jika terjadi error koneksi internet, kembalikan tabel kosong agar tidak crash

if nama_kota:
    with st.spinner(f"Mencari data museum di {nama_kota} dari database satelit global..."):
        df_museum = cari_museum_wikipedia(nama_kota)
    
    if not df_museum.empty:
        st.success(f"Berhasil menemukan **{len(df_museum)}** museum yang memiliki data peta valid di sekitar '{nama_kota}'!")
        
        # BAGIAN 1: Menampilkan titik koordinat ke dalam Peta Interaktif
        st.map(df_museum, zoom=10)
        st.divider()
        
        # BAGIAN 2: Menampilkan Galeri dan Informasi Sejarah
        st.subheader("🏛️ Eksplorasi Detail Museum")
        st.write("Pilih salah satu museum dari peta di atas untuk melihat koleksi dan sejarahnya:")
        
        # Membuat kotak pilihan (*Dropdown*)
        pilihan = st.selectbox("Daftar Museum Ditemukan:", df_museum['Nama_Museum'].sort_values())
        
        if pilihan:
            # Mencari baris data spesifik yang dipilih pengguna
            data_pilihan = df_museum[df_museum['Nama_Museum'] == pilihan].iloc[0]
            
            # Membagi layar menjadi 2 kolom (Kiri untuk gambar, Kanan untuk teks)
            kolom1, kolom2 = st.columns([1, 1.5])
            with kolom1:
                st.image(data_pilihan['gambar'], use_container_width=True, caption=data_pilihan['Nama_Museum'])
            with kolom2:
                st.header(data_pilihan['Nama_Museum'])
                st.write(data_pilihan['deskripsi'])
                
                # Tombol pintasan untuk mengeksplorasi lebih jauh
                st.link_button("📖 Baca Sejarah Lengkap (Wikipedia)", data_pilihan['url_wiki'])
                
                kata_kunci = data_pilihan['Nama_Museum'].replace(" ", "+")
                st.link_button(f"🔍 Telusuri Gambar Lainnya di Google", f"https://www.google.com/search?q={kata_kunci}&tbm=isch")
    else:
        st.warning(f"Tidak dapat menemukan titik lokasi valid untuk museum di wilayah '{nama_kota}'. Coba gunakan nama kota dalam bahasa Inggris (Misal: 'Yogyakarta', 'Rome', 'New York').")
