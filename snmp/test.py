from host_resource_mib import HostResourceMIB
from if_mib import IFMIB
import configparser

def test_query():
   config = configparser.SafeConfigParser()
   config_path = './example.ini'
   config.read(config_path)

   device = _validate_device(config)
   authentication = _validate_authentication(config)

   hr_mib = HostResourceMIB(device, authentication)
   hr_mib.poll_metrics()

   #if_mib = IFMIB(device, authentication)
   #if_mib.poll_metrics()

def _validate_device(config):
    hostname = config.get('device','hostname')
    group_name = config.get('device', 'group')
    device_type = config.get('device', 'type')

    # Default port
    port = 161
    # If entered as 127.0.0.1:1234, extract the ip and the port
    split_host = hostname.split(":")
    if len(split_host) > 1:
        hostname = split_host[0]
        port = split_host[1]

    # Check inputs are valid...

    device = {
        "host": hostname,
        "port": int(port)
    }

    return device

def _validate_authentication(config):
    snmp_version = config.get('authentication', 'version')
    snmp_user = config.get('authentication', 'user')
    auth_protocol = config.get('authentication', 'auth_protocol', fallback=None)
    auth_key = config.get('authentication', 'auth_key', fallback=None)
    priv_protocol = config.get('authentication', 'priv_protocol', fallback=None)
    priv_key = config.get('authentication', 'priv_key', fallback=None)

    # Check inputs are valid...

    authentication = {
        "version": int(snmp_version),
        "user": snmp_user,
        "auth": {
            "protocol": auth_protocol,
            "key": auth_key
        },
        "priv": {
            "protocol": priv_protocol,
            "key": priv_key
        }
    }

    return authentication

if __name__ == '__main__':
    test_query()