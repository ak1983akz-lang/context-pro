import streamlit as st
import requests
import time
from PIL import Image
import io
import re
from datetime import datetime

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
if 'contract_type' not in st.session_state:
    st.session_state.contract_type = "Другое"
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
if 'risk_summary' not in st.session_state:
    st.session_state.risk_summary = None

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
# 📸 OCR (АВТОКОМПРЕССИЯ ДЛЯ МОБИЛЬНЫХ)
# =============================================================================
def extract_text_from_image(uploaded_file):
    try:
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        
        max_size = 5 * 1024 * 1024
        
        if len(file_bytes) > max_size:
            img = Image.open(io.BytesIO(file_bytes))
            
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            scale = min(1.0, 1920 / max(img.width, img.height))
            if scale < 1.0:
                img = img.resize((int(img.width*scale), int(img.height*scale)), Image.Resampling.LANCZOS)
            
            img_byte_arr = io.BytesIO()
            quality = 80
            while quality >= 20:
                img.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
                if len(img_byte_arr.getvalue()) <= max_size:
                    break
                quality -= 10
            img_byte_arr.seek(0)
            
            file_bytes = img_byte_arr.getvalue()
        
        processed_file = io.BytesIO(file_bytes)
        processed_file.name = uploaded_file.name
        processed_file.type = uploaded_file.type or 'image/jpeg'
        
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={'file': (processed_file.name, processed_file, processed_file.type)},
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
        
        return None, "Ошибка распознавания"
        
    except Exception as e:
        return None, "Ошибка обработки фото"

# =============================================================================
# 🔄 СБРОС
# =============================================================================
def reset_session():
    st.session_state.contract_txt = ""
    st.session_state.question_txt = ""
    st.session_state.result = ""
    st.session_state.risk_summary = None
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
        return None, "Ошибка сервиса"
    except Exception as e:
        return None, "Ошибка соединения"

