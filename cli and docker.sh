sudo apt update -y
sudo apt upgrade -y
sudo apt install -y curl unzip
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version



sudo apt update -y
sudo apt install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker
docker --version
sudo usermod -aG docker $USER
newgrp docker

docker run -d --name nginx-server -p 8000:80 nginx:latest

 docker exec -it b060 bash

 docker logs -f nginx-server

 sed -i 's/Welcome to nginx!/Welcome to Learning Devops with Kandasamy Murugan !/g' /path/to/index.html

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 205930609030.dkr.ecr.us-east-1.amazonaws.com
docker build -t ecs-ecr-repo .
docker tag ecs-ecr-repo:latest 205930609030.dkr.ecr.us-east-1.amazonaws.com/ecs-ecr-repo:latest
docker push 205930609030.dkr.ecr.us-east-1.amazonaws.com/ecs-ecr-repo:latest


{
  "requiresCompatibilities": [
    "EC2"
  ],
  "containerDefinitions": [
    {
      "name": "ecs-ecr",
      "image": "205930609030.dkr.ecr.us-east-1.amazonaws.com/ecs-ecr-repo:latest",
      "memory": 256,
      "cpu": 256,
      "essential": true,
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
          "logDriver": "awslogs",
          "options": {
              "awslogs-group": "awslogs-nginx-ecs",
              "awslogs-region": "us-east-1",
              "awslogs-stream-prefix": "nginx"
          }
      }
    }
  ],
  "volumes": [],
  "networkMode": "bridge",
  "placementConstraints": [],
  "family": "ecs-ecr"
}