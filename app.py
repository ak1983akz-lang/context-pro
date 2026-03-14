import streamlit as st
import requests
import re

# =============================================================================
# 🏛 CONTEXT.PRO LEGAL — IMPERIUM EDITION v0.3.3 (TAB LOGIC FIX)
# 🇷🇺 РФ • 🇧🇾 РБ • Стиль: Ампир • Лимиты: 50/10 • Вкладки: ИСПРАВЛЕНО
# =============================================================================

st.set_page_config(page_title="Context.Pro Legal", page_icon="⚖️", layout="centered", initial_sidebar_state="expanded")

# --- SESSION STATE ---
if 'contract_txt' not in st.session_state:
    st.session_state.contract_txt = ""
if 'question_txt' not in st.session_state:
    st.session_state.question_txt = ""
if 'result' not in st.session_state:
    st.session_state.result = ""
if 'analysis_lock' not in st.session_state:
    st.session_state.analysis_lock = False
if 'active_mode' not in st.session_state:
    st.session_state.active_mode = "contract"  # "contract" или "question"
if 'jurisdiction' not in st.session_state:
    st.session_state.jurisdiction = "🇷🇺 РФ"

# =============================================================================
# 🎨 CSS "АМПИР"
# =============================================================================
EMPIRE_CSS = """
<style>
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
.stApp, .main, .block-container, .stMarkdown, .stAlert, .stInfo, .stSuccess, .stWarning, .stError,
div[data-testid="stMarkdownContainer"], div[data-testid="stTextArea"], div[data-testid="stTextInput"],
div[data-testid="stButton"], div[data-testid="stRadio"], div[data-testid="stTabs"],
section[data-testid="stSidebar"], .stSidebar {
    background: var(--empire-bg-primary) !important;
    color: var(--empire-text) !important;
}
* { color: var(--empire-text) !important; }
h1, h2, h3, h4, h5, h6 { color: var(--empire-gold) !important; font-family: 'Cormorant Garamond', serif !important; font-weight: 600 !important; }
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
.stWarning, .stError {
    background: var(--empire-bg-secondary) !important;
    border-left: 4px solid var(--empire-danger) !important;
    color: var(--empire-text) !important;
}
.stWarning *, .stError * { color: var(--empire-text) !important; }
section[data-testid="stSidebar"] {
    background: var(--empire-bg-secondary) !important;
    border-right: var(--empire-border) !important;
}
section[data-testid="stSidebar"] * { color: var(--empire-text) !important; }
#MainMenu, .stDeployButton, footer, header, div[data-testid="stDecoration"], .mobile-menu-btn,
[data-testid="stSidebar"] > div:first-child button, div[data-testid="stMarkdown"] pre code {
    display: none !important;
}
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
.empire-loading::before { content: "⚖️"; margin-right: 0.75rem !important; font-size: 1.4rem !important; }
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
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500&display=swap');
</style>
"""
st.markdown(EMPIRE_CSS, unsafe_allow_html=True)

# =============================================================================
# 🔒 ВАЛИДАЦИЯ — ЛИМИТЫ 50/10
# =============================================================================
def validate_input(text: str, mode: str) -> tuple[bool, str]:
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
        return f"""Ты — ИИ-помощник юриста Context.Pro Legal. Юрисдикция: {jur_base}.
ПРАВИЛА: 1) Если текст не договор или <50 символов → ОТВЕТЬ: "⚠️ Это не похоже на договор." 2) Выдели риски [🔴//🟢], цитируй статьи, дай рекомендации. 3) Не выдумывай статьи. 4) Формат: ### 🔍 Риски • ### ✅ Что в порядке • ### 📋 Итог"""
    else:
        return f"""Ты — ИИ-консультант по праву. Юрисдикция: {jur_base}.
ПРАВИЛА: Отвечай только на юридические вопросы. Указывай статьи ГК/ФЗ. Структура: 📌 Суть → ⚖️ Нормы → 🔄 Рекомендации → ⚠️ Нюансы. Дисклеймер в конце."""

