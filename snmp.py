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
        self._build_auth_object()

    def snmp_connect(self, oid):
        gen = getCmd(
            SnmpEngine(),
            self.auth_object,
            UdpTransportTarget((self.device["host"], self.device["port"])),
            ContextData(),
            ObjectType(ObjectIdentity(oid)))
        return next(gen)

    def snmp_connect_bulk(self, oids):
        non_repeaters = 0
        max_repetitions = 25

        if (isinstance(oids, str)):
            oid_object = [ObjectType(ObjectIdentity(oids))]
        elif (isinstance(oids, tuple)):
            oid_object = [ObjectType(ObjectIdentity(*oids))]
        elif(isinstance(oids, list)):
            #oid_object = [ObjectType(ObjectIdentity(oid)) for oid in oids]
            oid_object = [ObjectType(ObjectIdentity(*oid)) for oid in oids]

        gen = bulkCmd(
            SnmpEngine(),
            self.auth_object,
            UdpTransportTarget((self.device["host"], self.device["port"])),
            ContextData(),
            non_repeaters,
            max_repetitions,             
            *oid_object,
            lexicographicMode=False)

        return gen

    def _build_auth_object(self):
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

    oids = [
        ('HOST-RESOURCES-MIB', 'hrProcessorLoad'),
        ('IF-MIB', 'ifInOctets')
    ]

    poller = Poller(device, authentication)
    gen = poller.snmp_connect_bulk(oids)

    for item in gen:
        errorIndication, errorStatus, errorIndex, varBinds = item
        
        if errorIndication:
            print(errorIndication)
        elif errorStatus:
            print('%s at %s' % (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        else:
            for varBind in varBinds:
                print(' = '.join([x.prettyPrint() for x in varBind]))

if __name__ == '__main__':
    test_poller()
