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

echo "=== Шаг 1/2: git pull и сборка образа ==="
"${SCRIPT_DIR}/git_pull.sh" "${VERSION}"

echo ""
echo "=== Шаг 2/2: деплой ==="
"${SCRIPT_DIR}/deploy.sh" "${VERSION}"

echo ""
echo "pull_deploy версии ${VERSION} успешно завершён!"
