import streamlit as st
from components.layout import render_layout
import pandas as pd
import plotly.express as px
from datetime import datetime
from kmodes.kprototypes import KPrototypes
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import numpy as np
import matplotlib.pyplot as plt


def dashboard(df):
    st.subheader("Dashboard Pelanggan")

    if df is None or df.empty:
        st.warning("Dataset kosong")
        return

    filtered_df = df.copy()
    if "date_join" in filtered_df.columns:
        filtered_df["date_join"] = pd.to_datetime(
            filtered_df["date_join"],
            errors="coerce"
        )

    st.markdown("## 📊 Data Quality Overview")

    total_rows = len(filtered_df)
    total_columns = len(filtered_df.columns)
    total_missing = filtered_df.isna().sum().sum()
    total_duplicate = filtered_df.duplicated().sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Baris", total_rows)
    col2.metric("Total Kolom", total_columns)
    col3.metric("Total Missing Value", int(total_missing))
    col4.metric("Total Duplikat", int(total_duplicate))

    st.markdown("---")
    # MISSING VALUE PER KOLOM (OTOMATIS SEMUA KOLOM)

    missing = filtered_df.isna().mean() * 100
    missing = missing[missing > 0].sort_values(ascending=False)

    if not missing.empty:
        st.subheader("Persentase Missing Value per Kolom")

        q_df = pd.DataFrame({
            "Kolom": missing.index,
            "Missing (%)": missing.values
        })

        fig = px.bar(
            q_df,
            x="Kolom",
            y="Missing (%)"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("Tidak ditemukan missing value pada dataset.")

  
    # DISTRIBUSI AREA

    if "areas_codes" in filtered_df.columns:
        st.subheader("Distribusi Area Pelanggan")

        area_count = (
            filtered_df["areas_codes"]
            .value_counts()
            .head(10)
        )

        fig = px.bar(
            x=area_count.index,
            y=area_count.values,
            labels={"x": "Area", "y": "Jumlah"}
        )

        st.plotly_chart(fig, use_container_width=True)

    # COHORT PELANGGAN
 
    if "date_join" in filtered_df.columns:
        st.subheader("Cohort Pelanggan (Tahun Bergabung)")

        cohort = (
            filtered_df["date_join"]
            .dt.year
            .value_counts()
            .sort_index()
        )

        fig = px.bar(
            x=cohort.index,
            y=cohort.values,
            labels={"x": "Tahun", "y": "Jumlah Pelanggan"}
        )

        st.plotly_chart(fig, use_container_width=True)

    
    # CHURN / STATUS
   
    if "states" in filtered_df.columns:
        st.subheader("Distribusi Status Pelanggan")

        status_count = filtered_df["states"].value_counts()

        fig = px.pie(
            values=status_count.values,
            names=status_count.index
        )

        st.plotly_chart(fig, use_container_width=True)

def ml(df):

    st.subheader("Clustering Pelanggan - K-Prototypes")

    if df is None or df.empty:
        st.warning("Dataset kosong")
        return

    df = df.copy()

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

    if not numeric_cols or not categorical_cols:
        st.error("Dataset harus memiliki minimal 1 kolom numerik dan 1 kolom kategorikal.")
        return

    col1, col2 = st.columns(2)

    selected_numeric = col1.multiselect(
        "Pilih Kolom Numerik",
        numeric_cols,
        default=numeric_cols[:2] if len(numeric_cols) >= 2 else numeric_cols
    )

    selected_categorical = col2.multiselect(
        "Pilih Kolom Kategorikal",
        categorical_cols,
        default=categorical_cols[:1]
    )

    if not selected_numeric or not selected_categorical:
        st.error("Minimal pilih 1 kolom numerik dan 1 kolom kategorikal.")
        return

    max_k = st.slider("Range Maksimal K", 2, 6, 4)

    use_sampling = st.checkbox(
        "Gunakan Sampling untuk Elbow (lebih cepat)",
        value=True
    )

 
    # PREPROCESSING


    data_model = df[selected_numeric + selected_categorical].copy()

    for col in selected_numeric:
        data_model[col] = data_model[col].fillna(data_model[col].median())

    for col in selected_categorical:
        data_model[col] = data_model[col].fillna(data_model[col].mode()[0])

    scaler = StandardScaler()
    data_model[selected_numeric] = scaler.fit_transform(
        data_model[selected_numeric]
    )

    if use_sampling and len(data_model) > 1500:
        data_elbow = data_model.sample(1000, random_state=42)
    else:
        data_elbow = data_model.copy()

    data_np = data_elbow.to_numpy()

    categorical_index = list(
        range(len(selected_numeric),
              len(selected_numeric) + len(selected_categorical))
    )


    # ELBOW + SILHOUETTE

    st.subheader("Evaluasi Jumlah Cluster")

    costs = []
    silhouettes = []
    K_range = range(2, max_k + 1)

    with st.spinner("Menghitung evaluasi cluster..."):

        for k in K_range:

            kp = KPrototypes(
                n_clusters=k,
                init='Cao',
                n_init=2,
                max_iter=50,
                verbose=0,
                random_state=42
            )

            clusters = kp.fit_predict(
                data_np,
                categorical=categorical_index
            )

            costs.append(kp.cost_)

            try:
                sil = silhouette_score(
                    data_elbow[selected_numeric],
                    clusters
                )
            except:
                sil = -1

            silhouettes.append(sil)

    fig1, ax1 = plt.subplots()
    ax1.plot(K_range, costs, marker='o')
    ax1.set_xlabel("Jumlah Cluster (K)")
    ax1.set_ylabel("Cost")
    st.pyplot(fig1)

    fig2, ax2 = plt.subplots()
    ax2.plot(K_range, silhouettes, marker='o')
    ax2.set_xlabel("Jumlah Cluster (K)")
    ax2.set_ylabel("Silhouette Score")
    st.pyplot(fig2)

    if max(silhouettes) <= 0:
        best_k = list(K_range)[0]
        st.warning("Silhouette kurang optimal, menggunakan K terkecil sebagai default.")
    else:
        best_k = list(K_range)[np.argmax(silhouettes)]

    st.success(f"Jumlah cluster optimal: {best_k}")

    st.subheader("Proses Clustering Final")

    data_full_np = data_model.to_numpy()

    kproto = KPrototypes(
        n_clusters=best_k,
        init='Cao',
        n_init=3,
        max_iter=100,
        verbose=0,
        random_state=42
    )

    final_clusters = kproto.fit_predict(
        data_full_np,
        categorical=categorical_index
    )

    df_clustered = df.copy()
    df_clustered["cluster"] = final_clusters

    st.subheader("Distribusi Cluster")
    st.bar_chart(df_clustered["cluster"].value_counts())

    st.subheader("Rata-rata Numerik per Cluster")
    st.dataframe(
        df_clustered.groupby("cluster")[selected_numeric].mean()
    )

    st.subheader("Dominasi Kategori per Cluster")

    for col in selected_categorical:
        mode_table = df_clustered.groupby("cluster")[col] \
            .agg(lambda x: x.value_counts().index[0])
        st.write(f"**{col}**")
        st.dataframe(mode_table)



    st.subheader("Ringkasan Insight")

    cluster_means = df_clustered.groupby("cluster")[selected_numeric].mean()
    highest_cluster = cluster_means.mean(axis=1).idxmax()
    lowest_cluster = cluster_means.mean(axis=1).idxmin()

    st.write(f"- Cluster {highest_cluster} menunjukkan rata-rata nilai numerik paling tinggi.")
    st.write(f"- Cluster {lowest_cluster} menunjukkan rata-rata nilai numerik paling rendah.")
    st.write("- Hasil segmentasi dapat digunakan untuk strategi layanan yang lebih terarah.")

    csv = df_clustered.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Hasil Clustering",
        csv,
        "hasil_cluster_pelanggan.csv",
        "text/csv"
    )
def prediksi(df):
    st.subheader("Prediksi Pelanggan")
    st.info("Fitur prediksi bisa ditambahkan di sini")



def show():
    render_layout(
        "📊 Data Pelanggan",
        "df_pelanggan",
        dashboard,
        ml,
        prediksi
    )