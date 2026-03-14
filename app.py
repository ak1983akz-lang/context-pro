import streamlit as st
import requests

st.set_page_config(page_title="Context.Pro Legal", page_icon="⚖️", layout="wide")

# Session state
for key in ['jurisdiction', 'contract_txt', 'question_txt', 'result', 'active_tab']:
    if key not in st.session_state:
        st.session_state[key] = "🇷 РФ" if key == 'jurisdiction' else "" if key in ['contract_txt', 'question_txt', 'result'] else "contract"

# =============================================================================
# 🎨 ШАПКА С ЛОГОТИПОМ
# =============================================================================
st.markdown("""
<div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%); 
            border-radius: 10px; margin: 10px 0;">
    <h1 style="margin: 0; color: white; font-size: 2.5rem;">⚖️ Context.Pro Legal</h1>
    <p style="margin: 5px 0; color: #e2e8f0; font-size: 1.1rem;">Анализ договоров • Консультации • РФ/РБ</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# ⚙️ НАСТРОЙКИ НА ГЛАВНОЙ (не в сайдбаре)
# =============================================================================
col_jur1, col_jur2, col_jur3 = st.columns([1, 2, 1])
with col_jur2:
    jurisdiction = st.radio(
        "⚖️ Юрисдикция:",
        ["🇷🇺 РФ", "🇧🇾 РБ"],
        index=0 if st.session_state.jurisdiction == "🇷🇺 РФ" else 1,
        key="jurisdiction_radio_unique",
        horizontal=True
    )
    st.session_state.jurisdiction = jurisdiction

st.markdown("---")

# =============================================================================
# 📋 ВКЛАДКИ
# =============================================================================
tab_contract, tab_question = st.tabs(["📋 Анализ договора", "💬 Юридический вопрос"])

# =============================================================================
# ВКЛАДКА 1: АНАЛИЗ ДОГОВОРА
# =============================================================================
with tab_contract:
    st.session_state.active_tab = "contract"
    
    st.markdown("#### 📄 Вставьте текст договора")
    st.caption("💡 Минимум 50 символов")
    
    contract_text = st.text_area(
        "Текст договора:",
        value=st.session_state.contract_txt,
        height=250,
        key="contract_text_area_unique",
        placeholder="Скопируйте сюда текст договора..."
    )
    st.session_state.contract_txt = contract_text
    
    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        if st.button("⚖️ Проверить договор", use_container_width=True, type="primary", key="btn_contract_check_unique"):
            if len(contract_text.strip()) < 50:
                st.error("📋 Для анализа нужно минимум 50 символов")
            else:
                with st.spinner("⚖️ Анализирую договор..."):
                    # Здесь вызов AI
                    st.session_state.result = "✅ Анализ завершён"
                    st.success("Готово!")
    
    with col_btn2:
        if st.button("🗑️ Очистить", use_container_width=True, key="btn_contract_clear_unique"):
            st.session_state.contract_txt = ""
            st.session_state.result = ""
            st.rerun()
    
    if st.session_state.result and st.session_state.active_tab == "contract":
        st.markdown("---")
        st.markdown("### 🔍 Результаты анализа")
        st.info(st.session_state.result)

# =============================================================================
# ВКЛАДКА 2: ЮРИДИЧЕСКИЙ ВОПРОС
# =============================================================================
with tab_question:
    st.session_state.active_tab = "question"
    
    st.markdown("#### ⚖️ Задайте юридический вопрос")
    st.caption("💡 Минимум 10 символов")
    
    question_text = st.text_area(
        "Ваш вопрос:",
        value=st.session_state.question_txt,
        height=250,
        key="question_text_area_unique",
        placeholder="Сформулируйте ваш вопрос..."
    )
    st.session_state.question_txt = question_text
    
    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        if st.button("⚡ Получить ответ", use_container_width=True, type="primary", key="btn_question_ask_unique"):
            if len(question_text.strip()) < 10:
                st.error("💬 Минимум 10 символов")
            else:
                with st.spinner("📝 Готовлю ответ..."):
                    # Здесь вызов AI
                    st.session_state.result = "✅ Ответ готов"
                    st.success("Готово!")
    
    with col_btn2:
        if st.button("🗑️ Очистить", use_container_width=True, key="btn_question_clear_unique"):
            st.session_state.question_txt = ""
            st.session_state.result = ""
            st.rerun()
    
    if st.session_state.result and st.session_state.active_tab == "question":
        st.markdown("---")
        st.markdown("### 💬 Консультация")
        st.info(st.session_state.result)

# =============================================================================
# ПОДВАЛ
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px; color: #718096; font-size: 0.9rem;">
    <p>⚖️ <strong>Context.Pro Legal</strong> | 🇷🇺 РФ • 🇧🇾 РБ</p>
    <p style="font-size: 0.8rem;">⚠️ ИИ-помощник не заменяет очную консультацию юриста</p>
</div>
""", unsafe_allow_html=True)
