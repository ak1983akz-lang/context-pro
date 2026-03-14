import streamlit as st
import requests

st.set_page_config(page_title="Context.Pro Legal", page_icon="⚖️", layout="centered")

# Session state
if 'jurisdiction' not in st.session_state:
    st.session_state.jurisdiction = "🇷 РФ"

# Простой CSS - только цвета
st.markdown("""
<style>
.stApp { background: #0e1117; color: #fafafa; }
.stTextArea textarea { background: #262730; color: #fafafa; }
.stButton>button { background: #1f77b4; color: white; }
</style>
""", unsafe_allow_html=True)

# Заголовок
st.title("⚖️ Context.Pro Legal")
st.caption("Анализ договоров • Консультации • РФ/РБ")

# Переключатель юрисдикции
jur = st.sidebar.radio("⚖️ Юрисдикция:", ["🇷🇺 РФ", "🇧🇾 РБ"])
st.session_state.jurisdiction = jur

# Вкладки
tab1, tab2 = st.tabs(["📋 Договор", "💬 Вопрос"])

with tab1:
    text = st.text_area("Текст договора:", height=200, placeholder="Вставьте текст договора...")
    if st.button("⚖️ Проверить"):
        if len(text) < 50:
            st.warning("📋 Нужно минимум 50 символов")
        else:
            with st.spinner("Анализирую..."):
                # Здесь вызов AI
                st.info("✅ Анализ завершён (заглушка)")

with tab2:
    question = st.text_area("Ваш вопрос:", height=200, placeholder="Задайте вопрос...")
    if st.button("⚡ Ответить"):
        if len(question) < 10:
            st.warning("💬 Нужно минимум 10 символов")
        else:
            with st.spinner("Готовлю ответ..."):
                # Здесь вызов AI
                st.info("✅ Ответ готов (заглушка)")

st.sidebar.markdown("---")
st.sidebar.caption("🔒 Приватно • Без логов")
