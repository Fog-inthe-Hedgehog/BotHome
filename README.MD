# BotHome

Telegram-бот на **aiogram 3**, который периодически читает RSS-ленту, фильтрует новости по ключевым словам и отправляет уведомления администратору.

## Возможности

- Фоновая проверка RSS по расписанию (`CHECK_INTERVAL_HOURS`)
- Фильтрация по ключевым словам в заголовке и описании
- Команды: `/start`, `/help`, `/check_now` (ручная проверка, только для admin)
- При первом запуске старые записи ленты не отправляются (warm-up)

## Требования

- Python 3.13.12 (локально) или Docker
- Токен бота от [@BotFather](https://t.me/BotFather)
- Chat ID администратора (узнать через `/start` у бота)

## Настройка

Скопируйте пример и заполните переменные:

```bash
cp .env.example .env
```

| Переменная | Описание |
|------------|----------|
| `TELEGRAM_BOT_TOKEN` | Токен бота |
| `ADMIN_ID` | Chat ID для уведомлений |
| `RSS_URL` | URL RSS-ленты |
| `RSS_KEYWORDS` | Ключевые слова через запятую |
| `CHECK_INTERVAL_HOURS` | Интервал проверки (часы) |
| `TAG` | Тег Docker-образа (для compose) |
| `DEBUG` | Подробные логи (`true` / `false`) |

## Локальный запуск

```bash
poetry install
poetry run python -m app.main
```

## Запуск в Docker

```bash
docker compose build
docker compose up -d
docker compose logs -f
```

Остановка:

```bash
docker compose down
```

## Деплой на сервер (Orange Pi и др.)

**На сервере (Или на рабочей машине, но в случае с ARM есть нюанс ниже)** — сборка и экспорт образа:

```bash
./git_pull.sh 0.0.6
```

Создаётся файл `bot-home_0.0.6.tar`. Или какую вы там версию в аргументе дадите.

**Тож На сервере** — в каталоге проекта с заполненным `.env`:

```bash
./deploy.sh 0.0.6
```

Скрипт загрузит образ, обновит `TAG` в `.env` и запустит `docker compose up -d`.

> На **ARM** (Orange Pi) образ нужно собирать на самой плате или через `docker buildx build --platform linux/arm64`.

## Структура проекта

```
app/
  main.py              # точка входа
  settings.py          # конфигурация из .env
  commands/common.py   # обработчики команд
  services/rss_parser.py
  logger.py
git_pull.sh            # сборка образа
deploy.sh              # деплой на сервер
docker-compose.yml
```
