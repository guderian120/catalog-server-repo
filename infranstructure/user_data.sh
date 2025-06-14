#!/bin/bash
set -e
exec > >(tee -a /var/log/user-data.log) 2>&1

# --- Update and install Docker & Docker Compose ---
apt-get update -y
apt-get install -y \
    docker.io \
    git \
    curl

# Enable Docker service
systemctl start docker
systemctl enable docker

# Install Docker Compose (v2 plugin-style)
DOCKER_COMPOSE_VERSION="v2.24.2"
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.24.2/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Set environment variables (replace with actual values if you want)
DB_NAME="${db_name}"
DB_USER="${db_user}"
DB_PASS="${db_password}"
DATABASE_URL="${db_url}"
jwt_secret_key="${jwt_secret_key}"

# --- Clone your app code from GitHub ---
cd /home/ubuntu
git clone https://github.com/guderian120/catalog-server-repo.git
cd catalog-server-repo

# (Optional) Inject .env file if used
cat <<EOF > .env
DATABASE_URL="$DATABASE_URL"
JWT_SECRET_KEY="$jwt_secret_key"
EOF

# --- Build and run using Docker Compose ---
docker compose up -d
