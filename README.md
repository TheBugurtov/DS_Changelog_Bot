# Figma to Telegram Changelog Bot

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![GPT](https://img.shields.io/badge/Made_with-ChatGPT-10a37f?style=flat&logo=openai&logoColor=white)
![Build](https://img.shields.io/github/actions/workflow/status/TheBugurtov/DS_Changelog_Bot/bot.yml?label=Build&logo=githubactions&style=flat)




Бот для автоматической публикации изменений из Figma в Telegram-канал. Отслеживает изменения в указанных фреймах и публикует их в формате changelog.

## Основные функции

- Автоматическая проверка изменений в Figma по расписанию
- Публикация в Telegram с форматированием
- Поддержка нескольких фреймов из разных файлов
- Сохранение истории изменений
- Настройка через конфигурационный файл

## Быстрый старт

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/TheBugurtov/DS_Changelog_Bot.git
cd DS_Changelog_Bot
```

### 2. Настройте Secrets в GitHub

В `Settings → Secrets → Actions` добавьте:

- `FIGMA_TOKEN` — Personal Access Token из Figma
- `BOT_TOKEN` — токен Telegram бота (через @BotFather)
- `CHANNEL_ID` — ID вашего канала (например `@yourchannel`)

### 3. Настройте отслеживаемые фреймы

Отредактируйте `config.py`:

```python
FRAME_CONFIGS = [
    {
        "file_id": "7V4UQ61IVRxGArYZ20n7MH",  # Из URL Figma
        "node_id": "18723:231737",           # После node-id=
        "title": "App Components"            # Заголовок для сообщений
    },
    # Добавьте другие фреймы по аналогии
]
```

Бот будет запускаться автоматически каждый день в 10:00 МСК.

## Конфигурация

### Добавление нового фрейма

1. Откройте нужный файл в Figma
2. Скопируйте из URL:
   - `file_id` — часть между /design/ и ?
   - `node_id` — часть после node-id=
3. Добавьте в `config.py`:

```python
{
    "file_id": "ВАШ_FILE_ID",
    "node_id": "ВАШ_NODE_ID",
    "title": "Название компонента"
}
```

### Изменение Telegram канала

Обновите `CHANNEL_ID` в Secrets.

Для приватных каналов используйте числовой ID (можно получить через @getmyid_bot)

## Формат сообщений

Пример отправляемого сообщения:

```
🔄 Обновление в App Components

<b>15 июля 2025</b>
Updated  
Button Component  
Исправлены отступы

<b>10 июля 2025</b>
Added  
Новый компонент Modal
```

## Структура проекта

```
DS_Changelog_Bot/
├── .github/
│   └── workflows/
│       └── bot.yml          # Workflow для GitHub Actions
├── config.py               # Конфигурация фреймов
├── figma_to_tg.py          # Основной код бота
├── history/                # История изменений
└── README.md               # Этот файл
```

## Логи и отладка

- Все изменения сохраняются в папке `history/`
- Логи выполнения можно посмотреть в GitHub Actions
- Для ручного запуска: `Actions → Figma Changelog Bot → Run workflow`
