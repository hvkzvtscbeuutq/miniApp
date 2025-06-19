import os
from flask import Flask, jsonify, request
import requests
from dotenv import load_dotenv
from flask_cors import CORS # Импортируем Flask-CORS для разрешения CORS запросов

# Загружаем переменные окружения из файла .env
load_dotenv()

app = Flask(__name__)
# Включаем CORS для всех доменов. В продакшене лучше указать конкретные домены,
# откуда ожидаются запросы (например, домен вашего Mini App).
CORS(app) 

# Получаем API ключ CoinMarketCap из переменных окружения
# Убедитесь, что у вас есть файл .env в том же каталоге с содержимым:
# COINMARKETCAP_API_KEY="ВАШ_API_КЛЮЧ_CMC"
COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY")

# URL для API CoinMarketCap
CMC_API_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

# Список популярных стейблкоинов (для исключения) - можно перенести на клиент, но для примера пусть будет здесь
STABLECOINS = [
    "USDT", "USDC", "BUSD", "DAI", "UST", "TUSD", "PAX", "GUSD", "USDP", "FRAX", "LUSD", "CRVUSD"
]

@app.route('/api/top-crypto', methods=['GET'])
def get_top_crypto():
    """
    Эндпоинт для получения топ-10 криптовалют через CoinMarketCap API.
    Фильтрует стейблкоины и возвращает данные.
    """
    if not COINMARKETCAP_API_KEY:
        return jsonify({"error": "API ключ CoinMarketCap не настроен."}), 500

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY,
    }
    params = {
        'start': '1',
        'limit': '50', # Берем больше, чтобы исключить стейблкоины и получить топ-10
        'convert': 'USD'
    }

    try:
        response = requests.get(CMC_API_URL, headers=headers, params=params)
        response.raise_for_status() # Вызовет исключение для ошибок HTTP (4xx или 5xx)
        data = response.json()

        crypto_list = []
        count = 0
        for crypto in data['data']:
            symbol = crypto['symbol']
            name = crypto['name']

            # Проверяем, не является ли монета стейблкоином
            if symbol.upper() in STABLECOINS:
                continue

            if 'quote' not in crypto or 'USD' not in crypto['quote']:
                print(f"Предупреждение: Пропускаем {name} ({symbol}) из-за отсутствия данных о котировках.")
                continue

            quote_data = crypto['quote']['USD']

            # Собираем только необходимые данные для отправки клиенту
            crypto_info = {
                "name": name,
                "symbol": symbol,
                "price": quote_data.get('price'),
                "volume_24h": quote_data.get('volume_24h'),
                "percent_change_24h": quote_data.get('percent_change_24h'),
                "percent_change_7d": quote_data.get('percent_change_7d'),
                "percent_change_30d": quote_data.get('percent_change_30d'),
            }
            crypto_list.append(crypto_info)
            count += 1
            if count >= 10:
                break

        return jsonify({"data": crypto_list}), 200

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к CoinMarketCap API: {e}")
        return jsonify({"error": "Ошибка при получении данных от внешнего API.", "details": str(e)}), 500
    except Exception as e:
        print(f"Неизвестная ошибка на сервере: {e}")
        return jsonify({"error": "Произошла непредвиденная ошибка на сервере.", "details": str(e)}), 500

if __name__ == '__main__':
    # В продакшене используйте Gunicorn, Waitress или другой WSGI-сервер
    # для более надежной и производительной работы.
    # Для разработки:
    app.run(host='0.0.0.0', port=5000, debug=True)
