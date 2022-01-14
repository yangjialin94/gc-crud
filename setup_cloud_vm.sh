#!/bin/bash
set -e
set -x

################################################################################
#
# Overview:
#
# This script sets up a Google Compute Engine instance to run docker optimized
# for SAP. The main feature here is that we use a "Local SSD" as block storage
# for docker since need to use docker's "devicemapper" storage driver (needed
# becase SAP has huge files for its DB and we need block-level copy-on-write
# semantics instead of the default file-level semantics that comes with docker's
# default "overlay2" storage engine.
#
# Note that this is pretty similar to Google's provided solution for running a
# docker container in a Compute Engine instance, but we weren't able to make the
# necessary configuration changes for docker (i.e. the storage engine), so we
# had to do this ourselves.
#
# This could be expanded to run multiple containers. Most of the work is in
# setting up docker, and at the end we just "docker pull" and "docker run" one
# image.
#
# Note that we benchmarked various configurations and found out some interesting
# things. We measured how long it took to download and extract an image that
# started out as a 47GB download and was 130GB after extraction.
#
# * The speed of the storage docker uses to download images can be a bottleneck,
#   and it lives at "/var/lib/docker/tmp". We addressed this by putting it onto
#   a Local SSD.
#
# * Using multiple Local SSDs in a RAID0 configuration did not speed up extract
#   phase at all. It seems like the bottleneck becomes the CPU with storage
#   running around ~190MB/s (the documentation says an SSD can do 660MB/s read
#   and 350MB/s write, and this seems accurate).
#   https://cloud.google.com/compute/docs/disks/local-ssd#performance
#
# * I was able to speed up the docker extract stage by installing a parallel
#   gzip implementation "pigz". When extracting, docker checks to see if this is
#   installed and uses it if so -- all we have to do is install it and it will
#   get used.
################################################################################

# Variables
# ------------------------------------------------------------------------------

# Path to the Local SSD that we will use for docker's devicemapper storage, and
# also as fast storage for docker image downloads:
LVM_DEVICE="/dev/disk/by-id/google-local-nvme-ssd-0"

# Pre-install status script
# ------------------------------------------------------------------------------

