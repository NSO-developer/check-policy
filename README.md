# check-policy
## NSO Python Policy Script

This policy script lets you put a safe guard on leafs so that you can warn a user that changing that leaf might be a bad idea. With normal policy rules you can only set true/false rules.

To use it copy it to your NSO runtime script/policy folder (you might have to create the folder) and then open the check-policy.py file in you favourite editor and modify the CONFIG part to you likings
```
CONFIG = {
    'xpath': '/vpn/l3vpn/endpoint/as-number',
    'dependency': '/vpn/l3vpn/endpoint/',
    'exitstatus': 'WARNING',  # WARNING or ERROR
    'warningmsg': 'Are you sure you want to change the BGP AS number? Doing so might disconnect the management interface!',
    'errormsg': 'You are not allowed to change the BGP AS number, doing so will disconnect the management interface!'
}
```
then from the cli reload the scripts

```
ncs_cli -u admin

admin connected from 127.0.0.1 using console on HNISKA-M-H455
admin@ncs> script reload
/Users/hniska/ncs-release/5.1.1/examples.ncs/service-provider/mpls-vpn/scripts: ok
    policy:
        check-policy.py: new
```

The CONFIGs in the script works with the examples.ncs/service-provider/mpls-vpn example.
```
admin@ncs% show vpn
l3vpn volvo {
    route-distinguisher 999;
    endpoint branch-office1 {
        ce-device    ce1;
        ce-interface GigabitEthernet0/11;
        ip-network   10.7.7.0/24;
        bandwidth    6000000;
        as-number    244;
    }
    endpoint branch-office2 {
        ce-device    ce4;
        ce-interface GigabitEthernet0/18;
        ip-network   10.8.8.0/24;
        bandwidth    30000;
        as-number    65103;
    }
    endpoint main-office {
        ce-device    ce6;
        ce-interface GigabitEthernet0/11;
        ip-network   10.10.1.0/24;
        bandwidth    12000000;
        as-number    65101;
    }
}
[ok][2019-06-14 12:49:53]

[edit]
admin@ncs% set vpn l3vpn volvo endpoint branch-office2 as-number 8482
[ok][2019-06-14 12:50:02]

[edit]
admin@ncs% commit
The following warnings were generated:
  'vpn l3vpn volvo endpoint branch-office2 as-number': Are you sure you want to change the BGP AS number? Doing so might disconnect the management
interface!
Proceed? [yes,no]

```
### About policy scripts

Policy scripts are invoked at validation time, before a change is committed. A policy script can reject the data, accept it, or accept it with a warning. If a warning is produced, it will be displayed for interactive users (e.g. through the CLI or Web UI). The user may choose to abort or continue to commit the transaction.

Policy scripts are typically assigned to individual leafs or containers. In some cases it may be feasible to use a single policy script, e.g. on the top level node of the configuration. In such a case, this script is responsible for the validation of all values and their relationships throughout the configuration.

All policy scripts are invoked on every configuration change. The policy scripts can be configured
to depend on certain subtrees of the configuration, which can save time but it is very important that all dependencies are stated and also updated when the validation logic of the policy script is updated. Otherwise an update may be accepted even though a dependency should have denied it.

### Contact

Contact Hakan Niska hniska@cisco.com with any suggestions or comments. If you find any bugs please fix them and send me a pull request.
