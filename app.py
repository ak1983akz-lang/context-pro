import streamlit as st
import time
import os

# Настройка страницы (должна быть первой командой)
st.set_page_config(
    page_title="umnyj-yurist",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================
# VK BRIDGE: Вставка JavaScript в <head>
# ============================================
st.markdown("""
<script src="https://unpkg.com/@vkontakte/vk-bridge/dist/browser.min.js"></script>
<script>
    window.addEventListener('load', function() {
        if (window.vkBridge) {
            vkBridge.send('VKWebAppInit')
                .then(() => console.log('VK Bridge: OK'))
                .catch(err => console.log('VK Bridge error:', err));
        }
    });
    
    // Функция для вибрации (вызывается из Python)
    function triggerHaptic(style) {
        if (window.vkBridge) {
            vkBridge.send('VKWebAppTapticImpactOccurred', { style: style });
        }
    }
</script>
""", unsafe_allow_html=True)

# ============================================
# CSS СТИЛИ (флаги, кнопки, адаптив)
# ============================================
st.markdown("""
<style>
    /* Скрыть лишние элементы Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Контейнер */
    .main .block-container {
        padding: 20px 16px;
        max-width: 600px;
    }
    
    /* Заголовок */
    .app-title {
        text-align: center;
        font-size: 24px;
        font-weight: 700;
        margin: 10px 0 20px;
        color: #1c1d1f;
    }
    
    /* Секции */
    .section {
        background: #ffffff;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    
    .section-title {
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 12px;
        color: #1c1d1f;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Флаги */
    .flags-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
    }
    
    .flag-card {
        background: #f0f2f5;
        border: 2px solid transparent;
        border-radius: 10px;
        padding: 12px;
        cursor: pointer;
        transition: all 0.2s;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }
    
    .flag-card:hover { transform: translateY(-2px); }
    .flag-card.active {
        border-color: #2688eb;
        background: #e5f1fa;
    }
    
    .flag-svg {
        width: 48px;
        height: 32px;
        border-radius: 4px;
        margin-bottom: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .flag-label {
        font-size: 13px;
        font-weight: 500;
        color: #1c1d1f;
    }
    
    /* Загрузка файлов */
    .upload-area {
        border: 2px dashed #e1e3e6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        cursor: pointer;
        transition: border-color 0.2s;
    }
    .upload-area:hover { border-color: #2688eb; }
    
    .upload-text {
        font-size: 14px;
        font-weight: 500;
        color: #2688eb;
        margin: 8px 0 4px;
    }
    
    .upload-subtext {
        font-size: 12px;
        color: #818c99;
    }
    
    /* Кнопка */
    .stButton > button {
        width: 100%;
        background: #2688eb;
        color: white;
        border: none;
        border-radius: 10px;
        padding: 14px;
        font-size: 15px;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s;
    }
    .stButton > button:hover { background: #1d78d4; }
    .stButton > button:disabled {
        background: #c7cfd6;
        cursor: not-allowed;
    }
    
    /* Статус */
    .status-box {
        margin-top: 15px;
        padding: 12px;
        border-radius: 8px;
        font-size: 14px;
        text-align: center;
    }
    .status-success {
        background: #e5f6ea;
        color: #2c2d2e;
        border: 1px solid #4bb34b;
    }
    .status-error {
        background: #ffebee;
        color: #ff3347;
        border: 1px solid #ff3347;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# ЛОГИКА ПРИЛОЖЕНИЯ
# ============================================

# Заголовок
st.markdown('<div class="app-title">umnyj-yurist</div>', unsafe_allow_html=True)

# Session state для хранения выбора
if 'jurisdiction' not in st.session_state:
    st.session_state.jurisdiction = None
if 'files' not in st.session_state:
    st.session_state.files = []

# --- Блок 1: Выбор юрисдикции ---
st.markdown('<div class="section"><div class="section-title">🌍 Юрисдикция</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    # Флаг Беларуси
    by_active = st.session_state.jurisdiction == 'BY'
    if st.button(
        '🇧🇾 Беларусь',
        key='btn_by',
        use_container_width=True,
        type='primary' if by_active else 'secondary'
    ):
        st.session_state.jurisdiction = 'BY'
        st.rerun()

with col2:
    # Флаг России
    ru_active = st.session_state.jurisdiction == 'RU'
    if st.button(
        '🇷🇺 Россия',
        key='btn_ru',
        use_container_width=True,
        type='primary' if ru_active else 'secondary'
    ):
        st.session_state.jurisdiction = 'RU'
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# --- Блок 2: Загрузка файлов ---
st.markdown('<div class="section"><div class="section-title">📄 Документы</div>', unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Нажмите, чтобы загрузить файлы",
    type=['pdf', 'docx', 'jpg', 'jpeg', 'png'],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

if uploaded_files:
    st.session_state.files = uploaded_files
    st.write(f"✅ Загружено файлов: {len(uploaded_files)}")
    for f in uploaded_files:
        st.caption(f"• {f.name} ({f.size // 1024} KB)")

st.markdown('</div>', unsafe_allow_html=True)

# --- Блок 3: Кнопка анализа ---
can_analyze = st.session_state.jurisdiction and len(st.session_state.files) > 0

if st.button("🔍 Анализировать документы", disabled=not can_analyze):
    # Вибрация при нажатии (через JS)
    st.markdown("""
    <script>
        if (typeof triggerHaptic === 'function') {
            triggerHaptic('medium');
        }
    </script>
    """, unsafe_allow_html=True)
    
    # Имитация анализа
    with st.spinner('Чтение документов...'):
        time.sleep(1.5)
        
        # Простая логика
        jur_name = "РФ" if st.session_state.jurisdiction == 'RU' else "РБ"
        file_count = len(st.session_state.files)
        
        result = f"✅ Проверено {file_count} файл(ов) по законодательству {jur_name}. Формат документов корректен."
    
    # Показать результат
    st.markdown(f'<div class="status-box status-success">{result}</div>', unsafe_allow_html=True)
    
    # Вибрация успеха
    st.markdown("""
    <script>
        if (typeof triggerHaptic === 'function') {
            triggerHaptic('success');
        }
    </script>
    """, unsafe_allow_html=True)

# Футер
st.markdown("---")
st.caption("umnyj-yurist • VK Mini App")
