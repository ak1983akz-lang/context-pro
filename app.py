import streamlit as st
import requests
import re
import os
from PIL import Image
import io

# =============================================================================
# 🔑 НАСТРОЙКИ API (ЗАПОЛНИ СВОИ КЛЮЧИ)
# =============================================================================
# Вариант 1: Вставь ключи прямо сюда (для тестов)
MANUAL_OCR_KEY = ""          # Вставь ключ от ocr.space
MANUAL_OPENROUTER_KEY = ""   # Вставь ключ от openrouter.ai

# Вариант 2: Streamlit Cloud автоматически подтянет из Secrets (рекомендуется)
OCR_API_KEY = MANUAL_OCR_KEY or st.secrets.get("OCR_API_KEY", os.getenv("OCR_API_KEY", "helloworld"))
OPENROUTER_API_KEY = MANUAL_OPENROUTER_KEY or st.secrets.get("OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY", ""))
MODEL_NAME = "deepseek/deepseek-chat"

# =============================================================================
# 💾 СОСТОЯНИЕ ПРИЛОЖЕНИЯ
# =============================================================================
if 'contract_txt' not in st.session_state: st.session_state.contract_txt = ""
if 'result' not in st.session_state: st.session_state.result = None
if 'risk_summary' not in st.session_state: st.session_state.risk_summary = None
if 'jurisdiction' not in st.session_state: st.session_state.jurisdiction = "RU"
if 'contract_type' not in st.session_state: st.session_state.contract_type = "Другое"

# =============================================================================
# 🌉 VK BRIDGE
# =============================================================================
st.markdown("""
<script src="https://unpkg.com/@vkontakte/vk-bridge/dist/browser.min.js"></script>
<script>
if (window.vkBridge) {
    vkBridge.send('VKWebAppInit').catch(()=>{});
}
function haptic(style) {
    if (window.vkBridge) vkBridge.send('VKWebAppTapticImpactOccurred', {style}).catch(()=>{});
}
</script>
""", unsafe_allow_html=True)

