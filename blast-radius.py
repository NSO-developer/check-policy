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
    'xpath': '/devices/device',
    'dependency': '/devices/device',
    'warning_level': 2,  # WARNING or ERROR
    'error_level': 3,  # WARNING or ERROR
    'warning_msg': 'To many devices in transaction(max 2)!',
    'error_msg': 'Far to many devices in transaction(max 3)!'
}


OPER = {
    1: 'MOP_CREATED',
    2: 'MOP_DELETED',
    3: 'MOP_MODIFIED',
    4: 'MOP_VALUE_SET',
    5: 'MOP_MOVED_AFTER',
    6: 'MOP_ATTR_SET'
}

class DiffIterator(object):
    def __init__(self):
        self.count = 0
        self.answers = []
        self.devices = set()

    def __call__(self, kp, op, oldv, newv):
        self.count += 1
        self.answers.append([str(kp)])
        keypath = str(kp)
        values = keypath.split('}')
        if len(values) == 2 and values[1] == '' and keypath.startswith('/ncs:devices/device'):
            device = keypath.split('{')
            self.devices.add(device[1])
        return ncs.ITER_RECURSE


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
            2 - error message   is printed on stdout
            """)
    sys.exit(1)

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
                CONFIG.get('warning_msg') or not\
                CONFIG.get('error_msg'):
            usage_and_exit()
        else:
            xpath = CONFIG.get('xpath')
            dependency = CONFIG.get('dependency')
            exitstatus = CONFIG.get('exitstatus')
            warning_msg = CONFIG.get('warning_msg')
            error_msg = CONFIG.get('error_msg')

        m = ncs.maapi.Maapi()
        keypath = m.xpath2kpath(xpath)
        if ar.policy:
            print("""
                  begin policy
                        keypath: {}
                        dependency: {}
                        priority: 2
                        call: each
                  end
                  """.format(keypath, dependency))
            sys.exit(0)

        if not ar.keypath:
            print("<ERROR> --value <value> - leaf value omitted")
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

        devices_in_trans = 0

        # Get the values from the current transaction
        with m.attach(ctx_or_th=NCS_MAAPI_THANDLE, usid=NCS_MAAPI_USID) as t:
            iterator = DiffIterator()
            t.diff_iterate(iterator, ncs.ITER_WANT_ATTR)
            devices_in_trans = len(iterator.devices)
            logging.info('Number of devices in transaction: ' + str(devices_in_trans))

        # Exit with warning or error?
        if CONFIG.get('error_level') > devices_in_trans >= CONFIG.get('warning_level'):
            print(CONFIG.get('warning_msg'))
            sys.exit(1)
        elif devices_in_trans >= CONFIG.get('error_level'):
            print(CONFIG.get('error_msg'))
            sys.exit(2)
        sys.exit(0)