# =============================================================================
# 📊 ИЗВЛЕЧЕНИЕ КРАТКИХ ИТОГОВ
# =============================================================================
def extract_risk_summary(full_result: str, contract_type: str) -> dict:
    return {
        "critical": full_result.count("🔴"),
        "medium": full_result.count("🟡"),
        "low": full_result.count("🟢"),
        "verdict": "Требует правок" if "требует" in full_result.lower() else "Нормально"
    }

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
[data-testid="stFileUploaderDropzoneInstructions"] { display: none; }
[data-testid="stFileUploaderInput"] { display: none; }
.stFileUploaderDropzone { border: 2px dashed #333; padding: 20px; border-radius: 12px; margin-top: 10px; cursor: pointer; }

/* Карта рисков */
.risk-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 15px;
    margin: 20px 0;
}
.risk-card {
    background: #1e2329;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    border: 2px solid;
}
.risk-card.critical { border-color: #ef4444; }
.risk-card.medium { border-color: #f59e0b; }
.risk-card.low { border-color: #22c55e; }
.risk-card.verdict { border-color: #3b82f6; background: #1e3a5f; }
.risk-number { font-size: 2.5rem; font-weight: bold; display: block; }
.risk-label { font-size: 0.9rem; opacity: 0.8; }

@media (max-width: 768px) {
    .block-container { padding-top: max(1rem, env(safe-area-inset-top)) !important; }
    h1 { font-size: 1.3rem !important; }
    .risk-cards { grid-template-columns: 1fr 1fr; }
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 🏗 ИНТЕРФЕЙС
# =============================================================================

# ШАПКА
col_h1, col_h2, col_h3 = st.columns([3, 1, 1])
with col_h1:
    st.title("⚖️ Context.Pro")
    st.caption("Анализ договоров")
with col_h2:
    if st.button("Правила", use_container_width=True, key="btn_rules"):
        st.session_state.show_rules = not st.session_state.show_rules
with col_h3:
    if st.button("Обновить", use_container_width=True, key="btn_reset"):
        reset_session()
        st.success("✅ Готово")
        st.rerun()

# ПРАВИЛА ПОЛЬЗОВАНИЯ
if st.session_state.show_rules:
    st.markdown("### Правила пользования сервисом")
    
    with st.expander("1. Как пользоваться", expanded=True):
        st.markdown("""
        **1.1.** Выберите юрисдикцию (Россия или Беларусь) — это влияет на применяемые законы
        
        **1.2.** Выберите тип договора для более точного анализа
        
        **1.3.** **Загрузите фото из галереи телефона** (не камера напрямую)
        
        **1.4.** Нажмите «Распознать» и дождитесь результата (10-30 секунд)
        
        **1.5.** Проверьте распознанный текст и нажмите «Анализировать»
        """)
    
    st.warning("**Важно:** Сервис не заменяет консультацию юриста.")
    
    st.info("**Поддержка:** Используйте кнопку «Обновить» при проблемах.")
    
    st.divider()

# НАСТРОЙКИ: ЮРИСДИКЦИЯ + ТИП ДОГОВОРА
col_jur, col_type = st.columns(2)

with col_jur:
    st.markdown("**Юрисдикция:**")
    jur_option = st.selectbox(
        "Законодательство:",
        options=["🇷🇺 Россия", "🇧🇾 Беларусь"],
        index=0,
        key="jur_select",
        label_visibility="collapsed"
    )
    st.session_state.jurisdiction = "🇷🇺 РФ" if "Россия" in jur_option else "🇧🇾 РБ"

with col_type:
    st.markdown("**Тип договора:**")
    contract_type = st.selectbox(
        "Выберите тип:",
        options=[
            "Договор аренды",
            "Договор купли-продажи",
            "Договор услуг",
            "Договор подряда",
            "Трудовой договор",
            "Договор поставки",
            "Договор займа",
            "Другое"
        ],
        index=7,
        key="contract_type_select",
        label_visibility="collapsed"
    )
    st.session_state.contract_type = contract_type

st.divider()

# ВКЛАДКИ
tab_photo, tab_manual, tab_q = st.tabs(["Фото", "Текст", "Вопрос"])

# === ВКЛАДКА 1: ФОТО (ОЧИЩЕННЫЙ ИНТЕРФЕЙС) ===
with tab_photo:
    st.markdown("#### 📄 Загрузка фото документа")
    
    st.markdown("💡 **Как загрузить фото:**\nОткройте **Галерею** → выберите фото → нажмите загрузить")
    
    current_files = st.file_uploader(
        "Выберите фото из галереи",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key=f"up_{st.session_state.ocr_counter}",
        label_visibility="hidden",
        help="Выбирайте фото из галереи телефона"
    )
    
    if current_files:
        if isinstance(current_files, list):
            files_to_process = current_files
        else:
            files_to_process = [current_files]
        
        for f in files_to_process:
            if not any(x.name == f.name and x.size == f.size for x in st.session_state.uploaded_files_list):
                st.session_state.uploaded_files_list.append(f)
        
        st.success(f"✅ Файлов: {len(st.session_state.uploaded_files_list)}")
        
        for i, f in enumerate(st.session_state.uploaded_files_list):
            size_kb = round(f.size / 1024, 1)
            st.markdown(f"<div class='file-info'>Стр. {i+1}: {f.name} ({size_kb} КБ)</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Очистить всё", key="clear_q"):
                st.session_state.uploaded_files_list = []
                st.rerun()
        with c2:
            if st.button("🔍 Распознать", type="primary", key="btn_ocr_go"):
                progress_bar = st.progress(0)
                status = st.empty()
                all_text = ""
                
                st.markdown('<div class="loading-box">Распознавание текста...</div>', unsafe_allow_html=True)
                
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
                        st.warning(f"Стр. {idx+1}: ошибка")
                
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
        st.markdown("### Текст документа")
        
        txt = st.text_area(
            "Текст:", 
            value=st.session_state.contract_txt, 
            height=400, 
            key=f"area_{st.session_state.ocr_counter}",
            label_visibility="collapsed"
        )
        st.session_state.contract_txt = txt
        
        if st.button("Анализировать", type="primary", disabled=len(txt)<50):
            st.session_state.is_analyzing = True
            st.session_state.last_mode = "contract"
            st.markdown('<div class="loading-box">Анализ договора...</div>', unsafe_allow_html=True)
            
            jur_base = "РФ" if "РФ" in st.session_state.jurisdiction else "РБ"
            prompt = f"""Юрист-эксперт по праву {jur_base}. Тип договора: {st.session_state.contract_type}.
Проанализируй договор и укажи:
1. Ключевые риски с уровнем опасности (🔴 Критический / 🟡 Средний / 🟢 Низкий)
2. Что составлено грамотно
3. Рекомендации по изменению пунктов
4. Итоговый вердикт (Безопасно / Требует правок / Опасно)

Используй эмодзи 🔴🟡🟢 для маркировки рисков."""
            
            res, err = query_ai(prompt, txt)
            
            st.session_state.is_analyzing = False
            if err: st.error(err)
            else:
                st.session_state.result = res
                st.session_state.risk_summary = extract_risk_summary(res, st.session_state.contract_type)
                st.success("✅ Готово!")
                st.rerun()
        
        # КАРТА РИСКОВ
        if st.session_state.result and st.session_state.risk_summary:
            st.divider()
            st.markdown("### Карта рисков")
            
            summary = st.session_state.risk_summary
            
            st.markdown(f"""
            <div class="risk-cards">
                <div class="risk-card critical">
                    <span class="risk-number" style="color: #ef4444;">{summary['critical']}</span>
                    <span class="risk-label">Критических</span>
                </div>
                <div class="risk-card medium">
                    <span class="risk-number" style="color: #f59e0b;">{summary['medium']}</span>
                    <span class="risk-label">Средних</span>
                </div>
                <div class="risk-card low">
                    <span class="risk-number" style="color: #22c55e;">{summary['low']}</span>
                    <span class="risk-label">В норме</span>
                </div>
                <div class="risk-card verdict">
                    <span class="risk-number" style="color: #3b82f6; font-size: 1.2rem;">{summary['verdict']}</span>
                    <span class="risk-label">Вердикт</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            st.markdown("### Полный анализ")
            st.markdown(st.session_state.result)
            st.download_button("Скачать отчёт", st.session_state.result, "report.txt")
    
    elif st.session_state.result and st.session_state.last_mode == "contract":
        if st.session_state.risk_summary:
            st.divider()
            st.markdown("### Карта рисков")
            summary = st.session_state.risk_summary
            st.markdown(f"""
            <div class="risk-cards">
                <div class="risk-card critical">
                    <span class="risk-number" style="color: #ef4444;">{summary['critical']}</span>
                    <span class="risk-label">Критических</span>
                </div>
                <div class="risk-card medium">
                    <span class="risk-number" style="color: #f59e0b;">{summary['medium']}</span>
                    <span class="risk-label">Средних</span>
                </div>
                <div class="risk-card low">
                    <span class="risk-number" style="color: #22c55e;">{summary['low']}</span>
                    <span class="risk-label">В норме</span>
                </div>
                <div class="risk-card verdict">
                    <span class="risk-number" style="color: #3b82f6; font-size: 1.2rem;">{summary['verdict']}</span>
                    <span class="risk-label">Вердикт</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.divider()
            st.markdown(st.session_state.result)

# === ВКЛАДКА 2: РУЧНОЙ ВВОД ===
with tab_manual:
    st.markdown("#### Вставьте текст")
    txt = st.text_area("Текст:", value=st.session_state.contract_txt, height=400, key="man_area", label_visibility="collapsed")
    st.session_state.contract_txt = txt
    if st.button("Анализ", disabled=len(txt)<50):
        st.session_state.last_mode = "contract"
        st.markdown('<div class="loading-box">Анализ...</div>', unsafe_allow_html=True)
        jur_base = "РФ" if "РФ" in st.session_state.jurisdiction else "РБ"
        prompt = f"""Юрист-эксперт по праву {jur_base}. Тип договора: {st.session_state.contract_type}.
Проанализируй договор:
1. Риски (🔴/🟡/🟢)
2. Плюсы
3. Рекомендации
4. Итог"""
        res, err = query_ai(prompt, txt)
        if not err:
            st.session_state.result = res
            st.session_state.risk_summary = extract_risk_summary(res, st.session_state.contract_type)
            st.rerun()
    if st.session_state.result and st.session_state.last_mode == "contract":
        if st.session_state.risk_summary:
            st.divider()
            st.markdown("### Карта рисков")
            summary = st.session_state.risk_summary
            st.markdown(f"""
            <div class="risk-cards">
                <div class="risk-card critical">
                    <span class="risk-number" style="color: #ef4444;">{summary['critical']}</span>
                    <span class="risk-label">Критических</span>
                </div>
                <div class="risk-card medium">
                    <span class="risk-number" style="color: #f59e0b;">{summary['medium']}</span>
                    <span class="risk-label">Средних</span>
                </div>
                <div class="risk-card low">
                    <span class="risk-number" style="color: #22c55e;">{summary['low']}</span>
                    <span class="risk-label">В норме</span>
                </div>
                <div class="risk-card verdict">
                    <span class="risk-number" style="color: #3b82f6; font-size: 1.2rem;">{summary['verdict']}</span>
                    <span class="risk-label">Вердикт</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.divider()
        st.markdown(st.session_state.result)

# === ВКЛАДКА 3: ВОПРОС ===
with tab_q:
    st.markdown("#### Юридический вопрос")
    q = st.text_area("Вопрос:", value=st.session_state.question_txt, height=200, key="q_ar", label_visibility="collapsed")
    st.session_state.question_txt = q
    if st.button("Получить ответ", disabled=len(q)<5):
        st.markdown('<div class="loading-box">Обработка...</div>', unsafe_allow_html=True)
        jur_base = "РФ" if "РФ" in st.session_state.jurisdiction else "РБ"
        res, err = query_ai(f"Юрист ({jur_base}). Дай ответ со статьями законов.", q)
        if not err:
            st.divider()
            st.markdown("### Ответ")
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
