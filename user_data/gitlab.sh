#!/bin/bash

# Update
echo "Update..."
echo "================================"
apt update

# Mount EBS
echo "Mount..."
echo "================================"
mkfs -t ext4 /dev/nvme1n1
mkdir /var/opt/gitlab
mount /dev/nvme1n1 /var/opt/gitlab
echo "/dev/nvme1n1 /var/opt/gitlab ext4 defaults,discard 0 1" >>/etc/fstab

# GitLab CE
echo "Install GitLab..."
echo "================================"
curl https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce/script.deb.sh -o /tmp/script.deb.sh
bash /tmp/script.deb.sh
apt install gitlab-ce

# Upgrade
echo "Upgrade..."
echo "================================"
apt update
apt upgrade -y

# Start
echo "Reconfigure..."
echo "================================"
gitlab-ctl reconfigure
gitlab-ctl restart
