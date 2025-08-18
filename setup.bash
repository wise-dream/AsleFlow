#!/usr/bin/env bash
# AsleFlow bootstrap: PostgreSQL + Redis + .env
# Run as root. No sudo used inside.

set -euo pipefail

### ---------- CONFIG (you can change defaults here) ----------
PROJECT_DIR="${PROJECT_DIR:-/opt/asleflow}"     # куда положить .env (если существует git-проект — укажи его путь)
APP_NAME="${APP_NAME:-AsleFlow}"

# PostgreSQL
PG_DB="${PG_DB:-asleflow}"
PG_USER="${PG_USER:-asleflow}"
PG_HOST="${PG_HOST:-127.0.0.1}"
PG_PORT="${PG_PORT:-5432}"

# Redis
REDIS_HOST="${REDIS_HOST:-127.0.0.1}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_DB="${REDIS_DB:-0}"

# .env
ENV_FILE="${ENV_FILE:-${PROJECT_DIR}/.env}"

# Дополнительные Python-пакеты/утилиты (можно выключить)
INSTALL_PY_STACK="${INSTALL_PY_STACK:-1}"   # 1=установить python3-venv,pip,libpq-dev и т.п.

### ---------- HELPERS ----------
rand_b64() { openssl rand -base64 "$1" | tr -d '\n'; }
ensure_dir() { mkdir -p "$1"; }
msg() { printf "\n=== %s ===\n" "$*"; }

require_root() {
  if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "Запусти скрипт от root (без sudo внутри)."; exit 1
  fi
}

detect_os() {
  if [ -f /etc/os-release ]; then . /etc/os-release; OS_ID="$ID"; else OS_ID=""; fi
  case "$OS_ID" in
    debian|ubuntu) PKG_MANAGER="apt";;
    *) echo "Поддержаны Debian/Ubuntu. Обнаружено: ${OS_ID:-unknown}. Останов."; exit 1;;
  esac
}

apt_install() {
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y --no-install-recommends "$@"
}

psql_exec() {
  local sql="$1"
  su - postgres -c "psql -v ON_ERROR_STOP=1 -Atqc \"$sql\""
}

file_backup() {
  local f="$1"
  if [ -f "$f" ] && [ ! -f "${f}.bak" ]; then cp -a "$f" "${f}.bak"; fi
}

### ---------- PRECHECK ----------
require_root
detect_os

### ---------- INSTALL PACKAGES ----------
msg "Установка PostgreSQL и Redis"
apt_install ca-certificates curl gnupg lsb-release
apt_install postgresql postgresql-contrib redis-server

if [ "$INSTALL_PY_STACK" = "1" ]; then
  msg "Установка Python окружения (venv/pip) и dev-заголовков"
  apt_install python3 python3-venv python3-pip build-essential pkg-config libpq-dev
fi

### ---------- ENABLE & START SERVICES ----------
msg "Включение и запуск сервисов"
systemctl enable postgresql
systemctl enable redis-server
systemctl restart postgresql
systemctl restart redis-server

### ---------- GENERATE SECRETS ----------
msg "Генерация секретов"
PG_PASSWORD="$(rand_b64 24)"
REDIS_PASSWORD="$(rand_b64 24)"
SECRET_KEY="$(rand_b64 32)"

### ---------- CONFIGURE POSTGRES ----------
msg "Настройка PostgreSQL: пользователь/БД"

# Создать пользователя, если нет
psql_exec "SELECT 1 FROM pg_roles WHERE rolname='${PG_USER}'" >/dev/null 2>&1 || \
  psql_exec "CREATE ROLE ${PG_USER} LOGIN PASSWORD '${PG_PASSWORD}';"

# Создать БД, если нет
psql_exec "SELECT 1 FROM pg_database WHERE datname='${PG_DB}'" >/dev/null 2>&1 || \
  psql_exec "CREATE DATABASE ${PG_DB} OWNER ${PG_USER};"

