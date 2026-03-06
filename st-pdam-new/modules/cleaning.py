import streamlit as st
import pandas as pd
import io

def show():

    st.title("🧹 Preprocessing Data Dasar")
    uploaded_files = st.file_uploader(
        "📂 Upload dataset",
        type="csv",
        accept_multiple_files=True
    )

    @st.cache_data
    def load_data(files):
        if not files:
            return pd.DataFrame()

        dfs = []
        for f in files:
            df_part = pd.read_csv(f, sep=None, engine="python")
            dfs.append(df_part)

        df = pd.concat(dfs, ignore_index=True)
        df.reset_index(drop=True, inplace=True)
        return df

    # Load hanya jika ada file
    if uploaded_files:
        df = load_data(uploaded_files)
    else:
        df = pd.DataFrame()

    if df.empty:
        st.info("⬅️ Upload file CSV terlebih dahulu")
        return

    if "original_df" not in st.session_state:
        st.session_state.original_df = df.copy()

    if "processed_df" not in st.session_state:
        st.session_state.processed_df = df.copy()

    # Reset jika file baru diupload
    if uploaded_files and not st.session_state.original_df.equals(df):
        st.session_state.original_df = df.copy()
        st.session_state.processed_df = df.copy()

    st.subheader("📋 Preview Data Awal")
    st.dataframe(st.session_state.processed_df, use_container_width=True)

    data = st.session_state.processed_df

    st.markdown("---")
    st.subheader("1️⃣ Cek Duplikat")

    duplicate_count = data.duplicated().sum()
    st.write(f"Jumlah data duplikat: **{duplicate_count}** baris")

    if duplicate_count > 0:
        if st.button("Hapus Duplikat"):
            st.session_state.processed_df = (
                data.drop_duplicates().reset_index(drop=True)
            )
            st.success("Duplikat berhasil dihapus!")
    else:
        st.success("Tidak ada data duplikat")

    st.markdown("---")
    st.subheader("2️⃣ Cek Missing Value")

    data = st.session_state.processed_df
    missing = data.isnull().sum()
    missing = missing[missing > 0]

    if missing.empty:
        st.success("Tidak ada missing value")
    else:
        missing_df = pd.DataFrame({
            "Jumlah Missing": missing,
            "Persentase (%)": (missing / len(data)) * 100
        }).sort_values("Jumlah Missing", ascending=False)

        st.dataframe(missing_df, use_container_width=True)

        st.markdown("### ⚙️ Handling Missing Value")

        col_selected = st.selectbox("Pilih kolom:", missing.index)

        method = st.selectbox(
            "Pilih metode:",
            ["Mean", "Median", "Mode", "Hapus Baris"]
        )

        if st.button("Proses Missing Value"):

            if method == "Mean":
                if pd.api.types.is_numeric_dtype(data[col_selected]):
                    st.session_state.processed_df[col_selected] = \
                        data[col_selected].fillna(data[col_selected].mean())
                    st.success("Missing diisi dengan Mean")
                else:
                    st.error("Kolom bukan numerik")

            elif method == "Median":
                if pd.api.types.is_numeric_dtype(data[col_selected]):
                    st.session_state.processed_df[col_selected] = \
                        data[col_selected].fillna(data[col_selected].median())
                    st.success("Missing diisi dengan Median")
                else:
                    st.error("Kolom bukan numerik")

            elif method == "Mode":
                st.session_state.processed_df[col_selected] = \
                    data[col_selected].fillna(data[col_selected].mode()[0])
                st.success("Missing diisi dengan Mode")

            elif method == "Hapus Baris":
                st.session_state.processed_df = \
                    data.dropna(subset=[col_selected]).reset_index(drop=True)
                st.success("Baris dengan missing berhasil dihapus")
    st.markdown("---")
    st.subheader("📋 Preview Data Setelah Preprocessing")
    st.dataframe(st.session_state.processed_df, use_container_width=True)

    st.markdown("---")
    st.subheader("⬇️ Download Data Bersih")

    csv_buffer = io.StringIO()
    st.session_state.processed_df.to_csv(csv_buffer, index=False)

    st.download_button(
        "⬇️ Download Data Final",
        csv_buffer.getvalue(),
        "data_bersih.csv",
        "text/csv"
    )