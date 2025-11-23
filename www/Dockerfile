# Використовуємо офіційний Python образ
FROM python:3.11-slim

# Встановлюємо системні залежності для PostgreSQL та інших пакетів
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Створюємо робочу директорію
WORKDIR /app

# Копіюємо файли вимог та встановлюємо Python залежності
COPY requirements.txt .

# Встановлюємо Python залежності
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь код додатка
COPY . .

# Створюємо директорію для бекапів
RUN mkdir -p backups

# Відкриваємо порт, на якому працює Flask
EXPOSE 5000

# Змінні середовища за замовчуванням
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV DB_HOST=db
ENV DB_PORT=5432
ENV DB_NAME=wdb
ENV DB_USER=webadmin
ENV DB_PASSWORD=admin
ENV PG_DUMP_PATH=/usr/bin/pg_dump

# Запускаємо додаток
CMD ["python", "app.py"]