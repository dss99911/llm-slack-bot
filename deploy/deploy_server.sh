set -ex

source config.sh

pem_path="set-your-pem-path"
ip_address="set-your-ip-address"
env_path="set-env-path-on-server"
ssh -i "$pem_path" ec2-user@"$ip_address" "sudo docker rm -f $image_name" || true
ssh -i "$pem_path" ec2-user@"$ip_address" "sudo docker run -d --restart unless-stopped -v $env_path:/opt/code/.env --name $image_name $image_uri"
