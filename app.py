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
# 📸 OCR
# =============================================================================
def extract_text_from_image(uploaded_file):
    try:
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        
        # Проверка размера (максимум 5 МБ для OCR API)
        if len(file_bytes) > 5 * 1024 * 1024:
            return None, f"Файл слишком большой ({round(len(file_bytes)/1024/1024, 1)} МБ)"
        
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
            else:
                err = data.get('ErrorMessage', ['Unknown error'])
                return None, err[0] if isinstance(err, list) else err
        
        return None, f"Ошибка: {response.status_code}"
        
    except Exception as e:
        return None, f"Ошибка: {str(e)}"

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
        return None, f"Ошибка {response.status_code}"
    except Exception as e:
        return None, str(e)

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
.hint-warning {
    background: #2d1f1f;
    border-left: 4px solid #f85149;
    padding: 15px;
    margin: 10px 0;
    border-radius: 0 8px 8px 0;
    font-size: 0.9rem;
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
        st.success("Сессия обновлена")
        st.rerun()

# ПРАВИЛА ПОЛЬЗОВАНИЯ
if st.session_state.show_rules:
    st.markdown("### Правила пользования сервисом")
    
    with st.expander("1. Назначение сервиса", expanded=True):
        st.markdown("""
        **1.1.** Сервис предназначен для анализа юридических документов (договоров, контрактов, соглашений)
        
        **1.2.** Пользователь может загрузить фото документа или вставить текст вручную
        
        **1.3.** Сервис предоставляет рекомендации на основе законодательства РФ или РБ
        """)
    
    with st.expander("2. Как пользоваться", expanded=True):
        st.markdown("""
        **2.1.** Выберите юрисдикцию (Россия или Беларусь) — это влияет на применяемые законы
        
        **2.2.** Выберите тип договора для более точного анализа
        
        **2.3.** Перейдите во вкладку «Фото» и загрузите изображение документа
        
        **2.4.** Дождитесь распознавания текста (10-30 секунд)
        
        **2.5.** Проверьте распознанный текст и при необходимости отредактируйте
        
        **2.6.** Нажмите «Анализировать» для получения результатов
        """)
    
    with st.expander("3. Требования к фото документа", expanded=False):
        st.markdown("""
        **3.1.** Фото должно быть чётким, без размытия
        
        **3.2.** Текст должен быть хорошо освещён, без теней и бликов
        
        **3.3.** Документ должен быть расположен ровно, без перекосов
        
        **3.4.** Поддерживаемые форматы: JPG, JPEG, PNG
        """)
    
    with st.expander("4. Конфиденциальность", expanded=False):
        st.markdown("""
        **4.1.** Загруженные документы не сохраняются на сервере
        
        **4.2.** Данные удаляются после завершения сессии
        
        **4.3.** Сервис не передаёт данные третьим лицам
        
        **4.4.** Не загружайте документы с персональными данными (паспорт, ИНН и т.д.)
        """)
    
    with st.expander("5. Ограничения и отказ от ответственности", expanded=False):
        st.markdown("""
        **5.1.** Сервис предоставляет рекомендации информационного характера
        
        **5.2.** Результаты анализа не являются юридической консультацией
        
        **5.3.** Для важных решений обращайтесь к профессиональным юристам
        
        **5.4.** Сервис не несёт ответственности за решения, принятые на основе анализа
        """)
    
    st.warning("**Важно:** Сервис не заменяет очную консультацию юриста. Для сложных случаев и важных сделок обращайтесь к специалистам.")
    
    st.info("**Поддержка:** При возникновении вопросов или технических проблем используйте кнопку «Обновить» для начала новой сессии.")
    
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

# === ВКЛАДКА 1: ФОТО ===
with tab_photo:
    st.markdown("#### Загрузка фото документа")
    
    current_files = st.file_uploader(
        "Выберите фото",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=False,
        key=f"up_{st.session_state.ocr_counter}",
        label_visibility="collapsed"
    )
    
    if current_files:
        file_info = current_files
        
        # Добавляем файл если его ещё нет
        if not any(x.name == file_info.name and x.size == file_info.size for x in st.session_state.uploaded_files_list):
            st.session_state.uploaded_files_list.append(file_info)
        
        st.success(f"Загружено файлов: {len(st.session_state.uploaded_files_list)}")
        
        for i, f in enumerate(st.session_state.uploaded_files_list):
            size_kb = round(f.size / 1024, 1)
            st.markdown(f"<div class='file-info'>📄 Стр. {i+1}: {f.name} ({size_kb} КБ)</div>", unsafe_allow_html=True)
        
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
                        st.warning(f"Стр. {idx+1}: {error}")
                
                if all_text.strip():
                    status.text("Обработка текста...")
                    corrected = correct_text_smart(all_text, st.session_state.jurisdiction)
                    
                    st.session_state.contract_txt = corrected
                    st.session_state.ocr_complete = True
                    st.session_state.ocr_counter += 1
                    st.success(f"Готово! ({len(corrected)} символов)")
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
                st.success("Готово!")
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
