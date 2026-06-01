# 📁 School Bot Storage

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://t.me/BotFather)

Telegram-бот для хранения и управления документами школы.  
Загружайте файлы, добавляйте категории через #теги, ищите документы и сохраняйте в избранное.

---

## ✨ Возможности

| Функция | Описание |
|---------|----------|
| 📤 **Загрузка** | Отправьте файл → введите название и #категорию |
| ⭐ **Избранное** | Добавляйте важные документы в отдельный список |
| 🔍 **Поиск** | Быстрый поиск по названиям документов |
| 📂 **Категории** | Автоматическая группировка по #тегам |
| 📊 **Статистика** | Количество документов, категорий, избранного |
| 🔐 **Доступ** | Только авторизованные сотрудники по Telegram ID |

---

## Быстрый старт

### 1️⃣ Требования
- Python 3.9 или выше
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))

### 2️⃣ Установка

```bash
# Клонируем репозиторий
git clone https://github.com/theqarden/school-bot-storage
cd school-bot-storage

# Создаём виртуальное окружение
python -m venv venv

# Активируем
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt


# Переходим в папку с ботом
cd school-bot-storage

# Запускаем бота
python school-bot-storage.py
