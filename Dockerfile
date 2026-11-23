# Берем готовый легкий образ с Python 3.11
FROM python:3.11-slim

# Создаем внутри контейнера рабочую папку /app
WORKDIR /app

# Копируем список библиотек и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все ваши .py файлы внутрь контейнера
COPY *.py .

# Команда по умолчанию: при запуске контейнера прогнать все тесты
CMD ["pytest", "-v"]