from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import os

app = Flask(__name__)
CORS(app)  # Разрешаем запросы с любого источника

# ================= CONFIG =================
OCR_API_KEY = os.getenv('OCR_API_KEY', 'helloworld')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_MODEL = 'deepseek/deepseek-chat'

# ================= OCR =================
def ocr_space(file_bytes, filename='image.jpg'):
    """Отправка изображения в OCR.space"""
    files = {'file': (filename, file_bytes, 'image/jpeg')}
    data = {
        'apikey': OCR_API_KEY,
        'language': 'rus',
        'isOverlayRequired': 'false',
        'detectOrientation': 'true',
        'OCREngine': '2'
    }
    
    response = requests.post('https://api.ocr.space/parse/image', files=files, data=data, timeout=60)
    result = response.json()
    
    if result.get('IsErroredOnProcessing'):
        return None, result.get('ErrorMessage', ['Unknown error'])[0]
    
    text = result.get('ParsedResults', [{}])[0].get('ParsedText', '')
    return text.strip() if text else None, None

# ================= TEXT CORRECTION =================
def correct_text(text, jurisdiction):
    """Исправление опечаток через AI"""
    if not OPENROUTER_API_KEY or len(text) < 50:
        return text
    
    jur_name = 'Российская Федерация' if jurisdiction == 'RU' else 'Республика Беларусь'
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://umnyj-yurist.ru'
            },
            json={
                'model': OPENROUTER_MODEL,
                'messages': [
                    {'role': 'system', 'content': f'Ты редактор юридических документов ({jur_name}). Исправь опечатки.'},
                    {'role': 'user', 'content': f'Исправь текст:\n\n{text}'}
                ],
                'temperature': 0.1,
                'max_tokens': 3000
            },
            timeout=120
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
    except:
        pass
    return text

# ================= AI ANALYSIS =================
def analyze_contract(text, jurisdiction, contract_type):
    """Анализ договора через AI"""
    if not OPENROUTER_API_KEY:
        return None, "API ключ не настроен"
    
    jur_base = 'РФ' if jurisdiction == 'RU' else 'РБ'
    
    system_prompt = f"""Ты — юрист-эксперт по праву {jur_base}. Тип договора: {contract_type}.
Проанализируй договор и верни ответ в формате:
1. 🔴 Критические риски (с пояснением)
2. 🟡 Средние риски
3. 🟢 Что составлено грамотно
4. 💡 Рекомендации по изменению
5. ✅ Итоговый вердикт: Безопасно / Требует правок / Опасно"""

    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://umnyj-yurist.ru'
            },
            json={
                'model': OPENROUTER_MODEL,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f'Текст договора:\n\n{text}'}
                ],
                'temperature': 0.2,
                'max_tokens': 3000
            },
            timeout=120
        )
        if response.status_code == 200:
            result = response.json()['choices'][0]['message']['content'].strip()
            return result, None
        return None, "Ошибка сервиса"
    except Exception as e:
        return None, f"Ошибка: {str(e)}"

# ================= API ENDPOINTS =================

@app.route('/api/ocr', methods=['POST'])
def api_ocr():
    """Эндпоинт для OCR"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    file_bytes = file.read()
    text, error = ocr_space(file_bytes, file.filename)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({'text': text})

@app.route('/api/correct', methods=['POST'])
def api_correct():
    """Эндпоинт для коррекции текста"""
    data = request.json
    text = data.get('text', '')
    jurisdiction = data.get('jurisdiction', 'RU')
    
    corrected = correct_text(text, jurisdiction)
    return jsonify({'text': corrected})

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """Эндпоинт для анализа договора"""
    data = request.json
    text = data.get('text', '')
    jurisdiction = data.get('jurisdiction', 'RU')
    contract_type = data.get('contract_type', 'Другое')
    
    if len(text) < 50:
        return jsonify({'error': 'Текст слишком короткий'}), 400
    
    result, error = analyze_contract(text, jurisdiction, contract_type)
    
    if error:
        return jsonify({'error': error}), 500
    
    # Подсчёт рисков для фронтенда
    risk_summary = {
        'critical': len(re.findall(r'🔴', result)),
        'medium': len(re.findall(r'🟡', result)),
        'low': len(re.findall(r'🟢', result)),
        'verdict': 'Требует правок' if 'требует' in result.lower() else 'Нормально'
    }
    
    return jsonify({'result': result, 'risk_summary': risk_summary})

@app.route('/api/ask', methods=['POST'])
def api_ask():
    """Эндпоинт для юридических вопросов"""
    data = request.json
    question = data.get('question', '')
    jurisdiction = data.get('jurisdiction', 'RU')
    
    if not OPENROUTER_API_KEY:
        return jsonify({'error': 'API ключ не настроен'}), 500
    
    jur_base = 'РФ' if jurisdiction == 'RU' else 'РБ'
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://umnyj-yurist.ru'
            },
            json={
                'model': OPENROUTER_MODEL,
                'messages': [
                    {'role': 'system', 'content': f'Ты юрист ({jur_base}). Отвечай чётко, со ссылками на законы.'},
                    {'role': 'user', 'content': question}
                ],
                'temperature': 0.2,
                'max_tokens': 2000
            },
            timeout=90
        )
        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content'].strip()
            return jsonify({'answer': answer})
        return jsonify({'error': 'Ошибка сервиса'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Проверка работоспособности сервера"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
