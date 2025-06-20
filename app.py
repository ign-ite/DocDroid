import streamlit as st
import pandas as pd

st.set_page_config(page_title="Content Generator", layout="centered")

st.markdown("<b><h2 style='text-align: center;'>Content Generator</h2></b>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Generate a consolidated file from repository or local directory contents</p>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["GitHub Repository", "Local Directory"])

with tab1:
    repo_url = st.text_input("Repository URL", 
                             placeholder="https://github.com/username/repo")
    if st.button("Generate README", key="repo"):
        code_content = "Hello World!"
        st.text_area("Generated README", code_content, height=400)
        st.button("Copy Content")