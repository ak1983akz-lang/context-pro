import streamlit as st
import requests
import re
import os
import time
import base64
from PIL import Image

# =============================================================================
# 📱 PWA MANIFEST
# =============================================================================
pwa_manifest = """
<link rel="manifest" href="application/manifest+json,{
    &quot;name&quot;: &quot;Context.Pro Legal&quot;,
    &quot;short_name&quot;: &quot;ContextPro&quot;,
    &quot;description&quot;: &quot;AI-анализ договоров РФ и РБ с OCR&quot;,
    &quot;start_url&quot;: &quot;/&quot;,
    &quot;display&quot;: &quot;standalone&quot;,
    &quot;background_color&quot;: &quot;#0e1117&quot;,
    &quot;theme_color&quot;: &quot;#1f77b4&quot;,
    &quot;orientation&quot;: &quot;portrait&quot;,
    &quot;icons&quot;: [{
        &quot;src&quot;: &quot;https://cdn-icons-png.flaticon.com/512/3094/3094427.png&quot;,
        &quot;sizes&quot;: &quot;512x512&quot;,
        &quot;type&quot;: &quot;image/png&quot;
    }]
}">
<meta name="theme-color" content="#1f77b4">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Context.Pro">
<link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/3094/3094427.png">
"""
st.markdown(pwa_manifest, unsafe_allow_html=True)

# =============================================================================
# SESSION STATE INIT
# =============================================================================
defaults = {
    'contract_txt': "",
    'question_txt': "",
    'result': "",
    'is_analyzing': False,
    'is_processing_ocr': False,
    'last_mode': None,
    'jurisdiction': "🇷🇺 РФ",
    'history': [],
    'show_rules': False,
    'uploaded_image': None,
    'ocr_api_key': 'helloworld'  # API ключ по умолчанию
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# =============================================================================
# 📸 OCR ФУНКЦИЯ №1 (через OCR.space API - Method 1: file upload)
# =============================================================================
def extract_text_ocr_space_v1(uploaded_file, api_key='helloworld'):
    """Метод 1: Прямая загрузка файла"""
    try:
        uploaded_file.seek(0)
        
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={'file': uploaded_file},
            data={
                'apikey': api_key,
                'language': 'rus',
                'isOverlayRequired': 'false',
                'detectOrientation': 'true',
                'isTable': 'true',
                'scale': 'true',
                'OCREngine': '2'
            },
            timeout=60
        )
        
        if response.status_code != 200:
            return None, f"HTTP {response.status_code}"
        
        data = response.json()
        
        if data.get('IsErroredOnProcessing'):
            error_msg = data.get('ErrorMessage', ['Unknown error'])
            return None, error_msg[0] if isinstance(error_msg, list) else error_msg
        
        text = data.get('ParsedResults', [{}])[0].get('ParsedText', '')
        return text.strip() if text.strip() else None, None
        
    except Exception as e:
        return None, str(e)

