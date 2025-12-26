# Due to wiping and regenerating ssh keys on the lab devices, we need to refresh the known_hosts file

#!/bin/bash


ssh-keygen -R 192.168.150.203
ssh-keyscan -H 192.168.150.203 >> ~/.ssh/known_hosts

ssh-keygen -R 192.168.150.204
ssh-keyscan -H 192.168.150.204 >> ~/.ssh/known_hosts

