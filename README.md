# ☁️ Cloud Storage

Многопользовательское файловое облако для безопасной загрузки, хранения и управления личными файлами. Проект построен на современной микросервисной архитектуре с использованием объектного S3-хранилища и полной контейнеризацией.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.1-092E20?logo=django&logoColor=white)
![React](https://img.shields.io/badge/React-Vite-61DAFB?logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-S3_Storage-C7202C?logo=minio&logoColor=white)

## ✨ Ключевые возможности
* **Изолированное хранилище:** У каждого пользователя своя защищенная директория для файлов.
* **S3-совместимость:** Файлы физически сохраняются в высокопроизводительном хранилище MinIO (через `boto3` и `django-storages`).
* **Продвинутое управление:** Создание вложенных директорий, загрузка, переименование и удаление файлов.
* **Современный UI:** Адаптивный SPA-интерфейс, построенный на React (Vite) и Material UI.
* **Безопасность:** Защищенные маршруты, JWT/Session-авторизация и строгая изоляция переменных окружения (`django-environ`).

---

## 🛠 Технологический стек

### Бэкенд
* **Язык и фреймворки:** Python 3.12, Django 6.1, Django REST Framework 3.18.
* **Управление зависимостями:** Poetry.
* **База данных и кэш:** PostgreSQL (`psycopg`), Redis (`django-redis`).
* **Сервер приложений:** Gunicorn.

### Инфраструктура и Фронтенд
* **Nginx** (веб-сервер и обратный прокси).
* **Docker & Docker Compose** (оркестрация 5 связанных контейнеров: web, frontend, postgres, redis, minio).
* **React 18**, Vite, React Router DOM.

---

## 🚀 Запуск проекта (Docker Compose)

Проект полностью контейнеризирован. Для запуска требуется только **Docker** и **Docker Compose**.

### 1. Клонирование репозитория
```bash
git clone [https://github.com/artikano27-blip/cloud-storage.git](https://github.com/artikano27-blip/cloud-storage.git)
cd cloud-storage
```

### 2. Настройка переменных окружения
Создайте файл `.env` в корневой директории. Пример конфигурации:
```env
# Django
SECRET_KEY=your_super_secret_key
DEBUG=False
ALLOWED_HOSTS=127.0.0.1,localhost,web

# PostgreSQL
POSTGRES_DB=storage_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis (Для Docker Compose используйте хост 'redis')
REDIS_HOST=redis
REDIS_PORT=6379

# MinIO (S3)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_STORAGE_BUCKET_NAME=cloud-storage
AWS_S3_ENDPOINT_URL=http://minio:9000

# React Frontend
VITE_BASE=/
```

### 3. Сборка и запуск
Выполните команду для сборки образов и запуска проекта в фоновом режиме:
```bash
docker compose up -d --build
```

### 4. Применение миграций
После того как контейнеры поднимутся, примените миграции базы данных:
```bash
docker compose exec web python manage.py migrate
```

👉 **Приложение доступно по адресу:** `http://localhost`

---

## 🧪 Локальное тестирование для разработчиков

Бэкенд покрыт тестами с использованием `pytest`. Интеграционные тесты работают через `testcontainers`, который автоматически изолированно поднимает тестовую базу данных PostgreSQL.

⚠️ **Требования для запуска тестов на хост-машине:**
1. Приложение **Docker Desktop** должно быть запущено (для создания временной БД через testcontainers).
2. Тестам требуется доступ к Redis. Так как тесты запускаются вне сети Docker Compose, им нужен локальный Redis.

### Инструкция по запуску тестов:

1. **Поднимите локальный Redis** (из контейнера):
   ```bash
   docker compose up -d redis
   ```

2. **Обновите `.env` для локальных тестов:**
   В вашем локальном файле `.env` временно измените хост Redis на локальный IP, чтобы тесты могли до него достучаться:
   ```env
   REDIS_HOST=127.0.0.1
   ```
   *(Не забудьте вернуть `REDIS_HOST=redis` перед деплоем на сервер).*

3. **Запустите тесты через Poetry:**
   ```bash
   poetry run pytest
   ```
   *Testcontainers автоматически скачает образ PostgreSQL, прогонит тесты и удалит тестовый контейнер, не оставляя мусора.*
