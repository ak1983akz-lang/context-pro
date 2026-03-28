import streamlit as st
import requests
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
    &quot;start_url&quot;: &quot;/&quot;,
    &quot;display&quot;: &quot;standalone&quot;,
    &quot;background_color&quot;: &quot;#0e1117&quot;,
    &quot;theme_color&quot;: &quot;#1f77b4&quot;
}">
<meta name="theme-color" content="#1f77b4">
<meta name="apple-mobile-web-app-capable" content="yes">
"""
st.markdown(pwa_manifest, unsafe_allow_html=True)

# =============================================================================
# SESSION STATE
# =============================================================================
if 'contract_txt' not in st.session_state:
    st.session_state.contract_txt = ""
if 'result' not in st.session_state:
    st.session_state.result = ""
if 'jurisdiction' not in st.session_state:
    st.session_state.jurisdiction = "🇷 РФ"
if 'is_analyzing' not in st.session_state:
    st.session_state.is_analyzing = False
if 'last_mode' not in st.session_state:
    st.session_state.last_mode = None
if 'ocr_counter' not in st.session_state:
    st.session_state.ocr_counter = 0
if 'ocr_complete' not in st.session_state:
    st.session_state.ocr_complete = False
if 'show_rules' not in st.session_state:
    st.session_state.show_rules = False  # ← Для кнопки правил

# =============================================================================
# 📸 OCR ЧЕРЕЗ OCR.SPACE
# =============================================================================
def extract_text_from_image(uploaded_file):
    """Распознавание текста через OCR.space API"""
    try:
        uploaded_file.seek(0)
        api_key = 'helloworld'
        
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={'file': uploaded_file},
            data={
                'apikey': api_key,
                'language': 'rus',
                'isOverlayRequired': 'false',
                'detectOrientation': 'true',
                'OCREngine': '2'
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if not data.get('IsErroredOnProcessing'):
                text = data.get('ParsedResults', [{}])[0].get('ParsedText', '')
                if text.strip():
                    return text.strip(), None
        return None, "API_LIMIT"
    except Exception as e:
        return None, str(e)

# =============================================================================
# 🧠 AI ЗАПРОС
# =============================================================================
def get_api_key():
    try:
        if "openrouter" in st.secrets:
            return st.secrets["openrouter"]["api_key"]
    except:
        pass
    return None

def query_ai(system_prompt: str, user_text: str):
    api_key = get_api_key()
    if not api_key:
        return None, "❌ API ключ не настроен"
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://context-pro.streamlit.app"
            },
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                "temperature": 0.2,
                "max_tokens": 2000
            },
            timeout=90
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"], None
        return None, f"Ошибка {response.status_code}"
    except Exception as e:
        return None, str(e)

# =============================================================================
# 🎨 CSS
# =============================================================================
st.markdown("""
<style>
.stApp { background: #0e1117; color: #fafafa; }
.stTextArea textarea { background: #1e2329; color: #fff; font-size: 16px !important; }
.stButton>button { 
    background: #1f77b4; 
    color: white; 
    font-weight: bold; 
    border-radius: 8px; 
    height: 50px; 
    font-size: 16px;
}
h1 { font-size: 1.6rem !important; }
.loading-box {
    background: #1a233a; 
    border: 2px dashed #D4AF37; 
    color: #D4AF37;
    padding: 20px; 
    border-radius: 10px; 
    text-align: center;
    margin: 20px 0;
}
.ocr-warning {
    background: #1e3a5f; 
    border-left: 4px solid #3b82f6; 
    padding: 15px; 
    margin: 15px 0;
    border-radius: 0 8px 8px 0;
    color: #fff;
}
.manual-hint {
    background: #fff3cd; 
    border-left: 4px solid #ffc107; 
    padding: 15px; 
    margin: 15px 0;
    border-radius: 0 8px 8px 0;
    color: #000;
}
.rules-box {
    background: #161b22; 
    border-left: 4px solid #1f77b4; 
    padding: 15px; 
    border-radius: 0 8px 8px 0; 
    margin-bottom: 20px;
}
.rule-item { 
    display: flex; 
    align-items: start; 
    margin-bottom: 10px; 
    font-size: 0.95rem; 
}
.rule-icon { 
    margin-right: 10px; 
    min-width: 24px; 
}
@media (max-width: 768px) {
    .block-container { padding-top: 1rem !important; }
    h1 { font-size: 1.3rem !important; }
    .stButton>button { width: 100%; }
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 🏗 ИНТЕРФЕЙС
# =============================================================================

# 1. ШАПКА С КНОПКОЙ ПРАВИЛ
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.title("⚖️ Context.Pro Legal")
    st.caption("📸 Сфотографируй документ → Получи анализ")
with col_h2:
    # ✅ КНОПКА ПРАВИЛ ВОССТАНОВЛЕНА
    if st.button("❓ Правила", use_container_width=True, key="btn_rules_toggle"):
        st.session_state.show_rules = not st.session_state.show_rules

# 2. БЛОК ПРАВИЛ (показывается если нажали кнопку)
if st.session_state.show_rules:
    st.markdown("""
    <div class="rules-box">
        <h3 style="margin-top:0; color: #fff;">📜 Правила сервиса</h3>
        <div class="rule-item"><span class="rule-icon">1️⃣</span><span>Выберите юрисдикцию (РФ или РБ) — это важно для ссылок на законы</span></div>
        <div class="rule-item"><span class="rule-icon">2️⃣</span><span>Сфотографируйте документ камерой телефона</span></div>
        <div class="rule-item"><span class="rule-icon">3️⃣</span><span>Загрузите фото во вкладку «📸 Загрузить фото»</span></div>
        <div class="rule-item"><span class="rule-icon">4️⃣</span><span>Нажмите «🔍 Распознать текст» и подождите 10-30 секунд</span></div>
        <div class="rule-item"><span class="rule-icon">5️⃣</span><span>Проверьте текст и нажмите «🚀 Анализировать договор»</span></div>
        <div class="rule-item"><span class="rule-icon">🔒</span><span>Ваши данные не сохраняются после завершения сессии</span></div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# 3. ВЫБОР ЮРИСДИКЦИИ
st.markdown("### ⚖️ Юрисдикция")
jur = st.radio(
    "Выберите:",
    ["🇷🇺 РФ — Россия", "🇧 РБ — Беларусь"],
    horizontal=True,
    label_visibility="collapsed"
)
st.session_state.jurisdiction = "🇷🇺 РФ" if "РФ" in jur else "🇧🇾 РБ"
st.divider()

# 4. ВКЛАДКИ
tab_photo, tab_manual, tab_question = st.tabs(["📸 Загрузить фото", "✍️ Вставить текст", "💬 Вопрос"])

# === ВКЛАДКА 1: ФОТО ===
with tab_photo:
    st.markdown("#### 📷 Загрузите фото договора")
    st.info("💡 Сделайте фото документа камерой телефона, затем загрузите сюда")
    
    st.markdown("""
    <div class="ocr-warning">
    ⏱️ <strong>Важно:</strong> Распознавание текста занимает 10-30 секунд. 
    Пожалуйста, подождите — индикатор загрузки покажет процесс.
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Нажмите чтобы выбрать фото",
        type=["jpg", "jpeg", "png"],
        key=f"photo_upload_{st.session_state.ocr_counter}"
    )
    
    if uploaded_file:
        st.image(uploaded_file, caption="📷 Ваше фото", use_container_width=True)
        
        if st.button("🔍 Распознать текст", type="primary", use_container_width=True, key="btn_ocr"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            st.markdown('<div class="loading-box">🔄 Распознаю текст с фото...<br><small>Это займёт 10-30 секунд</small></div>', unsafe_allow_html=True)
            
            for i in range(10):
                time.sleep(0.3)
                progress_bar.progress((i + 1) * 10)
                if i < 3:
                    status_text.text("📡 Отправка фото на сервер...")
                elif i < 6:
                    status_text.text("🔍 Анализ изображения...")
                else:
                    status_text.text("✍️ Извлечение текста...")
            
            text, error = extract_text_from_image(uploaded_file)
            
            progress_bar.progress(100)
            status_text.empty()
            
            if text:
                st.session_state.contract_txt = text
                st.session_state.ocr_complete = True
                st.session_state.ocr_counter += 1
                st.success(f"✅ Текст распознан! ({len(text)} символов)")
                st.rerun()
            else:
                st.error("⚠️ Не удалось распознать текст")
                st.markdown("""
                <div class="manual-hint">
                <strong>📱 Быстрое решение:</strong><br>
                • <strong>iPhone:</strong> Откройте фото → зажмите текст → «Копировать»<br>
                • <strong>Android:</strong> Google Lens → «Текст» → «Копировать»<br>
                • Перейдите во вкладку «✍️ Вставить текст»
                </div>
                """, unsafe_allow_html=True)
    
    st.divider()
    
    if st.session_state.ocr_complete and st.session_state.contract_txt:
        st.markdown("### 📝 Распознанный текст")
        st.caption(f"✅ Загружено {len(st.session_state.contract_txt)} символов")
        
        contract_text = st.text_area(
            "Текст договора:",
            value=st.session_state.contract_txt,
            height=300,
            key=f"contract_area_{st.session_state.ocr_counter}"
        )
        
        if contract_text != st.session_state.contract_txt:
            st.session_state.contract_txt = contract_text
        
        if st.button("🚀 Анализировать договор", type="primary", use_container_width=True, 
                     disabled=len(contract_text.strip()) < 50, key="btn_analyze"):
            st.session_state.is_analyzing = True
            st.session_state.last_mode = "contract"
            
            st.markdown('<div class="loading-box">⚖️ Анализирую договор...</div>', unsafe_allow_html=True)
            
            jur_base = "РФ (ГК РФ, ФЗ)" if "РФ" in st.session_state.jurisdiction else "РБ (ГК РБ)"
            system_prompt = f"""Ты — юрист-эксперт по праву {jur_base}.
Проанализируй договор и укажи:
1. 🔍 Ключевые риски (🔴/🟡/🟢)
2. ✅ Что хорошо
3. 📝 Рекомендации
4. ⚖️ Итог: Безопасно/Требует правок/Опасно"""
            
            result, error = query_ai(system_prompt, contract_text)
            
            st.session_state.is_analyzing = False
            
            if error:
                st.error(error)
            else:
                st.session_state.result = result
                st.success("✅ Готово!")
                st.rerun()
        
        if st.session_state.last_mode == "contract" and st.session_state.result:
            st.divider()
            st.markdown("### 📊 Результаты анализа")
            st.markdown(st.session_state.result)
            
            st.download_button(
                "📥 Скачать отчёт",
                st.session_state.result,
                "analysis.txt",
                use_container_width=True,
                key="btn_download"
            )
    else:
        st.markdown("### 📝 Текстовое поле")
        st.caption("Текст появится здесь после распознавания фото")
        
        contract_text = st.text_area(
            "Текст договора:",
            value="",
            height=300,
            key=f"contract_area_empty_{st.session_state.ocr_counter}"
        )

# === ВКЛАДКА 2: РУЧНОЙ ВВОД ===
with tab_manual:
    st.markdown("#### ✍️ Вставьте текст договора")
    st.info("💡 Откройте фото на телефоне → выделите текст → Копировать → Вставить сюда")
    
    manual_text = st.text_area(
        "Текст:",
        value=st.session_state.contract_txt,
        height=300,
        key="manual_area"
    )
    st.session_state.contract_txt = manual_text
    
    if st.button("🚀 Анализировать", type="primary", use_container_width=True,
                 disabled=len(manual_text.strip()) < 50):
        st.session_state.is_analyzing = True
        st.session_state.last_mode = "contract"
        
        st.markdown('<div class="loading-box">⚖️ Анализирую...</div>', unsafe_allow_html=True)
        
        jur_base = "РФ (ГК РФ, ФЗ)" if "РФ" in st.session_state.jurisdiction else "РБ (ГК РБ)"
        system_prompt = f"""Ты — юрист по праву {jur_base}.
Проанализируй договор:
1. 🔍 Риски
2. ✅ Плюсы
3. 📝 Рекомендации
4. ⚖️ Итог"""
        
        result, error = query_ai(system_prompt, manual_text)
        st.session_state.is_analyzing = False
        
        if error:
            st.error(error)
        else:
            st.session_state.result = result
            st.success("✅ Готово!")
            st.rerun()
    
    if st.session_state.last_mode == "contract" and st.session_state.result:
        st.divider()
        st.markdown(st.session_state.result)

# === ВКЛАДКА 3: ВОПРОС ===
with tab_question:
    st.markdown("#### 💬 Задайте юридический вопрос")
    
    question = st.text_area(
        "Ваш вопрос:",
        height=200,
        key="question_area",
        placeholder="Например: Какие риски при расторжении договора аренды?"
    )
    
    if st.button("⚡ Получить ответ", type="primary", use_container_width=True,
                 disabled=len(question.strip()) < 10):
        st.markdown('<div class="loading-box">🧠 Готовлю ответ...</div>', unsafe_allow_html=True)
        
        jur_base = "РФ" if "РФ" in st.session_state.jurisdiction else "РБ"
        system_prompt = f"Ты — юрист по праву {jur_base}. Дай чёткий ответ со ссылками на статьи законов."
        
        result, error = query_ai(system_prompt, question)
        
        if not error:
            st.divider()
            st.markdown("### 💡 Ответ")
            st.markdown(result)

# FOOTER
st.divider()
st.markdown("""
<div style="text-align: center; color: #555; font-size: 0.75rem; padding: 20px;">
⚖️ Context.Pro Legal | Фото → Текст → Анализ<br>
Не заменяет консультацию юриста
</div>
""", unsafe_allow_html=True)
