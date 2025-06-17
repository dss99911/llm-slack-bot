set -xe
FILE="$1"
docker-compose -f "$FILE" down
docker-compose -f "$FILE" pull
docker-compose -f "$FILE" up -d
docker image prune -a --force