# =============================================================================
# 🎨 СТИЛИ
# =============================================================================
st.markdown("""
<style>
    #MainMenu, footer, .stDeployButton {visibility: hidden;}
    .stApp { background: #0e1117; color: #fafafa; }
    .stTextArea textarea { background: #1e2329 !important; color: #fff !important; border: 1px solid #3a3f47 !important; }
    .stButton>button { 
        background: #1f77b4 !important; color: white !important; 
        border: none !important; border-radius: 8px !important; 
        height: 48px !important; font-weight: 600 !important; width: 100% !important;
    }
    .stButton>button:disabled { background: #3a3f47 !important; color: #666 !important; cursor: not-allowed; }
    .risk-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 15px 0; }
    .risk-card { background: #1e2329; border-radius: 10px; padding: 12px; text-align: center; border: 2px solid #3a3f47; }
    .risk-card.critical { border-color: #ef4444; }
    .risk-card.medium { border-color: #f59e0b; }
    .risk-card.low { border-color: #22c55e; }
    .risk-card.verdict { border-color: #1f77b4; background: #1e3a5f; }
    .risk-num { font-size: 22px; font-weight: bold; display: block; }
    .risk-num.critical { color: #ef4444; }
    .risk-num.medium { color: #f59e0b; }
    .risk-num.low { color: #22c55e; }
    .risk-label { font-size: 11px; color: #a0a0a0; }
    .result-box { background: #1e2329; border-radius: 10px; padding: 16px; margin-top: 15px; white-space: pre-wrap; font-size: 14px; line-height: 1.5; border: 1px solid #3a3f47; }
    .answer-box { background: #1e3a5f; border-radius: 10px; padding: 16px; margin-top: 15px; white-space: pre-wrap; font-size: 14px; line-height: 1.5; border: 1px solid #1f77b4; }
    @media (max-width: 600px) { .risk-cards { grid-template-columns: repeat(2, 1fr); } }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 🛠 ФУНКЦИИ
# =============================================================================
def compress_image(file_bytes, max_size_kb=500):
    try:
        img = Image.open(io.BytesIO(file_bytes))
        if img.mode in ('RGBA', 'P', 'LA'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P': img = img.convert('RGBA')
            bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = bg
        elif img.mode != 'RGB': img = img.convert('RGB')
        w, h = img.size
        if max(w, h) > 1600:
            scale = 1600 / max(w, h)
            img = img.resize((int(w*scale), int(h*scale)), Image.Resampling.LANCZOS)
        quality = 85
        for _ in range(10):
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=quality, optimize=True)
            if buf.tell() <= max_size_kb * 1024: return buf.getvalue()
            quality -= 5
        return buf.getvalue()
    except: return file_bytes

def call_openrouter(system_prompt, user_text, max_tokens=3000):
    if not OPENROUTER_API_KEY: return None, "⚠️ API ключ OpenRouter не настроен. Добавь его в настройки Streamlit Cloud."
    try:
        resp = requests.post('https://openrouter.ai/api/v1/chat/completions',
            headers={'Authorization': f'Bearer {OPENROUTER_API_KEY}', 'Content-Type': 'application/json', 'HTTP-Referer': 'https://context-pro.streamlit.app'},
            json={'model': MODEL_NAME, 'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_text}
            ], 'temperature': 0.2, 'max_tokens': max_tokens}, timeout=120)
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content'].strip(), None
        return None, f"Ошибка API: {resp.status_code}"
    except Exception as e: return None, str(e)

def ocr_space(file_bytes, filename="img.jpg"):
    try:
        compressed = compress_image(file_bytes)
        files = {'file': (filename, io.BytesIO(compressed), 'image/jpeg')}
        data = {'apikey': OCR_API_KEY, 'language': 'rus', 'isOverlayRequired': 'false', 'detectOrientation': 'true', 'OCREngine': '2'}
        resp = requests.post('https://api.ocr.space/parse/image', files=files, data=data, timeout=60)
        result = resp.json()
        if result.get('IsErroredOnProcessing'): return None, result.get('ErrorMessage', ['Error'])[0]
        text = result.get('ParsedResults', [{}])[0].get('ParsedText', '')
        return text.strip() if text else None, None
    except Exception as e: return None, str(e)

def correct_text(text, jurisdiction):
    if len(text) < 50: return text
    jur_name = 'Российская Федерация' if jurisdiction == 'RU' else 'Республика Беларусь'
    sys_prompt = f"Ты редактор юридических документов ({jur_name}). Исправь опечатки и ошибки распознавания, сохрани юридический смысл и структуру."
    res, err = call_openrouter(sys_prompt, f"Исправь текст:\n\n{text}", max_tokens=3000)
    return res if not err else text

def analyze_contract(text, jurisdiction, contract_type):
    jur_base = 'РФ' if jurisdiction == 'RU' else 'РБ'
    sys_prompt = f"""Ты опытный юрист по праву {jur_base}. Специализация: {contract_type}.
Проанализируй договор строго по структуре:
1. 🔴 Критические риски (нарушения закона, кабальные условия)
2. 🟡 Средние риски (неоднозначные формулировки)
3. 🟢 Что составлено грамотно
4. 💡 Конкретные рекомендации по правкам
5. ✅ Итоговый вердикт: Безопасно / Требует правок / Опасно
Отвечай чётко, без воды."""
    return call_openrouter(sys_prompt, text)

def ask_question(question, jurisdiction):
    jur_base = 'РФ' if jurisdiction == 'RU' else 'РБ'
    sys_prompt = f"Ты практикующий юрист ({jur_base}). Отвечай на вопросы граждан, ссылаясь на статьи законов (ГК РФ/РБ, ТК РФ/РБ и т.д.). Формат: краткий ответ -> правовое обоснование -> рекомендация."
    return call_openrouter(sys_prompt, question, max_tokens=2000)

def extract_risks(text):
    return {
        'critical': len(re.findall(r'🔴', text)),
        'medium': len(re.findall(r'🟡', text)),
        'low': len(re.findall(r'🟢', text)),
        'verdict': 'Требует правок' if 'требует' in text.lower() else 'Опасно' if 'опасно' in text.lower() else 'Нормально'
    }

# =============================================================================
# 🖥 ИНТЕРФЕЙС
# =============================================================================
st.title("⚖️ umnyj-yurist")
st.caption("AI-анализ договоров и юридические консультации")

# Настройки
col_j, col_t = st.columns(2)
with col_j:
    st.session_state.jurisdiction = st.selectbox("🌍 Юрисдикция", ["🇷🇺 Россия (РФ)", "🇧🇾 Беларусь (РБ)"], index=0, label_visibility="collapsed")
    st.session_state.jurisdiction = "RU" if "РФ" in st.session_state.jurisdiction else "BY"
with col_t:
    st.session_state.contract_type = st.selectbox("📄 Тип договора", ["Договор аренды", "Купли-продажи", "Услуг", "Подряда", "Трудовой", "Поставки", "Займа", "Другое"], index=7, label_visibility="collapsed")

st.divider()

# Вкладки
tab_photo, tab_text, tab_question = st.tabs(["📸 Фото документа", "📝 Ввести текст", "❓ Юридический вопрос"])

# === ВКЛАДКА 1: ФОТО ===
with tab_photo:
    uploaded = st.file_uploader("Загрузи фото или скан договора (JPG/PNG)", type=['jpg','jpeg','png'], label_visibility="collapsed")
    if uploaded:
        with st.spinner("🔍 Распознаю текст и исправляю ошибки..."):
            raw_text, err = ocr_space(uploaded.read(), uploaded.name)
            if err:
                st.error(f"❌ OCR ошибка: {err}")
            elif raw_text:
                st.session_state.contract_txt = correct_text(raw_text, st.session_state.jurisdiction)
                st.success("✅ Текст распознан и проверен!")
    
    if st.session_state.contract_txt:
        st.session_state.contract_txt = st.text_area("Отредактируй текст при необходимости:", value=st.session_state.contract_txt, height=200, label_visibility="collapsed")
        
        if st.button("⚖️ Анализировать договор", disabled=len(st.session_state.contract_txt)<50):
            with st.spinner("🧠 AI анализирует риски..."):
                res, err = analyze_contract(st.session_state.contract_txt, st.session_state.jurisdiction, st.session_state.contract_type)
                if err: st.error(err)
                else:
                    st.session_state.result = res
                    st.session_state.risk_summary = extract_risks(res)
                    st.success("✅ Анализ завершён!")

# === ВКЛАДКА 2: ТЕКСТ ===
with tab_text:
    txt = st.text_area("Вставь текст договора сюда:", height=200, label_visibility="collapsed")
    if st.button("⚖️ Анализировать", disabled=len(txt)<50):
        with st.spinner("🧠 AI анализирует..."):
            res, err = analyze_contract(txt, st.session_state.jurisdiction, st.session_state.contract_type)
            if err: st.error(err)
            else:
                st.session_state.result = res
                st.session_state.risk_summary = extract_risks(res)
                st.rerun()

# === ВКЛАДКА 3: ВОПРОС ===
with tab_question:
    q = st.text_area("Задай вопрос юристу (например: 'Может ли работодатель удержать зарплату за штраф?')", height=120, label_visibility="collapsed")
    if st.button("💬 Получить ответ", disabled=len(q)<5):
        with st.spinner(" Ищу правовое обоснование..."):
            ans, err = ask_question(q, st.session_state.jurisdiction)
            if err: st.error(err)
            else:
                st.session_state.question_answer = ans
                st.rerun()
    if 'question_answer' in st.session_state and st.session_state.question_answer:
        st.markdown("### 📜 Ответ юриста:")
        st.markdown(f"<div class='answer-box'>{st.session_state.question_answer}</div>", unsafe_allow_html=True)
        if st.button("🗑 Очистить ответ"):
            st.session_state.question_answer = None
            st.rerun()

# =============================================================================
# 📊 РЕЗУЛЬТАТЫ АНАЛИЗА
# =============================================================================
if st.session_state.result and st.session_state.risk_summary:
    st.divider()
    st.markdown("### 📊 Карта рисков")
    rs = st.session_state.risk_summary
    st.markdown(f"""
    <div class="risk-cards">
        <div class="risk-card critical"><span class="risk-num critical">{rs['critical']}</span><span class="risk-label">Критич.</span></div>
        <div class="risk-card medium"><span class="risk-num medium">{rs['medium']}</span><span class="risk-label">Средн.</span></div>
        <div class="risk-card low"><span class="risk-num low">{rs['low']}</span><span class="risk-label">В норме</span></div>
        <div class="risk-card verdict"><span class="risk-num">{rs['verdict']}</span><span class="risk-label">Вердикт</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📋 Полный разбор")
    st.markdown(f"<div class='result-box'>{st.session_state.result}</div>", unsafe_allow_html=True)
    
    st.download_button("📥 Скачать отчёт (TXT)", data=st.session_state.result, file_name="legal_analysis.txt", mime="text/plain", use_container_width=True)
    
    if st.button("🔄 Новый анализ"):
        st.session_state.contract_txt = ""
        st.session_state.result = None
        st.session_state.risk_summary = None
        st.rerun()

# Футер
st.divider()
st.markdown("<div style='text-align:center;color:#555;font-size:11px;margin-top:20px'>⚖️ umnyj-yurist • Данные не сохраняются • Не является публичной офертой</div>", unsafe_allow_html=True)
