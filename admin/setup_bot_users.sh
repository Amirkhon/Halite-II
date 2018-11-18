#!/usr/bin/env bash

set -e

NUM_BOTS=4

sudo chmod 544 /home/worker/fix_cgroups.sh

## No access to 10. addresses (which are our own servers)
## We are giving them general network access (to download dependencies)
sudo iptables -A OUTPUT -d 10.0.0.0/8 -m owner --uid-owner bot_compilation -j DROP
## Grant sudo access to the worker as this user.
sudo sh -c "echo \"worker ALL=(bot_compilation) NOPASSWD: ALL\" > /etc/sudoers.d/worker_bot_compilation"
## Grant sudo access to the cgroup fixer script as root.
sudo sh -c "echo \"worker ALL=(root) NOPASSWD: /home/worker/fix_cgroups.sh\" >> /etc/sudoers.d/worker_bot_compilation"
sudo chmod 0400 /etc/sudoers.d/worker_bot_compilation

## Create four users to isolate bots.
for i in $(seq 0 $((NUM_BOTS-1))); do
    USERNAME="bot_${i}"
    #sudo useradd -m -g bots ${USERNAME}
    ## Deny all network access to this user.
    sudo iptables -A OUTPUT -m owner --uid-owner ${USERNAME} -j DROP
    ## Grant sudo access to the worker.
    sudo sh -c "echo \"worker ALL=(${USERNAME}) NOPASSWD: ALL\" > /etc/sudoers.d/worker_${USERNAME}"
    sudo chmod 0400 /etc/sudoers.d/worker_${USERNAME}
    echo 'export PATH="$PATH:/usr/local/go/bin"' | sudo -iu ${USERNAME} tee -a /home/${USERNAME}/.profile
done

## Make sure iptables rules persist
sudo iptables-save | sudo tee /etc/iptables/rules.v4
sudo ip6tables-save | sudo tee /etc/iptables/rules.v6

## Make sure cgroups persist
cat <<EOF | sudo tee /etc/systemd/system/cgroups.service
[Unit]
Description=Recreate cgroups on startup

[Service]
Type=oneshot
ExecStart=/usr/sbin/cgconfigparser -l /etc/cgconfig.conf

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable cgroups.service