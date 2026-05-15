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
    echo "Пример: $0 0.0.2"
    exit 1
fi

VERSION=$1

if ! validate_version "$VERSION"; then
    echo "Ошибка: Неверный формат версии '$VERSION'"
    echo "Версия должна быть в формате X.X.X (например, 0.0.2)"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

IMAGE="bot-home:${VERSION}"
ARCHIVE="bot-home_${VERSION}.tar"

echo "Обновление репозитория..."
git pull

echo "Сборка Docker-образа ${IMAGE}..."
docker build -t "${IMAGE}" .

echo "Сохранение образа в ${ARCHIVE}..."
docker save -o "${ARCHIVE}" "${IMAGE}"

echo "Сборка версии ${VERSION} завершена: ${ARCHIVE}"
