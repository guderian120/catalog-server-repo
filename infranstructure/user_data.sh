#!/bin/bash
set -e
exec > >(tee -a /var/log/user-data.log) 2>&1
# Update packages and install Docker
apt-get update -y
apt-get install -y docker.io

# Start Docker service
systemctl start docker
systemctl enable docker

DB_NAME="${db_name}"
DB_USER="${db_user}"
DB_PASS="${db_password}"
DATABASE_URL="${db_url}"


# Pull Flask app Docker image (replace with your actual image if needed)

# Pull MySQL image
docker network create app-network
# Run MySQL container
docker run -d \
  --name mysql-container \
  --network app-network \
  -e MYSQL_ROOT_PASSWORD="$DB_PASS" \
  -e MYSQL_DATABASE= "$DB_NAME"\
  -e MYSQL_USER="$DB_USER"\
  -e MYSQL_PASSWORD="$DB_PASS"\
  -p 3306:3306 \
  mysql:5.7

# Run Flask container and link to MySQL (assuming your app connects to mysql-container:3306)
docker run -d \
  --name flask-app \
  --network app-network \
  -e DATABASE_URL="$DATABASE_URL" \
  -p 80:5000 \
  realamponsah/catalog-server
