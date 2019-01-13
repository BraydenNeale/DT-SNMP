import logging
from pysnmp.hlapi import *

logger = logging.getLogger(__name__)

class Poller():
    """
    snmp.Poller
    This module wraps the pysnmp APIs to connect to a device

    Usage
    poller = Poller(device, authentication)
    gen = poller.snmp_connect_bulk(self.oids)

    You can then iterate through the generator:
    for item in gen:
        errorIndication, errorStatus, errorIndex, varBinds = item
    """
    
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

    def snmp_connect_bulk(self, oids):
        """
        Optimised get - supported with SNMPv2C
        Send a single getbulk request
        Supported inputs:
        String - e.g. 1.3.6.1.2.1.31.1.1.1
        Tuple - e.g. (IF-MIB, ifSpeed)
        List of Tuple - e.g. ([(IF-MIB,ifSpeed), (HOST-RESOURCES-MIB,cpu)])

        Recommended to only call with lists of OIDs from the same table
        Otherwise you can end up polling for End of MIB.
        """

        non_repeaters = 0 # pysnmp default
        max_repetitions = 25 # pysnmp default
        timeout = 5
        retries = 0
        oid_object = None

        if (isinstance(oids, str)):
            oid_object = [ObjectType(ObjectIdentity(oids))]
        elif (isinstance(oids, tuple)):
            oid_object = [ObjectType(ObjectIdentity(*oids))]
        elif(isinstance(oids, list)):
            if len(oids) > 0:
                if (isinstance(oids[0], str)): # List of Str
                    oid_object = [ObjectType(ObjectIdentity(oid)) for oid in oids]
                elif (isinstance(oids[0], tuple)): # List of Tuple
                    oid_object = [ObjectType(ObjectIdentity(*oid)) for oid in oids]

        gen = iter(())
        if not oid_object:
            logger.error('Invalid OID list passed to Poller')
            return gen

        try:
            gen = bulkCmd(
                SnmpEngine(),
                self.auth_object,
                UdpTransportTarget((self.device['host'], self.device['port']), timeout=timeout, retries=retries),
                ContextData(),
                non_repeaters,
                max_repetitions,             
                *oid_object,
                lexicographicMode=False)
        except Exception as e:
            logger.error(e)

        return gen

    def _build_auth_object(self):
        authentication = self.authentication
        if (authentication['version'] == 3):
            self.auth_object = UsmUserData(
                authentication['user'],
                authentication['auth']['key'],
                authentication['priv']['key'],
                self.auth_protocols.get(authentication['auth']['protocol'], None),
                self.priv_protocols.get(authentication['priv']['protocol'], None))
        elif(authentication['version'] == 2):
            self.auth_object = CommunityData(authentication['user'], mpModel=1)
        elif(authentication['version'] == 1):
            self.auth_object = CommunityData(authentication['user'], mpModel=0)
