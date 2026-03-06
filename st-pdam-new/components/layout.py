import streamlit as st
import pandas as pd


def render_layout(title, key_name, dashboard_fn, ml_fn, prediksi_fn):

    st.title(title)

    uploaded_file = st.file_uploader(
        f"📂 Upload File CSV {title}",
        type=["csv"],
        key=f"upload_{key_name}"
    )

    if uploaded_file is None:
        st.info("Silakan upload data terlebih dahulu")
        return

    # ==========================
    # LOAD DATA (AMAN)
    # ==========================
    try:
        df = pd.read_csv(uploaded_file, sep=None, engine="python")
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
        return

    # Simpan ke session state
    st.session_state[key_name] = df

    st.success("Data berhasil diupload ✅")

    # ==========================
    # INFO DATA
    # ==========================
    st.subheader("📄 Preview Data")

    total_rows, total_cols = df.shape

    # ==========================
    # DROPDOWN JUMLAH DATA
    # ==========================
    opsi_preview = st.selectbox(
        "Tampilkan jumlah data:",
        ["100", "200", "500", "1000", "Semua"],
        index=0
    )

    if opsi_preview == "Semua":
        preview_df = df
    else:
        jumlah = int(opsi_preview)
        preview_df = df.head(min(jumlah, total_rows))

    # ==========================
    # TAMPILKAN DATA
    # ==========================
    st.dataframe(
        preview_df,
        use_container_width=True,
        height=500
    )

    st.markdown("---")

    # ==========================
    # TABS MENU
    # ==========================
    tab1, tab2, tab3 = st.tabs([
        "📊 Dashboard",
        "🔍 Analisis ML",
        "🧾 Prediksi & Rekomendasi"
    ])

    with tab1:
        dashboard_fn(df)

    with tab2:
        ml_fn(df)

    with tab3:
        prediksi_fn(df)
