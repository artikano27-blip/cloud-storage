from concurrent.futures import ThreadPoolExecutor
import requests

# 1. Задайте URL вашего эндпоинта
URL = "http://127.0.0.1/api/directory/?path=race-folder"

# 2. Передайте Cookie сессии авторизованного пользователя (возьмите из DevTools)
COOKIES = {
    "sessionid": "4l086wqmnami0qkr59tnad3qxurtxa34",
    # "csrftoken": "..." # если включена CSRF-защита
}


def create_directory(request_id):
    try:
        # Передаем path в теле POST-запроса
        response = requests.post(
            URL, data={"path": "123"}, cookies=COOKIES
        )
        return request_id, response.status_code, response.text
    except Exception as e:
        return request_id, "ERR", str(e)


# Запускаем 5 одновременных запросов в 5 потоков
with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(create_directory, range(1, 6)))

for req_id, status, body in results:
    print(f"Запрос #{req_id}: статус {status} -> {body[:80]}")