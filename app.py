import streamlit as st
import requests
import os

st.set_page_config(
    page_title="Context.Pro Legal", 
    page_icon="⚖️", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# CSS для мобильных устройств
st.markdown("""
<style>
@media (max-width: 768px) {
    .main > div { padding: 1rem !important; }
    h1 { font-size: 1.5rem !important; }
    .stTextArea textarea { font-size: 14px !important; }
}
.stApp { background: #f5f7fa; }
</style>
""", unsafe_allow_html=True)

# Session state
for key in ['jurisdiction', 'contract_txt', 'question_txt', 'result', 'show_result']:
    if key not in st.session_state:
        st.session_state[key] = "" if key != 'show_result' else False

# =============================================================================
# 🎨 ШАПКА
# =============================================================================
st.markdown("""
<div style="background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%); 
            padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
    <h1 style="margin: 0; color: white; font-size: 2rem;">⚖️ Context.Pro Legal</h1>
    <p style="margin: 5px 0 0; color: #e2e8f0;">Анализ договоров • РФ/РБ</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# 🔧 SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("### ⚙️ Настройки")
    jurisdiction = st.radio(
        "⚖️ Юрисдикция:",
        ["🇷🇺 РФ", "🇧🇾 РБ"],
        index=0
    )
    st.session_state.jurisdiction = jurisdiction
    
    st.markdown("---")
    if st.button("🗑️ Очистить всё", use_container_width=True):
        for k in ['contract_txt', 'question_txt', 'result', 'show_result']:
            st.session_state[k] = "" if k != 'show_result' else False
        st.rerun()
    st.caption("🔒 Приватно • Без логов")

# =============================================================================
# 📋 ВКЛАДКИ
# =============================================================================
tab_contract, tab_question = st.tabs(["📋 Анализ договора", "💬 Вопрос"])

# =============================================================================
# ВКЛАДКА 1: ДОГОВОР
# =============================================================================
with tab_contract:
    st.markdown("#### 📄 Текст договора")
    st.caption("💡 Минимум 50 символов")
    
    contract_text = st.text_area(
        "Вставьте текст:",
        value=st.session_state.contract_txt,
        height=200,
        key="contract_area",
        placeholder="Скопируйте текст договора..."
    )
    
    # Сохраняем текст
    if contract_text != st.session_state.contract_txt:
        st.session_state.contract_txt = contract_text
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        analyze_btn = st.button("⚖️ Проверить договор", use_container_width=True, type="primary", key="btn_analyze")
    
    with col2:
        if st.button("🗑️", key="btn_clear_contract"):
            st.session_state.contract_txt = ""
            st.session_state.result = ""
            st.session_state.show_result = False
            st.rerun()
    
    # ОБРАБОТКА КНОПКИ
    if analyze_btn:
        if len(contract_text.strip()) < 50:
            st.error("📋 Минимум 50 символов")
        else:
            with st.spinner("🔍 Анализирую..."):
                # ЗДЕСЬ ВАШ AI ЗАПРОС
                # result, error = query_ai(...)
                
                # ЗАГЛУШКА ДЛЯ ТЕСТА:
                st.session_state.result = """
### 🔍 Найденные риски:

**🔴 Критический:**
• Отсутствует пункт о неустойке → Добавьте ст. 330 ГК РФ

**🟡 Средний:**  
• Нет сроков оплаты → Укажите по ст. 314 ГК РФ

### ✅ Что в порядке:
• Предмет договора указан верно
• Стороны определены

### 📋 Итог:
Договор требует доработки (2 риска)
"""
                st.session_state.show_result = True
                st.success("✅ Готово!")
    
    # ПОКАЗЫВАЕМ РЕЗУЛЬТАТ
    if st.session_state.show_result and st.session_state.result:
        st.markdown("---")
        st.markdown("### 🔍 Результаты анализа")
        st.markdown(st.session_state.result)
        
        st.download_button(
            "📥 Скачать отчёт",
            st.session_state.result,
            "analysis.txt",
            "text/plain",
            use_container_width=True
        )

# =============================================================================
# ВКЛАДКА 2: ВОПРОС
# =============================================================================
with tab_question:
    st.markdown("#### ⚖️ Ваш вопрос")
    st.caption("💡 Минимум 10 символов")
    
    question_text = st.text_area(
        "Задайте вопрос:",
        value=st.session_state.question_txt,
        height=200,
        key="question_area",
        placeholder="Например: Какие риски по ст. 651 ГК РФ?"
    )
    
    if question_text != st.session_state.question_txt:
        st.session_state.question_txt = question_text
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        ask_btn = st.button("⚡ Получить ответ", use_container_width=True, type="primary", key="btn_ask")
    
    with col2:
        if st.button("🗑️", key="btn_clear_question"):
            st.session_state.question_txt = ""
            st.session_state.result = ""
            st.session_state.show_result = False
            st.rerun()
    
    # ОБРАБОТКА КНОПКИ
    if ask_btn:
        if len(question_text.strip()) < 10:
            st.error("💬 Минимум 10 символов")
        else:
            with st.spinner("📝 Готовлю ответ..."):
                # ЗДЕСЬ ВАШ AI ЗАПРОС
                # result, error = query_ai(...)
                
                # ЗАГЛУШКА:
                st.session_state.result = """
### 📌 Суть вопроса:
Консультация по законодательству

### ⚖️ Нормативная база:
• ГК РФ (соответствующие статьи)
• Практика ВС РФ

### 🔄 Рекомендации:
1. Изучите условия договора
2. Проверьте соответствие нормам
3. При необходимости — обратитесь к юристу

⚠️ Консультация носит информационный характер
"""
                st.session_state.show_result = True
                st.success("✅ Ответ готов!")
    
    # ПОКАЗЫВАЕМ РЕЗУЛЬТАТ
    if st.session_state.show_result and st.session_state.result:
        st.markdown("---")
        st.markdown("### 💬 Консультация")
        st.markdown(st.session_state.result)

# =============================================================================
# ПОДВАЛ
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 15px; color: #718096; font-size: 0.85rem;">
    <p>⚖️ <strong>Context.Pro Legal</strong> | 🇷🇺 РФ • 🇧🇾 РБ</p>
    <p style="font-size: 0.75rem;">⚠️ ИИ-помощник не заменяет консультацию юриста</p>
</div>
""", unsafe_allow_html=True)
