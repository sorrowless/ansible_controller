How to implement monitoring
===========================

Basically you have to have master node with monitoring servers - prometheus,
alertmanager, victoriametrics, whatever else. And you have to have several
nodes to get information from. These nodes will set SSH reverse connection to
master and master will connect to them by connect to localhost. It means you
have to have master trust to slaves. ssh_trust configuration is placed on all
config because of that. Then there is an example of 3 nodes - one master and
two slaves with monitoring config. Look on all of them and create your own one
based on provided configuration. Hope this helps.
