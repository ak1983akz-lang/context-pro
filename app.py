import streamlit as st
import requests
import os

st.set_page_config(page_title="Context.Pro Legal", page_icon="⚖️", layout="wide")

# Инициализация session state
if 'jurisdiction' not in st.session_state:
    st.session_state.jurisdiction = "🇷🇺 РФ"
if 'contract_txt' not in st.session_state:
    st.session_state.contract_txt = ""
if 'question_txt' not in st.session_state:
    st.session_state.question_txt = ""
if 'result' not in st.session_state:
    st.session_state.result = ""

# =============================================================================
# 🎨 ШАПКА С ЛОГОТИПОМ
# =============================================================================
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    # Логотип (можно заменить на свою картинку)
    st.markdown("""
    <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%); 
                border-radius: 10px; margin: 10px 0;">
        <h1 style="margin: 0; color: white; font-size: 2.5rem;">⚖️ Context.Pro Legal</h1>
        <p style="margin: 5px 0; color: #e2e8f0; font-size: 1.1rem;">Анализ договоров • Консультации • РФ/РБ</p>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# 🔧 БОКОВАЯ ПАНЕЛЬ (МЕНЮ)
# =============================================================================
with st.sidebar:
    st.markdown("### ⚙️ Настройки")
    
    # Выбор юрисдикции
    jurisdiction = st.radio(
        "⚖️ Юрисдикция:",
        ["🇷🇺 РФ", "🇧🇾 РБ"],
        index=0 if st.session_state.jurisdiction == "🇷 РФ" else 1
    )
    st.session_state.jurisdiction = jurisdiction
    
    st.markdown("---")
    
    # Кнопка очистки
    if st.button("🗑️ Очистить всё", use_container_width=True):
        st.session_state.contract_txt = ""
        st.session_state.question_txt = ""
        st.session_state.result = ""
        st.rerun()
    
    st.markdown("---")
    st.caption("🔒 Приватно • Без логов • Конфиденциально")

# =============================================================================
# 📋 ОСНОВНЫЕ ВКЛАДКИ
# =============================================================================
tab_contract, tab_question = st.tabs(["📋 Анализ договора", "💬 Юридический вопрос"])

# =============================================================================
# ВКЛАДКА 1: АНАЛИЗ ДОГОВОРА
# =============================================================================
with tab_contract:
    st.markdown("#### 📄 Вставьте текст договора")
    st.caption("💡 Минимум 50 символов")
    
    contract_text = st.text_area(
        "Текст договора:",
        value=st.session_state.contract_txt,
        height=250,
        key="contract_input",
        placeholder="Скопируйте сюда текст договора для анализа..."
    )
    st.session_state.contract_txt = contract_text
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("⚖️ Проверить договор", use_container_width=True, type="primary"):
            if len(contract_text.strip()) < 50:
                st.error("📋 Для анализа нужно минимум 50 символов")
            else:
                with st.spinner(" Анализирую договор..."):
                    # Здесь будет вызов AI
                    st.session_state.result = "✅ Анализ завершён (заглушка)"
                    st.success("Анализ завершён!")
    
    with col2:
        if st.button("🗑️ Очистить", use_container_width=True):
            st.session_state.contract_txt = ""
            st.session_state.result = ""
            st.rerun()
    
    # Отображение результата
    if st.session_state.result and contract_text.strip():
        st.markdown("---")
        st.markdown("### 🔍 Результаты анализа")
        st.info(st.session_state.result)
        
        st.download_button(
            "📥 Скачать отчёт",
            st.session_state.result,
            file_name="analysis.txt",
            mime="text/plain",
            use_container_width=True
        )

# =============================================================================
# ВКЛАДКА 2: ЮРИДИЧЕСКИЙ ВОПРОС
# =============================================================================
with tab_question:
    st.markdown("#### ⚖️ Задайте юридический вопрос")
    st.caption("💡 Минимум 10 символов")
    
    question_text = st.text_area(
        "Ваш вопрос:",
        value=st.session_state.question_txt,
        height=250,
        key="question_input",
        placeholder="Сформулируйте ваш юридический вопрос..."
    )
    st.session_state.question_txt = question_text
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("⚡ Получить ответ", use_container_width=True, type="primary"):
            if len(question_text.strip()) < 10:
                st.error("💬 Сформулируйте вопрос подробнее (мин. 10 символов)")
            else:
                with st.spinner("📝 Готовлю ответ..."):
                    # Здесь будет вызов AI
                    st.session_state.result = "✅ Ответ готов (заглушка)"
                    st.success("Ответ подготовлен!")
    
    with col2:
        if st.button("🗑️ Очистить", use_container_width=True):
            st.session_state.question_txt = ""
            st.session_state.result = ""
            st.rerun()
    
    # Отображение результата
    if st.session_state.result and question_text.strip():
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
