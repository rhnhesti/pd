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




