import streamlit as st
import pandas as pd

st.set_page_config(page_title="Content Generator", layout="centered")

st.markdown("<b><h2 style='text-align: center;'>Content Generator</h2></b>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Generate a consolidated file from repository or local directory contents</p>", unsafe_allow_html=True)