set -ex

source config.sh

cd ..

ssh -i "$pem_path" ec2-user@"$ip_address" "mkdir -p $server_project_dir"
scp -i "$pem_path" .env docker-compose.yml deploy/restart_docker_compose.sh ec2-user@"$ip_address":"$server_project_dir/"

ssh -i "$pem_path" ec2-user@"$ip_address" "cd $server_project_dir && sudo sh ./restart_docker_compose.sh"