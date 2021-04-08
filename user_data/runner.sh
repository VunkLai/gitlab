#!/bin/bash

# Update
echo "Update..."
echo "================================"
apt update

# Runner
echo "Install Runner..."
echo "================================"
apt install -y docker.io

docker run -d --restart always \
    --name gitlab-runner-1 \
    --volume /srv/gitlab-runner/1/config:/etc/gitlab-runner \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    gitlab/gitlab-runner:latest

docker run -d --restart always \
    --name gitlab-runner-2 \
    --volume /srv/gitlab-runner/2/config:/etc/gitlab-runner \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    gitlab/gitlab-runner:latest

# Upgrade
echo "Upgrade..."
echo "================================"
apt update
apt upgrade -y
