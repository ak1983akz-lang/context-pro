import streamlit as st
import requests
import re
import os
from PIL import Image

# =============================================================================
# SESSION STATE
# =============================================================================
for key in ['contract_txt', 'question_txt', 'result', 'is_analyzing', 'last_mode', 'jurisdiction']:
    if key not in st.session_state:
        st.session_state[key] = "" if key in ['contract_txt', 'question_txt', 'result', 'jurisdiction'] else False

# =============================================================================
# 📱 CSS — МОБИЛЬНАЯ АДАПТАЦИЯ
# =============================================================================
st.markdown("""
<style>
.stApp { background: #0e1117; color: #fafafa; }
.stTextArea textarea { background: #262730; color: #fafafa; font-size: 16px !important; }
.stButton>button { background: #1f77b4; color: white; font-size: 16px !important; padding: 12px 24px !important; min-height: 50px !important; }
h1 { font-size: 1.8rem !important; }
h2 { font-size: 1.4rem !important; }
h3 { font-size: 1.2rem !important; }

@keyframes empire-pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(0.98); }
}
.empire-loading {
    display: flex !important; align-items: center !important; justify-content: center !important;
    color: #D4AF37 !important; font-weight: 500 !important; font-size: 1rem !important;
    animation: empire-pulse 2s infinite ease-in-out !important;
    padding: 1.5rem !important; margin: 1rem 0 !important;
    background: #1a233a !important; border: 1px dashed #B8962E !important; border-radius: 8px !important;
}
.empire-loading::before { content: "⚖️"; margin-right: 0.75rem !important; font-size: 1.4rem !important; }

@media (max-width: 768px) {
    .main > div { padding: 0.5rem !important; }
    .block-container { padding: 0.5rem 1rem !important; }
    h1 { font-size: 1.5rem !important; }
    .stButton>button { font-size: 18px !important; padding: 15px 30px !important; min-height: 55px !important; border-radius: 10px !important; }
    .stTextArea textarea, .stTextInput input { font-size: 18px !important; padding: 12px !important; }
    .stRadio > div { flex-direction: column !important; }
    .stRadio label { width: 100% !important; padding: 10px !important; margin: 5px 0 !important; }
    .stColumns > div { width: 100% !important; margin-bottom: 10px !important; }
}
</style>
""", unsafe_allow_html=True)

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
# 📷 OCR — TESSERACT
# =============================================================================
def extract_text_from_image_tesseract(image_file):
    try:
        import pytesseract
        img = Image.open(image_file).convert('L')
        text = pytesseract.image_to_string(img, lang='rus+eng')
        text = text.strip()
        if len(text) < 10:
            return None, "⚠️ Текст не распознан. Сделайте фото чётче."
        return text, None
    except Exception as e:
        return None, f"❌ Tesseract: {str(e)}"

# =============================================================================
# 📷 OCR — OCR.SPACE API (АЛЬТЕРНАТИВА)
# =============================================================================
def extract_text_from_image_ocrspace(image_file):
    try:
        api_key = st.secrets.get("ocr_space_api_key", "helloworld")
        files = {'file': image_file.getvalue()}
        data = {'apikey': api_key, 'language': 'rus', 'isOverlayRequired': 'false', 'scale': 'true'}
        response = requests.post('https://apiv2.ocr.space/parse/image', files=files, data=data, timeout=30)
        result = response.json()
        if result.get('IsErroredOnProcessing'):
            return None, "❌ Ошибка OCR сервиса"
        text = result['ParsedResults'][0]['ParsedText'].strip()
        if len(text) < 10:
            return None, "⚠️ Текст не распознан"
        return text, None
    except Exception as e:
        return None, f"❌ OCR.Space: {str(e)}"

# =============================================================================
# 📷 OCR — ВЫБОР МЕТОДА
# =============================================================================
def extract_text_from_image(image_file):
    # Пробуем Tesseract сначала
    text, err = extract_text_from_image_tesseract(image_file)
    if text:
        return text, None
    # Если не сработало — пробуем OCR.Space
    return extract_text_from_image_ocrspace(image_file)

# =============================================================================
# 🧪 ТЕСТ TESSERACT
# =============================================================================
def test_tesseract():
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        return True, f"✅ Tesseract {version}"
    except Exception as e:
        return False, f"❌ {str(e)}"

# =============================================================================
# 🎨 UI — ШАПКА
# =============================================================================
st.title("⚖️ Context.Pro Legal")
st.caption("Анализ договоров • РФ/РБ")

