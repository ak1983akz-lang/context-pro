import streamlit as st
import requests
import re

# =============================================================================
# 🏛 CONTEXT.PRO LEGAL — IMPERIUM EDITION v0.3
# 🇷🇺 РФ • 🇧🇾 РБ • Стиль: Ампир • Валидация: Hard • Анимация: Строгая
# =============================================================================

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(
    page_title="Context.Pro Legal", 
    page_icon="⚖️", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- ИНИЦИАЛИЗАЦИЯ SESSION STATE ---
if 'contract_txt' not in st.session_state:
    st.session_state.contract_txt = ""
if 'question_txt' not in st.session_state:
    st.session_state.question_txt = ""
if 'result' not in st.session_state:
    st.session_state.result = ""
if 'analysis_lock' not in st.session_state:
    st.session_state.analysis_lock = False  # Блокировка повторных кликов

# =============================================================================
# 🎨 ГЛОБАЛЬНЫЙ CSS "АМПИР" — ПЕРЕОПРЕДЕЛЕНИЕ ВСЕХ СТИЛЕЙ STREAMLIT
# =============================================================================
EMPIRE_CSS = """
<style>
/* === ПЕРЕМЕННЫЕ ЦВЕТОВ === */
:root {
    --empire-bg-primary: #0A1128;
    --empire-bg-secondary: #1a233a;
    --empire-gold: #D4AF37;
    --empire-gold-dim: #B8962E;
    --empire-text: #FFFFF0;
    --empire-text-dim: #C0C0C0;
    --empire-danger: #B22222;
    --empire-border: 1px solid var(--empire-gold);
}

/* === СБРОС ФОНА ДЛЯ ВСЕХ ЭЛЕМЕНТОВ === */
.stApp, .main, .block-container,
.stMarkdown, .stAlert, .stInfo, .stSuccess, .stWarning, .stError,
div[data-testid="stMarkdownContainer"], div[data-testid="stTextArea"],
div[data-testid="stTextInput"], div[data-testid="stButton"],
div[data-testid="stRadio"], div[data-testid="stTabs"],
section[data-testid="stSidebar"], .stSidebar {
    background: var(--empire-bg-primary) !important;
    color: var(--empire-text) !important;
}

/* === ТЕКСТ === */
* { color: var(--empire-text) !important; }
h1, h2, h3, h4, h5, h6 { 
    color: var(--empire-gold) !important; 
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 600 !important;
}
p, span, label, div { color: var(--empire-text) !important; }

/* === ПОЛЯ ВВОДА === */
.stTextArea textarea, .stTextInput input {
    background: var(--empire-bg-secondary) !important;
    color: var(--empire-text) !important;
    border: 1px solid var(--empire-gold-dim) !important;
    border-radius: 6px !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--empire-gold) !important;
    box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.2) !important;
}

/* === КНОПКИ — ИМПЕРСКИЙ СТИЛЬ === */
.stButton>button {
    background: transparent !important;
    border: 2px solid var(--empire-gold) !important;
    color: var(--empire-gold) !important;
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    border-radius: 6px !important;
    padding: 12px 24px !important;
    transition: all 0.3s ease !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
.stButton>button:hover {
    background: var(--empire-gold) !important;
    color: var(--empire-bg-primary) !important;
    box-shadow: 0 4px 20px rgba(212, 175, 55, 0.4) !important;
    transform: translateY(-1px) !important;
}
.stButton>button:disabled {
    border-color: var(--empire-text-dim) !important;
    color: var(--empire-text-dim) !important;
    cursor: not-allowed !important;
    opacity: 0.6 !important;
}

/* === КАРТОЧКА РЕЗУЛЬТАТА — "МРАМОРНАЯ ПАНЕЛЬ" === */
.empire-card {
    background: linear-gradient(135deg, var(--empire-bg-secondary) 0%, var(--empire-bg-primary) 100%) !important;
    border: var(--empire-border) !important;
    border-radius: 8px !important;
    padding: 1.5rem !important;
    margin: 1.5rem 0 !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;
}
.empire-card * { color: var(--empire-text) !important; }
.empire-card h4 { color: var(--empire-gold) !important; border-bottom: 1px solid var(--empire-gold-dim); padding-bottom: 0.5rem; }

/* === ПРЕДУПРЕЖДЕНИЯ И ОШИБКИ === */
.stWarning, .stError {
    background: var(--empire-bg-secondary) !important;
    border-left: 4px solid var(--empire-danger) !important;
    color: var(--empire-text) !important;
}
.stWarning *, .stError * { color: var(--empire-text) !important; }

/* === SIDEBAR === */
section[data-testid="stSidebar"] {
    background: var(--empire-bg-secondary) !important;
    border-right: var(--empire-border) !important;
}
section[data-testid="stSidebar"] * { color: var(--empire-text) !important; }

/* === СКРЫТИЕ ТЕХНИЧЕСКИХ АРТЕФАКТОВ === */
#MainMenu, .stDeployButton, footer, header, 
div[data-testid="stDecoration"], .mobile-menu-btn,
[data-testid="stSidebar"] > div:first-child button,
div[data-testid="stMarkdown"] pre code {
    display: none !important;
}

/* === СТРОГИЙ СПИННЕР — ПУЛЬСАЦИЯ ЗОЛОТА (НИКАКОГО СПОРТА!) === */
@keyframes empire-pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(0.98); }
}
.empire-loading {
    display: flex !important; align-items: center !important; justify-content: center !important;
    color: var(--empire-gold) !important; font-weight: 500 !important; font-size: 1.1rem !important;
    animation: empire-pulse 2s infinite ease-in-out !important;
    padding: 1.5rem !important; margin: 1rem 0 !important;
    background: var(--empire-bg-secondary) !important;
    border: 1px dashed var(--empire-gold-dim) !important;
    border-radius: 8px !important;
}
.empire-loading::before {
    content: "⚖️"; margin-right: 0.75rem !important; font-size: 1.4rem !important;
}

/* === МОБИЛЬНАЯ АДАПТАЦИЯ === */
@media (max-width: 768px) {
    .mobile-jurisdiction { display: block !important; }
    .desktop-only { display: none !important; }
    .block-container { padding: 1rem !important; }
    .empire-card { padding: 1rem !important; }
    .stButton>button { font-size: 14px !important; padding: 10px 20px !important; }
}
@media (min-width: 769px) {
    .mobile-jurisdiction { display: none !important; }
}

/* === ШРИФТЫ === */
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500&display=swap');
</style>
"""
st.markdown(EMPIRE_CSS, unsafe_allow_html=True)

# =============================================================================
# 🔒 ВАЛИДАЦИЯ ВВОДА — HARD MODE (ALIBABA-STYLE GUARDRAILS)
# =============================================================================
def validate_input(text: str, mode: str) -> tuple[bool, str]:
    """
    Валидация ввода ДО отправки в AI.
    mode: 'contract' или 'question'
    Возвращает: (passed: bool, message: str)
    """
    text = text.strip()
    
    # 1. Пустой ввод
    if not text:
        return False, "⚠️ Поле не может быть пустым"
    
    # 2. Проверка на "мусор" (слишком мало уникальных символов или нет букв)
    if len(set(text.lower())) < 5 or not re.search(r'[а-яА-Яa-zA-Z]', text):
        return False, "⚠️ Введите осмысленный текст"
    
    if mode == "contract":
        # 3. Минимальная длина для договора
        if len(text) < 100:
            return False, "📋 Для анализа договора нужно минимум 100 символов"
        
        # 4. Проверка на юридические маркеры
        legal_markers = [
            "договор", "контракт", "сторона", "обязательство", "статья", 
            "ГК", "ФЗ", "пункт", "параграф", "соглашение", "аренда", 
            "поставка", "услуга", "оплата", "ответственность"
        ]
        text_lower = text.lower()
        if not any(marker in text_lower for marker in legal_markers):
            return False, "🔍 Это не похоже на текст договора. Проверьте текст или перейдите во вкладку «💬 Вопрос»"
    
    elif mode == "question":
        # 5. Минимальная длина для вопроса
        if len(text) < 20:
            return False, "💬 Сформулируйте вопрос подробнее (мин. 20 символов)"
    
    return True, ""


# =============================================================================
# 🧠 СИСТЕМНЫЕ ПРОМПТЫ С GUARDRAILS
# =============================================================================
def build_system_prompt(jur: str, mode: str) -> str:
    """Формирует жесткий системный промпт с ограничениями"""
    
    jur_base = "Российская Федерация (ГК РФ, ФЗ, практика ВС РФ)" if "РФ" in jur else "Республика Беларусь (ГК РБ, Декреты, практика ВС РБ)"
    
    if mode == "contract":
        return f"""Ты — профессиональный ИИ-помощник юриста Context.Pro Legal. Юрисдикция: {jur_base}.

🔒 ПРАВИЛА РАБОТЫ (СТРОГО):
1. ВХОДНОЙ КОНТРОЛЬ: Если текст не является договором, не содержит юридических терминов или слишком короткий → НЕМЕДЛЕННО ОТВЕТЬ: "⚠️ Это не похоже на текст договора. Пожалуйста, вставьте полный текст договора или задайте вопрос во вкладке «💬 Вопрос»." Не продолжай анализ.

2. АНАЛИЗ (только если текст прошел проверку):
   - Выдели риски: [🔴 Критический] / [🟡 Средний] / [🟢 Низкий]
   - Цитируй конкретные статьи законов (ГК РФ/РБ, ФЗ, Декреты)
   - Дай практическую рекомендацию по исправлению
   - Будь краток, но точен

3. ЗАПРЕТЫ:
   - Не выдумывай статьи законов. Если не уверен — напиши "Требуется уточнение по практике"
   - Не смешивай нормы РФ и РБ
   - Не давай ответ, если входной текст не прошел валидацию

4. ФОРМАТ ОТВЕТА:
   ### 🔍 Выявленные риски
   • [Уровень] Риск: описание → Статья закона → Рекомендация
   
   ### ✅ Что в порядке
   • Пункты без рисков
   
   ### 📋 Итог
   Краткая оценка + дисклеймер: "Результат носит рекомендательный характер"
"""
    
    else:  # question mode
        return f"""Ты — профессиональный ИИ-консультант по праву. Юрисдикция: {jur_base}.

🔒 ПРАВИЛА РАБОТЫ:
1. Отвечай ТОЛЬКО на юридические вопросы. Если вопрос не по теме → вежливо уточни: "Пожалуйста, задайте вопрос по договорному праву, обязательствам или законодательству {jur_base}."

2. Всегда указывай нормативную базу: статьи ГК РФ/РБ, номера ФЗ, Декретов.

3. Структура ответа:
   ### 📌 Суть вопроса
   ### ⚖️ Нормативная база
   ### 🔄 Пошаговые рекомендации
   ### ⚠️ Важные нюансы

4. Дисклеймер в конце: "Консультация носит информационный характер. Для представления интересов обратитесь к практикующему юристу."

5. Не заменяй очную консультацию. Будь точен, но доступен.
"""


# =============================================================================
# 🔑 ПОЛУЧЕНИЕ API КЛЮЧА
# =============================================================================
def get_api_key() -> str | None:
    """Безопасное получение ключа из secrets"""
    try:
        if "openrouter" in st.secrets and "api_key" in st.secrets["openrouter"]:
            return st.secrets["openrouter"]["api_key"]
    except:
        pass
    return None


# =============================================================================
# 🤖 ЗАПРОС К AI (OPENROUTER / DEEPSEEK)
# =============================================================================
def query_ai(system_prompt: str, user_text: str) -> tuple[str | None, str | None]:
    """
    Отправляет запрос к AI.
    Возвращает: (ответ_или_None, ошибка_или_None)
    """
    api_key = get_api_key()
    if not api_key:
        return None, "❌ API ключ не настроен. Обратитесь к администратору."
    
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
            return None, f"❌ Ошибка сервиса ({response.status_code}). Попробуйте позже."
        
        data = response.json()
        if "choices" not in data or not data["choices"]:
            return None, "❌ Пустой ответ от сервиса"
        
        return data["choices"][0]["message"]["content"], None
        
    except requests.exceptions.Timeout:
        return None, "⏱ Тайм-аут соединения. Проверьте интернет."
    except requests.exceptions.ConnectionError:
        return None, "🔌 Ошибка подключения. Проверьте сеть."
    except Exception as e:
        return None, f"❌ Неожиданная ошибка: {type(e).__name__}"


# =============================================================================
# 🎨 UI КОМПОНЕНТЫ В СТИЛЕ "АМПИР"
# =============================================================================
def render_header():
    st.markdown('<div style="text-align:center; font-size:2.5rem; margin:0.5rem 0;">🇷🇺 &nbsp; ⚖️ &nbsp; 🇧🇾</div>', unsafe_allow_html=True)
    st.markdown('<h1 style="text-align:center; margin:0; color:#D4AF37 !important;">Context.Pro Legal</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#C0C0C0; margin:0.5rem 0 1.5rem; font-size:0.95rem;">Анализ договоров • Консультации • РФ/РБ</p>', unsafe_allow_html=True)


def render_jurisdiction_toggle() -> str:
    """Рендерит переключатель юрисдикции для мобильных и десктопа"""
    # Мобильный переключатель (виден только на малых экранах)
    st.markdown('<div class="mobile-jurisdiction">', unsafe_allow_html=True)
    jur_mobile = st.radio(
        "⚖️ Юрисдикция:",
        ["🇷🇺 РФ", "🇧🇾 РБ"],
        horizontal=True,
        index=0,
        key="jur_mobile_radio",
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Десктопный переключатель (в сайдбаре)
    with st.sidebar:
        st.markdown("### ⚙️ Настройки", unsafe_allow_html=True)
        jur_desktop = st.radio(
            "⚖️ Юрисдикция:",
            ["🇷🇺 РФ", "🇧🇾 РБ"],
            horizontal=False,
            index=0,
            key="jur_desktop_radio"
        )
        st.markdown("---")
        if st.button("🗑️ Очистить всё", use_container_width=True):
            st.session_state.contract_txt = ""
            st.session_state.question_txt = ""
            st.session_state.result = ""
            st.session_state.analysis_lock = False
            st.rerun()
        st.markdown("---")
        st.caption("🔒 Данные не сохраняются • Конфиденциально")
    
    # Определяем активную юрисдикцию
    if st.session_state.get("jur_mobile_radio"):
        return st.session_state.jur_mobile_radio
    elif st.session_state.get("jur_desktop_radio"):
        return st.session_state.jur_desktop_radio
    return "🇷🇺 РФ"


def render_result_card(content: str, title: str = "📋 Результат анализа"):
    """Отображает результат в стилизованной карточке"""
    st.markdown(f"""
    <div class="empire-card">
        <h4 style="margin-top:0; border-bottom:1px solid #B8962E; padding-bottom:0.5rem;">{title}</h4>
        <div style="line-height:1.6;">{content}</div>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    st.markdown("""
    <div style="text-align:center; color:#666; font-size:0.75rem; padding:2rem 1rem 1rem; border-top:1px solid #333; margin-top:2rem;">
        ⚖️ <strong>Context.Pro Legal</strong> | 🇷🇺 РФ • 🇧🇾 РБ | Приватно • Без логов • Без сохранения данных
        <br><span style="color:#888; font-size:0.7rem;">⚠️ ИИ-помощник не заменяет очную консультацию юриста. Результаты носят рекомендательный характер.</span>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# 🚀 ОСНОВНАЯ ЛОГИКА ПРИЛОЖЕНИЯ
# =============================================================================
def main():
    # Рендерим шапку
    render_header()
    
    # Переключатель юрисдикции
    jurisdiction = render_jurisdiction_toggle()
    
    # Вкладки
    tab_contract, tab_question = st.tabs(["📋 Анализ договора", "💬 Юридический вопрос"])
    
    # -------------------------------------------------------------------------
    # ВКЛАДКА 1: АНАЛИЗ ДОГОВОРА
    # -------------------------------------------------------------------------
    with tab_contract:
        st.markdown("#### 📄 Вставьте текст договора")
        st.caption("💡 Пример: «Договор аренды №123 от 01.01.2024 между ООО «Ромашка» и ИП Иванов...»")
        
        contract_text = st.text_area(
            "Текст договора:",
            value=st.session_state.contract_txt,
            height=220,
            key="contract_input",
            placeholder="Скопируйте сюда полный текст договора для анализа рисков..."
        )
        st.session_state.contract_txt = contract_text
        
        # Кнопка анализа с блокировкой
        analyze_disabled = st.session_state.analysis_lock or not contract_text.strip()
        
        if st.button("⚖️ Проверить договор", use_container_width=True, disabled=analyze_disabled):
            # Валидация
            is_valid, message = validate_input(contract_text, mode="contract")
            if not is_valid:
                st.warning(message)
            else:
                # Блокируем повторные клики
                st.session_state.analysis_lock = True
                st.rerun()
        
        # Если анализ в процессе
        if st.session_state.analysis_lock and contract_text.strip():
            with st.container():
                st.markdown('<div class="empire-loading">Сверяем с нормами ' + jurisdiction + '...</div>', unsafe_allow_html=True)
                
                # Системный промпт
                sys_prompt = build_system_prompt(jurisdiction, mode="contract")
                
                # Запрос к AI
                result, error = query_ai(sys_prompt, contract_text)
                
                # Разблокировка
                st.session_state.analysis_lock = False
                
                if error:
                    st.error(error)
                else:
                    st.session_state.result = result
                    render_result_card(result, "🔍 Результаты анализа")
                    
                    # Кнопка скачивания
                    st.download_button(
                        "📥 Скачать отчёт",
                        result,
                        file_name="context_pro_analysis.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
        
        # Отображение сохраненного результата
        elif st.session_state.result and tab_contract == st.session_state.get("active_tab", "contract"):
            render_result_card(st.session_state.result, "🔍 Результаты анализа")
        
        # Кнопка очистки
        if st.button("🗑️ Очистить поле", key="clear_contract"):
            st.session_state.contract_txt = ""
            st.session_state.result = ""
            st.rerun()
    
    # -------------------------------------------------------------------------
    # ВКЛАДКА 2: ЮРИДИЧЕСКИЙ ВОПРОС
    # -------------------------------------------------------------------------
    with tab_question:
        st.markdown("#### ⚖️ Задайте юридический вопрос")
        st.caption("💡 Пример: «Какие риски по ст. 651 ГК РФ при аренде нежилого помещения?»")
        
        question_text = st.text_area(
            "Ваш вопрос:",
            value=st.session_state.question_txt,
            height=200,
            key="question_input",
            placeholder="Сформулируйте вопрос по законодательству РФ или РБ..."
        )
        st.session_state.question_txt = question_text
        
        # Кнопка получения ответа с блокировкой
        answer_disabled = st.session_state.analysis_lock or not question_text.strip()
        
        if st.button("⚡ Получить ответ", use_container_width=True, disabled=answer_disabled):
            # Валидация
            is_valid, message = validate_input(question_text, mode="question")
            if not is_valid:
                st.warning(message)
            else:
                st.session_state.analysis_lock = True
                st.rerun()
        
        # Если ответ в процессе
        if st.session_state.analysis_lock and question_text.strip():
            with st.container():
                st.markdown('<div class="empire-loading">Готовим консультацию по ' + jurisdiction + '...</div>', unsafe_allow_html=True)
                
                sys_prompt = build_system_prompt(jurisdiction, mode="question")
                result, error = query_ai(sys_prompt, question_text)
                
                st.session_state.analysis_lock = False
                
                if error:
                    st.error(error)
                else:
                    st.session_state.result = result
                    render_result_card(result, "💬 Консультация")
        
        # Отображение сохраненного ответа
        elif st.session_state.result and tab_question == st.session_state.get("active_tab", "question"):
            render_result_card(st.session_state.result, "💬 Консультация")
        
        # Кнопка очистки
        if st.button("🗑️ Очистить поле", key="clear_question"):
            st.session_state.question_txt = ""
            st.session_state.result = ""
            st.rerun()
    
    # Сохраняем активную вкладку для корректного отображения результата
    st.session_state.active_tab = "contract" if tab_contract else "question"
    
    # Футер
    render_footer()


# =============================================================================
# 🏁 ЗАПУСК
# =============================================================================
if __name__ == "__main__":
    main()
