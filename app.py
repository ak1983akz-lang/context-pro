import streamlit as st
import requests
import time
from PIL import Image
import io
import re

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
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
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
    st.session_state.jurisdiction = "🇷🇺 РФ"
if 'is_analyzing' not in st.session_state:
    st.session_state.is_analyzing = False
if 'last_mode' not in st.session_state:
    st.session_state.last_mode = None
if 'ocr_counter' not in st.session_state:
    st.session_state.ocr_counter = 0
if 'ocr_complete' not in st.session_state:
    st.session_state.ocr_complete = False
if 'show_rules' not in st.session_state:
    st.session_state.show_rules = False
if 'question_txt' not in st.session_state:
    st.session_state.question_txt = ""
if 'uploaded_files_list' not in st.session_state:
    st.session_state.uploaded_files_list = []
if 'page_texts' not in st.session_state:
    st.session_state.page_texts = {}

# =============================================================================
# 🔤 КОРРЕКЦИЯ ТЕКСТА
# =============================================================================
def correct_text_smart(raw_text: str, jurisdiction: str) -> str:
    api_key = None
    try:
        if "openrouter" in st.secrets:
            api_key = st.secrets["openrouter"]["api_key"]
    except:
        pass
    
    if not api_key or len(raw_text) < 50:
        return raw_text
    
    try:
        jur_base = "Российская Федерация" if "РФ" in jurisdiction else "Республика Беларусь"
        
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
                    {"role": "system", "content": f"Ты — редактор юридических документов ({jur_base}). Исправь опечатки и ошибки распознавания в тексте, не меняя смысл. Верни только исправленный текст."},
                    {"role": "user", "content": f"Исправь ошибки в тексте:\n\n{raw_text}"}
                ],
                "temperature": 0.1,
                "max_tokens": 3000
            },
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            corrected = data["choices"][0]["message"]["content"]
            if corrected and corrected.strip():
                return corrected.strip()
        
        return raw_text
    except:
        return raw_text

# =============================================================================
# 📸 OCR
# =============================================================================
def extract_text_from_image(uploaded_file):
    try:
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        
        if len(file_bytes) > 5 * 1024 * 1024:
            return None, "Файл больше 5MB"
        
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={'file': (uploaded_file.name, file_bytes, uploaded_file.type or 'image/jpeg')},
            data={
                'apikey': 'helloworld',
                'language': 'rus',
                'isOverlayRequired': 'false',
                'detectOrientation': 'true',
                'OCREngine': '2'
            },
            timeout=90
        )
        
        if response.status_code == 200:
            data = response.json()
            if not data.get('IsErroredOnProcessing'):
                text = data.get('ParsedResults', [{}])[0].get('ParsedText', '')
                if text and text.strip():
                    return text.strip(), None
        
        return None, f"Ошибка: {response.status_code}" if response.status_code != 200 else "Текст не распознан"
    except Exception as e:
        return None, f"Ошибка: {str(e)}"

# =============================================================================
# 🔄 СБРОС
# =============================================================================
def reset_session():
    st.session_state.contract_txt = ""
    st.session_state.question_txt = ""
    st.session_state.result = ""
    st.session_state.is_analyzing = False
    st.session_state.last_mode = None
    st.session_state.ocr_counter = 0
    st.session_state.ocr_complete = False
    st.session_state.show_rules = False
    st.session_state.uploaded_files_list = []
    st.session_state.page_texts = {}

