import streamlit as st
import requests
import re
from pathlib import Path

# =============================================================================
# CONTEXT.PRO LEGAL — v1.2 PROFESSIONAL EDITION
# Модель: Qwen 2.5 72B | Тайм-аут: 120 сек | Стиль: Строгий юридический
# Без эмодзи | С поддержкой изображения | Чистый код
# =============================================================================

st.set_page_config(
    page_title="Context.Pro Legal",
    page_icon="⚖️",
    layout="centered",
    menu_items={
        'About': "Context.Pro Legal — AI-помощник для анализа договоров (РФ/РБ). Конфиденциально. Без логов."
    }
)

# --- SESSION STATE ---
for key in ['jurisdiction', 'contract_txt', 'question_txt', 'result', 'last_mode']:
    if key not in st.session_state:
        st.session_state[key] = "РФ" if key == 'jurisdiction' else "" if key in ['contract_txt', 'question_txt', 'result'] else None

# =============================================================================
# 🎨 ПРОФЕССИОНАЛЬНЫЙ CSS (СТРОГИЙ СТИЛЬ, БЕЗ ЭМОДЗИ)
# =============================================================================
PROFESSIONAL_CSS = """
<style>
/* Цветовая палитра: строгая юридическая */
:root {
    --bg-primary: #f8f9fa;
    --bg-secondary: #ffffff;
    --text-primary: #1a1a2e;
    --text-secondary: #4a4a6a;
    --accent: #2c3e50;
    --accent-hover: #34495e;
    --border: #dfe3e8;
    --success: #27ae60;
    --warning: #f39c12;
    --error: #c0392b;
}

/* Основной фон */
.stApp {
    background: var(--bg-primary) !important;
}

/* Заголовки */
h1, h2, h3, h4 {
    color: var(--text-primary) !important;
    font-family: 'Georgia', 'Times New Roman', serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
}

/* Текст */
p, span, label, div[data-testid="stMarkdownContainer"] {
    color: var(--text-primary) !important;
    font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif !important;
}

/* Поля ввода */
.stTextArea textarea, .stTextInput input {
    background: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    font-size: 14px !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(44, 62, 80, 0.1) !important;
}

/* Кнопки */
.stButton>button {
    background: var(--accent) !important;
    color: white !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    padding: 10px 20px !important;
    transition: background 0.2s ease !important;
}
.stButton>button:hover {
    background: var(--accent-hover) !important;
}
.stButton>button:disabled {
    background: var(--border) !important;
    color: var(--text-secondary) !important;
    cursor: not-allowed !important;
}

/* Вкладки */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-secondary) !important;
    border-bottom: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
}

/* Предупреждения и ошибки */
.stWarning {
    background: #fef3c7 !important;
    border-left: 4px solid var(--warning) !important;
    color: var(--text-primary) !important;
}
.stError {
    background: #fee2e2 !important;
    border-left: 4px solid var(--error) !important;
    color: var(--text-primary) !important;
}
.stSuccess {
    background: #dcfce7 !important;
    border-left: 4px solid var(--success) !important;
    color: var(--text-primary) !important;
}

/* Карточка результата */
.result-card {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    padding: 1.5rem !important;
    margin: 1rem 0 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
}
.result-card * {
    color: var(--text-primary) !important;
    line-height: 1.6 !important;
}

/* Сайдбар */
section[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
}

/* Футер */
.footer {
    text-align: center;
    color: var(--text-secondary) !important;
    font-size: 0.75rem !important;
    padding: 2rem 1rem !important;
    border-top: 1px solid var(--border) !important;
    margin-top: 2rem !important;
}

/* Скрытие технических элементов */
#MainMenu, .stDeployButton, footer {
    visibility: hidden !important;
}

/* Адаптивность */
@media (max-width: 768px) {
    .block-container { padding: 1rem !important; }
    .result-card { padding: 1rem !important; }
}
</style>
"""
st.markdown(PROFESSIONAL_CSS, unsafe_allow_html=True)

# =============================================================================
# 🔒 ВАЛИДАЦИЯ (БЕЗ ЭМОДЗИ)
# =============================================================================
def validate_input(text: str, mode: str):
    text = text.strip()
    if not text:
        return False, "Поле не может быть пустым"
    if len(set(text.lower())) < 5 or not re.search(r'[а-яА-Яa-zA-Z]', text):
        return False, "Введите осмысленный текст"
    if mode == "contract":
        if len(text) < 50:
            return False, "Для анализа договора необходимо минимум 50 символов"
        markers = ["договор", "контракт", "сторона", "обязательство", "статья", "ГК", "ФЗ", "пункт", "аренда", "оплата", "соглашение", "услуга", "поставка"]
        if not any(m in text.lower() for m in markers):
            return False, "Текст не распознан как договор. Перейдите во вкладку «Вопрос» для консультации"
    elif mode == "question":
        if len(text) < 10:
            return False, "Сформулируйте вопрос подробнее (минимум 10 символов)"
    return True, ""