# =============================================================================
# 🔑 API
# =============================================================================
def get_api_key() -> str | None:
    try:
        if "openrouter" in st.secrets and "api_key" in st.secrets["openrouter"]:
            return st.secrets["openrouter"]["api_key"]
    except:
        pass
    return None

def query_ai(system_prompt: str, user_text: str) -> tuple[str | None, str | None]:
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
            return None, f"❌ Ошибка сервиса ({response.status_code})."
        data = response.json()
        if "choices" not in data or not data["choices"]:
            return None, "❌ Пустой ответ"
        return data["choices"][0]["message"]["content"], None
    except requests.exceptions.Timeout:
        return None, "⏱ Тайм-аут."
    except Exception as e:
        return None, f"❌ Ошибка: {type(e).__name__}"

# =============================================================================
# 🎨 UI
# =============================================================================
def render_header():
    st.markdown('<div style="text-align:center; font-size:2.5rem; margin:0.5rem 0;">🇷🇺 &nbsp; ⚖️ &nbsp; 🇧🇾</div>', unsafe_allow_html=True)
    st.markdown('<h1 style="text-align:center; margin:0; color:#D4AF37 !important;">Context.Pro Legal</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#C0C0C0; margin:0.5rem 0 1.5rem; font-size:0.95rem;">Анализ договоров • Консультации • РФ/РБ</p>', unsafe_allow_html=True)