# Disable extraneous MOTD scripts
sudo chmod -x /etc/update-motd.d/*

# Re-enable useful MOTD scripts
sudo chmod +x /etc/update-motd.d/00-header
sudo chmod +x /etc/update-motd.d/50-landscape-sysinfo

# Create a temporary MOTD script before installation has completed:
sudo cat <<'EOF' | sudo tee /etc/update-motd.d/60-instance-status
#!/bin/bash

RED='\033[91m'
END='\033[0m'

echo ""
echo -e "${RED}Setup is not complete!${END} If it's been more than a reasonable amount of time since this VM was created, check the output of this command:\n"
echo "> sudo journalctl -u google-startup-scripts.service"
echo ""
echo "Otherwise, log out and log back in in a few minutes."
echo ""
EOF

sudo chmod +x /etc/update-motd.d/60-instance-status

# Install dependencies
# ------------------------------------------------------------------------------

# Add tailscale apt repository
curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/bionic.gpg | sudo apt-key add -
curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/bionic.list | sudo tee /etc/apt/sources.list.d/tailscale.list

# Install required packages
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  lvm2 \
  thin-provisioning-tools \
  containerd=1.5.2-0ubuntu1~18.04.3 \
  pigz \
  members \
  tailscale

# Install latest docker-compose
VERSION=$(curl --silent https://api.github.com/repos/docker/compose/releases/latest | grep -Po '"tag_name": "\K.*\d')
echo VERSION=$VERSION
DESTINATION=/usr/local/bin/docker-compose
sudo curl -L https://github.com/docker/compose/releases/download/${VERSION}/docker-compose-$(uname -s)-$(uname -m) -o $DESTINATION
sudo chmod 755 $DESTINATION

# Install cloud monitoring agent
curl -sSO https://dl.google.com/cloudagents/add-monitoring-agent-repo.sh
sudo bash add-monitoring-agent-repo.sh --also-install
sudo service stackdriver-agent start

# Set up docker and devicemapper
# ------------------------------------------------------------------------------

# LVM Setup:
sudo pvcreate "${LVM_DEVICE}"
sudo vgcreate docker "${LVM_DEVICE}"

# Create one volume for docker image downloads and two for docker's thinpool.
# This is a percentage of 375GB. The rest of 95% of the disk goes to docker's
# thinpool.
TOTAL_PCT=95
IMAGES_PCT=15
DOCKER_PCT=$((${TOTAL_PCT} - ${IMAGES_PCT}))
if [[ $((((${DOCKER_PCT} * 375) / 100) < 200)) -eq 1 ]]; then
	echo "DOCKER_PCT=\"${DOCKER_PCT}\" would be < 200GB, too small!"
	exit 1
fi
sudo lvcreate --wipesignatures y -n images docker -l ${IMAGES_PCT}%VG
# Mount a tmp volume on the local SSD to hold downloaded container images:
sudo mkfs.ext4 /dev/docker/images
sudo mkdir -p /var/lib/docker/tmp
sudo mount -o discard,defaults,nobarrier /dev/docker/images /var/lib/docker/tmp

# Create two volumes for docker's thinpool and join them:
sudo lvcreate --wipesignatures y -n thinpool docker -l ${DOCKER_PCT}%VG
sudo lvcreate --wipesignatures y -n thinpoolmeta docker -l 1%VG
sudo lvconvert -y \
  --zero n \
  -c 512K \
  --thinpool docker/thinpool \
  --poolmetadata docker/thinpoolmeta

# Setup monitoring for the docker thinpool:
sudo cat <<'EOF' | sudo tee /etc/lvm/profile/docker-thinpool.profile
activation {
  thin_pool_autoextend_threshold=80
  thin_pool_autoextend_percent=20
}
EOF
sudo lvchange --metadataprofile docker-thinpool docker/thinpool
sudo lvchange --monitor y docker/thinpool
sudo lvs -o+seg_monitor

# Set up 4G of swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo "/swapfile swap swap defaults 0 0" | sudo tee -a /etc/fstab

# Configure docker to use the devicemapper storage driver:
sudo mkdir -p /etc/docker
sudo cat <<'EOF' | sudo tee /etc/docker/daemon.json
{
  "storage-driver": "devicemapper",
  "storage-opts": [
    "dm.thinpooldev=/dev/mapper/docker-thinpool",
    "dm.use_deferred_removal=true",
    "dm.use_deferred_deletion=true",
    "dm.basesize=200G"
  ]
}
EOF

# Install latest docker.io version

sudo apt-get install -y --no-install-recommends docker.io

# Enable docker
# ------------------------------------------------------------------------------

# Start docker:
sudo systemctl start docker

# Add users to docker group
for x in $(members google-sudoers); do
  # Add user to docker group:
  gpasswd -a "${x}" docker
  # Configure auth to our private Container Registry:
  sudo -u "${x}" gcloud -q auth configure-docker us.gcr.io
done

# Create status script
# ------------------------------------------------------------------------------

# Update the MOTD script to show docker status:
sudo cat <<'EOF' | sudo tee /etc/update-motd.d/60-instance-status
#!/usr/bin/python3
import subprocess

print('')

class AnsiColors:
    green = '\033[92m'
    red = '\033[91m'
    yellow = '\033[93m'
    end = '\033[0m'

# Check status of Docker
docker_ps_result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}\t{{.Ports}}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Success, docker is up
if docker_ps_result.returncode == 0:
    output = docker_ps_result.stdout.decode('utf-8').strip()
    if len(output) == 0:
        print(f"{AnsiColors.yellow}Docker is running with 0 containers{AnsiColors.end}\n")
    else:
        containers = output.split('\n')
        print(f"{AnsiColors.green}Docker is running with {len(containers)} container{'s' if len(containers) > 1 else ''}:{AnsiColors.end}\n")
        for container in containers:
            [name, running, ports] = container.split('\t')
            print(name)
            print('    ' + running)
            for port in ports.split(' '):
                print('    Port ' + port)
            print('')

# Failed, docker is down or not installed
else:
    print(f"{AnsiColors.red}Docker is not running!{AnsiColors.end} Try starting the service:\n")
    print("> sudo systemctl start docker")
    print('')

# Check status of Tailscale
tailscale_result = subprocess.run(['tailscale', 'status'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
tailscale_status = tailscale_result.stdout.decode('utf-8')

if ('Logged out' in tailscale_status) or ('is stopped' in tailscale_status):
    print(f"{AnsiColors.yellow}Tailscale is not connected!{AnsiColors.end} Run this command and follow the instructions:\n")
    print("> sudo tailscale up")
else:
    tailscale_ip_result = subprocess.run(['tailscale', 'ip'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    tailscale_ip = tailscale_ip_result.stdout.decode('utf-8').strip().split('\n')[0]
    hostname_result = subprocess.run(['hostname'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    hostname = hostname_result.stdout.decode('utf-8').strip().split('\n')[0]
    print(f"{AnsiColors.green}Tailscale for {hostname} is connected at {tailscale_ip}{AnsiColors.end}")

print('')
EOF
