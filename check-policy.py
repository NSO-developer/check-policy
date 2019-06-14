#!/usr/bin/env python
import sys
import argparse
import os
import ncs
import logging


# xpath = is a path to a node in the configuration data tree.
# The policy script will be associated with this node. The path must be absolute.
#
# dependency = The dependency must be an absolute keypath.
# Multiple dependency settings can be declared. Default is /.
#
# exitstatus =
# WARNING When the outcome of the validation is dubious it is possible for the
# script to issue a warning message. The message is extracted from the script
# output on stdout. An interactive user has the possibility to choose to abort
# or continue to commit the transaction. Non-interactive users automatically
# vote for commit.
# ERROR When the validation fails it is possible for the script to issue an error
# message. The message is extracted from the script output on stdout.
# The transaction will be aborted.

CONFIG = {
    'xpath': '/vpn/l3vpn/endpoint/as-number',
    'dependency': '/vpn/l3vpn/endpoint/',
    'exitstatus': 'WARNING',  # WARNING or ERROR
    'warningmsg': 'Are you sure you want to change the BGP AS number? \
Doing so might disconnect the management interface!',
    'errormsg': 'You are not allowed to change the BGP AS number, \
doing so will disconnect the management interface!'
}


OPER = {
    1: 'MOP_CREATED',
    2: 'MOP_DELETED',
    3: 'MOP_MODIFIED',
    4: 'MOP_VALUE_SET',
    5: 'MOP_MOVED_AFTER',
    6: 'MOP_ATTR_SET'
}


def get_changes(th, xpath):
    answers = []

    def add_to_list(kp, v, answers=answers):
        answers.append([str(kp), str(v)])
    m.xpath_eval(th, xpath, add_to_list, None, '')
    return answers


def usage_and_exit():
    print("""Usage: $0 -h
       $0 --policy
       $0 --keypath <keypath> [--value <value>]

  -h                    display this help and exit
  --policy              display policy configuration and exit
  --keypath <keypath>   path to node
  --value <value>       value of leaf

Return codes:

  0 - ok
  1 - warning message is printed on stdout
  2 - error message   is printed on stdout""")
    sys.exit(1)


# def main(argv):
#     print("argv: " + str(argv))

if __name__ == '__main__':
    if len(sys.argv[1:]) == 0:
        usage_and_exit()
        exit
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument('--keypath', action='store', dest='keypath', help='path to node')
        parser.add_argument('--value', action='store', dest='value', help='value of leaf')
        parser.add_argument('--policy', action='store_true', dest='policy', help='display policy configuration and exit')
        ar = parser.parse_args()

        if not CONFIG.get('xpath') or not CONFIG.get('dependency') or not\
                CONFIG.get('exitstatus') or not CONFIG.get('warningmsg') or not\
                CONFIG.get('errormsg'):
            usage_and_exit()
        else:
            xpath = CONFIG.get('xpath')
            dependency = CONFIG.get('dependency')
            exitstatus = CONFIG.get('exitstatus')
            warningmsg = CONFIG.get('warningmsg')
            errormsg = CONFIG.get('errormsg')

        m = ncs.maapi.Maapi()
        keypath = m.xpath2kpath(xpath)

        if ar.policy:
            print("""begin policy
keypath: {}
dependency: {}
priority: 2
call: each
end""".format(keypath, dependency))
            sys.exit(0)

        if not ar.keypath:
            print("<ERROR> --value <value> - leaf value omitted")
            usage_and_exit()

        if not ar.value:
            print("<ERROR> --keypath <keypath> - path omitted")
            usage_and_exit()

        logging.basicConfig(filename='check-policy.log',
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)  # change to INFO or lower to enable debug logging
        logging.info("NCS_MAAPI_USID " + os.environ.get('NCS_MAAPI_USID'))
        logging.info("NCS_MAAPI_THANDLE " + os.environ.get('NCS_MAAPI_THANDLE'))

        NCS_MAAPI_USID = int(os.environ.get('NCS_MAAPI_USID'))
        NCS_MAAPI_THANDLE = int(os.environ.get('NCS_MAAPI_THANDLE'))

        m.set_user_session(NCS_MAAPI_USID)

        old_values = []
        new_values = []

        # Get the current value for the xpath
        with m.start_read_trans() as t:
            root = ncs.maagic.get_root(t)
            old_values = get_changes(t.th, xpath)
            logging.info('old value: ' + str(old_values))

        # Get the new value from the current transaction
        with m.attach(ctx_or_th=NCS_MAAPI_THANDLE, usid=NCS_MAAPI_USID) as t:
            new_values = get_changes(t.th, xpath)
            logging.info('new value: ' + str(new_values))

        old_set = set(map(tuple, old_values))
        new_set = set(map(tuple, new_values))
        diff = old_set.symmetric_difference(new_set)
        # Exit with warning or error?
        if diff:
            logging.info('diff: ' + str(diff))
            if exitstatus == 'WARNING':
                print(CONFIG.get('warningmsg'))
                #  for x in diff:
                #     print(x[0], x[1])
                sys.exit(1)
            elif exitstatus == 'ERROR':
                print(CONFIG.get('errormsg'))
                # for x in diff:
                #     print(x[0], x[1])
                sys.exit(2)
            else:
                print('Something went wrong, something went very, very wrong')
                sys.exit(2)
        sys.exit(0)




