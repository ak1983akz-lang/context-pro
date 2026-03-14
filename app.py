import streamlit as st
import requests
import os

st.set_page_config(page_title="Context.Pro Legal", page_icon="⚖️")

# API ключ
API_KEY = os.getenv("OPENROUTER_API_KEY")

if 'result' not in st.session_state:
    st.session_state.result = None

st.title("⚖️ Context.Pro Legal")

jur = st.sidebar.radio("Юрисдикция:", ["🇷🇺 РФ", "🇧 РБ"])

tab1, tab2 = st.tabs(["📋 Анализ договора", "💬 Вопрос"])

with tab1:
    text = st.text_area("Текст договора:", height=250)
    if st.button("Проверить договор"):
        if len(text) < 50:
            st.warning("Минимум 50 символов")
        else:
            with st.spinner("Анализирую..."):
                # Здесь вызов AI
                st.success("Готово!")

with tab2:
    q = st.text_area("Вопрос:", height=250)
    if st.button("Получить ответ"):
        if len(q) < 10:
            st.warning("Минимум 10 символов")
        else:
            with st.spinner("Готовлю ответ..."):
                # Здесь вызов AI  
                st.success("Ответ готов!")
