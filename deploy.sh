#!/bin/bash
set -euo pipefail

validate_version() {
    if [[ $1 =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        return 0
    fi
    return 1
}

if [ $# -eq 0 ]; then
    echo "Ошибка: Не указана версия"
    echo "Использование: $0 X.X.X"
    echo "Пример: $0 0.0.43"
    exit 1
fi

VERSION=$1

if ! validate_version "$VERSION"; then
    echo "Ошибка: Неверный формат версии '$VERSION'"
    echo "Версия должна быть в формате X.X.X (например, 0.0.43)"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ARCHIVE="bot-home_${VERSION}.tar"
ENV_FILE=".env"

if [ ! -f "${ENV_FILE}" ]; then
    echo "Ошибка: файл ${ENV_FILE} не найден"
    exit 1
fi

if [ ! -f "${ARCHIVE}" ]; then
    echo "Ошибка: архив ${ARCHIVE} не найден"
    exit 1
fi

if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
else
    COMPOSE="docker-compose"
fi

echo "Запуск деплоя версии ${VERSION}..."

echo "Останавливаем контейнеры..."
${COMPOSE} down

echo "Загружаем Docker-образ..."
docker load -i "${ARCHIVE}"

if grep -q '^TAG=' "${ENV_FILE}"; then
    sed -i "s/^TAG=.*/TAG=${VERSION}/" "${ENV_FILE}"
else
    echo "TAG=${VERSION}" >> "${ENV_FILE}"
fi

echo "Обновлён TAG=${VERSION} в ${ENV_FILE}"

echo "Запускаем контейнеры..."
${COMPOSE} up -d

echo "Деплой версии ${VERSION} успешно завершён!"
