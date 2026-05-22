#!/bin/bash
# ============================================================
# Attribly — автоматический деплой на сервер
# Запуск: bash deploy.sh
# ============================================================
set -e

SERVER="85.239.61.39"
SSH_PORT="2222"
USER="root"
PASS='tVBR_S3vFJ#m7k'
KEY="$HOME/.ssh/id_attribly"
REMOTE_DIR="/opt/attribly"
DOMAIN="atributle.ru"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${GREEN}[✓]${NC} $1"; }
warning() { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; exit 1; }
step()    { echo -e "\n${YELLOW}══════════════════════════════════════${NC}"; echo -e "${YELLOW}  $1${NC}"; echo -e "${YELLOW}══════════════════════════════════════${NC}"; }

# SSH / SCP функции (пробуем ключ, затем пароль)
SSH() { ssh -o StrictHostKeyChecking=no -o ConnectTimeout=20 -i "$KEY" -p "$SSH_PORT" "${USER}@${SERVER}" "$@"; }
SCP() { scp -o StrictHostKeyChecking=no -i "$KEY" -P "$SSH_PORT" "$@"; }
RSYNC() {
    rsync -avz --progress \
        --exclude 'node_modules' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '.git' \
        --exclude 'dist' \
        --exclude '.vite' \
        --exclude '*.log' \
        -e "ssh -o StrictHostKeyChecking=no -i $KEY -p $SSH_PORT" \
        "$@"
}

# ── 0. Проверка SSH ──────────────────────────────────────────
step "Проверка SSH-соединения (порт $SSH_PORT)"
if SSH 'echo ok' &>/dev/null; then
    info "SSH по ключу работает"
elif command -v sshpass &>/dev/null && sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -p "$SSH_PORT" "${USER}@${SERVER}" 'echo ok' &>/dev/null; then
    info "SSH по паролю работает"
    SSH()   { sshpass -p "$PASS" ssh   -o StrictHostKeyChecking=no -p "$SSH_PORT" "${USER}@${SERVER}" "$@"; }
    SCP()   { sshpass -p "$PASS" scp   -o StrictHostKeyChecking=no -P "$SSH_PORT" "$@"; }
    RSYNC() {
        rsync -avz --progress \
            --exclude 'node_modules' --exclude '__pycache__' --exclude '*.pyc' \
            --exclude '.git' --exclude 'dist' --exclude '.vite' --exclude '*.log' \
            -e "sshpass -p $PASS ssh -o StrictHostKeyChecking=no -p $SSH_PORT" \
            "$@"
    }
else
    error "Не удаётся подключиться. Проверь что порт $SSH_PORT открыт и ключ $KEY существует."
fi

# ── 1. Установка Docker ──────────────────────────────────────
step "Установка Docker"
SSH bash << 'ENDSSH'
set -e
if command -v docker &>/dev/null; then
    echo "Docker уже установлен: $(docker --version)"
else
    apt-get update -qq
    apt-get install -y -qq ca-certificates curl gnupg lsb-release
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable docker && systemctl start docker
    echo "Docker установлен: $(docker --version)"
fi
ENDSSH
info "Docker готов"

# ── 2. Генерация ключей ──────────────────────────────────────
step "Генерация секретных ключей"
SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || openssl rand -base64 32 | tr -d '\n=')
POSTGRES_PASS="Pg_$(openssl rand -hex 10)"
REDIS_PASS="Rd_$(openssl rand -hex 10)"
info "Ключи сгенерированы"

# ── 3. Создание папки и .env на сервере ─────────────────────
step "Создание конфигурации"
SSH "mkdir -p ${REMOTE_DIR}"
SSH "cat > ${REMOTE_DIR}/.env" << ENVEOF
APP_ENV=production
SECRET_KEY=${SECRET_KEY}
ENCRYPTION_KEY=${ENCRYPTION_KEY}
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=attribly
POSTGRES_USER=attribly
POSTGRES_PASSWORD=${POSTGRES_PASS}
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=${REDIS_PASS}
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_DB=attribly
CLICKHOUSE_USER=attribly
CLICKHOUSE_PASSWORD=dummy_not_used
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_CLICKS=attribly.clicks
KAFKA_TOPIC_ORDERS=attribly.orders
KAFKA_TOPIC_EVENTS=attribly.events
KAFKA_GROUP_ID=etl-consumer
CELERY_BROKER_URL=memory://
CELERY_RESULT_BACKEND=cache+memory://
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioaccess
MINIO_SECRET_KEY=miniosecret
MINIO_BUCKET=attribly-reports
MINIO_BUCKET_RAW=attribly-raw
MINIO_BUCKET_PROCESSED=attribly-processed
MINIO_SECURE=false
MINIO_PRESIGNED_TTL=3600
SEGMENT_QUEUE_KEY=queue:segment_jobs
WORKER_POLL_INTERVAL=2.0
NOTIFICATIONS_CHANNEL=notifications
BATCH_SIZE=500
FLUSH_INTERVAL=5.0
MODELS_DIR=/tmp/attribly-models
GRAFANA_PASSWORD=testpass
SENTRY_DSN=
ENVEOF
info ".env создан"

