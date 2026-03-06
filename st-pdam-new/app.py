import os
from PIL import Image
import streamlit as st
import modules.pelanggan as pelanggan
import modules.aduan as aduan
import modules.transaksi as transaksi
import modules.cleaning as cleaning

st.set_page_config(layout="wide")

if "menu" not in st.session_state:
    st.session_state.menu = "Home"


BASE_DIR = os.path.dirname(__file__)
logo_path = os.path.join(BASE_DIR, "assets", "LOGO.png")

logo = Image.open(logo_path)
st.sidebar.image(logo, width=200)

st.sidebar.title("📊 Dashboard Analisis Data")

if st.sidebar.button("🏠 Home"):
    st.session_state.menu = "Home"

if st.sidebar.button("🧹 Cleaning Data"):
    st.session_state.menu = "Cleaning"

if st.sidebar.button("📊 Data Pelanggan"):
    st.session_state.menu = "Pelanggan"

if st.sidebar.button("📞 Data Aduan"):
    st.session_state.menu = "Aduan"

if st.sidebar.button("💳 Data Transaksi"):
    st.session_state.menu = "Transaksi"


# Routing

if st.session_state.menu == "Home":
    st.title("🏠 Home")
    st.subheader("Sistem Analisis Data Pelanggan Terintegrasi")

    st.markdown("""
    Sistem ini digunakan untuk mengelola dan menganalisis data pelanggan, data aduan, dan data transaksi 
    dalam satu platform terpadu. Aplikasi mendukung proses unggah data, pembersihan dataset, 
    visualisasi dashboard, hingga analisis lanjutan berbasis Machine Learning.

    Silakan pilih modul pada sidebar untuk memulai proses analisis.
    """)

    st.divider()

    st.markdown("### 🔄 Alur Penggunaan")

    st.markdown("""
    1. **Upload Dataset (CSV)**  
       Dataset akan divalidasi dan ditampilkan dalam bentuk preview.

    2. **Data Cleaning**  
       Tersedia fitur penghapusan data duplikat dan penanganan missing value.

    3. **Dashboard Analitik**  
       Menyajikan ringkasan statistik dan visualisasi utama.

    4. **Analisis Machine Learning**  
       Segmentasi atau pengelompokan data untuk menemukan pola.

    5. **Prediksi / Rekomendasi**  
       Insight berbasis model sebagai pendukung pengambilan keputusan.
    """)

    st.divider()

    st.markdown("### 📂 Ruang Lingkup Modul")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("👥 **Data Pelanggan**\n\nAnalisis profil dan segmentasi pelanggan.")

    with col2:
        st.info("📞 **Data Aduan**\n\nIdentifikasi tren dan pola keluhan layanan.")

    with col3:
        st.info("💳 **Data Transaksi**\n\nAnalisis aktivitas dan perilaku transaksi.")

    st.divider()

    st.caption(
        "Sistem dirancang untuk mendukung evaluasi kinerja dan pengambilan keputusan berbasis data.")

elif st.session_state.menu == "Cleaning":
    cleaning.show()

elif st.session_state.menu == "Pelanggan":
    pelanggan.show()

elif st.session_state.menu == "Aduan":
    aduan.show()

elif st.session_state.menu == "Transaksi":
    transaksi.show()
