#!/bin/bash
# Build Command для Render

echo "🚀 Начинаю сборку бота..."

# Обновление pip до последней версии
python -m pip install --upgrade pip

# Установка Python зависимостей
pip install -r requirements.txt

# Создание необходимых директорий
mkdir -p data logs

# Установка прав на запись (для Unix-систем)
chmod -R 777 data logs 2>/dev/null || true

echo "✅ Сборка завершена!"