# ── 4. Копирование проекта ───────────────────────────────────
step "Копирование проекта на сервер (3-7 мин)"
RSYNC "${LOCAL_DIR}/" "${USER}@${SERVER}:${REMOTE_DIR}/"
# Копируем .env поверх (rsync мог перезаписать)
SSH "cat > ${REMOTE_DIR}/.env" << ENVEOF
APP_ENV=production
SECRET_KEY=${SECRET_KEY}
ENCRYPTION_KEY=${ENCRYPTION_KEY}
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=attribly
POSTGRES_USER=attribly
POSTGRES_PASSWORD=${POSTGRES_PASS}
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=${REDIS_PASS}
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_DB=attribly
CLICKHOUSE_USER=attribly
CLICKHOUSE_PASSWORD=dummy_not_used
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_CLICKS=attribly.clicks
KAFKA_TOPIC_ORDERS=attribly.orders
KAFKA_TOPIC_EVENTS=attribly.events
KAFKA_GROUP_ID=etl-consumer
CELERY_BROKER_URL=memory://
CELERY_RESULT_BACKEND=cache+memory://
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioaccess
MINIO_SECRET_KEY=miniosecret
MINIO_BUCKET=attribly-reports
MINIO_BUCKET_RAW=attribly-raw
MINIO_BUCKET_PROCESSED=attribly-processed
MINIO_SECURE=false
MINIO_PRESIGNED_TTL=3600
SEGMENT_QUEUE_KEY=queue:segment_jobs
WORKER_POLL_INTERVAL=2.0
NOTIFICATIONS_CHANNEL=notifications
BATCH_SIZE=500
FLUSH_INTERVAL=5.0
MODELS_DIR=/tmp/attribly-models
GRAFANA_PASSWORD=testpass
SENTRY_DSN=
ENVEOF
info "Проект скопирован"

# ── 5. Запуск контейнеров ────────────────────────────────────
step "Запуск Docker Compose (первый раз 10-15 мин)"
SSH bash << ENDSSH
set -e
cd ${REMOTE_DIR}
docker compose -f docker-compose.test.yml pull 2>/dev/null || true
docker compose -f docker-compose.test.yml up -d --build
echo ""
echo "=== Статус контейнеров ==="
docker compose -f docker-compose.test.yml ps
ENDSSH
info "Контейнеры запущены"

# ── 6. Ждём готовности ───────────────────────────────────────
step "Проверка готовности (подождём 40 сек)"
sleep 40
SSH bash << 'ENDSSH'
cd /opt/attribly
echo "=== Контейнеры ==="
docker compose -f docker-compose.test.yml ps
echo ""
echo "=== Health check ==="
curl -sf http://localhost:8080/healthz && echo "nginx OK" || echo "nginx не готов"
curl -sf http://localhost:8000/health  && echo "api OK"   || echo "api не готов"
ENDSSH

# ── 7. SSL сертификат ────────────────────────────────────────
step "SSL сертификат для ${DOMAIN}"
warning "Для SSL домен ${DOMAIN} должен указывать на ${SERVER}"
read -r -p "DNS уже настроен? (y/n): " dns_ready

if [ "$dns_ready" = "y" ] || [ "$dns_ready" = "Y" ]; then
    SSH bash << ENDSSH
apt-get install -y -qq certbot
cd /opt/attribly
docker compose -f docker-compose.test.yml stop nginx
certbot certonly --standalone -d ${DOMAIN} -d www.${DOMAIN} \
    --non-interactive --agree-tos \
    --email admin@${DOMAIN} --no-eff-email
cp /etc/letsencrypt/live/${DOMAIN}/fullchain.pem /opt/attribly/infra/nginx/ssl/cert.pem
cp /etc/letsencrypt/live/${DOMAIN}/privkey.pem   /opt/attribly/infra/nginx/ssl/key.pem
docker compose -f docker-compose.test.yml start nginx
echo "SSL готов!"
ENDSSH
    info "SSL сертификат получен"
else
    warning "SSL пропущен. Запусти позже: bash deploy_ssl.sh"
fi

# ── Итог ─────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║       ДЕПЛОЙ ЗАВЕРШЁН УСПЕШНО! 🚀           ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  🌐 Сайт:    ${GREEN}http://${SERVER}:8080${NC}"
echo -e "  🌐 Домен:   ${GREEN}http://${DOMAIN}${NC}"
echo -e "  📖 API:     ${GREEN}http://${SERVER}:8080/docs${NC}"
echo ""
echo -e "  SSH на сервер:"
echo -e "  ${YELLOW}ssh -i ~/.ssh/id_attribly -p 2222 root@${SERVER}${NC}"
echo ""
echo -e "  Управление контейнерами:"
echo -e "  ${YELLOW}cd /opt/attribly && docker compose -f docker-compose.test.yml ps${NC}"