# Выдать права
psql_exec "ALTER DATABASE ${PG_DB} OWNER TO ${PG_USER};"
psql_exec "GRANT ALL PRIVILEGES ON DATABASE ${PG_DB} TO ${PG_USER};"

# Разрешить расширения (опционально)
psql_exec "ALTER ROLE ${PG_USER} IN DATABASE ${PG_DB} SET search_path TO public;"

### ---------- CONFIGURE REDIS ----------
msg "Настройка Redis: пароль и bind 127.0.0.1"

REDIS_CONF="/etc/redis/redis.conf"
file_backup "$REDIS_CONF"

# bind только 127.0.0.1
if grep -qE '^\s*bind\s' "$REDIS_CONF"; then
  sed -i 's/^\s*bind .*/bind 127.0.0.1/' "$REDIS_CONF"
else
  echo "bind 127.0.0.1" >> "$REDIS_CONF"
fi

# включить requirepass
if grep -qE '^\s*requirepass\s' "$REDIS_CONF"; then
  sed -i "s|^\s*requirepass .*|requirepass ${REDIS_PASSWORD}|" "$REDIS_CONF"
else
  echo "requirepass ${REDIS_PASSWORD}" >> "$REDIS_CONF"
fi

# supervised systemd (как правило уже так)
if grep -qE '^\s*supervised\s' "$REDIS_CONF"; then
  sed -i 's/^\s*supervised .*/supervised systemd/' "$REDIS_CONF"
else
  echo "supervised systemd" >> "$REDIS_CONF"
fi

systemctl restart redis-server

### ---------- PREPARE PROJECT DIR ----------
msg "Подготовка каталога проекта и .env"
ensure_dir "$PROJECT_DIR"

DATABASE_URL="postgresql+psycopg2://${PG_USER}:${PG_PASSWORD}@${PG_HOST}:${PG_PORT}/${PG_DB}"
REDIS_URL="redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}"

# Создаём .env
cat > "$ENV_FILE" <<EOF
# ====== ${APP_NAME} runtime env ======
APP_NAME=${APP_NAME}
APP_ENV=production
SECRET_KEY=${SECRET_KEY}

# Database
DATABASE_URL=${DATABASE_URL}

# Redis
REDIS_URL=${REDIS_URL}

# Adapters (пример — заполни своими ключами при необходимости)
TELEGRAM_BOT_TOKEN=
OPENAI_API_KEY=

# Logging
LOG_LEVEL=INFO

# Alembic (если используешь)
# SQLALCHEMY_DATABASE_URI дублируем на всякий случай для некоторых тулов
SQLALCHEMY_DATABASE_URI=${DATABASE_URL}
EOF

chmod 600 "$ENV_FILE"

### ---------- OPTIONAL: PYTHON VENV BOOTSTRAP ----------
if [ "$INSTALL_PY_STACK" = "1" ] && [ -d "$PROJECT_DIR" ]; then
  if [ ! -d "${PROJECT_DIR}/venv" ]; then
    msg "Создание Python venv"
    python3 -m venv "${PROJECT_DIR}/venv"
  fi
  # Установка зависимостей, если есть requirements.txt/pyproject
  if [ -f "${PROJECT_DIR}/requirements.txt" ]; then
    msg "Установка зависимостей из requirements.txt"
    "${PROJECT_DIR}/venv/bin/pip" install --upgrade pip wheel
    "${PROJECT_DIR}/venv/bin/pip" install -r "${PROJECT_DIR}/requirements.txt"
  fi
fi

### ---------- SUMMARY ----------
msg "Готово"
echo "PostgreSQL:"
echo "  DB:     ${PG_DB}"
echo "  USER:   ${PG_USER}"
echo "  PASS:   ${PG_PASSWORD}"
echo
echo "Redis:"
echo "  URL:    ${REDIS_URL}"
echo
echo ".env создан: ${ENV_FILE}"
echo "Проверь значения и дополни токены (Telegram/OpenAI и пр.)."
