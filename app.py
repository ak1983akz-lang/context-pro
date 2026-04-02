import streamlit as st
import os
import requests
import time
from PIL import Image
import io
import re
from datetime import datetime

# =============================================================================
# SESSION STATE
# =============================================================================
if 'contract_txt' not in st.session_state:
    st.session_state.contract_txt = ""
if 'result' not in st.session_state:
    st.session_state.result = ""
if 'jurisdiction' not in st.session_state:
    st.session_state.jurisdiction = "🇷 🇺 РФ"
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
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
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
                "HTTP-Referer": os.getenv("APP_URL", "https://context-pro.streamlit.app")
            },
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": f"Ты — редактор юридических документов ({jur_base}). Исправь опечатки и ошибки."},
                    {"role": "user", "content": f"Исправь текст:\n\n{raw_text}"}
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
                return re.sub(r'\s+', ' ', corrected).strip()
        
        return raw_text
    except:
        return raw_text

# =============================================================================
# 📸 OCR (МАКСИАЛЬНАЯ КОМПРЕССИЯ ДО 500 КБ)
# =============================================================================
def optimize_image_for_upload(original_bytes):
    """Сжимает изображение до 500 КБ максимум"""
    try:
        img = Image.open(io.BytesIO(original_bytes))
        
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        width, height = img.size
        
        if width > 1600 or height > 1600:
            scale = min(1.0, 1600 / max(width, height))
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            width, height = new_width, new_height
        
        quality = 80
        img_byte_arr = io.BytesIO()
        target_size = 500 * 1024
        
        while quality >= 10:
            img.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
            size_kb = len(img_byte_arr.getvalue()) / 1024
            
            if size_kb <= target_size:
                break
                
            quality -= 5
            img_byte_arr.seek(0)
        
        img_byte_arr.seek(0)
        return img_byte_arr.getvalue(), True
        
    except Exception as e:
        return original_bytes, False

# =============================================================================
# 📸 OCR С ОПТИМИЗАЦИЕЙ
# =============================================================================
def extract_text_from_image(uploaded_file):
    try:
        uploaded_file.seek(0)
        original_bytes = uploaded_file.read()
        
        if not original_bytes or len(original_bytes) == 0:
            return None, "Файл пустой"
        
        processed_bytes, success = optimize_image_for_upload(original_bytes)
        
        if not success:
            return None, "Не удалось обработать изображение"
        
        size_mb = len(processed_bytes) / (1024 * 1024)
        if size_mb > 5:
            return None, f"Файл слишком большой: {size_mb:.1f} МБ (макс. 5 МБ)"
        
        processed_file = io.BytesIO(processed_bytes)
        processed_file.name = getattr(uploaded_file, 'name', 'photo.jpg')
        processed_file.type = getattr(uploaded_file, 'type', 'image/jpeg')
        
        for attempt in range(2):
            try:
                response = requests.post(
                    'https://api.ocr.space/parse/image',
                    files={'file': (processed_file.name, processed_file, processed_file.type)},
                    data={
                        'apikey': os.getenv("OCR_API_KEY", "helloworld"),
                        'language': 'rus',
                        'isOverlayRequired': 'false',
                        'detectOrientation': 'true',
                        'OCREngine': '2',
                        'scale': 'true'
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if not data.get('IsErroredOnProcessing'):
                        text = data.get('ParsedResults', [{}])[0].get('ParsedText', '')
                        if text and text.strip():
                            return text.strip(), None
                    
                    err_msg = data.get('ErrorMessage', ['Unknown error'])
                    if isinstance(err_msg, list):
                        err_msg = ' | '.join(err_msg)
                    if attempt == 1:
                        return None, f"Ошибка OCR: {err_msg}"
                        
            except Exception as e:
                if attempt == 1:
                    return None, f"Ошибка сети: {str(e)}"
                continue
                
        return None, "Не удалось распознать"
        
    except Exception as e:
        return None, f"Ошибка обработки: {str(e)}"

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
    """Получение ключа OpenRouter: приоритет — env, затем st.secrets"""
    key = os.getenv("OPENROUTER_API_KEY")
    if key:
        return key
    try:
        if "openrouter" in st.secrets:
            return st.secrets["openrouter"]["api_key"]
    except:
        pass
    return None

def query_ai(system_prompt: str, user_text: str):
    api_key = get_api_key()
    if not api_key:
        return None, "API ключ не настроен"
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.getenv("APP_URL", "https://context-pro.streamlit.app")
            },
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                "temperature": 0.2,
                "max_tokens": 3000
            },
            timeout=90
        )
        if response.status_code == 200:
            data = response.json()
            result = data["choices"][0]["message"]["content"]
            return re.sub(r'\s+', ' ', result).strip(), None
        return None, "Ошибка сервиса"
    except Exception as e:
        return None, "Ошибка соединения"

# =============================================================================
# 📊 ИЗВЛЕЧЕНИЕ ИТОГОВ
# =============================================================================
def extract_risk_summary(full_result: str, contract_type: str) -> dict:
    return {
        "critical": full_result.count("🔴"),
        "medium": full_result.count("🟡"),
        "low": full_result.count("🟢"),
        "verdict": "Требует правок" if "требует" in full_result.lower() else "Нормально"
    }