# =============================================================================
# 🧪 КНОПКА ТЕСТА OCR
# =============================================================================
with st.expander("🧪 Тест OCR (нажмите для проверки)"):
    tesseract_ok, tesseract_msg = test_tesseract()
    if tesseract_ok:
        st.success(tesseract_msg)
    else:
        st.error(tesseract_msg)
        st.info("💡 Tesseract не работает — используется OCR.Space API")

# =============================================================================
# ⚖️ ЮРИСДИКЦИЯ
# =============================================================================
st.markdown("### ⚖️ Юрисдикция")
jur = st.radio(
    "Выберите законодательство:",
    ["🇷🇺 РФ", "🇧🇾 РБ"],
    horizontal=True,
    index=0,
    key="jurisdiction_radio",
    label_visibility="collapsed"
)
st.session_state.jurisdiction = jur
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
    st.caption("💡 Вставьте текст ИЛИ сфотографируйте")
    
    input_mode = st.radio(
        "Способ ввода:",
        ["✍️ Текст", "📷 Фото"],
        horizontal=True,
        key="contract_input_mode"
    )
    
    contract_text = ""
    
    if input_mode == "✍️ Текст":
        contract_text = st.text_area("Текст:", value=st.session_state.contract_txt, height=200, key="contract_text_input", placeholder="Скопируйте текст договора...")
    else:
        st.info("📱 Нажмите кнопку и сфотографируйте договор")
        img_file = st.camera_input("📸 Сделайте фото", key="contract_camera")
        if img_file:
            with st.spinner("🔍 Распознаю..."):
                extracted, error = extract_text_from_image(img_file)
                if error:
                    st.error(error)
                elif extracted:
                    contract_text = extracted
                    st.success(f"✅ Распознано {len(extracted)} симв.")
                    with st.expander("👁️ Текст"):
                        st.text(extracted[:300] + "..." if len(extracted) > 300 else extracted)
                    st.session_state.contract_txt = extracted
    
    if contract_text:
        st.session_state.contract_txt = contract_text
    
    analyze_btn = st.button("⚖️ Проверить договор", use_container_width=True, type="primary", key="btn_contract", disabled=st.session_state.is_analyzing or not (contract_text.strip() if contract_text else False))
    
    if st.button("🗑️ Очистить", key="clear_contract"):
        for k in ['contract_txt', 'result', 'last_mode']:
            st.session_state[k] = "" if k != 'last_mode' else None
        st.rerun()
    
    if analyze_btn and contract_text and contract_text.strip():
        is_valid, message = validate_input(contract_text, "contract")
        if not is_valid:
            st.warning(message)
        else:
            st.session_state.is_analyzing = True
            st.session_state.last_mode = "contract"
            st.markdown('<div class="empire-loading">Анализирую...</div>', unsafe_allow_html=True)
            sys_prompt = build_system_prompt(jur, "contract")
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
        st.markdown("### 🔍 Результаты")
        st.markdown(st.session_state.result)
        st.download_button("📥 Скачать", st.session_state.result, "analysis.txt", "text/plain", use_container_width=True, key="download_contract")

# =============================================================================
# ВКЛАДКА 2: ВОПРОС
# =============================================================================
with tab2:
    st.markdown("#### ⚖️ Ваш вопрос")
    st.caption("💡 Минимум 10 символов")
    
    q = st.text_area("Вопрос:", value=st.session_state.question_txt, height=200, key="question_input", placeholder="Например: Какие риски по ст. 651 ГК РФ?")
    st.session_state.question_txt = q
    
    ask_btn = st.button("⚡ Получить ответ", use_container_width=True, type="primary", key="btn_question", disabled=st.session_state.is_analyzing or not (q.strip() if q else False))
    
    if st.button("🗑️ Очистить", key="clear_question"):
        for k in ['question_txt', 'result', 'last_mode']:
            st.session_state[k] = "" if k != 'last_mode' else None
        st.rerun()
    
    if ask_btn and q and q.strip():
        is_valid, message = validate_input(q, "question")
        if not is_valid:
            st.warning(message)
        else:
            st.session_state.is_analyzing = True
            st.session_state.last_mode = "question"
            st.markdown('<div class="empire-loading">Готовлю ответ...</div>', unsafe_allow_html=True)
            sys_prompt = build_system_prompt(jur, "question")
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
        st.markdown("### 💬 Ответ")
        st.markdown(st.session_state.result)

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 15px; color: #718096; font-size: 0.85rem;">
    <p>⚖️ <strong>Context.Pro Legal</strong> | 🇷🇺 РФ • 🇧🇾 РБ</p>
    <p style="font-size: 0.75rem;">🔒 Приватно • Без логов</p>
</div>
""", unsafe_allow_html=True)