# =============================================================================
# 📸 OCR ФУНКЦИЯ №2 (через OCR.space API - Method 2: base64)
# =============================================================================
def extract_text_ocr_space_v2(uploaded_file, api_key='helloworld'):
    """Метод 2: Base64 encoding (более надёжный)"""
    try:
        uploaded_file.seek(0)
        image_bytes = uploaded_file.read()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        payload = {
            "apikey": api_key,
            "language": "rus",
            "isOverlayRequired": "false",
            "detectOrientation": "true",
            "isTable": "true",
            "scale": "true",
            "OCREngine": "2",
            "base64Image": f"data:image/jpeg;base64,{base64_image}"
        }
        
        response = requests.post(
            'https://api.ocr.space/parse/image',
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            return None, f"HTTP {response.status_code}"
        
        data = response.json()
        
        if data.get('IsErroredOnProcessing'):
            error_msg = data.get('ErrorMessage', ['Unknown error'])
            return None, error_msg[0] if isinstance(error_msg, list) else error_msg
        
        text = data.get('ParsedResults', [{}])[0].get('ParsedText', '')
        return text.strip() if text.strip() else None, None
        
    except Exception as e:
        return None, str(e)

# =============================================================================
# 📸 OCR ФУНКЦИЯ №3 (резервный метод)
# =============================================================================
def extract_text_manual_hint(uploaded_file):
    """Показываем фото и просим пользователя скопировать текст"""
    try:
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
        
        st.markdown("""
        <div style="background: #fff3cd; border: 2px solid #ffc107; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <strong>⚠️ Автоматическое распознавание не сработало</strong><br><br>
        <strong>Быстрое решение:</strong><br>
        1. Откройте это фото на телефоне<br>
        2. <strong>iPhone:</strong> зажмите текст → «Копировать текст» (Live Text)<br>
        3. <strong>Android:</strong> Google Lens → «Текст» → «Копировать»<br>
        4. Вставьте в поле ниже
        </div>
        """, unsafe_allow_html=True)
        
        st.image(image, caption="📷 Ваше фото", use_container_width=True)
        
        return None, "manual"
        
    except Exception as e:
        return None, str(e)

# =============================================================================
# 🔒 ВАЛИДАЦИЯ
# =============================================================================
def validate_input(text: str, mode: str):
    text = text.strip()
    if not text:
        return False, "⚠️ Поле не может быть пустым"
    if len(text) < 10:
        return False, "⚠️ Слишком короткий текст"
    
    if mode == "contract":
        if len(text) < 50:
            return False, "📋 Для анализа договора нужно минимум 50 символов"
        legal_markers = ["договор", "контракт", "сторона", "обязательство", "статья", "ГК", "ФЗ", "пункт", "соглашение", "аренда", "поставка", "услуга", "оплата"]
        if not any(marker in text.lower() for marker in legal_markers):
            return True, "⚠️ Внимание: Текст может не быть договором, но мы попробуем проанализировать." 
    return True, ""

# =============================================================================
# 🧠 ПРОМПТЫ
# =============================================================================
def build_system_prompt(jur: str, mode: str) -> str:
    jur_base = "Российская Федерация (ГК РФ, ФЗ, практика ВС РФ)" if "РФ" in jur else "Республика Беларусь (ГК РБ, Декреты, практика ВС РБ)"
    
    base_rules = "Ты — профессиональный ИИ-помощник юриста Context.Pro Legal. Отвечай строго, по делу, без воды. Используй маркированные списки."
    
    if mode == "contract":
        return f"""{base_rules}
Юрисдикция: {jur_base}.
ЗАДАЧА: Проанализируй текст договора.
СТРУКТУРА ОТВЕТА:
1. ### 🔍 Ключевые риски (с указанием статей закона и уровня опасности 🔴//🟢)
2. ### ✅ Что составлено грамотно
3. ### 📝 Рекомендации по изменению пунктов
4. ### ⚖️ Итоговый вердикт (Безопасно / Требует правок / Опасно)
Если текст не похож на договор, сразу напиши об этом."""
    else:
        return f"""{base_rules}
Юрисдикция: {jur_base}.
ЗАДАЧА: Дать юридическую консультацию.
СТРУКТУРА ОТВЕТА:
1. 📌 **Суть вопроса** (кратко)
2. ⚖️ **Нормативная база** (конкретные статьи ГК, ФЗ, кодексов)
3. 🔄 **Практическое решение** (пошаговый алгоритм действий)
4. ⚠️ **Подводные камни** (нюансы судебной практики)
В конце добавь дисклеймер: 'Ответ носит информационный характер'."""

# =============================================================================
# 🔑 API KEY & REQUEST
# =============================================================================
def get_api_key():
    try:
        if "openrouter" in st.secrets and "api_key" in st.secrets["openrouter"]:
            return st.secrets["openrouter"]["api_key"]
    except:
        pass
    return os.getenv("OPENROUTER_API_KEY")

def query_ai(system_prompt: str, user_text: str):
    api_key = get_api_key()
    if not api_key:
        return None, "❌ Ошибка конфигурации: Не найден API ключ."
    
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
                "max_tokens": 2000, 
                "top_p": 0.9
            },
            timeout=90
        )
        if response.status_code != 200:
            return None, f"❌ Ошибка сервиса ({response.status_code})"
        
        data = response.json()
        if "choices" not in data or not data["choices"]:
            return None, "❌ Пустой ответ от нейросети"
            
        return data["choices"][0]["message"]["content"], None
    except requests.exceptions.Timeout:
        return None, "⏱ Превышено время ожидания. Попробуйте сократить текст."
    except Exception as e:
        return None, f"❌ Ошибка соединения: {type(e).__name__}"

