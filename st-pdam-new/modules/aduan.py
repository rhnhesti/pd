import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from components.layout import render_layout


def _cari_kolom(df, kandidat: list):
    """Cari kolom pertama yang cocok (case-insensitive) dari daftar kandidat."""
    kandidat_lower = [k.lower() for k in kandidat]
    for col in df.columns:
        if col.lower() in kandidat_lower:
            return col
    return None


def _parse_tanggal(df, col):
    """Parse kolom tanggal dengan aman."""
    try:
        return pd.to_datetime(df[col], dayfirst=True, errors="coerce")
    except Exception:
        return pd.NaT

def dashboard(df):
    st.markdown(
        """
        <style>
        .metric-card {
            background: linear-gradient(135deg, #1e3a5f 0%, #0d2137 100%);
            border: 1px solid #2e6da4;
            border-radius: 12px;
            padding: 18px 22px;
            color: #e8f4fd;
        }
        .metric-card h1 { font-size: 2.4rem; margin: 0; color: #56b4e9; }
        .metric-card p  { margin: 0; font-size: 0.9rem; color: #a8c9e8; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("📊 Dashboard Ringkas Aduan")

    # Deteksi kolom umum
    col_tgl_buat   = _cari_kolom(df, ["tgl_buat", "tanggal_buat", "tanggal", "created_at", "tgl_masuk", "tgl_aduan"])
    col_tgl_update = _cari_kolom(df, ["tgl_update", "tanggal_update", "updated_at", "tgl_selesai"])
    col_jenis      = _cari_kolom(df, ["jenis_keluhan", "jenis", "kategori", "keluhan", "keterangan_keluhan"])
    col_kanal      = _cari_kolom(df, ["kanal", "via", "media", "channel", "sumber"])
    col_unit       = _cari_kolom(df, ["unit", "unit_kerja", "petugas_unit", "bagian"])
    col_petugas    = _cari_kolom(df, ["petugas", "nama_petugas", "officer"])
    col_status     = _cari_kolom(df, ["status", "status_aduan", "kondisi"])
    col_area       = _cari_kolom(df, ["area", "wilayah", "kecamatan", "kelurahan", "zona"])
    col_nama       = _cari_kolom(df, ["nama", "nama_pelanggan", "customer_name"])
    col_lat        = _cari_kolom(df, ["lat", "latitude"])
    col_lon        = _cari_kolom(df, ["lon", "lng", "longitude"])

    # Parsing tanggal
    if col_tgl_buat:
        df["_tgl_buat_parsed"] = _parse_tanggal(df, col_tgl_buat)
    if col_tgl_update:
        df["_tgl_update_parsed"] = _parse_tanggal(df, col_tgl_update)

    # KPI
    total_aduan = len(df)
    total_selesai = (
        df[col_status].str.lower().str.contains("selesai|closed|done|complete", na=False).sum()
        if col_status else "N/A"
    )
    total_proses = (
        df[col_status].str.lower().str.contains("proses|pending|open|baru", na=False).sum()
        if col_status else "N/A"
    )

    if col_tgl_buat and col_tgl_update:
        waktu_respon = (
            df["_tgl_update_parsed"] - df["_tgl_buat_parsed"]
        ).dt.days.dropna()
        rata_respon = f"{waktu_respon.mean():.1f} hari" if not waktu_respon.empty else "N/A"
    else:
        rata_respon = "N/A"

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f'<div class="metric-card"><h1>{total_aduan:,}</h1><p>Total Aduan</p></div>',
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f'<div class="metric-card"><h1>{total_selesai}</h1><p>Selesai</p></div>',
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f'<div class="metric-card"><h1>{total_proses}</h1><p>Dalam Proses</p></div>',
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f'<div class="metric-card"><h1>{rata_respon}</h1><p>Rata-rata Waktu Respon</p></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Aduan
    if col_tgl_buat and "_tgl_buat_parsed" in df.columns:
        st.markdown("#### 📅 Tren Aduan")
        granu = st.radio(
            "Granularitas:", ["Harian", "Bulanan"], horizontal=True, key="tren_granu"
        )
        df_tren = df.dropna(subset=["_tgl_buat_parsed"]).copy()
        if granu == "Harian":
            df_tren["_periode"] = df_tren["_tgl_buat_parsed"].dt.date
        else:
            df_tren["_periode"] = df_tren["_tgl_buat_parsed"].dt.to_period("M").dt.to_timestamp()

        tren = df_tren.groupby("_periode").size().reset_index(name="Jumlah Aduan")
        fig_tren = px.line(
            tren, x="_periode", y="Jumlah Aduan",
            markers=True,
            color_discrete_sequence=["#56b4e9"],
            template="plotly_dark",
        )
        fig_tren.update_layout(
            xaxis_title="Periode",
            yaxis_title="Jumlah Aduan",
            plot_bgcolor="#0d2137",
            paper_bgcolor="#0d2137",
        )
        st.plotly_chart(fig_tren, use_container_width=True)
    else:
        st.info("Kolom tanggal buat tidak ditemukan — tren tidak dapat ditampilkan.")

    # Distribusi Jenis & Kanal 
    c1, c2 = st.columns(2)

    with c1:
        if col_jenis:
            st.markdown("#### 🔴 Distribusi Jenis Keluhan")
            jenis_count = df[col_jenis].value_counts().head(10).reset_index()
            jenis_count.columns = ["Jenis Keluhan", "Jumlah"]
            fig_jenis = px.bar(
                jenis_count, x="Jumlah", y="Jenis Keluhan",
                orientation="h",
                color="Jumlah",
                color_continuous_scale="Blues",
                template="plotly_dark",
            )
            fig_jenis.update_layout(
                plot_bgcolor="#0d2137",
                paper_bgcolor="#0d2137",
                coloraxis_showscale=False,
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig_jenis, use_container_width=True)
        else:
            st.info("Kolom jenis keluhan tidak ditemukan.")

    with c2:
        if col_kanal:
            st.markdown("#### 📡 Distribusi Kanal Aduan")
            kanal_count = df[col_kanal].value_counts().reset_index()
            kanal_count.columns = ["Kanal", "Jumlah"]
            fig_kanal = px.pie(
                kanal_count, names="Kanal", values="Jumlah",
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Blues_r,
                template="plotly_dark",
            )
            fig_kanal.update_layout(
                plot_bgcolor="#0d2137",
                paper_bgcolor="#0d2137",
            )
            st.plotly_chart(fig_kanal, use_container_width=True)
        else:
            st.info("Kolom kanal aduan tidak ditemukan.")

    #  Status Aduan
    if col_status:
        st.markdown("#### 🚦 Status Aduan")
        status_count = df[col_status].value_counts().reset_index()
        status_count.columns = ["Status", "Jumlah"]
        warna_map = {
            "selesai": "#2ecc71", "closed": "#2ecc71", "done": "#2ecc71",
            "proses": "#f39c12", "pending": "#f39c12", "open": "#f39c12",
            "baru": "#3498db",
        }
        colors = [
            warna_map.get(s.lower(), "#56b4e9") for s in status_count["Status"]
        ]
        fig_status = go.Figure(
            go.Bar(
                x=status_count["Status"],
                y=status_count["Jumlah"],
                marker_color=colors,
                text=status_count["Jumlah"],
                textposition="outside",
            )
        )
        fig_status.update_layout(
            template="plotly_dark",
            plot_bgcolor="#0d2137",
            paper_bgcolor="#0d2137",
            xaxis_title="Status",
            yaxis_title="Jumlah",
        )
        st.plotly_chart(fig_status, use_container_width=True)

    #  Statistik per Unit & Petugas
    st.markdown("---")
    st.markdown("#### 🏢 Statistik per Unit & Petugas")
    u1, u2 = st.columns(2)

    with u1:
        if col_unit:
            unit_count = df[col_unit].value_counts().head(10).reset_index()
            unit_count.columns = ["Unit", "Jumlah Aduan"]
            fig_unit = px.bar(
                unit_count, x="Unit", y="Jumlah Aduan",
                color="Jumlah Aduan",
                color_continuous_scale="Blues",
                template="plotly_dark",
                title="Top 10 Unit dengan Aduan Terbanyak",
            )
            fig_unit.update_layout(
                plot_bgcolor="#0d2137",
                paper_bgcolor="#0d2137",
                coloraxis_showscale=False,
                xaxis_tickangle=-30,
            )
            st.plotly_chart(fig_unit, use_container_width=True)
        else:
            st.info("Kolom unit tidak ditemukan.")

    with u2:
        if col_petugas:
            pet_count = df[col_petugas].value_counts().head(10).reset_index()
            pet_count.columns = ["Petugas", "Jumlah Aduan"]
            fig_pet = px.bar(
                pet_count, x="Petugas", y="Jumlah Aduan",
                color="Jumlah Aduan",
                color_continuous_scale="Teal",
                template="plotly_dark",
                title="Top 10 Petugas Penanganan",
            )
            fig_pet.update_layout(
                plot_bgcolor="#0d2137",
                paper_bgcolor="#0d2137",
                coloraxis_showscale=False,
                xaxis_tickangle=-30,
            )
            st.plotly_chart(fig_pet, use_container_width=True)
        else:
            st.info("Kolom petugas tidak ditemukan.")

    #  Peta Area 
    if col_lat and col_lon:
        st.markdown("---")
        st.markdown("#### 🗺️ Peta Sebaran Keluhan")
        df_map = df[[col_lat, col_lon]].dropna().copy()
        df_map.columns = ["lat", "lon"]
        df_map["lat"] = pd.to_numeric(df_map["lat"], errors="coerce")
        df_map["lon"] = pd.to_numeric(df_map["lon"], errors="coerce")
        df_map = df_map.dropna()
        if not df_map.empty:
            st.map(df_map, zoom=10)
        else:
            st.warning("Data koordinat tidak valid / kosong.")
    elif col_area:
        st.markdown("---")
        st.markdown("#### 📍 Distribusi per Area")
        area_count = df[col_area].value_counts().head(15).reset_index()
        area_count.columns = ["Area", "Jumlah"]
        fig_area = px.bar(
            area_count, x="Jumlah", y="Area",
            orientation="h",
            color="Jumlah",
            color_continuous_scale="Viridis",
            template="plotly_dark",
        )
        fig_area.update_layout(
            plot_bgcolor="#0d2137",
            paper_bgcolor="#0d2137",
            coloraxis_showscale=False,
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_area, use_container_width=True)

    # Monitoring Waktu Respon 
    if col_tgl_buat and col_tgl_update and "_tgl_buat_parsed" in df.columns:
        st.markdown("---")
        st.markdown("#### ⏱️ Monitoring Waktu Respon (hari)")
        df_wr = df.dropna(subset=["_tgl_buat_parsed", "_tgl_update_parsed"]).copy()
        df_wr["waktu_respon"] = (
            df_wr["_tgl_update_parsed"] - df_wr["_tgl_buat_parsed"]
        ).dt.days
        df_wr = df_wr[df_wr["waktu_respon"] >= 0]
        if not df_wr.empty:
            fig_wr = px.histogram(
                df_wr, x="waktu_respon",
                nbins=30,
                color_discrete_sequence=["#56b4e9"],
                template="plotly_dark",
                labels={"waktu_respon": "Waktu Respon (hari)"},
                title="Distribusi Waktu Respon Aduan",
            )
            fig_wr.update_layout(
                plot_bgcolor="#0d2137",
                paper_bgcolor="#0d2137",
            )
            st.plotly_chart(fig_wr, use_container_width=True)

            wr_metrics = df_wr["waktu_respon"].describe()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Rata-rata", f"{wr_metrics['mean']:.1f} hari")
            m2.metric("Median",    f"{wr_metrics['50%']:.1f} hari")
            m3.metric("Tercepat",  f"{wr_metrics['min']:.0f} hari")
            m4.metric("Terlama",   f"{wr_metrics['max']:.0f} hari")

  # Tabel Aduan dengan Filter
    st.markdown("---")
    st.markdown("#### 📋 Tabel Data Aduan")

    df_filter = df.copy()

    with st.expander("🔽 Filter Data", expanded=False):
        fc = st.columns(3)
        idx = 0

        if col_tgl_buat and "_tgl_buat_parsed" in df_filter.columns:
            valid_dates = df_filter["_tgl_buat_parsed"].dropna()
            if not valid_dates.empty:
                min_d, max_d = valid_dates.min().date(), valid_dates.max().date()
                with fc[idx % 3]:
                    rentang = st.date_input(
                        "Rentang Tanggal", value=(min_d, max_d),
                        min_value=min_d, max_value=max_d, key="filter_tgl"
                    )
                if len(rentang) == 2:
                    df_filter = df_filter[
                        df_filter["_tgl_buat_parsed"].dt.date.between(rentang[0], rentang[1])
                    ]
                idx += 1

        if col_jenis:
            semua_jenis = ["Semua"] + sorted(df[col_jenis].dropna().unique().tolist())
            with fc[idx % 3]:
                jenis_sel = st.selectbox("Jenis Keluhan", semua_jenis, key="filter_jenis")
            if jenis_sel != "Semua":
                df_filter = df_filter[df_filter[col_jenis] == jenis_sel]
            idx += 1

        if col_kanal:
            semua_kanal = ["Semua"] + sorted(df[col_kanal].dropna().unique().tolist())
            with fc[idx % 3]:
                kanal_sel = st.selectbox("Kanal", semua_kanal, key="filter_kanal")
            if kanal_sel != "Semua":
                df_filter = df_filter[df_filter[col_kanal] == kanal_sel]
            idx += 1

        if col_status:
            semua_status = ["Semua"] + sorted(df[col_status].dropna().unique().tolist())
            with fc[idx % 3]:
                status_sel = st.selectbox("Status", semua_status, key="filter_status")
            if status_sel != "Semua":
                df_filter = df_filter[df_filter[col_status] == status_sel]
            idx += 1

        if col_area:
            semua_area = ["Semua"] + sorted(df[col_area].dropna().unique().tolist())
            with fc[idx % 3]:
                area_sel = st.selectbox("Area", semua_area, key="filter_area")
            if area_sel != "Semua":
                df_filter = df_filter[df_filter[col_area] == area_sel]

    cols_bantu = [c for c in ["_tgl_buat_parsed", "_tgl_update_parsed"] if c in df_filter.columns]
    tampil_df = df_filter.drop(columns=cols_bantu)

    st.markdown(f"**{len(tampil_df):,} baris** setelah filter")
    st.dataframe(tampil_df, use_container_width=True, height=400)




def ml(df):
    st.subheader("🤖 Prioritas Penanganan Aduan (ML Scoring)")

    st.markdown(
        """
        <style>
        .priority-KRITIS { background:#7b0000;border-left:5px solid #ff1744;padding:10px 14px;border-radius:8px;margin:4px 0; }
        .priority-TINGGI { background:#5c3000;border-left:5px solid #ff6d00;padding:10px 14px;border-radius:8px;margin:4px 0; }
        .priority-SEDANG { background:#3e3000;border-left:5px solid #ffd600;padding:10px 14px;border-radius:8px;margin:4px 0; }
        .priority-RENDAH { background:#0d2137;border-left:5px solid #56b4e9;padding:10px 14px;border-radius:8px;margin:4px 0; }
        .badge-KRITIS { background:#ff1744;color:#fff;padding:2px 10px;border-radius:20px;font-weight:700;font-size:0.8rem; }
        .badge-TINGGI { background:#ff6d00;color:#fff;padding:2px 10px;border-radius:20px;font-weight:700;font-size:0.8rem; }
        .badge-SEDANG { background:#ffd600;color:#000;padding:2px 10px;border-radius:20px;font-weight:700;font-size:0.8rem; }
        .badge-RENDAH { background:#56b4e9;color:#000;padding:2px 10px;border-radius:20px;font-weight:700;font-size:0.8rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    #  Deteksi kolom 
    col_jenis  = _cari_kolom(df, ["jenis_keluhan", "jenis", "kategori", "keluhan", "keterangan_keluhan", "uraian"])
    col_uraian = _cari_kolom(df, ["uraian", "uraian_keluhan", "deskripsi", "keterangan", "detail"])
    col_area   = _cari_kolom(df, ["area", "wilayah", "kecamatan", "kelurahan", "zona"])
    col_status = _cari_kolom(df, ["status", "status_aduan", "kondisi"])
    col_nama   = _cari_kolom(df, ["nama", "nama_pelanggan", "customer_name"])
    col_tgl    = _cari_kolom(df, ["tgl_buat", "tanggal_buat", "tanggal", "created_at", "tgl_masuk"])

    if not col_jenis and not col_uraian:
        st.warning("⚠️ Kolom jenis keluhan / uraian tidak ditemukan. Tidak bisa menghitung skor prioritas.")
        return

    DEFAULT_RULES = {
        "air mati total"    : 95,
        "emergency"         : 95,
        "darurat"           : 90,
        "urgent"            : 90,
        "air mati"          : 85,
        "tidak ada air"     : 85,
        "tidak mengalir"    : 80,
        "bocor besar"       : 80,
        "pipa peca "       : 78,
        "banjir"            : 75,
        "kebocoran"         : 65,
        "bocor"             : 60,
        "air kotor"         : 55,
        "air keruh"         : 50,
        "bau"               : 45,
        "tekanan rendah"    : 40,
        "air kecil"         : 38,
        "tagihan salah"     : 35,
        "tagihan tinggi"    : 30,
        "meter rusak"       : 30,
        "gangguan"          : 25,
        "pelayanan lambat"  : 20,
        "air keruh sedikit" : 15,
        "pertanyaan"        : 10,
        "informasi"         : 10,
    }

    DEFAULT_AREA_BOBOT = {
        "rumah sakit" : 20,
        "rs "         : 20,
        "puskesmas"   : 15,
        "sekolah"     : 10,
        "pasar"       : 8,
        "industri"    : 12,
        "pabrik"      : 12,
    }

    # Panel kustomisasi bobot (opsional) 
    with st.expander("⚙️ Kustomisasi Bobot Kata Kunci", expanded=False):
        st.markdown(
            "Sesuaikan bobot tiap kata kunci (0–100). "
            "Skor akhir = nilai kata kunci tertinggi yang cocok + bonus area strategis."
        )
        rules_edit = {}
        cols_rule = st.columns(3)
        for i, (kw, bw) in enumerate(DEFAULT_RULES.items()):
            with cols_rule[i % 3]:
                rules_edit[kw] = st.slider(kw, 0, 100, bw, key=f"kw_{kw}")

        st.markdown("**Bonus Area Strategis:**")
        cols_area_s = st.columns(3)
        area_edit = {}
        for i, (ak, av) in enumerate(DEFAULT_AREA_BOBOT.items()):
            with cols_area_s[i % 3]:
                area_edit[ak] = st.slider(ak, 0, 30, av, key=f"area_{ak}")

    # Gunakan default jika expander tidak diubah
    if not rules_edit:
        rules_edit = DEFAULT_RULES
    if not area_edit:
        area_edit = DEFAULT_AREA_BOBOT

    def hitung_skor(row):
        teks = ""
        if col_jenis  and col_jenis  in row.index: teks += " " + str(row[col_jenis]).lower()
        if col_uraian and col_uraian in row.index: teks += " " + str(row[col_uraian]).lower()

        skor = 5  # baseline minimum
        matched_kw = []
        for kw, bw in rules_edit.items():
            if kw in teks:
                matched_kw.append((kw, bw))
                if bw > skor:
                    skor = bw

        bonus_area = 0
        teks_area = str(row[col_area]).lower() if col_area and col_area in row.index else ""
        for ak, av in area_edit.items():
            if ak in teks_area and av > bonus_area:
                bonus_area = av

        skor_final = min(skor + bonus_area, 100)

        if skor_final >= 80:   label = "KRITIS"
        elif skor_final >= 55: label = "TINGGI"
        elif skor_final >= 30: label = "SEDANG"
        else:                  label = "RENDAH"

        return pd.Series({
            "skor_prioritas"   : skor_final,
            "label_prioritas"  : label,
            "kata_kunci_cocok" : ", ".join(kw for kw, _ in matched_kw) or "-",
        })

    with st.spinner("Menghitung skor prioritas..."):
        skor_df = df.apply(hitung_skor, axis=1)
        df_ml   = pd.concat([df.reset_index(drop=True), skor_df.reset_index(drop=True)], axis=1)

   
    #  KPI DISTRIBUSI
  
    st.markdown("---")
    st.markdown("#### 📊 Ringkasan Distribusi Prioritas")

    counts = df_ml["label_prioritas"].value_counts()
    k1, k2, k3, k4 = st.columns(4)
    for col_ui, label, emoji in zip(
        [k1, k2, k3, k4],
        ["KRITIS", "TINGGI", "SEDANG", "RENDAH"],
        ["🔴", "🟠", "🟡", "🔵"],
    ):
        col_ui.metric(f"{emoji} {label}", counts.get(label, 0))

    warna_prior = {"KRITIS": "#ff1744", "TINGGI": "#ff6d00", "SEDANG": "#ffd600", "RENDAH": "#56b4e9"}

    ch1, ch2 = st.columns(2)
    with ch1:
        dist_df = df_ml["label_prioritas"].value_counts().reset_index()
        dist_df.columns = ["Prioritas", "Jumlah"]
        fig_dist = px.pie(
            dist_df, names="Prioritas", values="Jumlah",
            hole=0.5,
            color="Prioritas",
            color_discrete_map=warna_prior,
            template="plotly_dark",
            title="Proporsi Prioritas",
        )
        fig_dist.update_layout(paper_bgcolor="#0d2137", plot_bgcolor="#0d2137")
        st.plotly_chart(fig_dist, use_container_width=True)

    with ch2:
        fig_hist = px.histogram(
            df_ml, x="skor_prioritas", nbins=20,
            color="label_prioritas",
            color_discrete_map=warna_prior,
            template="plotly_dark",
            title="Distribusi Skor Prioritas",
            labels={"skor_prioritas": "Skor (0–100)"},
        )
        fig_hist.update_layout(
            paper_bgcolor="#0d2137", plot_bgcolor="#0d2137", barmode="stack"
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    # Area dengan aduan kritis terbanyak
    if col_area:
        df_kritis_area = df_ml[df_ml["label_prioritas"].isin(["KRITIS", "TINGGI"])]
        if not df_kritis_area.empty:
            st.markdown("#### 📍 Area dengan Aduan KRITIS & TINGGI Terbanyak")
            area_kritis = df_kritis_area[col_area].value_counts().head(10).reset_index()
            area_kritis.columns = ["Area", "Jumlah"]
            fig_ak = px.bar(
                area_kritis, x="Jumlah", y="Area", orientation="h",
                color_discrete_sequence=["#ff1744"],
                template="plotly_dark",
            )
            fig_ak.update_layout(
                paper_bgcolor="#0d2137", plot_bgcolor="#0d2137",
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig_ak, use_container_width=True)


    st.markdown("---")
    st.markdown("#### 📋 Tabel Hasil Scoring")

    filter_label = st.multiselect(
        "Filter Prioritas:",
        ["KRITIS", "TINGGI", "SEDANG", "RENDAH"],
        default=["KRITIS", "TINGGI"],
        key="ml_filter_label",
    )

    tampil_ml = df_ml[df_ml["label_prioritas"].isin(filter_label)].copy()
    tampil_ml = tampil_ml.sort_values("skor_prioritas", ascending=False)

    kolom_tampil = []
    for c in [col_nama, col_jenis, col_uraian, col_area, col_status, col_tgl]:
        if c and c in tampil_ml.columns:
            kolom_tampil.append(c)
    kolom_tampil += ["skor_prioritas", "label_prioritas", "kata_kunci_cocok"]

    st.markdown(f"**{len(tampil_ml):,} aduan** dengan prioritas **{', '.join(filter_label)}**")
    st.dataframe(
        tampil_ml[kolom_tampil].reset_index(drop=True),
        use_container_width=True,
        height=420,
        column_config={
            "skor_prioritas": st.column_config.ProgressColumn(
                "Skor Prioritas", min_value=0, max_value=100, format="%d",
            ),
            "label_prioritas"  : st.column_config.TextColumn("Prioritas"),
            "kata_kunci_cocok" : st.column_config.TextColumn("Kata Kunci Terdeteksi"),
        },
    )

    # Kartu 5 aduan KRITIS teratas 
    df_top_kritis = df_ml[df_ml["label_prioritas"] == "KRITIS"].sort_values(
        "skor_prioritas", ascending=False
    ).head(5)

    if not df_top_kritis.empty:
        st.markdown("---")
        st.markdown("#### 🚨 5 Aduan KRITIS Teratas — Perlu Segera Ditangani")
        for _, row in df_top_kritis.iterrows():
            nama_val  = row[col_nama]   if col_nama   else "—"
            jenis_val = row[col_jenis]  if col_jenis  else "—"
            area_val  = row[col_area]   if col_area   else "—"
            urai_val  = row[col_uraian] if col_uraian else "—"
            skor_val  = int(row["skor_prioritas"])
            kw_val    = row["kata_kunci_cocok"]
            st.markdown(
                f"""
                <div class="priority-KRITIS">
                    <span class="badge-KRITIS">KRITIS &nbsp; {skor_val}/100</span>
                    &nbsp;&nbsp;<strong>{nama_val}</strong> — {area_val}<br>
                    <span style="color:#ffcdd2">📌 Jenis: {jenis_val}</span><br>
                    <span style="color:#ef9a9a">📝 {urai_val}</span><br>
                    <span style="color:#b71c1c;font-size:0.8rem">🔑 Kata kunci: {kw_val}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Download hasil
    st.markdown("---")
    csv_out = tampil_ml[kolom_tampil].to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Hasil Scoring (.csv)",
        data=csv_out,
        file_name="hasil_prioritas_aduan.csv",
        mime="text/csv",
        key="dl_ml_csv",
    )



import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import timedelta

try:
    from statsmodels.tsa.arima.model import ARIMA
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

def _col(df, candidates):
    cl = [c.lower() for c in candidates]
    for c in df.columns:
        if c.lower() in cl:
            return c
    return None


#  ENGINE 1 — ARIMA / WMA+Trend  (time-series per minggu)

def _predict_series(series: pd.Series, steps: int):
    """
    Coba ARIMA(2,1,2) → fallback ke Weighted Moving Average + Trend.
    Kembalikan (preds, lower_ci, upper_ci) masing-masing list panjang `steps`.
    """
    vals = series.dropna().values
    if len(vals) < 6:
        mean = float(np.mean(vals)) if len(vals) > 0 else 0
        return ([max(0, round(mean))] * steps,
                [max(0, round(mean * 0.7))] * steps,
                [round(mean * 1.3)] * steps)

    # ARIMA 
    if ARIMA_AVAILABLE and len(vals) >= 12:
        try:
            mdl = ARIMA(vals, order=(2, 1, 2))
            res = mdl.fit()
            fc  = res.get_forecast(steps=steps)
            pm  = fc.predicted_mean
            ci  = fc.conf_int(alpha=0.2)
            return ([max(0, round(float(p))) for p in pm],
                    [max(0, round(float(l))) for l in ci[:, 0]],
                    [round(float(u)) for u in ci[:, 1]])
        except Exception:
            pass

    # Prophet 
    if PROPHET_AVAILABLE and len(vals) >= 10:
        try:
            idx = series.dropna().index
            pdf = pd.DataFrame({"ds": idx, "y": vals})
            m   = Prophet(interval_width=0.80, weekly_seasonality=True,
                          yearly_seasonality=True, daily_seasonality=False)
            m.fit(pdf)
            future = m.make_future_dataframe(periods=steps, freq="W")
            fc     = m.predict(future).tail(steps)
            return ([max(0, round(v)) for v in fc["yhat"].values],
                    [max(0, round(v)) for v in fc["yhat_lower"].values],
                    [round(v) for v in fc["yhat_upper"].values])
        except Exception:
            pass

    # WMA + Trend (fallback)
    n       = min(len(vals), 8)
    weights = np.arange(1, n + 1, dtype=float)
    wma     = float(np.average(vals[-n:], weights=weights))
    half    = max(3, n // 2)
    prev    = float(vals[-n:-half].mean()) if (n - half) > 0 else wma
    curr    = float(vals[-half:].mean())
    trend   = float(np.clip((curr - prev) / (prev + 1e-9), -0.35, 0.35))

    preds, lowers, uppers = [], [], []
    for i in range(1, steps + 1):
        p = max(0, round(wma * (1 + trend * 0.45 * i)))
        u = max(1, round(p * 0.18))
        preds.append(p); lowers.append(max(0, p - u)); uppers.append(p + u)
    return preds, lowers, uppers



#  ENGINE 2 — Area Risk Scoring

def _area_risk(df, col_area, col_jenis, col_severity, col_waktu):
    window = df["_tgl"].max() - timedelta(days=90)
    recent = df[df["_tgl"] >= window]

    rows = []
    for area in sorted(recent[col_area].dropna().unique()):
        adf   = recent[recent[col_area] == area]
        total = len(adf)
        if total == 0:
            continue

        kritis = (adf[col_severity].str.upper() == "KRITIS").sum() \
                 if col_severity else 0
        avg_t  = adf[col_waktu].mean() if col_waktu else 0

        type_dist = (adf[col_jenis].value_counts(normalize=True) * 100).round(1) \
                    if col_jenis else pd.Series()
        dominant  = type_dist.idxmax() if len(type_dist) else "-"

        # Skor risiko (0–100)
        freq_s   = min(total / 30 * 40, 40)
        kritis_s = min((kritis / (total + 1e-9)) * 35, 35)
        time_s   = min((avg_t / 180) * 25, 25) if avg_t else 0
        score    = round(freq_s + kritis_s + time_s)

        # Tren (naik / turun / stabil) dalam 4 minggu terakhir
        w_series = adf.groupby(adf["_tgl"].dt.to_period("W")).size()
        if len(w_series) >= 3:
            diff   = w_series.diff().dropna()
            trend  = "🔺 Naik" if diff.tail(2).mean() > 0.5 else \
                     "🔻 Turun" if diff.tail(2).mean() < -0.5 else "➡️ Stabil"
        else:
            trend = "➡️ Stabil"

        rows.append({
            "area": area, "total_aduan": int(total),
            "aduan_kritis": int(kritis),
            "avg_waktu_mnt": round(float(avg_t), 1) if avg_t else 0,
            "jenis_dominan": dominant,
            "risk_score": score,
            "risk_level": "TINGGI" if score >= 62 else "SEDANG" if score >= 35 else "RENDAH",
            "tren": trend,
            "type_dist": type_dist.to_dict(),
            "prob_mgg_depan": round(min(0.95, 0.20 + score / 100 * 0.78), 2),
        })

    return pd.DataFrame(rows).sort_values("risk_score", ascending=False)

#  ENGINE 3 — Action Recommendations

ACTION_MAP = {
    "air mati":        ("Cek jaringan distribusi utama & katup induk",
                        "Periksa pompa booster, katup gate, dan pasokan dari IPA.",
                        "Katup gate, impeller pompa, seal"),
    "tidak mengalir":  ("Cek jaringan distribusi utama & katup induk",
                        "Sama seperti air mati — pastikan katup terbuka penuh.",
                        "Katup gate, impeller pompa"),
    "tidak ada air":   ("Cek jaringan distribusi utama & katup induk",
                        "Pastikan tidak ada gangguan di reservoir atau pompa.",
                        "Katup gate, impeller pompa"),
    "tekanan rendah":  ("Inspeksi tekanan pipa & kapasitas pompa distribusi",
                        "Ukur tekanan di titik kritis, cek kebocoran tersembunyi.",
                        "Pressure gauge, seal pipa, pompa portabel"),
    "air kecil":       ("Inspeksi tekanan pipa & kapasitas pompa distribusi",
                        "Kemungkinan kebocoran mikro atau pompa melemah.",
                        "Pressure gauge, seal pipa"),
    "bocor":           ("Terjunkan tim survey kebocoran pipa segera",
                        "Gunakan leak detector, periksa pipa di titik padat.",
                        "Repair clamp, pipa HDPE, fitting"),
    "kebocoran":       ("Terjunkan tim survey kebocoran pipa segera",
                        "Prioritaskan area padat penduduk dan jalan utama.",
                        "Repair clamp, pipa HDPE"),
    "air keruh":       ("Pengecekan kualitas sumber air & sistem filtrasi",
                        "Uji turbidity & coliform, periksa filter dan sedimentasi.",
                        "Media filter, karbon aktif, kaporit"),
    "air kotor":       ("Pengecekan kualitas sumber air & sistem filtrasi",
                        "Cuci tangki distribusi, uji kualitas fisik & kimia.",
                        "Media filter, karbon aktif"),
    "tagihan":         ("Audit meteran & verifikasi tagihan pelanggan",
                        "Cek fisik meteran, kalibrasi, rekonsiliasi data billing.",
                        "Meteran air, segel meteran"),
    "meter":           ("Penggantian / kalibrasi meteran",
                        "Ganti meteran yang rusak atau bacaan tidak valid.",
                        "Meteran air, segel"),
}

def _match_action(jenis_str: str):
    jl = str(jenis_str).lower()
    for kw, (act, det, spare) in ACTION_MAP.items():
        if kw in jl:
            return act, det, spare
    return "Pengecekan umum & inspeksi lapangan", \
           "Tim lapangan harap melakukan pengecekan menyeluruh.", \
           "Toolkit umum petugas"


def _build_recommendations(df, col_area, col_jenis, col_severity, col_waktu):
    window = df["_tgl"].max() - timedelta(days=14)
    recent = df[df["_tgl"] >= window]
    recs   = []

    if not col_area or not col_jenis:
        return recs

    for area in recent[col_area].dropna().unique():
        for jenis in recent[col_jenis].dropna().unique():
            sub    = recent[(recent[col_area] == area) & (recent[col_jenis] == jenis)]
            n      = len(sub)
            if n < 3:
                continue
            kritis = int((sub[col_severity].str.upper() == "KRITIS").sum()) \
                     if col_severity else 0
            priority = "TINGGI" if (kritis >= 2 or n >= 8) else \
                       "SEDANG" if n >= 5 else "RENDAH"
            act, det, spare = _match_action(jenis)
            recs.append({
                "area": area, "jenis": jenis,
                "jumlah": n, "kritis": kritis,
                "priority": priority,
                "action": f"{act} — {area}",
                "detail": det,
                "spare_part": spare,
                "confidence": min(96, 50 + n * 4 + kritis * 9),
            })

    return sorted(recs, key=lambda x: {"TINGGI": 0, "SEDANG": 1, "RENDAH": 2}[x["priority"]])



#  ENGINE 4 — Petugas Performance & Recommendation
def _petugas_performance(df, col_petugas, col_jenis, col_area, col_waktu, col_severity):
    if not col_petugas:
        return pd.DataFrame()

    rows = []
    for pet in df[col_petugas].dropna().unique():
        pdf   = df[df[col_petugas] == pet]
        total = len(pdf)
        avg_t = float(pdf[col_waktu].mean()) if col_waktu and total > 0 else 0
        kritis = int((pdf[col_severity].str.upper() == "KRITIS").sum()) \
                 if col_severity else 0

        by_type = {}
        if col_jenis:
            for t in pdf[col_jenis].dropna().unique():
                td = pdf[pdf[col_jenis] == t]
                by_type[t] = {
                    "count": len(td),
                    "avg_t": round(float(td[col_waktu].mean()), 1) if col_waktu and len(td) else 0,
                }
        by_area = {}
        if col_area:
            for a in pdf[col_area].dropna().unique():
                ad = pdf[pdf[col_area] == a]
                by_area[a] = {
                    "count": len(ad),
                    "avg_t": round(float(ad[col_waktu].mean()), 1) if col_waktu and len(ad) else 0,
                }

        eff = max(0, min(100, 100 - (avg_t / 200 * 50) + (kritis / (total + 1e-9) * 25)))
        rows.append({
            "petugas": pet, "total": total, "avg_waktu": round(avg_t, 1),
            "kritis": kritis, "efisiensi": round(eff, 1),
            "by_type": by_type, "by_area": by_area,
        })

    return pd.DataFrame(rows).sort_values("efisiensi", ascending=False)


def _recommend_petugas(pet_df, jenis, area):
    if pet_df.empty:
        return pet_df
    result = pet_df.copy()
    result["skor_rekomendasi"] = 0.0
    for idx, row in result.iterrows():
        s = row["efisiensi"] * 0.4
        bt = row["by_type"].get(jenis, {})
        ba = row["by_area"].get(area, {})
        if bt.get("avg_t", 0) > 0:
            s += max(0, 30 - bt["avg_t"] * 0.15)
        s += min(15, ba.get("count", 0) * 1.5)
        if bt.get("count", 0) >= 5:
            s += 10
        result.at[idx, "skor_rekomendasi"] = round(s, 1)
    return result.sort_values("skor_rekomendasi", ascending=False)


def prediksi(df):
    st.subheader("📈 Prediksi & Rekomendasi Aduan")

   
    st.markdown("""
    <style>
    .pred-card {
        background: linear-gradient(135deg,#1e3a5f,#0d2137);
        border:1px solid #2e6da4; border-radius:12px;
        padding:16px 20px; margin:6px 0; color:#e8f4fd;
    }
    .pred-card h4 { margin:0 0 4px 0; color:#56b4e9; font-size:1rem; }
    .pred-card p  { margin:0; font-size:0.88rem; color:#a8c9e8; }
    .risk-TINGGI { border-left:5px solid #ef4444!important; background:#1a0a0a!important; }
    .risk-SEDANG { border-left:5px solid #f59e0b!important; background:#1a1408!important; }
    .risk-RENDAH { border-left:5px solid #10b981!important; background:#081a12!important; }
    .badge { display:inline-block; padding:2px 10px; border-radius:20px;
             font-size:0.76rem; font-weight:700; margin-right:6px; }
    .badge-TINGGI { background:#ef4444; color:#fff; }
    .badge-SEDANG { background:#f59e0b; color:#000; }
    .badge-RENDAH { background:#10b981; color:#fff; }
    .badge-blue   { background:#3b82f6; color:#fff; }
    .info-analogi {
        background:#0f2a3f; border:1px solid #38bdf840;
        border-radius:10px; padding:14px 18px; margin:10px 0;
        color:#93c5fd; font-size:0.88rem;
    }
    </style>
    """, unsafe_allow_html=True)

    


    # Deteksi kolom 
    col_tgl      = _col(df, ["tgl_buat","tanggal_buat","tanggal","created_at","tgl_masuk","tgl_aduan"])
    col_jenis    = _col(df, ["jenis_keluhan","jenis","kategori","keluhan","keterangan_keluhan"])
    col_area     = _col(df, ["area","wilayah","kecamatan","kelurahan","zona"])
    col_severity = _col(df, ["severity","prioritas","label_prioritas","tingkat","urgency","status"])
    col_waktu    = _col(df, ["waktu_selesai","waktu_penyelesaian","durasi","response_time",
                             "waktu_respon","lama_penanganan","waktu_selesai_mnt"])
    col_petugas  = _col(df, ["petugas","nama_petugas","officer","assigned_to","teknisi"])

    # Parsing tanggal
    if not col_tgl:
        st.error("❌ Kolom tanggal tidak ditemukan. Kolom yang dibutuhkan: tgl_buat / tanggal / created_at")
        return

    df = df.copy()
    df["_tgl"] = pd.to_datetime(df[col_tgl], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["_tgl"])

    if df.empty:
        st.error("❌ Tidak ada baris dengan tanggal valid setelah parsing.")
        return

    # Parsing waktu numerik
    if col_waktu:
        df[col_waktu] = pd.to_numeric(df[col_waktu], errors="coerce")

    # Sidebar filter
    with st.sidebar:
        st.markdown("### ⚙️ Pengaturan Prediksi")
        weeks_ahead = st.slider("Prediksi berapa minggu ke depan?", 1, 12, 4, key="pred_weeks")
        if col_area:
            all_areas = ["Semua"] + sorted(df[col_area].dropna().unique().tolist())
            sel_area = st.selectbox("Filter Area", all_areas, key="pred_area")
        else:
            sel_area = "Semua"
        if col_jenis:
            all_types = ["Semua"] + sorted(df[col_jenis].dropna().unique().tolist())
            sel_type = st.selectbox("Filter Jenis Keluhan", all_types, key="pred_type")
        else:
            sel_type = "Semua"

        st.markdown("---")
        method_used = "ARIMA(2,1,2)" if ARIMA_AVAILABLE else \
                      "Prophet" if PROPHET_AVAILABLE else "WMA + Trend"
        st.info(f"**Metode:** {method_used}\n\n"
                f"ARIMA: {'✅' if ARIMA_AVAILABLE else '❌'}  "
                f"Prophet: {'✅' if PROPHET_AVAILABLE else '❌'}")

    # Tab utama
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Prediksi Lonjakan",
        "🎯 Rekomendasi Tindakan",
        "👷 Rekomendasi Petugas",
        "📍 Prioritas Area",
    ])

    
    #  TAB 1 — PREDIKSI LONJAKAN

    with tab1:
        st.markdown("#### 📈 Prediksi Jumlah Aduan per Minggu")

        # Filter data
        fdf = df.copy()
        if sel_area != "Semua" and col_area:
            fdf = fdf[fdf[col_area] == sel_area]
        if sel_type != "Semua" and col_jenis:
            fdf = fdf[fdf[col_jenis] == sel_type]

        if fdf.empty:
            st.warning("Tidak ada data untuk filter yang dipilih.")
        else:
            # Agregasi mingguan
            weekly = (fdf.groupby(fdf["_tgl"].dt.to_period("W"))
                        .size().reset_index(name="jumlah"))
            weekly["_ds"] = weekly["_tgl"].apply(lambda p: p.start_time)
            weekly = weekly.sort_values("_ds").set_index("_ds")

            # Prediksi
            preds, lowers, uppers = _predict_series(weekly["jumlah"], steps=weeks_ahead)
            last_date = weekly.index[-1]
            future_dates = [last_date + timedelta(weeks=i) for i in range(1, weeks_ahead + 1)]

            # Grafik
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=weekly.index, y=weekly["jumlah"].values,
                mode="lines+markers", name="Historis",
                line=dict(color="#56b4e9", width=2),
                marker=dict(size=4),
            ))
            fig.add_trace(go.Scatter(
                x=future_dates, y=preds,
                mode="lines+markers", name=f"Prediksi ({method_used})",
                line=dict(color="#f59e0b", width=2, dash="dash"),
                marker=dict(size=8, symbol="diamond"),
            ))
            # Confidence interval
            fig.add_trace(go.Scatter(
                x=future_dates + future_dates[::-1],
                y=uppers + lowers[::-1],
                fill="toself", fillcolor="rgba(245,158,11,0.12)",
                line=dict(color="rgba(255,255,255,0)"),
                name="Interval Kepercayaan 80%",
                showlegend=True,
            ))
            # Garis pemisah

            fig.add_shape(
                type="line",
                x0=last_date, x1=last_date,
                y0=0, y1=1,
                xref="x", yref="paper",
                line=dict(color="#94a3b8", width=1, dash="dot"),
            )
            fig.add_annotation(
                x=last_date, y=1,
                xref="x", yref="paper",
                text="Sekarang",
                showarrow=False,
                font=dict(color="#94a3b8", size=11),
                xanchor="left", yanchor="bottom",
            )            
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0d2137", plot_bgcolor="#0d2137",
                xaxis_title="Minggu", yaxis_title="Jumlah Aduan",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                height=420,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Tabel prediksi
            pred_df = pd.DataFrame({
                "Minggu ke-": [f"+{i}" for i in range(1, weeks_ahead + 1)],
                "Tanggal": [d.strftime("%d %b %Y") for d in future_dates],
                "Prediksi Aduan": preds,
                "Batas Bawah": lowers,
                "Batas Atas": uppers,
            })
            st.dataframe(pred_df, use_container_width=True, hide_index=True,
                         column_config={
                             "Prediksi Aduan": st.column_config.ProgressColumn(
                                 min_value=0, max_value=max(uppers + [1]), format="%d"),
                         })

        st.markdown("---")

        #  Prediksi per Jenis Keluhan (Seasonal Decomposition) 
        if col_jenis:
            st.markdown("#### 🔍 Prediksi Jenis Keluhan Dominan")
            st.caption("Berguna untuk: penjadwalan petugas, persiapan teknisi, stok spare part")

            jenis_list = df[col_jenis].value_counts().head(6).index.tolist()
            type_preds = []

            for jenis in jenis_list:
                jdf    = df[df[col_jenis] == jenis]
                wj     = (jdf.groupby(jdf["_tgl"].dt.to_period("W"))
                           .size().reset_index(name="jumlah"))
                wj["_ds"] = wj["_tgl"].apply(lambda p: p.start_time)
                wj = wj.sort_values("_ds").set_index("_ds")
                pj, _, _ = _predict_series(wj["jumlah"], steps=weeks_ahead)
                type_preds.append({
                    "Jenis Keluhan": jenis,
                    "Rata-rata Historis (mg)": round(float(wj["jumlah"].mean()), 1),
                    f"Prediksi Mg +1": pj[0],
                    f"Prediksi Mg +{weeks_ahead}": pj[-1],
                    "Tren": "🔺 Naik" if pj[-1] > pj[0] else "🔻 Turun" if pj[-1] < pj[0] else "➡️ Stabil",
                })

            type_df = pd.DataFrame(type_preds).sort_values(f"Prediksi Mg +{weeks_ahead}", ascending=False)
            st.dataframe(type_df, use_container_width=True, hide_index=True)

            # Bar chart prediksi minggu +1
            bar_fig = px.bar(
                type_df, x="Jenis Keluhan", y="Prediksi Mg +1",
                color="Prediksi Mg +1", color_continuous_scale="Blues",
                template="plotly_dark",
                title=f"Prediksi Aduan per Jenis — Minggu Depan",
                text="Prediksi Mg +1",
            )
            bar_fig.update_layout(
                paper_bgcolor="#0d2137", plot_bgcolor="#0d2137",
                coloraxis_showscale=False, height=350,
            )
            bar_fig.update_traces(textposition="outside")
            st.plotly_chart(bar_fig, use_container_width=True)

        st.markdown("---")

        #  Pola Musiman 
        st.markdown("#### 🗓️ Pola Musiman — Aduan per Bulan")
        monthly = (df.groupby(df["_tgl"].dt.month).size()
                     .reset_index(name="jumlah"))
        monthly.columns = ["Bulan", "Jumlah"]
        bulan_map = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"Mei",6:"Jun",
                     7:"Jul",8:"Agu",9:"Sep",10:"Okt",11:"Nov",12:"Des"}
        monthly["Nama Bulan"] = monthly["Bulan"].map(bulan_map)

        if col_jenis:
            monthly_type = (df.groupby([df["_tgl"].dt.month, col_jenis])
                              .size().reset_index(name="jumlah"))
            monthly_type.columns = ["Bulan", "Jenis", "Jumlah"]
            monthly_type["Nama Bulan"] = monthly_type["Bulan"].map(bulan_map)
            fig_seasonal = px.line(
                monthly_type, x="Nama Bulan", y="Jumlah", color="Jenis",
                markers=True, template="plotly_dark",
                title="Pola Musiman per Jenis Keluhan",
                category_orders={"Nama Bulan": list(bulan_map.values())},
            )
        else:
            fig_seasonal = px.bar(
                monthly, x="Nama Bulan", y="Jumlah",
                color="Jumlah", color_continuous_scale="Blues",
                template="plotly_dark", title="Pola Musiman Aduan",
            )
        fig_seasonal.update_layout(
            paper_bgcolor="#0d2137", plot_bgcolor="#0d2137",
            height=380, coloraxis_showscale=False,
        )
        st.plotly_chart(fig_seasonal, use_container_width=True)

        # Insight otomatis
        if not monthly.empty:
            peak_bulan = monthly.loc[monthly["Jumlah"].idxmax(), "Nama Bulan"]
            low_bulan  = monthly.loc[monthly["Jumlah"].idxmin(), "Nama Bulan"]
            st.info(
                f"📌 **Insight Musiman:** Puncak aduan terjadi di bulan **{peak_bulan}**, "
                f"paling sepi di bulan **{low_bulan}**. "
                f"Gunakan informasi ini untuk alokasi petugas dan stok material."
            )

    
    #  TAB 2 — REKOMENDASI TINDAKAN
   
    with tab2:
        st.markdown("#### 🎯 Rekomendasi Tindakan Otomatis")
        st.caption(
            "Dihasilkan dari pola aduan 14 hari terakhir. "
            "Jika satu area + jenis keluhan ≥ 3 kali → sistem merekomendasikan tindakan."
        )

        if not col_area or not col_jenis:
            st.warning("⚠️ Kolom area dan/atau jenis keluhan tidak ditemukan.")
        else:
            recs = _build_recommendations(df, col_area, col_jenis, col_severity, col_waktu)

            if not recs:
                st.success("✅ Tidak ada kombinasi area + jenis yang melampaui threshold dalam 14 hari terakhir.")
            else:
                # KPI ringkasan
                n_t = sum(1 for r in recs if r["priority"] == "TINGGI")
                n_s = sum(1 for r in recs if r["priority"] == "SEDANG")
                n_r = sum(1 for r in recs if r["priority"] == "RENDAH")
                k1, k2, k3 = st.columns(3)
                k1.metric("🔴 Prioritas TINGGI", n_t)
                k2.metric("🟡 Prioritas SEDANG", n_s)
                k3.metric("🟢 Prioritas RENDAH", n_r)
                st.markdown("---")

                for rec in recs:
                    badge_cls = f"badge-{rec['priority']}"
                    card_cls  = f"risk-{rec['priority']}"
                    st.markdown(f"""
                    <div class="pred-card {card_cls}">
                        <div style="margin-bottom:6px">
                            <span class="badge {badge_cls}">{rec['priority']}</span>
                            <span class="badge badge-blue">Confidence {rec['confidence']}%</span>
                            <b style="color:#f1f5f9">{rec['area']}</b>
                            &nbsp;·&nbsp;
                            <span style="color:#94a3b8">{rec['jenis']}</span>
                        </div>
                        <h4>🔧 {rec['action']}</h4>
                        <p>📋 {rec['detail']}</p>
                        <p>📦 <b>Spare Part Dibutuhkan:</b> {rec['spare_part']}</p>
                        <p style="color:#64748b;font-size:0.8rem">
                            📊 Aduan 14 hari: <b>{rec['jumlah']}</b>
                            &nbsp;·&nbsp; KRITIS: <b>{rec['kritis']}</b>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

            # Heatmap area × jenis
            st.markdown("---")
            st.markdown("#### 🌡️ Heatmap Intensitas Aduan (14 Hari Terakhir)")
            window14 = df["_tgl"].max() - timedelta(days=14)
            recent14 = df[df["_tgl"] >= window14]
            if not recent14.empty:
                heat = recent14.groupby([col_area, col_jenis]).size().reset_index(name="n")
                heat_pivot = heat.pivot(index=col_area, columns=col_jenis, values="n").fillna(0)
                fig_heat = go.Figure(go.Heatmap(
                    z=heat_pivot.values,
                    x=heat_pivot.columns.tolist(),
                    y=heat_pivot.index.tolist(),
                    colorscale="Reds",
                    text=heat_pivot.values.astype(int),
                    texttemplate="%{text}",
                    showscale=True,
                ))
                fig_heat.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#0d2137", plot_bgcolor="#0d2137",
                    xaxis_title="Jenis Keluhan", yaxis_title="Area",
                    height=max(300, len(heat_pivot) * 45 + 100),
                )
                st.plotly_chart(fig_heat, use_container_width=True)

    
    #  TAB 3 — REKOMENDASI PETUGAS
   
    with tab3:
        st.markdown("#### 👷 Rekomendasi Penugasan Petugas Optimal")
        st.caption(
            "Sistem menilai efisiensi petugas berdasarkan "
            "rata-rata waktu penyelesaian per jenis keluhan dan per area."
        )

        if not col_petugas:
            st.warning("⚠️ Kolom petugas tidak ditemukan (nama kolom yang didukung: petugas, nama_petugas, officer, teknisi).")
        else:
            pet_df = _petugas_performance(
                df, col_petugas, col_jenis, col_area, col_waktu, col_severity
            )

            if pet_df.empty:
                st.info("Belum ada data performa petugas.")
            else:
                #Tabel performa
                st.markdown("##### 📊 Performa Keseluruhan Petugas")
                disp_cols = ["petugas", "total", "avg_waktu", "kritis", "efisiensi"]
                st.dataframe(
                    pet_df[disp_cols].reset_index(drop=True),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "petugas"   : st.column_config.TextColumn("Petugas"),
                        "total"     : st.column_config.NumberColumn("Total Tugas"),
                        "avg_waktu" : st.column_config.NumberColumn("Rata-rata Waktu (mnt)"),
                        "kritis"    : st.column_config.NumberColumn("Kasus KRITIS"),
                        "efisiensi" : st.column_config.ProgressColumn(
                            "Skor Efisiensi", min_value=0, max_value=100, format="%.1f"),
                    },
                )

                #  Bar chart efisiensi 
                fig_eff = px.bar(
                    pet_df.sort_values("efisiensi"),
                    x="efisiensi", y="petugas", orientation="h",
                    color="efisiensi", color_continuous_scale="Teal",
                    template="plotly_dark",
                    title="Skor Efisiensi Petugas",
                    text="efisiensi",
                )
                fig_eff.update_layout(
                    paper_bgcolor="#0d2137", plot_bgcolor="#0d2137",
                    coloraxis_showscale=False, height=350,
                )
                fig_eff.update_traces(texttemplate="%{text:.1f}", textposition="outside")
                st.plotly_chart(fig_eff, use_container_width=True)

                # Pencari rekomendasi
                st.markdown("---")
                st.markdown("##### 🔍 Cari Petugas Terbaik untuk Kasus Tertentu")

                c1, c2 = st.columns(2)
                with c1:
                    jenis_opts = sorted(df[col_jenis].dropna().unique()) if col_jenis else []
                    sel_jenis_rec = st.selectbox(
                        "Jenis Keluhan", jenis_opts, key="pet_jenis_sel"
                    ) if jenis_opts else None
                with c2:
                    area_opts = sorted(df[col_area].dropna().unique()) if col_area else []
                    sel_area_rec = st.selectbox(
                        "Area", area_opts, key="pet_area_sel"
                    ) if area_opts else None

                if sel_jenis_rec and sel_area_rec:
                    ranked = _recommend_petugas(pet_df, sel_jenis_rec, sel_area_rec)
                    st.markdown(
                        f"**Rekomendasi petugas untuk** `{sel_jenis_rec}` "
                        f"**di** `{sel_area_rec}` **(dari yang terbaik):**"
                    )
                    for i, (_, row) in enumerate(ranked.head(3).iterrows()):
                        medal = ["🥇", "🥈", "🥉"][i]
                        bt    = row["by_type"].get(sel_jenis_rec, {})
                        ba    = row["by_area"].get(sel_area_rec, {})
                        rank_badge = "badge-TINGGI" if i == 0 else \
                                     "badge-SEDANG" if i == 1 else "badge-RENDAH"
                        st.markdown(f"""
                        <div class="pred-card">
                            {medal}
                            <span class="badge {rank_badge}">Skor {row['skor_rekomendasi']}</span>
                            &nbsp;<b style="color:#f1f5f9">{row['petugas']}</b><br>
                            <span style="color:#94a3b8;font-size:0.85rem">
                                🕐 Waktu rata-rata jenis ini:
                                <b>{bt.get('avg_t', 'N/A')} mnt</b>
                                ({bt.get('count', 0)} kasus)
                                &nbsp;·&nbsp;
                                Pengalaman di area:
                                <b>{ba.get('count', 0)} kasus</b>
                                &nbsp;·&nbsp;
                                Efisiensi: <b>{row['efisiensi']}</b>
                            </span>
                        </div>
                        """, unsafe_allow_html=True)

                    # Waktu rata-rata per petugas × jenis (jika ada data waktu)
                    if col_waktu and col_jenis:
                        pet_type_time = (
                            df.groupby([col_petugas, col_jenis])[col_waktu]
                            .mean().reset_index()
                        )
                        pet_type_time.columns = ["Petugas", "Jenis", "Rata-rata Waktu (mnt)"]
                        fig_ptt = px.density_heatmap(
                            pet_type_time,
                            x="Jenis", y="Petugas",
                            z="Rata-rata Waktu (mnt)",
                            color_continuous_scale="RdYlGn_r",
                            template="plotly_dark",
                            title="Waktu Penyelesaian (mnt): Petugas × Jenis Keluhan"
                                  " — lebih hijau = lebih cepat",
                        )
                        fig_ptt.update_layout(
                            paper_bgcolor="#0d2137", plot_bgcolor="#0d2137",
                            height=max(300, len(ranked) * 40 + 120),
                        )
                        st.plotly_chart(fig_ptt, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 4 — PRIORITAS AREA
    # ══════════════════════════════════════════════════════════════════════════
    with tab4:
        st.markdown("#### 📍 Peta Risiko & Prioritas Area")
        st.caption("Skor risiko dihitung dari: frekuensi aduan + proporsi KRITIS + rata-rata waktu penyelesaian (90 hari terakhir).")

        if not col_area:
            st.warning("⚠️ Kolom area tidak ditemukan.")
        else:
            risk_df = _area_risk(df, col_area, col_jenis, col_severity, col_waktu)

            if risk_df.empty:
                st.info("Tidak cukup data untuk menghitung risiko area.")
            else:
                # KPI
                n_hi = (risk_df["risk_level"] == "TINGGI").sum()
                n_md = (risk_df["risk_level"] == "SEDANG").sum()
                n_lo = (risk_df["risk_level"] == "RENDAH").sum()
                k1, k2, k3 = st.columns(3)
                k1.metric("🔴 Area Risiko TINGGI", int(n_hi))
                k2.metric("🟡 Area Risiko SEDANG", int(n_md))
                k3.metric("🟢 Area Risiko RENDAH", int(n_lo))

                # ── Grafik skor risiko ──────────────────────────────────────────
                color_map = {"TINGGI": "#ef4444", "SEDANG": "#f59e0b", "RENDAH": "#10b981"}
                fig_risk = px.bar(
                    risk_df.sort_values("risk_score"),
                    x="risk_score", y="area", orientation="h",
                    color="risk_level",
                    color_discrete_map=color_map,
                    template="plotly_dark",
                    title="Skor Risiko per Area (0–100)",
                    text="risk_score",
                )
                fig_risk.update_layout(
                    paper_bgcolor="#0d2137", plot_bgcolor="#0d2137",
                    height=max(350, len(risk_df) * 50 + 100),
                )
                fig_risk.update_traces(textposition="outside")
                st.plotly_chart(fig_risk, use_container_width=True)

                # ── Kartu detail per area ───────────────────────────────────────
                st.markdown("---")
                st.markdown("##### 📋 Detail Analisis per Area")

                for _, row in risk_df.iterrows():
                    card_cls  = f"risk-{row['risk_level']}"
                    badge_cls = f"badge-{row['risk_level']}"
                    level     = row["risk_level"]

                    # Distribusi jenis
                    if row["type_dist"]:
                        dist_str = " · ".join(
                            f"{k}: {v:.0f}%" for k, v in
                            sorted(row["type_dist"].items(), key=lambda x: -x[1])[:3]
                        )
                    else:
                        dist_str = "—"

                    st.markdown(f"""
                    <div class="pred-card {card_cls}">
                        <div style="margin-bottom:6px">
                            <span class="badge {badge_cls}">{level}</span>
                            <span class="badge badge-blue">Risiko {row['risk_score']}/100</span>
                            &nbsp;<b style="color:#f1f5f9;font-size:1rem">{row['area']}</b>
                            &nbsp;<span style="color:#94a3b8">{row['tren']}</span>
                        </div>
                        <p>
                            📊 <b>{row['total_aduan']}</b> aduan
                            &nbsp;·&nbsp;
                            🔴 KRITIS: <b>{row['aduan_kritis']}</b>
                            &nbsp;·&nbsp;
                            ⏱️ Avg selesai: <b>{row['avg_waktu_mnt']} mnt</b>
                        </p>
                        <p>🔑 Keluhan dominan: <b>{row['jenis_dominan']}</b></p>
                        <p>📈 Distribusi: {dist_str}</p>
                        <p>
                            🎲 Probabilitas aduan minggu depan:
                            <b style="color:#f59e0b">{row['prob_mgg_depan'] * 100:.0f}%</b>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                # ── Scatter plot: total aduan vs skor risiko ────────────────────
                st.markdown("---")
                fig_scatter = px.scatter(
                    risk_df,
                    x="total_aduan", y="risk_score",
                    size="aduan_kritis",
                    color="risk_level",
                    color_discrete_map=color_map,
                    hover_name="area",
                    hover_data=["jenis_dominan", "avg_waktu_mnt", "prob_mgg_depan"],
                    template="plotly_dark",
                    title="Peta Risiko: Volume Aduan vs Skor Risiko"
                          " (ukuran bubble = jumlah KRITIS)",
                    labels={"total_aduan": "Total Aduan (90 hari)",
                            "risk_score": "Skor Risiko"},
                    text="area",
                )
                fig_scatter.update_traces(textposition="top center")
                fig_scatter.update_layout(
                    paper_bgcolor="#0d2137", plot_bgcolor="#0d2137",
                    height=420,
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

                # ── Rekomendasi area prioritas ──────────────────────────────────
                top_risk = risk_df[risk_df["risk_level"] == "TINGGI"]
                if not top_risk.empty:
                    st.markdown("---")
                    st.error(
                        f"🚨 **{len(top_risk)} area membutuhkan perhatian segera** — "
                        f"risiko TINGGI: **{', '.join(top_risk['area'].tolist())}**\n\n"
                        "Rekomendasikan: audit infrastruktur, tambah kapasitas petugas, "
                        "dan persiapan stok material prioritas."
                    )

    st.markdown("---")
    st.caption(
        "⚙️ Metode: ARIMA(2,1,2) → Prophet → WMA+Trend (fallback otomatis) · "
        "Prediksi berbasis pola historis agregat · "
        f"Data: {len(df):,} baris · Rentang: {df['_tgl'].min().date()} s/d {df['_tgl'].max().date()}"
    )
def show():
    render_layout(
        "📞 Data Aduan",
        "df_aduan",
        dashboard,
        ml,
        prediksi,
    )