def render_jurisdiction_toggle() -> str:
    st.markdown('<div class="mobile-jurisdiction">', unsafe_allow_html=True)
    jur_mobile = st.radio("⚖️ Юрисдикция:", ["🇷🇺 РФ", "🇧 РБ"], horizontal=True, index=0, key="jur_mobile_radio", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("### ⚙️ Настройки", unsafe_allow_html=True)
        jur_desktop = st.radio("⚖️ Юрисдикция:", ["🇷 РФ", "🇧 РБ"], horizontal=False, index=0, key="jur_desktop_radio")
        st.markdown("---")
        if st.button("🗑️ Очистить всё", use_container_width=True):
            for key in ['contract_txt', 'question_txt', 'result', 'analysis_lock']:
                st.session_state[key] = "" if key != 'analysis_lock' else False
            st.rerun()
        st.markdown("---")
        st.caption("🔒 Конфиденциально • Без логов")
    if st.session_state.get("jur_mobile_radio"):
        return st.session_state.jur_mobile_radio
    elif st.session_state.get("jur_desktop_radio"):
        return st.session_state.jur_desktop_radio
    return "🇷🇺 РФ"

def render_result_card(content: str, title: str = "📋 Результат"):
    st.markdown(f"""<div class="empire-card"><h4 style="margin-top:0; border-bottom:1px solid #B8962E; padding-bottom:0.5rem;">{title}</h4><div style="line-height:1.6;">{content}</div></div>""", unsafe_allow_html=True)

def render_footer():
    st.markdown("""<div style="text-align:center; color:#666; font-size:0.75rem; padding:2rem 1rem 1rem; border-top:1px solid #333; margin-top:2rem;">⚖️ <strong>Context.Pro Legal</strong> | 🇷🇺 РФ • 🇧🇾 РБ | Приватно • Без логов<br><span style="color:#888; font-size:0.7rem;">⚠️ ИИ-помощник не заменяет очную консультацию юриста.</span></div>""", unsafe_allow_html=True)

# =============================================================================
# 🚀 MAIN — ИСПРАВЛЕННАЯ ЛОГИКА ВКЛАДОК
# =============================================================================
def main():
    render_header()
    jurisdiction = render_jurisdiction_toggle()
    st.session_state.jurisdiction = jurisdiction
    
    # Создаём вкладки
    tab_contract, tab_question = st.tabs(["📋 Анализ договора", "💬 Юридический вопрос"])
    
    # -------------------------------------------------------------------------
    # ВКЛАДКА 1: ДОГОВОР
    # -------------------------------------------------------------------------
    with tab_contract:
        # При открытии вкладки переключаем режим
        st.session_state.active_mode = "contract"
        
        st.markdown("#### 📄 Вставьте текст договора")
        st.caption("💡 Минимум 50 символов")
        
        contract_text = st.text_area(
            "Текст договора:",
            value=st.session_state.contract_txt,
            height=220,
            key="contract_input",
            placeholder="Скопируйте текст договора..."
        )
        st.session_state.contract_txt = contract_text
        
        # Кнопка анализа
        if st.button("⚖️ Проверить договор", use_container_width=True, 
                     disabled=st.session_state.analysis_lock or not contract_text.strip(),
                     key="btn_contract"):
            is_valid, message = validate_input(contract_text, "contract")  # ← Явно "contract"
            if not is_valid:
                st.warning(message)
            else:
                st.session_state.analysis_lock = True
                st.rerun()
        
        # Процесс анализа
        if st.session_state.analysis_lock and st.session_state.active_mode == "contract" and contract_text.strip():
            with st.container():
                st.markdown(f'<div class="empire-loading">Сверяем с нормами {jurisdiction}...</div>', unsafe_allow_html=True)
                result, error = query_ai(build_system_prompt(jurisdiction, "contract"), contract_text)
                st.session_state.analysis_lock = False
                if error:
                    st.error(error)
                else:
                    st.session_state.result = result
                    st.session_state.last_mode = "contract"
                    render_result_card(result, "🔍 Результаты анализа")
                    st.download_button("📥 Скачать отчёт", result, "context_pro_analysis.txt", "text/plain", use_container_width=True, key="dl_contract")
        
        # Показать сохранённый результат
        elif st.session_state.get("last_mode") == "contract" and st.session_state.result:
            render_result_card(st.session_state.result, "🔍 Результаты анализа")
        
        if st.button("🗑️ Очистить поле", key="clear_contract"):
            st.session_state.contract_txt = ""
            st.session_state.result = ""
            st.session_state.last_mode = ""
            st.rerun()
    
    # -------------------------------------------------------------------------
    # ВКЛАДКА 2: ВОПРОС
    # -------------------------------------------------------------------------
    with tab_question:
        # При открытии вкладки переключаем режим
        st.session_state.active_mode = "question"
        
        st.markdown("#### ⚖️ Задайте юридический вопрос")
        st.caption("💡 Минимум 10 символов")
        
        question_text = st.text_area(
            "Ваш вопрос:",
            value=st.session_state.question_txt,
            height=200,
            key="question_input",
            placeholder="Сформулируйте вопрос..."
        )
        st.session_state.question_txt = question_text
        
        # Кнопка получения ответа
        if st.button("⚡ Получить ответ", use_container_width=True,
                     disabled=st.session_state.analysis_lock or not question_text.strip(),
                     key="btn_question"):
            is_valid, message = validate_input(question_text, "question")  # ← Явно "question"
            if not is_valid:
                st.warning(message)
            else:
                st.session_state.analysis_lock = True
                st.rerun()
        
        # Процесс получения ответа
        if st.session_state.analysis_lock and st.session_state.active_mode == "question" and question_text.strip():
            with st.container():
                st.markdown(f'<div class="empire-loading">Готовим консультацию по {jurisdiction}...</div>', unsafe_allow_html=True)
                result, error = query_ai(build_system_prompt(jurisdiction, "question"), question_text)
                st.session_state.analysis_lock = False
                if error:
                    st.error(error)
                else:
                    st.session_state.result = result
                    st.session_state.last_mode = "question"
                    render_result_card(result, "💬 Консультация")
        
        # Показать сохранённый результат
        elif st.session_state.get("last_mode") == "question" and st.session_state.result:
            render_result_card(st.session_state.result, "💬 Консультация")
        
        if st.button("🗑️ Очистить поле", key="clear_question"):
            st.session_state.question_txt = ""
            st.session_state.result = ""
            st.session_state.last_mode = ""
            st.rerun()
    
    render_footer()

if __name__ == "__main__":
    main()
