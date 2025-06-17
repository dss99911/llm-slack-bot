set -ex

cd $(dirname "$0")/..
source deploy/config.sh

docker build -t "$image_name" .
docker tag "${image_name}:latest" "$image_uri"
docker push "$image_uri"