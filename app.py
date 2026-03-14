import streamlit as st
import requests
import re
import os
import time

st.set_page_config(page_title="Context.Pro Legal", page_icon="⚖️", layout="centered")

# =============================================================================
# SESSION STATE
# =============================================================================
for key in ['contract_txt', 'question_txt', 'result', 'is_analyzing', 'last_mode', 'jurisdiction']:
    if key not in st.session_state:
        st.session_state[key] = "" if key in ['contract_txt', 'question_txt', 'result', 'jurisdiction'] else False

# =============================================================================
# CSS
# =============================================================================
st.markdown("""
<style>
.stApp { background: #0e1117; color: #fafafa; }
.stTextArea textarea { background: #262730; color: #fafafa; }
.stButton>button { background: #1f77b4; color: white; }

/* Спинер - строгая пульсация */
@keyframes empire-pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(0.98); }
}
.empire-loading {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    color: #D4AF37 !important;
    font-weight: 500 !important;
    font-size: 1.1rem !important;
    animation: empire-pulse 2s infinite ease-in-out !important;
    padding: 1.5rem !important;
    margin: 1rem 0 !important;
    background: #1a233a !important;
    border: 1px dashed #B8962E !important;
    border-radius: 8px !important;
}
.empire-loading::before {
    content: "⚖️";
    margin-right: 0.75rem !important;
    font-size: 1.4rem !important;
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# ВАЛИДАЦИЯ
# =============================================================================
def validate_input(text: str, mode: str):
    text = text.strip()
    if not text:
        return False, "⚠️ Поле не может быть пустым"
    if len(set(text.lower())) < 5 or not re.search(r'[а-яА-Яa-zA-Z]', text):
        return False, "⚠️ Введите осмысленный текст"
    if mode == "contract":
        if len(text) < 50:
            return False, "📋 Для анализа договора нужно минимум 50 символов"
        legal_markers = ["договор", "контракт", "сторона", "обязательство", "статья", "ГК", "ФЗ", "пункт", "параграф", "соглашение", "аренда", "поставка", "услуга", "оплата", "ответственность"]
        if not any(marker in text.lower() for marker in legal_markers):
            return False, "🔍 Это не похоже на текст договора. Перейдите во вкладку «💬 Вопрос»"
    elif mode == "question":
        if len(text) < 10:
            return False, "💬 Сформулируйте вопрос подробнее (мин. 10 символов)"
    return True, ""

# =============================================================================
# СИСТЕМНЫЕ ПРОМПТЫ
# =============================================================================
def build_system_prompt(jur: str, mode: str) -> str:
    jur_base = "Российская Федерация (ГК РФ, ФЗ, практика ВС РФ)" if "РФ" in jur else "Республика Беларусь (ГК РБ, Декреты, практика ВС РБ)"
    if mode == "contract":
        return f"""Ты — профессиональный ИИ-помощник юриста Context.Pro Legal. Юрисдикция: {jur_base}.

ПРАВИЛА:
1. Если текст не является договором или не содержит юридических терминов → ОТВЕТЬ: "⚠️ Это не похоже на текст договора."
2. Выдели риски: [🔴 Критический] / [🟡 Средний] / [🟢 Низкий]
3. Цитируй конкретные статьи законов (ГК РФ/РБ, ФЗ, Декреты)
4. Дай практическую рекомендацию по исправлению
5. Будь краток, но точен
6. Не выдумывай статьи законов
7. Не смешивай нормы РФ и РБ

ФОРМАТ ОТВЕТА:
### 🔍 Выявленные риски
• [Уровень] Риск: описание → Статья закона → Рекомендация

### ✅ Что в порядке
• Пункты без рисков

### 📋 Итог
Краткая оценка + дисклеймер
"""
    else:
        return f"""Ты — профессиональный ИИ-консультант по праву. Юрисдикция: {jur_base}.

ПРАВИЛА:
1. Отвечай ТОЛЬКО на юридические вопросы
2. Всегда указывай нормативную базу: статьи ГК РФ/РБ, номера ФЗ, Декретов
3. Структура ответа:
   ### 📌 Суть вопроса
   ### ⚖️ Нормативная база
   ### 🔄 Пошаговые рекомендации
   ### ⚠️ Важные нюансы
4. Дисклеймер в конце: "Консультация носит информационный характер"
5. Будь точен, но доступен
"""

# =============================================================================
# API KEY
# =============================================================================
def get_api_key():
    try:
        if "openrouter" in st.secrets and "api_key" in st.secrets["openrouter"]:
            return st.secrets["openrouter"]["api_key"]
    except:
        pass
    return os.getenv("OPENROUTER_API_KEY")

# =============================================================================
# ЗАПРОС К AI
# =============================================================================
def query_ai(system_prompt: str, user_text: str):
    api_key = get_api_key()
    if not api_key:
        return None, "❌ API ключ не настроен. Проверьте secrets.toml"
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://context-pro.streamlit.app",
                "X-Title": "Context.Pro Legal"
            },
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                "temperature": 0.2,
                "max_tokens": 1500,
                "top_p": 0.9
            },
            timeout=60
        )
        
        if response.status_code != 200:
            return None, f"❌ Ошибка сервиса ({response.status_code})"
        
        data = response.json()
        if "choices" not in data or not data["choices"]:
            return None, "❌ Пустой ответ от сервиса"
        
        return data["choices"][0]["message"]["content"], None
        
    except requests.exceptions.Timeout:
        return None, "⏱ Тайм-аут соединения. Проверьте интернет."
    except requests.exceptions.ConnectionError:
        return None, "🔌 Ошибка подключения к сети."
    except Exception as e:
        return None, f"❌ Ошибка: {type(e).__name__}"

# =============================================================================
# UI - ШАПКА
# =============================================================================
st.title("⚖️ Context.Pro Legal")
st.caption("Анализ договоров • Консультации • РФ/РБ")

# =============================================================================
# ЮРИСДИКЦИЯ НА ГЛАВНОЙ (вместо сайдбара)
# =============================================================================
st.markdown("### ⚖️ Юрисдикция")
jur = st.radio(
    "Выберите законодательство:",
    ["🇷🇺 РФ", "🇧🇾 РБ"],
    horizontal=True,
    index=0 if st.session_state.jurisdiction == "🇷🇺 РФ" else 1,
    key="jurisdiction_radio"
)
st.session_state.jurisdiction = jur

st.markdown("---")

# =============================================================================
# ВКЛАДКИ
# =============================================================================
tab1, tab2 = st.tabs(["📋 Договор", "💬 Вопрос"])

# =============================================================================
# ВКЛАДКА 1: ДОГОВОР
# =============================================================================
with tab1:
    st.markdown("#### 📄 Текст договора")
    st.caption("💡 Минимум 50 символов")
    
    text = st.text_area(
        "Вставьте текст договора:",
        value=st.session_state.contract_txt,
        height=220,
        key="contract_input",
        placeholder="Скопируйте сюда полный текст договора..."
    )
    st.session_state.contract_txt = text
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        analyze_btn = st.button("⚖️ Проверить договор", use_container_width=True, key="btn_contract", disabled=st.session_state.is_analyzing)
    
    with col2:
        if st.button("🗑️", key="clear_contract"):
            st.session_state.contract_txt = ""
            st.session_state.result = ""
            st.session_state.last_mode = None
            st.rerun()
    
    # ОБРАБОТКА АНАЛИЗА
    if analyze_btn:
        is_valid, message = validate_input(text, "contract")
        if not is_valid:
            st.warning(message)
        else:
            # Показываем спинер
            st.session_state.is_analyzing = True
            st.session_state.last_mode = "contract"
            
            # СПИНЕР
            st.markdown('<div class="empire-loading">Анализирую договор по нормам ' + jur + '...</div>', unsafe_allow_html=True)
            
            sys_prompt = build_system_prompt(jur, "contract")
            result, error = query_ai(sys_prompt, text)
            
            st.session_state.is_analyzing = False
            
            if error:
                st.error(error)
            else:
                st.session_state.result = result
                st.success("✅ Анализ завершён!")
                st.rerun()
    
    # Показ результата
    if st.session_state.last_mode == "contract" and st.session_state.result:
        st.markdown("---")
        st.markdown("### 🔍 Результаты анализа")
        st.markdown(st.session_state.result)
        
        st.download_button(
            "📥 Скачать отчёт",
            st.session_state.result,
            "context_pro_analysis.txt",
            "text/plain",
            use_container_width=True,
            key="download_contract"
        )

# =============================================================================
# ВКЛАДКА 2: ВОПРОС
# =============================================================================
with tab2:
    st.markdown("#### ⚖️ Ваш вопрос")
    st.caption("💡 Минимум 10 символов")
    
    q = st.text_area(
        "Задайте юридический вопрос:",
        value=st.session_state.question_txt,
        height=220,
        key="question_input",
        placeholder="Например: Какие риски по ст. 651 ГК РФ?"
    )
    st.session_state.question_txt = q
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        ask_btn = st.button("⚡ Получить ответ", use_container_width=True, key="btn_question", disabled=st.session_state.is_analyzing)
    
    with col2:
        if st.button("🗑️", key="clear_question"):
            st.session_state.question_txt = ""
            st.session_state.result = ""
            st.session_state.last_mode = None
            st.rerun()
    
    # ОБРАБОТКА ВОПРОСА
    if ask_btn:
        is_valid, message = validate_input(q, "question")
        if not is_valid:
            st.warning(message)
        else:
            st.session_state.is_analyzing = True
            st.session_state.last_mode = "question"
            
            # СПИНЕР
            st.markdown('<div class="empire-loading">Готовлю консультацию по ' + jur + '...</div>', unsafe_allow_html=True)
            
            sys_prompt = build_system_prompt(jur, "question")
            result, error = query_ai(sys_prompt, q)
            
            st.session_state.is_analyzing = False
            
            if error:
                st.error(error)
            else:
                st.session_state.result = result
                st.success("✅ Ответ готов!")
                st.rerun()
    
    # Показ результата
    if st.session_state.last_mode == "question" and st.session_state.result:
        st.markdown("---")
        st.markdown("### 💬 Консультация")
        st.markdown(st.session_state.result)

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 15px; color: #718096; font-size: 0.85rem;">
    <p>⚖️ <strong>Context.Pro Legal</strong> | 🇷🇺 РФ • 🇧🇾 РБ</p>
    <p style="font-size: 0.75rem;">🔒 Приватно • Без логов • Конфиденциально</p>
    <p style="font-size: 0.75rem;">⚠️ ИИ-помощник не заменяет очную консультацию юриста</p>
</div>
""", unsafe_allow_html=True)
