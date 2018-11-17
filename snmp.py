from pysnmp.hlapi import *

class Poller():
    device = {}
    authentication = {}
    auth_object = None

    auth_protocols = {
        'md5': usmHMACMD5AuthProtocol,
        'sha': usmHMACSHAAuthProtocol,
        'sha224': usmHMAC128SHA224AuthProtocol,
        'sha256': usmHMAC192SHA256AuthProtocol,
        'sha384': usmHMAC256SHA384AuthProtocol,
        'sha512': usmHMAC384SHA512AuthProtocol,
        'noauth': usmNoAuthProtocol
    }

    priv_protocols = {
        'des': usmDESPrivProtocol,
        '3des': usm3DESEDEPrivProtocol,
        'aes': usmAesCfb128Protocol,
        'aes192': usmAesCfb192Protocol,
        'aes256': usmAesCfb256Protocol,
        'nopriv': usmNoPrivProtocol
    }

    def __init__(self, device, authentication):
        self.authentication = authentication
        self.device = device
        self.__build_auth_object()

    def snmp_connect(self, oid):
        iter = getCmd(SnmpEngine(),
            self.auth_object,
            UdpTransportTarget((self.device["host"], self.device["port"])),
            ContextData(),
            ObjectType(ObjectIdentity(oid)))
        return next(iter)

    def __build_auth_object(self):
        authentication = self.authentication
        if (authentication["version"] == 3):
            self.auth_object = UsmUserData(
                authentication["user"],
                authentication["auth"]["key"],
                authentication["priv"]["key"],
                self.auth_protocols.get(authentication["auth"]["protocol"], None),
                self.priv_protocols.get(authentication["priv"]["protocol"], None))
        elif(authentication["version"] == 2):
            self.auth_object = CommunityData(authentication["user"], mpModel=1)
        elif(authentication["version"] == 1):
            self.auth_object = CommunityData(authentication["user"], mpModel=0)

def test_poller():
    device = {
        "host":"demo.snmplabs.com",
        "port": 161
    }

    authentication = {
        "version": 2,
        "user": "public",
        "auth": {
            "protocol": None,
            "key": None
        },
        "priv": {
            "protocol": None,
            "key": None
        }
    }

    poller = Poller(device, authentication)
    oid = "1.3.6.1.2.1.1.1.0"
    value = poller.snmp_connect(oid)
    print(value)

if __name__ == '__main__':
    test_poller()
