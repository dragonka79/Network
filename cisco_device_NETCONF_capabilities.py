#!/usr/bin/env python
""" Get the capabilities of a remote device with NETCONF """

from ncclient import manager

NXOS_HOST = "192.168.150.201"
NETCONF_PORT = "830"
USERNAME = "admin"
PASSWORD = "admin"
# create a get_capabilities() method


def get_capabilities(save_path=f'netconf_capabilities_{NXOS_HOST}.txt'):
    """
    Method that prints NETCONF capabilities of remote device and saves them to a file.
    """
    with manager.connect(
        host=NXOS_HOST,
        port=int(NETCONF_PORT),
        username=USERNAME,
        password=PASSWORD,
        hostkey_verify=False
    ) as device:

        # print all NETCONF capabilities
        print('\n***NETCONF Capabilities for device {}***\n'.format(NXOS_HOST))
        capabilities = []
        for capability in device.server_capabilities:
            print(capability)
            capabilities.append(capability)

        # save capabilities to file
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as fh:
                for cap in capabilities:
                    fh.write(cap.rstrip() + '\n')
            print('\nCapabilities saved to: {}'.format(save_path))
        


if __name__ == '__main__':
    get_capabilities()