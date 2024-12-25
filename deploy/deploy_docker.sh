set -ex

source config.sh

cd $(dirname "$0")/..

docker build -t "$image_name" .
docker tag "${image_name}:latest" "$image_uri"
docker push "$image_uri"