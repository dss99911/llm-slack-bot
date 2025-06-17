set -ex
cd $(dirname "$0")/..
sh deploy/deploy_docker.sh
sh deploy/deploy_server.sh