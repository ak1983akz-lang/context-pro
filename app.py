import streamlit as st
import requests
import re
import os

# =============================================================================
# SESSION STATE
# =============================================================================
for key in ['contract_txt', 'question_txt', 'result', 'is_analyzing', 'last_mode', 'jurisdiction', 'first_visit']:
    if key not in st.session_state:
        st.session_state[key] = "" if key in ['contract_txt', 'question_txt', 'result', 'jurisdiction'] else False if key == 'is_analyzing' else None if key == 'last_mode' else True if key == 'first_visit' else False

<style>
.stApp { 
    background: #0e1117; 
    color: #fafafa; 
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding-top: 1rem !important; /* Отступ сверху для мобильных */
}
.stTextArea textarea { 
    background: #262730; 
    color: #fafafa; 
    font-size: 16px !important; 
    line-height: 1.5 !important;
}
.stButton>button { 
    background: #1f77b4; 
    color: white; 
    font-size: 16px !important; 
    padding: 12px 24px !important; 
    min-height: 50px !important; 
    border-radius: 8px !important;
}

/* Заголовки — адаптивные */
h1 { 
    font-size: 1.8rem !important; 
    margin-bottom: 0.5rem !important; 
    margin-top: 0.5rem !important;
}
h2 { font-size: 1.4rem !important; }
h3 { font-size: 1.2rem !important; }
h4 { font-size: 1rem !important; }

/* Спинер */
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
    font-size: 1rem !important; 
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

/* === МОБИЛЬНАЯ АДАПТАЦИЯ === */
@media (max-width: 768px) {
    /* Убираем лишние отступы Streamlit */
    .main > div { padding: 0 !important; }
    
    /* Контейнер с правильными отступами */
    .block-container { 
        padding: 1rem 1rem 0.5rem 1rem !important; 
        max-width: 100% !important;
        padding-top: max(1rem, env(safe-area-inset-top)) !important; /* Учёт "чёлки" */
    }
    
    /* Заголовки меньше на мобильных */
    h1 { font-size: 1.3rem !important; margin-top: 0.3rem !important; }
    h2 { font-size: 1.1rem !important; }
    h3 { font-size: 1rem !important; }
    h4 { font-size: 0.9rem !important; }
    
    /* Caption меньше */
    .stMarkdown p { font-size: 0.85rem !important; }
    
    /* Кнопки — большие для пальцев */
    .stButton>button { 
        font-size: 16px !important; 
        padding: 14px 24px !important; 
        min-height: 55px !important; 
        border-radius: 10px !important;
        width: 100% !important;
        margin: 0.2rem 0 !important;
    }
    
    /* Поля ввода */
    .stTextArea textarea, .stTextInput input { 
        font-size: 16px !important; 
        padding: 12px !important;
        min-height: 120px !important;
    }
    
    /* Радио-кнопки вертикально */
    .stRadio > div { 
        flex-direction: column !important; 
        gap: 6px !important; 
    }
    .stRadio label { 
        width: 100% !important; 
        padding: 12px !important; 
        margin: 3px 0 !important;
        border-radius: 8px !important;
        background: #262730 !important;
        min-height: 48px !important;
        display: flex !important;
        align-items: center !important;
        font-size: 0.95rem !important;
    }
    
    /* Колонки */
    .stColumns > div { 
        width: 100% !important; 
        margin-bottom: 10px !important; 
    }
    
    /* Вкладки */
    .stTabs [data-baseweb="tab-list"] { 
        gap: 4px !important;
        font-size: 14px !important;
        padding: 0 !important;
    }
    .stTabs [data-baseweb="tab"] { 
        padding: 10px 16px !important;
        min-height: 45px !important;
    }
    
    /* Скрываем сайдбар */
    section[data-testid="stSidebar"] { display: none !important; }
    
    /* Убираем горизонтальный скролл */
    body { overflow-x: hidden !important; max-width: 100vw !important; }
    div[data-testid="stAppViewContainer"] { overflow-x: hidden !important; }
}

/* Маленькие телефоны (до 480px) */
@media (max-width: 480px) {
    .block-container { padding: 0.8rem 0.8rem 0.5rem 0.8rem !important; }
    h1 { font-size: 1.2rem !important; }
    h2 { font-size: 1rem !important; }
    h3 { font-size: 0.95rem !important; }
    .stButton>button { font-size: 15px !important; padding: 16px 20px !important; }
    .stTextArea textarea, .stTextInput input { font-size: 15px !important; }
    .stRadio label { font-size: 0.9rem !important; padding: 10px !important; }
}

/* iPhone safe areas */
@supports (padding: max(0px)) {
    @media (max-width: 768px) {
        .block-container {
            padding-top: max(1rem, env(safe-area-inset-top)) !important;
            padding-left: max(1rem, env(safe-area-inset-left)) !important;
            padding-right: max(1rem, env(safe-area-inset-right)) !important;
            padding-bottom: max(0.5rem, env(safe-area-inset-bottom)) !important;
        }
    }
}

