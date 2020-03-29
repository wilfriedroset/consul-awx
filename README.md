# Consul inventory source for AWX/Tower

Aims to provide an inventory script for
[AWX/Tower](https://docs.ansible.com/ansible-tower/latest/html/userguide/inventories.html)
as first target but also usable by vanilla Ansible with Consul catalog as data
source.

Standalone Ansible inventory scripts can rely on INI configuration file where
AWX/Tower rely only on environment variables. All data are pulled from the catalog
API.

## Usage

### AWX
Simply add this script as inventory within AWX/Tower following the [official
documentation](https://docs.ansible.com/ansible-tower/latest/html/userguide/inventories.html).

### Standalone Ansible
Following [Working with dynamic inventory](https://docs.ansible.com/ansible/latest/user_guide/intro_dynamic_inventory.html) documentation, the simplest method to use this script as inventory is the implicit method:

```
wget https://raw.githubusercontent.com/wilfriedroset/consul-awx/master/consul_awx.py -o /etc/ansible/hosts
chmod +x /etc/ansible/hosts
# Configure it
cat << EOF > /etc/ansible/consul_awx.ini
[consul]
host: 127.0.0.1
port: 8500
scheme: http
verify: true
EOF
# Test it
/etc/ansible/hosts --list
```

## Credits

This script was mostly inspired by [consul_io.py](https://github.com/ansible/ansible/tree/devel/contrib/inventory)
