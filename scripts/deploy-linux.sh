#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/mengkecloud"
DOMAIN="_"
INSTALL_DEPS="yes"
RUN_TESTS="no"

usage() {
  cat <<'EOF'
One-click deployment for MengKeCloud (Ubuntu/Debian)

Usage:
  sudo bash scripts/deploy-linux.sh [options]

Options:
  --project-dir <path>   Project directory (default: /opt/mengkecloud)
  --domain <domain|ip>   Nginx server_name (default: _)
  --install-deps <yes|no> Install apt dependencies (default: yes)
  --run-tests <yes|no>   Run pytest before deploy (default: no)
  -h, --help             Show this help

Required:
  1) Repository code must already exist in project-dir
  2) .env file must exist at <project-dir>/.env
  3) .env must include production DB/JWT settings
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-dir)
      PROJECT_DIR="$2"
      shift 2
      ;;
    --domain)
      DOMAIN="$2"
      shift 2
      ;;
    --install-deps)
      INSTALL_DEPS="$2"
      shift 2
      ;;
    --run-tests)
      RUN_TESTS="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root: sudo bash scripts/deploy-linux.sh"
  exit 1
fi

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "Project directory not found: $PROJECT_DIR"
  exit 1
fi

if [[ ! -f "$PROJECT_DIR/.env" ]]; then
  echo "Missing env file: $PROJECT_DIR/.env"
  echo "Copy scripts/.env.production.example to .env and fill it first."
  exit 1
fi

if [[ "$INSTALL_DEPS" == "yes" ]]; then
  echo "[1/9] Installing system dependencies..."
  apt-get update
  apt-get install -y git nginx postgresql postgresql-contrib python3 python3-venv python3-pip curl
  if ! command -v node >/dev/null 2>&1; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
  fi
fi

echo "[2/9] Preparing backend virtualenv..."
cd "$PROJECT_DIR"
python3 -m venv .venv
"$PROJECT_DIR/.venv/bin/pip" install -U pip
"$PROJECT_DIR/.venv/bin/pip" install -r requirements-backend.txt

echo "[3/9] Installing frontend dependencies..."
if [[ -f "$PROJECT_DIR/package-lock.json" ]]; then
  npm ci
else
  npm install
fi

if [[ "$RUN_TESTS" == "yes" ]]; then
  echo "[4/9] Running backend tests..."
  "$PROJECT_DIR/.venv/bin/pytest" -q
else
  echo "[4/9] Skipping tests (--run-tests no)"
fi

echo "[5/9] Building frontend..."
npm run build

echo "[6/9] Applying DB migrations..."
set -a
# shellcheck disable=SC1090
source "$PROJECT_DIR/.env"
set +a
"$PROJECT_DIR/.venv/bin/alembic" upgrade head

echo "[7/9] Bootstrapping admin account..."
"$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/scripts/bootstrap-admin.py"

echo "[8/9] Writing systemd service..."
cat > /etc/systemd/system/mengke-api.service <<EOF
[Unit]
Description=MengKeCloud API
After=network.target

[Service]
Type=simple
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now mengke-api
systemctl restart mengke-api

echo "[9/9] Writing nginx site config..."
cat > /etc/nginx/sites-available/mengkecloud <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    root $PROJECT_DIR/dist;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location / {
        try_files \$uri /index.html;
    }
}
EOF

ln -sfn /etc/nginx/sites-available/mengkecloud /etc/nginx/sites-enabled/mengkecloud
nginx -t
systemctl enable --now nginx
systemctl reload nginx

echo "Deployment completed."
echo "API service status:"
systemctl --no-pager --full status mengke-api | sed -n '1,15p'
echo
echo "Migration status:"
"$PROJECT_DIR/.venv/bin/alembic" current
echo
echo "Health check:"
curl -sS http://127.0.0.1:8001/health || true
echo
echo "Access URL: http://$DOMAIN/"
echo "Admin phone: ${MENGKE_BOOTSTRAP_ADMIN_PHONE:-13800000001}"
echo "Admin password: ${MENGKE_BOOTSTRAP_ADMIN_PASSWORD:-ChangeMe123!}"
echo "Notice: first login requires password change"
