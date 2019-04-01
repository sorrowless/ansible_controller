sbog.controller
===============

Base framework to create further Ansible deploys for organization. It's nothing
more but just a carcass to further developing deployments.

#### Requirements

Ansible Galaxy

#### Dependencies

None

#### Base usage

This will install all needed roles to `roles` directory:

```
./tools/get-roles.sh
```

Then you just need to create according group/host vars, inventory files and run
your playbooks. Some examples can be found in `host_vars/.examples` directory.
In case you want to faster deploys there is a playbook which downloads mitogen
and installed it locally and configures as default strategy. You can run it by

```
ansible-playbook tools/switch-to-mitogen.yml
```

#### License

Apache 2.0

#### Author Information

Stanislaw Bogatkin (https://sbog.ru)
