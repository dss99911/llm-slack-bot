set -ex
cd $(dirname "$0")/..
sh deploy/deploy_docker.sh
sh deploy/restart_docker_compose.sh "docker-compose-local.yml"