# =============================================================================
# 🧠 АНАЛИЗ ДОГОВОРА
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
    background: #1f77b4; color: white; font-weight: bold; border-radius: 8px; height: 50px; font-size: 16px; width: 100%;
}
.stButton#btn_new_session { background: #dc2626 !important; }
.stButton#btn_rules { background: #2563eb !important; }
h1 { font-size: 1.5rem !important; }
.loading-box { background: #1a233a; border: 2px dashed #D4AF37; color: #D4AF37; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0; }
.success-box { background: #1a3a2a; border-left: 4px solid #22c55e; padding: 15px; margin: 15px 0; border-radius: 0 8px 8px 0; color: #4ade80; }
.file-info { background: #262730; padding: 12px; border-radius: 8px; margin: 8px 0; border: 1px solid #444; }

@media (max-width: 768px) {
    .block-container { padding-top: max(1rem, env(safe-area-inset-top)) !important; }
    h1 { font-size: 1.3rem !important; }
    .header-col { margin-bottom: 8px; }
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 🏗 ИНТЕРФЕЙС
# =============================================================================

# ШАПКА
col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
with col_h1:
    st.title("⚖️ Context.Pro")
    st.caption("Анализ договоров")
with col_h2:
    if st.button("📋 Правила", use_container_width=True, key="btn_rules"):
        st.session_state.show_rules = not st.session_state.show_rules
with col_h3:
    if st.button("🔄 Обновить", use_container_width=True, key="btn_reset"):
        reset_session()
        st.success("✅ Сессия обновлена")
        st.rerun()

# ПРАВИЛА ПОЛЬЗОВАНИЯ (через нативные компоненты Streamlit)
if st.session_state.show_rules:
    st.markdown("### 📜 Правила пользования сервисом")
    
    with st.expander("1️⃣ Назначение сервиса", expanded=True):
        st.markdown("""
        **1.1.** Сервис предназначен для анализа юридических документов (договоров, контрактов, соглашений)
        
        **1.2.** Пользователь может загрузить фото документа или вставить текст вручную
        
        **1.3.** Сервис предоставляет рекомендации на основе законодательства РФ или РБ
        """)
    
    with st.expander("2️⃣ Как пользоваться", expanded=True):
        st.markdown("""
        **2.1.** Выберите юрисдикцию (Россия или Беларусь) — это влияет на применяемые законы
        
        **2.2.** Перейдите во вкладку «📸 Фото» и загрузите изображение документа
        
        **2.3.** Дождитесь распознавания текста (10-30 секунд)
        
        **2.4.** Проверьте распознанный текст и при необходимости отредактируйте
        
        **2.5.** Нажмите «🚀 Анализировать» для получения результатов
        """)
    
    with st.expander("3️⃣ Требования к фото документа", expanded=False):
        st.markdown("""
        **3.1.** Фото должно быть чётким, без размытия
        
        **3.2.** Текст должен быть хорошо освещён, без теней и бликов
        
        **3.3.** Документ должен быть расположен ровно, без перекосов
        
        **3.4.** Поддерживаемые форматы: JPG, JPEG, PNG
        
        **3.5.** Максимальный размер файла: 5 MB
        """)
    
    with st.expander("4️⃣ Конфиденциальность", expanded=False):
        st.markdown("""
        **4.1.** Загруженные документы не сохраняются на сервере
        
        **4.2.** Данные удаляются после завершения сессии
        
        **4.3.** Сервис не передаёт данные третьим лицам
        
        **4.4.** Не загружайте документы с персональными данными (паспорт, ИНН и т.д.)
        """)
    
    with st.expander("5️⃣ Ограничения и отказ от ответственности", expanded=False):
        st.markdown("""
        **5.1.** Сервис предоставляет рекомендации информационного характера
        
        **5.2.** Результаты анализа не являются юридической консультацией
        
        **5.3.** Для важных решений обращайтесь к профессиональным юристам
        
        **5.4.** Сервис не несёт ответственности за решения, принятые на основе анализа
        """)
    
    st.warning("⚠️ **Важно:** Сервис не заменяет очную консультацию юриста. Для сложных случаев и важных сделок обращайтесь к специалистам.")
    
    st.info("ℹ️ **Поддержка:** При возникновении вопросов или технических проблем используйте кнопку «🔄 Обновить» для начала новой сессии.")
    
    st.divider()

# ЮРИСДИКЦИЯ С ФЛАГАМИ
st.markdown("**⚖️ Выберите юрисдикцию:**")

# Используем selectbox вместо radio для лучшей совместимости с эмодзи
jur_option = st.selectbox(
    "Законодательство:",
    options=["🇷🇺 Россия", "🇧🇾 Беларусь"],
    index=0,
    key="jur_select",
    label_visibility="collapsed"
)
st.session_state.jurisdiction = "🇷🇺 РФ" if "Россия" in jur_option else "🇧🇾 РБ"

st.divider()

# ВКЛАДКИ
tab_photo, tab_manual, tab_q = st.tabs(["📸 Фото", "✍️ Текст", "💬 Вопрос"])

# === ВКЛАДКА 1: ФОТО ===
with tab_photo:
    st.markdown("#### 📷 Загрузите фото документа")
    
    current_files = st.file_uploader(
        "Выберите фото",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key=f"up_{st.session_state.ocr_counter}",
        label_visibility="collapsed"
    )
    
    if current_files:
        for f in current_files:
            if not any(x.name == f.name and x.size == f.size for x in st.session_state.uploaded_files_list):
                st.session_state.uploaded_files_list.append(f)
        
        st.success(f"✅ Загружено файлов: {len(st.session_state.uploaded_files_list)}")
        
        for i, f in enumerate(st.session_state.uploaded_files_list):
            st.markdown(f"<div class='file-info'>📄 Стр. {i+1}: {f.name}</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗑️ Очистить", key="clear_q"):
                st.session_state.uploaded_files_list = []
                st.rerun()
        with c2:
            if st.button("🔍 Распознать", type="primary", key="btn_ocr_go"):
                progress_bar = st.progress(0)
                status = st.empty()
                all_text = ""
                
                st.markdown('<div class="loading-box">🔄 Распознавание текста...</div>', unsafe_allow_html=True)
                
                total = len(st.session_state.uploaded_files_list)
                for idx, file in enumerate(st.session_state.uploaded_files_list):
                    status.text(f"Страница {idx+1}/{total}...")
                    file.seek(0)
                    
                    text, error = extract_text_from_image(file)
                    
                    if text:
                        header = f"\n\n--- СТРАНИЦА {idx+1} ---\n\n" if idx > 0 else ""
                        all_text += header + text
                        st.session_state.page_texts[idx] = text
                        progress_bar.progress(int((idx+1)/total * 100))
                    else:
                        st.warning(f"Стр. {idx+1}: {error}")
                
                if all_text.strip():
                    status.text("Обработка текста...")
                    corrected = correct_text_smart(all_text, st.session_state.jurisdiction)
                    
                    st.session_state.contract_txt = corrected
                    st.session_state.ocr_complete = True
                    st.session_state.ocr_counter += 1
                    st.success(f"✅ Готово! ({len(corrected)} символов)")
                    st.rerun()
                
                status.empty()
                progress_bar.empty()
    
    st.divider()
    
    if st.session_state.ocr_complete and st.session_state.contract_txt:
        st.markdown("### 📝 Текст документа")
        
        txt = st.text_area(
            "Текст:", 
            value=st.session_state.contract_txt, 
            height=400, 
            key=f"area_{st.session_state.ocr_counter}",
            label_visibility="collapsed"
        )
        st.session_state.contract_txt = txt
        
        if st.button("🚀 Анализировать", type="primary", disabled=len(txt)<50):
            st.session_state.is_analyzing = True
            st.session_state.last_mode = "contract"
            st.markdown('<div class="loading-box">⚖️ Анализ договора...</div>', unsafe_allow_html=True)
            
            jur_base = "РФ" if "РФ" in st.session_state.jurisdiction else "РБ"
            prompt = f"""Юрист-эксперт по праву {jur_base}.
Проанализируй договор:
1. 🔍 Ключевые риски (🔴//🟢)
2. ✅ Что составлено грамотно
3. 📝 Рекомендации по изменению
4. ⚖️ Итог: Безопасно/Требует правок/Опасно"""
            
            res, err = query_ai(prompt, txt)
            
            st.session_state.is_analyzing = False
            if err: st.error(err)
            else:
                st.session_state.result = res
                st.success("✅ Готово!")
                st.rerun()
        
        if st.session_state.result:
            st.divider()
            st.markdown("### 📊 Результаты анализа")
            st.markdown(st.session_state.result)
            st.download_button("📥 Скачать", st.session_state.result, "report.txt")
    else:
        st.text_area("Ожидание...", value="", disabled=True, height=200)

# === ВКЛАДКА 2: РУЧНОЙ ВВОД ===
with tab_manual:
    st.markdown("#### ✍️ Вставьте текст")
    txt = st.text_area("Текст:", value=st.session_state.contract_txt, height=400, key="man_area", label_visibility="collapsed")
    st.session_state.contract_txt = txt
    if st.button("🚀 Анализ", disabled=len(txt)<50):
        st.session_state.last_mode = "contract"
        st.markdown('<div class="loading-box">⚖️ Анализ...</div>', unsafe_allow_html=True)
        jur_base = "РФ" if "РФ" in st.session_state.jurisdiction else "РБ"
        res, err = query_ai(f"Юрист ({jur_base}). Анализ договора.", txt)
        if not err:
            st.session_state.result = res
            st.rerun()
    if st.session_state.result and st.session_state.last_mode == "contract":
        st.divider()
        st.markdown(st.session_state.result)

# === ВКЛАДКА 3: ВОПРОС ===
with tab_q:
    st.markdown("#### 💬 Юридический вопрос")
    q = st.text_area("Вопрос:", value=st.session_state.question_txt, height=200, key="q_ar", label_visibility="collapsed")
    st.session_state.question_txt = q
    if st.button("⚡ Получить ответ", disabled=len(q)<5):
        st.markdown('<div class="loading-box">⏳ Обработка...</div>', unsafe_allow_html=True)
        jur_base = "РФ" if "РФ" in st.session_state.jurisdiction else "РБ"
        res, err = query_ai(f"Юрист ({jur_base}). Дай ответ со статьями законов.", q)
        if not err:
            st.divider()
            st.markdown("### 💡 Ответ")
            st.markdown(res)

# FOOTER
st.divider()
st.markdown("""
<div style="text-align: center; color: #555; font-size: 0.75rem; padding: 20px;">
⚖️ <b>Context.Pro Legal</b><br>
Конфиденциально • Без сохранения данных<br>
Не является публичной офертой
</div>
""", unsafe_allow_html=True)
