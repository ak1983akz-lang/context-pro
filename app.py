import streamlit as st
import requests
import re

st.set_page_config(page_title="Context.Pro Legal", page_icon="⚖️", layout="centered")

# Session state
for key in ['contract_txt', 'question_txt', 'result', 'is_analyzing', 'last_mode', 'jurisdiction']:
    if key not in st.session_state:
        st.session_state[key] = "" if key in ['contract_txt', 'question_txt', 'result', 'jurisdiction'] else False

# CSS
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

# Вкладка 1: Договор
with tab1:
    text = st.text_area("Текст договора:", height=200, key="contract_area")
    
    if st.button("⚖️ Проверить договор", key="btn_contract"):
        if len(text.strip()) < 50:
            st.error("📋 Нужно минимум 50 символов")
        else:
            with st.spinner("Анализирую..."):
                # Здесь вызов AI
                st.session_state.result = "✅ Анализ завершён"
                st.session_state.last_mode = "contract"
                st.success("Готово!")
    
    if st.session_state.last_mode == "contract" and st.session_state.result:
        st.markdown("---")
        st.markdown("### 🔍 Результаты:")
        st.write(st.session_state.result)
    
    if st.button("🗑️ Очистить", key="clear_contract"):
        st.session_state.contract_txt = ""
        st.session_state.result = ""
        st.session_state.last_mode = None
        st.rerun()

# Вкладка 2: Вопрос
with tab2:
    q = st.text_area("Ваш вопрос:", height=200, key="question_area")
    
    if st.button("⚡ Получить ответ", key="btn_question"):
        if len(q.strip()) < 10:
            st.error("💬 Нужно минимум 10 символов")
        else:
            with st.spinner("Готовлю ответ..."):
                # Здесь вызов AI
                st.session_state.result = "✅ Ответ готов"
                st.session_state.last_mode = "question"
                st.success("Готово!")
    
    if st.session_state.last_mode == "question" and st.session_state.result:
        st.markdown("---")
        st.markdown("### 💬 Консультация:")
        st.write(st.session_state.result)
    
    if st.button("🗑️ Очистить", key="clear_question"):
        st.session_state.question_txt = ""
        st.session_state.result = ""
        st.session_state.last_mode = None
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("🔒 Приватно • Без логов")
