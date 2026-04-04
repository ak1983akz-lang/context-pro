import streamlit as st
import time

# 1. Настройка страницы
st.set_page_config(
    page_title="umnyj-yurist",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. Подключение VK Bridge (скрипт выполняется в браузере)
st.markdown("""
<script src="https://unpkg.com/@vkontakte/vk-bridge/dist/browser.min.js"></script>
<script>
    window.addEventListener('load', function() {
        if (window.vkBridge) {
            vkBridge.send('VKWebAppInit')
                .then(() => console.log('VK Bridge initialized'))
                .catch(err => console.log('VK Bridge error:', err));
        }
    });
</script>
""", unsafe_allow_html=True)

# 3. Стили CSS (Магия, которая исправляет дизайн)
st.markdown("""
<style>
    /* Убираем лишнее меню Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Основной контейнер */
    .main .block-container {
        padding: 20px 16px;
        max-width: 600px;
        background-color: #f0f2f5; /* Светло-серый фон как в ВК */
    }

    /* Заголовок */
    h1 {
        text-align: center;
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 20px;
        color: #000;
    }

    /* Секции (белые блоки) */
    .section-box {
        background: white;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .section-title {
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 12px;
        color: #000;
    }

    /* === КНОПКИ ФЛАГОВ (Белые карточки) === */
    /* Мы целимся в кнопки внутри колонок */
    div[data-testid="column"] div.stButton > button {
        background-color: white !important;
        color: #333 !important;
        border: 2px solid #e1e3e6 !important;
        border-radius: 10px !important;
        width: 100% !important;
        padding: 15px 10px !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 8px !important;
        transition: all 0.2s !important;
        box-shadow: none !important;
    }

    /* Ховер эффект для флагов */
    div[data-testid="column"] div.stButton > button:hover {
        border-color: #2688eb !important;
        background-color: #f0f7ff !important;
        transform: translateY(-2px);
    }

    /* === ГЛАВНАЯ КНОПКА (Синяя) === */
    /* Это последняя кнопка на странице */
    div.stVerticalBlock > div:last-of-type div.stButton > button {
        background-color: #2688eb !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        width: 100% !important;
        padding: 16px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(38, 136, 235, 0.3) !important;
    }
    
    div.stVerticalBlock > div:last-of-type div.stButton > button:disabled {
        background-color: #c7cfd6 !important;
        box-shadow: none !important;
        cursor: not-allowed;
    }

    /* Статус успеха */
    .success-box {
        background-color: #e5f6ea;
        border: 1px solid #4bb34b;
        color: #2c2d2e;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        margin-top: 15px;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# 4. Логика приложения

# Инициализация переменных
if 'jurisdiction' not in st.session_state:
    st.session_state.jurisdiction = None
if 'result' not in st.session_state:
    st.session_state.result = None

# Заголовок
st.markdown("<h1>umnyj-yurist</h1>", unsafe_allow_html=True)

# --- Блок 1: Юрисдикция ---
st.markdown('<div class="section-box">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🌍 Юрисдикция</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    # Кнопка Беларусь
    # type="secondary" делает её белой по умолчанию (но мы переопределили CSS выше)
    if st.button("🇧🇾 Беларусь", key="btn_by", use_container_width=True):
        st.session_state.jurisdiction = "BY"
        st.session_state.result = None
        st.rerun()

with col2:
    # Кнопка Россия
    if st.button("🇷🇺 Россия", key="btn_ru", use_container_width=True):
        st.session_state.jurisdiction = "RU"
        st.session_state.result = None
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# --- Блок 2: Документы ---
st.markdown('<div class="section-box">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📄 Документы</div>', unsafe_allow_html=True)

# Загрузчик файлов
uploaded_files = st.file_uploader(
    "Нажмите, чтобы загрузить (PDF, DOCX, JPG)",
    type=['pdf', 'docx', 'jpg', 'jpeg', 'png'],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

if uploaded_files:
    st.success(f"✅ Загружено файлов: {len(uploaded_files)}")
    for f in uploaded_files:
        st.caption(f"• {f.name}")

st.markdown('</div>', unsafe_allow_html=True)

# --- Блок 3: Кнопка Анализа ---
# Кнопка активна только если выбрана страна и есть файлы
is_ready = st.session_state.jurisdiction is not None and uploaded_files

# Эта кнопка станет синей благодаря CSS (она последняя в блоке)
if st.button("🔍 Анализировать документы", disabled=not is_ready):
    with st.spinner('⏳ Идет анализ документов...'):
        time.sleep(2) # Имитация работы
        
        jur_text = "законодательству РФ" if st.session_state.jurisdiction == "RU" else "законодательству РБ"
        st.session_state.result = f"✅ Проверено {len(uploaded_files)} файл(ов) по {jur_text}. Нарушений не найдено."

# Показываем результат
if st.session_state.result:
    st.markdown(f'<div class="success-box">{st.session_state.result}</div>', unsafe_allow_html=True)