/* Touch-friendly */
@media (hover: none) and (pointer: coarse) {
    .stButton>button {
        min-height: 55px !important;
        min-width: 100px !important;
        touch-action: manipulation !important;
    }
    .stRadio label {
        min-height: 50px !important;
        touch-action: manipulation !important;
    }
}
</style>
# =============================================================================
# 🔒 ВАЛИДАЦИЯ
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
# 🧠 ПРОМПТЫ
# =============================================================================
def build_system_prompt(jur: str, mode: str) -> str:
    jur_base = "Российская Федерация (ГК РФ, ФЗ, практика ВС РФ)" if "РФ" in jur else "Республика Беларусь (ГК РБ, Декреты, практика ВС РБ)"
    if mode == "contract":
        return f"""Ты — профессиональный ИИ-помощник юриста Context.Pro Legal. Юрисдикция: {jur_base}.
ПРАВИЛА: 1) Если текст не договор → "⚠️ Это не похоже на договор." 2) Риски: [🔴/🟡/🟢] 3) Статьи законов 4) Рекомендации 5) ФОРМАТ: ### 🔍 Риски • ### ✅ Что в порядке • ### 📋 Итог"""
    else:
        return f"""Ты — ИИ-консультант по праву. Юрисдикция: {jur_base}.
ПРАВИЛА: 1) Только юридические вопросы 2) Статьи ГК/ФЗ 3) Структура: 📌 Суть → ⚖️ Нормы → 🔄 Рекомендации → ⚠️ Нюансы 4) Дисклеймер"""

# =============================================================================
# 🔑 API KEY
# =============================================================================
def get_api_key():
    try:
        if "openrouter" in st.secrets and "api_key" in st.secrets["openrouter"]:
            return st.secrets["openrouter"]["api_key"]
    except:
        pass
    return os.getenv("OPENROUTER_API_KEY")

# =============================================================================
# 🤖 AI ЗАПРОС
# =============================================================================
def query_ai(system_prompt: str, user_text: str):
    api_key = get_api_key()
    if not api_key:
        return None, "❌ API ключ не настроен."
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "HTTP-Referer": "https://context-pro.streamlit.app", "X-Title": "Context.Pro Legal"},
            json={"model": "deepseek/deepseek-chat", "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_text}], "temperature": 0.2, "max_tokens": 1500, "top_p": 0.9},
            timeout=60
        )
        if response.status_code != 200:
            return None, f"❌ Ошибка ({response.status_code})"
        data = response.json()
        if "choices" not in data or not data["choices"]:
            return None, "❌ Пустой ответ"
        return data["choices"][0]["message"]["content"], None
    except requests.exceptions.Timeout:
        return None, "⏱ Тайм-аут."
    except Exception as e:
        return None, f"❌ {type(e).__name__}"

# =============================================================================
# 🎨 UI — ШАПКА
# =============================================================================
st.title("⚖️ Context.Pro Legal")
st.caption("Анализ договоров • Консультации • РФ/РБ")

# =============================================================================
# 📋 ИНСТРУКЦИЯ ДЛЯ ПЕРВОГО ПОСЕЩЕНИЯ (ИСПРАВЛЕННАЯ)
# =============================================================================
if st.session_state.first_visit:
    st.markdown("### 📖 Как пользоваться Context.Pro Legal")
    
    with st.container():
        st.markdown("**1️⃣ Выберите юрисдикцию** (обязательно!):")
        col1, col2 = st.columns(2)
        with col1:
            st.info("🇷🇺 **РФ**\n\nДля договоров и вопросов по российскому праву")
        with col2:
            st.info("🇧🇾 **РБ**\n\nДля договоров и вопросов по праву Беларуси")
        st.warning("⚠️ **Важно:** Анализ зависит от выбранной юрисдикции! Если договор российский — выбирайте РФ, если белорусский — РБ.")
    
    st.markdown("**2️⃣ Выберите вкладку:**")
    col1, col2 = st.columns(2)
    with col1:
        st.success("📋 **Договор**\n\nВставьте текст договора для анализа рисков")
    with col2:
        st.success("💬 **Вопрос**\n\nЗадайте юридический вопрос")
    
    st.markdown("**3️⃣ Вставьте текст**")
    st.caption("• Минимум 50 символов для договора")
    st.caption("• Минимум 10 символов для вопроса")
    
    st.markdown("**4️⃣ Нажмите кнопку** и получите результат через 10-30 секунд")
    
    st.markdown("---")
    st.markdown("*⚖️ **Конфиденциально:** Ваши данные не сохраняются и не передаются третьим лицам.*")
    
    st.markdown("---")
    if st.button("✅ Я понял, начать работу", key="first_visit_done", use_container_width=True, type="primary"):
        st.session_state.first_visit = False
        st.rerun()
    
    st.markdown("---")

