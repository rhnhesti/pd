import streamlit as st
from components.layout import render_layout

def dashboard(df):
    st.subheader("Dashboard Transaksi")
    col = st.selectbox("Pilih Kolom Transaksi", df.columns)
    st.line_chart(df[col])

def ml(df):
    st.subheader("ML Transaksi")
    st.write("Forecasting model")

def prediksi(df):
    st.subheader("Prediksi Transaksi")
    st.write("Prediksi revenue")

def show():
    render_layout(
        "💳 Data Transaksi",
        "df_transaksi",
        dashboard,
        ml,
        prediksi
    )