# =============================================================================
# 🧠 ПРОМПТЫ (ПРОФЕССИОНАЛЬНЫЕ)
# =============================================================================
def build_prompt(jur: str, mode: str) -> str:
    jur_base = "Российская Федерация (ГК РФ, федеральные законы, практика Верховного Суда РФ)" if jur == "РФ" else "Республика Беларусь (Гражданский кодекс РБ, декреты, практика Верховного Суда РБ)"
    
    if mode == "contract":
        return f"""Вы — профессиональный ИИ-помощник юриста. Юрисдикция: {jur_base}.

ЗАДАЧА: Проведите правовой анализ представленного договора на предмет рисков и соответствия законодательству.

ТРЕБОВАНИЯ К ОТВЕТУ:
1. Структурируйте ответ по разделам:
   - Выявленные правовые риски (с указанием уровня: критический/средний/низкий)
   - Соответствующие нормы законодательства (точные ссылки на статьи)
   - Практические рекомендации по устранению рисков
   - Положения договора, не вызывающие правовых возражений
   - Итоговая оценка и дисклеймер

2. Цитируйте только действующие и проверенные нормы права.
3. Если норма вызывает сомнения — укажите это явно.
4. Избегайте общих фраз, давайте конкретные рекомендации.
5. В конце добавьте: «Результат анализа носит рекомендательный характер и не заменяет консультацию практикующего юриста».

ФОРМАТ: Используйте четкие заголовки, маркированные списки, профессиональную терминологию."""
    else:
        return f"""Вы — профессиональный ИИ-консультант по праву. Юрисдикция: {jur_base}.

ЗАДАЧА: Дайте квалифицированный ответ на юридический вопрос.

ТРЕБОВАНИЯ К ОТВЕТУ:
1. Структура ответа:
   - Краткая формулировка сути вопроса
   - Применимые нормы права (статьи кодексов, законов, подзаконных актов)
   - Пошаговые рекомендации или алгоритм действий
   - Важные процессуальные или практические нюансы
   - Дисклеймер о рекомендательном характере консультации

2. Ссылайтесь только на действующее законодательство.
3. Избегайте предположений — если информация неполная, укажите, что требуется уточнение.
4. Используйте профессиональную юридическую лексику, но сохраняйте доступность изложения.

ФОРМАТ: Четкие разделы, нумерованные списки для алгоритмов, выделение ключевых норм."""

# =============================================================================
# 🔑 API
# =============================================================================
def get_api_key():
    try:
        if "openrouter" in st.secrets and "api_key" in st.secrets["openrouter"]:
            return st.secrets["openrouter"]["api_key"].strip()
    except:
        pass
    return None

def query_ai(prompt: str, text: str):
    key = get_api_key()
    if not key:
        return None, "Ошибка: API-ключ не настроен. Обратитесь к администратору."
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://context-pro.streamlit.app",
                "X-Title": "Context.Pro Legal"
            },
            json={
                "model": "qwen/qwen-2.5-72b-instruct",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                "temperature": 0.2,
                "max_tokens": 1500,
                "top_p": 0.9
            },
            timeout=120
        )
        
        if response.status_code != 200:
            return None, f"Ошибка сервиса ({response.status_code}). Повторите запрос позже."
        
        data = response.json()
        if "choices" not in data or not data["choices"]:
            return None, "Пустой ответ от сервиса"
        
        return data["choices"][0]["message"]["content"], None
        
    except requests.exceptions.Timeout:
        return None, "Тайм-аут соединения. Проверьте интернет или повторите запрос."
    except requests.exceptions.ConnectionError:
        return None, "Ошибка подключения к сервису. Проверьте сетевое соединение."
    except Exception as e:
        return None, f"Ошибка: {type(e).__name__}"

# =============================================================================
# 🎨 UI — ПРОФЕССИОНАЛЬНЫЙ ИНТЕРФЕЙС
# =============================================================================

# === ЗАГОЛОВОК С ЛОГОТИПОМ ===
# Опционально: загрузка изображения логотипа
logo_col, title_col = st.columns([1, 4])

with logo_col:
    # Вариант 1: Загрузка логотипа пользователем
    uploaded_logo = st.sidebar.file_uploader(
        "Логотип",
        type=["png", "jpg", "jpeg", "svg"],
        key="logo_uploader",
        help="Загрузите логотип организации (опционально)"
    )
    if uploaded_logo:
        st.image(uploaded_logo, width=80)
    else:
        # Вариант 2: Дефолтный значок (без эмодзи)
        st.markdown("<div style='text-align:center; font-size:2.5rem; color:#2c3e50; font-family:serif;'>⚖</div>", unsafe_allow_html=True)

with title_col:
    st.title("Context.Pro Legal")
    st.caption("Система анализа договоров и юридической консультации • Российская Федерация • Республика Беларусь")

st.divider()

# === НАСТРОЙКИ: ЮРИСДИКЦИЯ И ТЕМА ===
st.subheader("Настройки")

col_jur, col_theme = st.columns(2)

