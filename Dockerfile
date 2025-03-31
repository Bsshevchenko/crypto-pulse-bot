FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости и устанавливаем
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаем директорию под БД (она будет заменена volume-том при запуске)
RUN mkdir -p /app/data

# Стартовая команда
CMD ["python3", "main.py"]
