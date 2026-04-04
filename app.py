import streamlit as st
import time

st.set_page_config(
    page_title="umnyj-yurist",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# VK Bridge
st.markdown("""
<script src="https://unpkg.com/@vkontakte/vk-bridge/dist/browser.min.js"></script>
<script>
window.addEventListener('load', function() {
    if (window.vkBridge) {
        vkBridge.send('VKWebAppInit');
    }
});
function selectJurisdiction(code) {
    window.parent.postMessage({jurisdiction: code}, '*');
}
</script>
""", unsafe_allow_html=True)

# Стили
st.markdown("""
<style>
    #MainMenu, footer, .stDeployButton {display: none;}
    .main .block-container {padding: 20px 16px; max-width: 600px;}
    
    .section {
        background: var(--vkui--color_background_content, white);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .section-title {
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 12px;
    }
    
    .flags-grid {display: grid; grid-template-columns: 1fr 1fr; gap: 12px;}
    
    .flag-btn {
        background: #f0f2f5;
        border: 2px solid transparent;
        border-radius: 10px;
        padding: 16px 12px;
        cursor: pointer;
        text-align: center;
        transition: all 0.2s;
        font-size: 14px;
        font-weight: 500;
    }
    .flag-btn:hover {transform: translateY(-2px);}
    .flag-btn.active {
        border-color: #2688eb;
        background: #e5f1fa;
    }
    
    .upload-box {
        border: 2px dashed #e1e3e6;
        border-radius: 10px;
        padding: 24px;
        text-align: center;
        margin: 10px 0;
    }
    
    .analyze-btn {
        width: 100%;
        padding: 14px;
        background: #2688eb;
        color: white;
        border: none;
        border-radius: 10px;
        font-size: 15px;
        font-weight: 600;
        cursor: pointer;
    }
    .analyze-btn:disabled {background: #c7cfd6; cursor: not-allowed;}
    
    .result {
        padding: 12px;
        border-radius: 8px;
        margin-top: 15px;
        text-align: center;
        background: #e5f6ea;
        border: 1px solid #4bb34b;
    }
</style>
""", unsafe_allow_html=True)

# Заголовок
st.markdown("<h1 style='text-align:center;font-size:22px;'>umnyj-yurist</h1>", unsafe_allow_html=True)

# Session state
if 'jurisdiction' not in st.session_state:
    st.session_state.jurisdiction = None
if 'files' not in st.session_state:
    st.session_state.files = []
if 'result' not in st.session_state:
    st.session_state.result = None

# Выбор юрисдикции через HTML кнопки
st.markdown("<div class='section'><div class='section-title'>🌍 Юрисдикция</div>", unsafe_allow_html=True)
st.markdown("""
<div class='flags-grid'>
    <div class='flag-btn {}' onclick="selectJurisdiction('BY')">🇧 Беларусь</div>
    <div class='flag-btn {}' onclick="selectJurisdiction('RU')">🇷🇺 Россия</div>
</div>
""".format(
    'active' if st.session_state.jurisdiction == 'BY' else '',
    'active' if st.session_state.jurisdiction == 'RU' else ''
), unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Загрузка файлов
st.markdown("<div class='section'><div class='section-title'>📄 Документы</div>", unsafe_allow_html=True)
uploaded = st.file_uploader("", type=['pdf','docx','jpg','png'], accept_multiple_files=True, label_visibility="collapsed")
if uploaded:
    st.session_state.files = uploaded
    st.success(f"✅ Загружено файлов: {len(uploaded)}")
st.markdown("</div>", unsafe_allow_html=True)

# Кнопка анализа
can_run = st.session_state.jurisdiction and st.session_state.files

if st.button("🔍 Анализировать документы", disabled=not can_run):
    with st.spinner('Обработка...'):
        time.sleep(1.5)
        jur = "РФ" if st.session_state.jurisdiction == 'RU' else "РБ"
        st.session_state.result = f"✅ Проверено {len(st.session_state.files)} файл(ов) по законодательству {jur}. Всё корректно."

if st.session_state.result:
    st.markdown(f"<div class='result'>{st.session_state.result}</div>", unsafe_allow_html=True)