# =============================================================================
# 🎨 UI — CSS & STYLING
# =============================================================================
st.markdown("""
<style>
.stApp { background: #0e1117; color: #fafafa; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
.stTextArea textarea { background: #1e2329; color: #fff; border: 1px solid #333; font-size: 16px !important; }
.stButton>button { 
    background: linear-gradient(90deg, #1f77b4, #2c8ad6); 
    color: white; font-weight: bold; 
    border: none; border-radius: 8px; 
    height: 50px; font-size: 16px; 
    transition: all 0.3s;
}
.stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(31, 119, 180, 0.4); }
.stButton>button:disabled { background: #444; color: #888; transform: none; }
h1 { font-size: 1.8rem !important; color: #fff; margin-bottom: 0.5rem !important; }
h2, h3, h4 { color: #ddd; }
.rules-box {
    background: #161b22; border-left: 4px solid #1f77b4; padding: 15px; border-radius: 0 8px 8px 0; margin-bottom: 20px;
}
.rule-item { display: flex; align-items: start; margin-bottom: 10px; font-size: 0.95rem; }
.rule-icon { margin-right: 10px; min-width: 24px; }
@keyframes pulse-gold { 
    0%, 100% { opacity: 1; } 50% { opacity: 0.6; } 
}
.loading-box {
    background: #1a233a; border: 1px dashed #D4AF37; color: #D4AF37;
    padding: 20px; border-radius: 10px; text-align: center; font-weight: bold;
    animation: pulse-gold 1.5s infinite;
}
.ocr-success {
    background: #1a3a2a; border: 1px solid #2d7a4e; color: #4ade80;
    padding: 15px; border-radius: 8px; margin: 10px 0;
}
.ocr-error {
    background: #3a1a1a; border: 1px solid #7a2d2d; color: #f87171;
    padding: 15px; border-radius: 8px; margin: 10px 0;
}
@media (max-width: 768px) {
    .block-container { padding-top: 1rem !important; }
    h1 { font-size: 1.4rem !important; }
    .stButton>button { width: 100%; }
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 🏗 СТРУКТУРА ПРИЛОЖЕНИЯ
# =============================================================================

# 1. ШАПКА
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("⚖️ Context.Pro Legal")
    st.caption("📸 Фото → Текст → Анализ")
with col_h2:
    if st.button("❓ Правила", use_container_width=True, key="btn_rules_toggle"):
        st.session_state.show_rules = not st.session_state.show_rules

# 2. БЛОК ПРАВИЛ
if st.session_state.show_rules:
    st.markdown("""
    <div class="rules-box">
        <h3 style="margin-top:0;">📜 Как пользоваться</h3>
        <div class="rule-item"><span class="rule-icon">1️⃣</span><span>Выберите юрисдикцию (РФ или РБ)</span></div>
        <div class="rule-item"><span class="rule-icon">2️⃣</span><span>Сфотографируйте документ</span></div>
        <div class="rule-item"><span class="rule-icon">3️⃣</span><span>Загрузите фото и нажмите «Распознать»</span></div>
        <div class="rule-item"><span class="rule-icon">4️⃣</span><span>Проверьте текст и нажмите «Анализировать»</span></div>
    </div>
    """, unsafe_allow_html=True)

# 3. НАСТРОЙКИ
st.markdown("### ⚙️ Настройки анализа")
jur = st.radio(
    "Законодательство:",
    ["🇷🇺 РФ (Россия)", "🇧 РБ (Беларусь)"],
    horizontal=True,
    index=0,
    label_visibility="collapsed",
    key="jur_radio"
)
st.session_state.jurisdiction = "🇷🇺 РФ" if "РФ" in jur else "🇧🇾 РБ"
st.divider()

# 4. ВКЛАДКИ
tab_doc, tab_q = st.tabs(["📸 Фото документа", "💬 Юридический вопрос"])

# --- ВКЛАДКА 1: ФОТО ДОКУМЕНТА ---
with tab_doc:
    st.markdown("#### 📤 Загрузите фото документа")
    
    # Настройка API ключа (опционально)
    with st.expander("🔑 Настройки OCR API (если не работает)", expanded=False):
        st.markdown("Если распознавание не работает, получите бесплатный ключ на [ocr.space](https://ocr.space/ocrapi)")
        api_key_input = st.text_input("API Key:", value=st.session_state.ocr_api_key, key="api_key_input")
        if api_key_input:
            st.session_state.ocr_api_key = api_key_input
    
    uploaded_file = st.file_uploader(
        "📷 Загрузить фото (JPG, PNG)", 
        type=["jpg", "jpeg", "png"], 
        help="Сфотографируйте документ и загрузите фото.",
        key="file_uploader_ocr"
    )
    
    if uploaded_file is not None:
        col_preview1, col_preview2 = st.columns([1, 2])
        with col_preview1:
            st.image(uploaded_file, caption="📷 Загруженное фото", use_container_width=True)
        
        with col_preview2:
            if st.button("🔍 Распознать текст", use_container_width=True, type="primary", disabled=st.session_state.is_processing_ocr):
                st.session_state.is_processing_ocr = True
                st.session_state.uploaded_image = uploaded_file
                st.rerun()
        
        if st.session_state.is_processing_ocr and st.session_state.uploaded_image:
            st.markdown('<div class="loading-box">🔄 Распознавание текста...</div>', unsafe_allow_html=True)
            
            # Пробуем метод 1
            ocr_text, error = extract_text_ocr_space_v1(st.session_state.uploaded_image, st.session_state.ocr_api_key)
            
            # Если метод 1 не сработал, пробуем метод 2
            if not ocr_text and error:
                st.info(f"⚠️ Метод 1: {error}. Пробуем альтернативный метод...")
                ocr_text, error = extract_text_ocr_space_v2(st.session_state.uploaded_image, st.session_state.ocr_api_key)
            
            # Если оба метода не сработали
            if not ocr_text and error:
                st.markdown(f'<div class="ocr-error">❌ OCR не сработал: {error}</div>', unsafe_allow_html=True)
                st.info("💡 Попробуйте:")
                st.markdown("- Получить бесплатный API ключ на [ocr.space](https://ocr.space/ocrapi/freekey)")
                st.markdown("- Или используйте ручное копирование текста (см. ниже)")
                extract_text_manual_hint(st.session_state.uploaded_image)
            
            elif ocr_text:
                st.session_state.contract_txt = ocr_text
                st.session_state.is_processing_ocr = False
                st.session_state.uploaded_image = None
                st.markdown('<div class="ocr-success">✅ Текст распознан!</div>', unsafe_allow_html=True)
                st.rerun()
            
            st.session_state.is_processing_ocr = False
            st.session_state.uploaded_image = None
    
    contract_text = st.text_area(
        "📝 Текст договора:", 
        value=st.session_state.contract_txt, 
        height=300, 
        key="area_contract",
        placeholder="Загрузите фото → текст появится здесь..."
    )
    
    if contract_text != st.session_state.contract_txt:
        st.session_state.contract_txt = contract_text

    c1, c2 = st.columns([3, 1])
    with c1:
        analyze_btn = st.button("🚀 Анализировать", use_container_width=True, type="primary", disabled=st.session_state.is_analyzing or len(contract_text.strip()) < 10)
    with c2:
        if st.button("🗑️ Очистить", use_container_width=True):
            st.session_state.contract_txt = ""
            st.session_state.result = ""
            st.rerun()

    with st.expander("📸 Как сделать хорошее фото?"):
        st.markdown("""
        ✅ Хорошее освещение<br>
        ✅ Фото сверху, без бликов<br>
        ✅ Весь текст в кадре<br>
        ❌ Избегайте теней и размытия
        """, unsafe_allow_html=True)

    if analyze_btn:
        is_valid, msg = validate_input(contract_text, "contract")
        if not is_valid:
            st.error(msg)
        else:
            if "Внимание" in msg: st.warning(msg)
            else: st.info("✅ Текст принят")
            
            st.session_state.is_analyzing = True
            st.session_state.last_mode = "contract"
            
            progress_bar = st.progress(0)
            loader = st.markdown('<div class="loading-box">⚖️ Анализ договора...</div>', unsafe_allow_html=True)
            
            for i in range(10):
                time.sleep(0.1)
                progress_bar.progress((i + 1) * 10)
            
            sys_prompt = build_system_prompt(st.session_state.jurisdiction, "contract")
            result, error = query_ai(sys_prompt, contract_text)
            
            progress_bar.progress(100)
            loader.empty()
            st.session_state.is_analyzing = False
            
            if error:
                st.error(error)
            else:
                st.session_state.result = result
                st.session_state.history.insert(0, {"type": "Договор", "preview": contract_text[:50], "res": result})
                st.rerun()

    if st.session_state.last_mode == "contract" and st.session_state.result:
        st.markdown("### 📊 Результаты")
        st.markdown(st.session_state.result)
        st.download_button("📥 Скачать", st.session_state.result, "analysis.txt", use_container_width=True)

# --- ВКЛАДКА 2: ВОПРОС ---
with tab_q:
    st.markdown("#### 💬 Ваш вопрос")
    q = st.text_area("Опишите ситуацию:", value=st.session_state.question_txt, height=200, key="area_question")
    st.session_state.question_txt = q
    
    if st.button("⚡ Получить ответ", use_container_width=True, type="primary", disabled=st.session_state.is_analyzing or len(q.strip()) < 5):
        st.session_state.is_analyzing = True
        st.session_state.last_mode = "question"
        
        loader = st.markdown('<div class="loading-box">🧠 Готовлю ответ...</div>', unsafe_allow_html=True)
        sys_prompt = build_system_prompt(st.session_state.jurisdiction, "question")
        result, error = query_ai(sys_prompt, q)
        
        loader.empty()
        st.session_state.is_analyzing = False
        
        if error:
            st.error(error)
        else:
            st.session_state.result = result
            st.session_state.history.insert(0, {"type": "Вопрос", "preview": q[:50], "res": result})
            st.rerun()

    if st.session_state.last_mode == "question" and st.session_state.result:
        st.markdown("### 💡 Ответ")
        st.markdown(st.session_state.result)

# FOOTER
st.divider()
st.markdown("<div style='text-align: center; color: #555; font-size: 0.8rem;'>⚖️ Context.Pro Legal AI v3.3</div>", unsafe_allow_html=True)