with col_jur:
    jurisdiction = st.radio(
        "Применимое законодательство:",
        ["РФ", "РБ"],
        horizontal=True,
        key="jur_radio",
        format_func=lambda x: "Российская Федерация" if x == "РФ" else "Республика Беларусь"
    )
    st.session_state.jurisdiction = jurisdiction

with col_theme:
    # Streamlit нативно поддерживает переключение темы через меню
    st.info("Тема интерфейса настраивается через меню ☰ в правом верхнем углу")

st.divider()

# === ВКЛАДКИ ===
tab_contract, tab_question = st.tabs(["Анализ договора", "Юридическая консультация"])

# -------------------------------------------------------------------------
# ВКЛАДКА 1: АНАЛИЗ ДОГОВОРА
# -------------------------------------------------------------------------
with tab_contract:
    st.session_state.last_mode = "contract"
    
    st.subheader("Текст договора")
    st.caption("Вставьте полный текст договора для проведения правового анализа")
    
    contract_text = st.text_area(
        "Содержание договора:",
        value=st.session_state.contract_txt,
        height=220,
        key="contract_area",
        placeholder="Пример: Договор аренды нежилого помещения №... от ... между ...",
        label_visibility="collapsed"
    )
    st.session_state.contract_txt = contract_text
    
    # Кнопки управления
    col_btn1, col_btn2 = st.columns([4, 1])
    
    with col_btn1:
        analyze_contract = st.button(
            "Провести анализ",
            use_container_width=True,
            type="primary",
            key="btn_contract_run",
            disabled=not contract_text.strip()
        )
    
    with col_btn2:
        clear_contract = st.button(
            "Очистить",
            use_container_width=True,
            key="btn_contract_clear"
        )
        if clear_contract:
            st.session_state.contract_txt = ""
            st.session_state.result = ""
            st.rerun()
    
    # Запуск анализа
    if analyze_contract:
        is_valid, message = validate_input(contract_text, "contract")
        if not is_valid:
            st.warning(message)
        else:
            with st.spinner("Выполняется правовой анализ..."):
                result, error = query_ai(build_prompt(jurisdiction, "contract"), contract_text)
                if error:
                    st.error(error)
                else:
                    st.session_state.result = result
                    st.success("Анализ завершён")
    
    # Отображение результата
    if st.session_state.result and st.session_state.last_mode == "contract":
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown("#### Результаты анализа")
        st.write(st.session_state.result)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.download_button(
            "Скачать отчёт",
            st.session_state.result,
            file_name="context_pro_legal_analysis.txt",
            mime="text/plain",
            use_container_width=True,
            key="btn_contract_download"
        )

# -------------------------------------------------------------------------
# ВКЛАДКА 2: ЮРИДИЧЕСКАЯ КОНСУЛЬТАЦИЯ
# -------------------------------------------------------------------------
with tab_question:
    st.session_state.last_mode = "question"
    
    st.subheader("Юридический вопрос")
    st.caption("Сформулируйте вопрос для получения консультации по законодательству")
    
    question_text = st.text_area(
        "Текст вопроса:",
        value=st.session_state.question_txt,
        height=220,
        key="question_area",
        placeholder="Пример: Каков порядок расторжения договора аренды по инициативе арендатора?",
        label_visibility="collapsed"
    )
    st.session_state.question_txt = question_text
    
    # Кнопки управления
    col_btn1, col_btn2 = st.columns([4, 1])
    
    with col_btn1:
        ask_question = st.button(
            "Получить ответ",
            use_container_width=True,
            type="primary",
            key="btn_question_run",
            disabled=not question_text.strip()
        )
    
    with col_btn2:
        clear_question = st.button(
            "Очистить",
            use_container_width=True,
            key="btn_question_clear"
        )
        if clear_question:
            st.session_state.question_txt = ""
            st.session_state.result = ""
            st.rerun()
    
    # Запуск консультации
    if ask_question:
        is_valid, message = validate_input(question_text, "question")
        if not is_valid:
            st.warning(message)
        else:
            with st.spinner("Формируется консультация..."):
                result, error = query_ai(build_prompt(jurisdiction, "question"), question_text)
                if error:
                    st.error(error)
                else:
                    st.session_state.result = result
                    st.success("Консультация готова")
    
    # Отображение результата
    if st.session_state.result and st.session_state.last_mode == "question":
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown("#### Ответ консультанта")
        st.write(st.session_state.result)
        st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# 📎 FOOTER — ПРОФЕССИОНАЛЬНЫЙ
# =============================================================================
st.markdown('<div class="footer">', unsafe_allow_html=True)
st.markdown("**Context.Pro Legal** — система поддержки принятия решений для юристов")
st.markdown("Юрисдикции: Российская Федерация • Республика Беларусь")
st.markdown("Конфиденциальность: данные не сохраняются, не передаются третьим лицам")
st.markdown("*Внимание: результаты анализа носят рекомендательный характер и не заменяют консультацию практикующего юриста*")
st.markdown('</div>', unsafe_allow_html=True)