# =============================================================================
# 🌉 VK BRIDGE INIT
# =============================================================================
def init_vk_bridge():
    """Подключает VK Bridge и отправляет событие инициализации"""
    vk_bridge_script = """
    <script src="https://unpkg.com/@vkontakte/vk-bridge@latest/browser/vk-bridge.min.js"></script>
    <script>
        if (window.vkBridge) {
            window.vkBridge.send('VKWebAppInit')
                .then(() => console.log('✅ VK Bridge initialized'))
                .catch(error => console.log('❌ VK Bridge init error:', error));
        }
    </script>
    """
    st.markdown(vk_bridge_script, unsafe_allow_html=True)

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

# Инициализация VK Bridge (обязательно для VK Mini Apps)
init_vk_bridge()

# =============================================================================
# ШАПКА
# =============================================================================
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
        **1.1.** Выберите юрисдикцию
        
        **1.2.** Выберите тип договора
        
        **1.3.** Загрузите фото из галереи
        
        **1.4.** Нажмите «Распознать» (ждите 10-30 сек)
        
        **1.5.** Проверьте текст и нажмите «Анализировать»
        """)
    
    st.warning("**Важно:** Сервис не заменяет консультацию юриста.")
    st.info("**Поддержка:** Используйте кнопку «Обновить».")
    st.divider()

# НАСТРОЙКИ
col_jur, col_type = st.columns(2)

with col_jur:
    st.markdown("**Юрисдикция:**")
    jur_option = st.selectbox(
        "Законодательство:",
        options=["🇷 🇺 Россия", "🇧 РБ"],
        index=0,
        key="jur_select",
        label_visibility="collapsed"
    )
    st.session_state.jurisdiction = "🇷 🇺 РФ" if "Россия" in jur_option else "🇧🇾 РБ"

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

# === ФОТО ===
with tab_photo:
    st.markdown("#### Загрузка фото документа")
    st.markdown("💡 **Как загрузить:** Откройте Галерею → выберите фото → загрузите")
    st.markdown("⚠️ **Важно:** Фото будут автоматически сжаты до оптимального размера")
    
    current_files = st.file_uploader(
        "Выберите фото",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key=f"up_{st.session_state.ocr_counter}",
        label_visibility="hidden"
    )
    
    if current_files:
        if isinstance(current_files, list):
            files_to_process = current_files
        else:
            files_to_process = [current_files]
        
        for f in files_to_process:
            if not any(x.name == f.name and x.size == f.size for x in st.session_state.uploaded_files_list):
                st.session_state.uploaded_files_list.append(f)
        
        st.success(f"Файлов: {len(st.session_state.uploaded_files_list)}")
        
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
                errors = []
                success_count = 0
                
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
                        success_count += 1
                        progress_bar.progress(int((idx+1)/total * 100))
                    else:
                        errors.append(f"Стр. {idx+1}: {error}")
                
                if success_count > 0:
                    status.text("Обработка текста...")
                    corrected = correct_text_smart(all_text, st.session_state.jurisdiction)
                    
                    st.session_state.contract_txt = corrected
                    st.session_state.ocr_complete = True
                    st.session_state.ocr_counter += 1
                    
                    if errors:
                        st.warning(f"Распознано: {success_count}/{total}")
                        st.markdown("""
                        **Советы при ошибках:**<br>
                        • Делайте скриншот вместо фотографии<br>
                        • Уменьшите качество исходного фото<br>
                        • Убедитесь что документ лежит ровно
                        """)
                    
                    st.success(f"Успешно: {success_count}/{total} страниц")
                    st.rerun()
                else:
                    status.empty()
                    progress_bar.empty()
                    st.error("Все страницы не распознаны")
                    st.markdown("""
                    **Попробуйте это:**<br>
                    1. Сделайте новый снимок при хорошем освещении<br>
                    2. Положите документ на светлую ровную поверхность<br>
                    3. Не делайте резких движений камерой<br>
                    4. Или используйте другой документ
                    """)

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
Проанализируй договор:
1. Риски с уровнем опасности (🔴 Критический / 🟡 Средний / 🟢 Низкий)
2. Что составлено грамотно
3. Рекомендации по изменению пунктов
4. Итоговый вердикт (Безопасно / Требует правок / Опасно)"""
            
            res, err = query_ai(prompt, txt)
            
            st.session_state.is_analyzing = False
            if err: st.error(err)
            else:
                st.session_state.result = res
                st.session_state.risk_summary = extract_risk_summary(res, st.session_state.contract_type)
                st.success("✅ Готово!")
                st.rerun()
        
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
            
            st.download_button(
                label="📥 Скачать отчёт",
                data=st.session_state.result,
                file_name="legal_analysis.txt",
                mime="text/plain",
                use_container_width=True
            )
    
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

# === РУЧНОЙ ВВОД ===
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

# === ВОПРОС ===
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