# =============================================================================
# ⚖️ ЮРИСДИКЦИЯ
# =============================================================================
st.markdown("### ⚖️ Юрисдикция")
st.caption("📌 Выберите законодательство — от этого зависит анализ!")

jur = st.radio(
    "Выберите законодательство:",
    ["🇷🇺 РФ — Российская Федерация", "🇧🇾 РБ — Республика Беларусь"],
    horizontal=False,
    index=0,
    key="jurisdiction_radio",
    label_visibility="collapsed",
    help="🇷🇺 РФ — ГК РФ, ФЗ, практика ВС РФ | 🇧🇾 РБ — ГК РБ, Декреты, практика ВС РБ"
)
st.session_state.jurisdiction = "🇷🇺 РФ" if "РФ" in jur else "🇧🇾 РБ"
st.markdown("---")

# =============================================================================
# 📋 ВКЛАДКИ
# =============================================================================
tab1, tab2 = st.tabs(["📋 Договор", "💬 Вопрос"])

# =============================================================================
# ВКЛАДКА 1: ДОГОВОР
# =============================================================================
with tab1:
    st.markdown("#### 📄 Текст договора")
    st.caption("💡 Скопируйте текст из PDF, Word или фото")
    
    with st.expander("📋 Как скопировать текст?"):
        st.markdown("**📱 С телефона:**\n• iPhone: зажмите текст → «Копировать текст»\n• Android: Google Lens → «Копировать текст»\n• Вставьте в поле ниже")
        st.markdown("**💻 С компьютера:**\n• Откройте документ → Выделите текст → Ctrl+C → Вставьте сюда")
    
    contract_text = st.text_area("Текст договора:", value=st.session_state.contract_txt, height=250, key="contract_text_input", placeholder="Вставьте текст договора... (мин. 50 символов)")
    st.session_state.contract_txt = contract_text
    
    analyze_btn = st.button("⚖️ Проверить договор", use_container_width=True, type="primary", key="btn_contract", disabled=st.session_state.is_analyzing or not (contract_text.strip() if contract_text else False))
    
    if st.button("🗑️ Очистить", key="clear_contract"):
        st.session_state.contract_txt = ""
        st.session_state.result = ""
        st.session_state.last_mode = None
        st.rerun()
    
    if analyze_btn and contract_text and contract_text.strip():
        is_valid, message = validate_input(contract_text, "contract")
        if not is_valid:
            st.warning(message)
        else:
            st.session_state.is_analyzing = True
            st.session_state.last_mode = "contract"
            st.markdown('<div class="empire-loading">Анализирую...</div>', unsafe_allow_html=True)
            sys_prompt = build_system_prompt(st.session_state.jurisdiction, "contract")
            result, error = query_ai(sys_prompt, contract_text)
            st.session_state.is_analyzing = False
            if error:
                st.error(error)
            else:
                st.session_state.result = result
                st.success("✅ Готово!")
                st.rerun()
    
    if st.session_state.last_mode == "contract" and st.session_state.result:
        st.markdown("---")
        st.markdown("### 🔍 Результаты анализа")
        st.markdown(st.session_state.result)
        st.download_button("📥 Скачать отчёт", st.session_state.result, "analysis.txt", "text/plain", use_container_width=True, key="download_contract")

# =============================================================================
# ВКЛАДКА 2: ВОПРОС
# =============================================================================
with tab2:
    st.markdown("#### ⚖️ Ваш вопрос")
    st.caption("💡 Минимум 10 символов")
    
    q = st.text_area("Вопрос:", value=st.session_state.question_txt, height=250, key="question_input", placeholder="Например: Какие риски по ст. 651 ГК РФ?")
    st.session_state.question_txt = q
    
    ask_btn = st.button("⚡ Получить ответ", use_container_width=True, type="primary", key="btn_question", disabled=st.session_state.is_analyzing or not (q.strip() if q else False))
    
    if st.button("🗑️ Очистить", key="clear_question"):
        st.session_state.question_txt = ""
        st.session_state.result = ""
        st.session_state.last_mode = None
        st.rerun()
    
    if ask_btn and q and q.strip():
        is_valid, message = validate_input(q, "question")
        if not is_valid:
            st.warning(message)
        else:
            st.session_state.is_analyzing = True
            st.session_state.last_mode = "question"
            st.markdown('<div class="empire-loading">Готовлю ответ...</div>', unsafe_allow_html=True)
            sys_prompt = build_system_prompt(st.session_state.jurisdiction, "question")
            result, error = query_ai(sys_prompt, q)
            st.session_state.is_analyzing = False
            if error:
                st.error(error)
            else:
                st.session_state.result = result
                st.success("✅ Готово!")
                st.rerun()
    
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
