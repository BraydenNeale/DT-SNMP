from .dtmonitoringbase import DTMonitoringBase
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.hlapi import *
from pysnmp.smi import builder, compiler, view, rfc1902
import requests
import time
import datetime
import sched
import random
import re
import logging


class DTSNMPMonitoring(DTMonitoringBase):
    propsUmbrella = '   '
    propsMap  = {"3.0": "Up Time", "1.0": "Description", "4.0":"Contact", "5.0": "Name", "6.0": "Location"}

    mibBuilder, mibViewController = None, None

    mib = {"use": False, 
        "locations": ["file:///usr/share/snmp/mibs"],
        "modules": ()}

    authProtoDict = {
        'md5': usmHMACMD5AuthProtocol,
        'sha': usmHMACSHAAuthProtocol,
        'sha224': usmHMAC128SHA224AuthProtocol,
        'sha256': usmHMAC192SHA256AuthProtocol,
        'sha384': usmHMAC256SHA384AuthProtocol,
        'sha512': usmHMAC384SHA512AuthProtocol,
        'noauth': usmNoAuthProtocol,
    }

    privProtoDict = {
        'des': usmDESPrivProtocol,
        '3des': usm3DESEDEPrivProtocol,
        'aes': usmAesCfb128Protocol,
        'aes192': usmAesCfb192Protocol,
        'aes256': usmAesCfb256Protocol,
        'nopriv': usmNoPrivProtocol,
    }
    snmpAuthDetails = object()

    def __init__(self,
                 dtEndpoint,
                 deviceAuth,
                 deviceDisplay,
                 timeout={"dtserver": 10,
                          "device": 10},
                 logDetails={"level": "error",
                             "location": "/tmp/DTSNMPMonitoring.log"},
                 memcachedServer={"use": True, 
                             "address": "localhost", 
                             "port": 11211},
                 mib={"use": False, 
                      "locations": ["file:///usr/share/snmp/mibs"],
                      "modules": ()},
                 tsPrefix="domain.genericsnmpdevice",
                 getLatency=False,
                 getSystemProps=True):
        super(DTSNMPMonitoring, self).__init__(dtEndpoint,
                                                deviceAuth,
                                                deviceDisplay,
                                                timeout=timeout,
                                                logDetails=logDetails,
                                                memcachedServer=memcachedServer,
                                                tsPrefix=tsPrefix,
                                                getLatency=getLatency)
        self.__validateInput()
        self.__buildAuthDetails()
        if(mib["use"]):
            self.mibBuilder = builder.MibBuilder()
            self.mibViewController = view.MibViewController(self.mibBuilder)
            if not "location" in mib:
                compiler.addMibCompiler(self.mibBuilder, sources=self.mib["locations"])
            else:
                compiler.addMibCompiler(self.mibBuilder, sources=mib["locations"])    
            if not "modules" in mib:    
                self.mibBuilder.loadModules(*self.mib["modules"])
            else:
                self.mibBuilder.loadModules(*mib["modules"])   
        if(getSystemProps==True):
            self.__getSystemProp()    



    def __validateInput(self):
        authVersionReq = ["authKey", "authProtocol"]
        if(not "snmpAuth" in self.deviceAuth):
            raise ValueError("No auth details for this SNMP Device")
        snmpAuth = self.deviceAuth["snmpAuth"]
        if (not "username" in snmpAuth
            or snmpAuth["username"].strip() == ""):
            raise ValueError('snmpAuth["username"] should not be empty')
        if (not "version" in snmpAuth
            or not isinstance(snmpAuth["version"], int)):
            raise ValueError('snmpAuth["version"] should not be empty'
                             ' and should be an integer')
        snmpAuthKeysSet = set(snmpAuth.keys())
        if(snmpAuth["version"] == 3):
            if(not set(authVersionReq).issubset(snmpAuthKeysSet)):
                raise ValueError(
                    "%s of auth should not be none if v3 is used" % (str(authVersionReq)))
            authProtoKeys = self.authProtoDict.keys()
            privProtoKeys = self.privProtoDict.keys()
            if(not snmpAuth["authProtocol"] in authProtoKeys):
                raise ValueError("snmpAuth['authProtocol'] should only has the following values: %s" % (
                    str(authProtoKeys)))
            if("privProtocol" in snmpAuth and not snmpAuth["privProtocol"] in privProtoKeys):
                raise ValueError("snmpAuth['privProtocol'] should only has the following values: %s" % (
                    str(privProtoKeys)))

    def __buildAuthDetails(self):
        snmpAuth = self.deviceAuth["snmpAuth"]
        if(snmpAuth["version"] == 3):
            self.snmpAuthDetails = UsmUserData(
                snmpAuth["username"],
                snmpAuth["authKey"],
                (snmpAuth["privKey"] if "privKey" in snmpAuth else None),
                authProtocol = self.authProtoDict[snmpAuth["authProtocol"]],
                privProtocol = (self.privProtoDict[snmpAuth["privProtocol"]] if "privKey" in snmpAuth else None)
            )
        elif(snmpAuth["version"] == 2):
            self.snmpAuthDetails = CommunityData(snmpAuth["username"],
                                                 mpModel=1)
        elif(snmpAuth["version"] == 1):
            self.snmpAuthDetails = CommunityData(snmpAuth["username"],
                                                 mpModel=0)                                         

    def snmp_connect(self, oid):
        iter = object()
        iter = getCmd(SnmpEngine(),
            self.snmpAuthDetails,
            UdpTransportTarget((self.deviceAuth["host"],
            self.deviceAuth["port"])),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )
        return next(iter)

    def _snmpBulkConnect(self, oids):
        iter = object()
        if(isinstance(oids, str)):
            oidTypes = [ObjectType(ObjectIdentity(oids))]
        elif(isinstance(oids, list)):
            oidTypes = [ObjectType(ObjectIdentity(oid)) for oid in oids]
        
        iter = cmdgen.bulkCmd(
            SnmpEngine(),
            self.snmpAuthDetails,
            UdpTransportTarget((self.deviceAuth["host"], self.deviceAuth["port"]),
                retries=0),
            ContextData(),
            0,25,
            *oidTypes,
            lexicographicMode=False)    
        return iter

    def _processIterBulk(self, iter, umbrella, detailedMap, callback, optionalParam=None):
        for item in iter:
            errorIndication, errorStatus, errorIndex, varBinds = item
            if errorIndication:
                logging.error('%s - Error: %s', self.deviceDisplay["displayName"],
                              errorIndication,
                              extra=self.logDetails)
                if str(errorIndication) == "No SNMP response received before timeout":
                    break              
            elif errorStatus:
                logging.error('%s - Error: %s at %s',  self.deviceDisplay["displayName"], errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex)-1][0] or '?',
                extra=self.logDetails)
            else:
                #success, emit the value to the log
                if callable(callback):
                    if optionalParam is None:
                        callback(varBinds, umbrella, detailedMap)
                    else:
                        callback(varBinds, umbrella, detailedMap, optionalParam)    
    

    '''
    This method map the index and the interface of the switch and build the a mapping into a dictionary in a form of <index>: <value | alias>
    return: the mapping in a format of <oid>:"<name> | <alias>"
    '''
    def _getInterfaceIndexAliasMapping(self, interfaceName, interfaceAlias=None):
        interfaceNameMap = {}
        interfaceAliasMap = {}
        mapping = {}

        iterIf = self._snmpBulkConnect(interfaceName)
        self._processIterBulk(iterIf, interfaceName, interfaceNameMap, self._getIfIdxStringValueMap)

        if(interfaceAlias is not None):
            iter = self._snmpBulkConnect(interfaceAlias)
            self._processIterBulk(iter, interfaceAlias, interfaceAliasMap, self._getIfIdxStringValueMap)

        for id, value in interfaceNameMap.items():
            try:
                if(interfaceAlias is not None):
                    alias = interfaceAliasMap[id] if (not interfaceAliasMap[id] == "") else "<empty>" 
                    mapping[id] = ("%s | %s" % (value, alias))
                else:
                    mapping[id] = ("%s" % (value))
            except Exception as e:
                logging.error("%s - Exception occured: %s", self.deviceDisplay["displayName"], e)
        return mapping

    '''
    Callback method to to be passed into _processIterBulk.
    This method will build a dictionary out of mapping with <key>: <value in string>
    '''	
    def _getIfIdxStringValueMap(self, varBinds, umbrella, mapping, optionalParam=None):
        resolvedOid = ""
        try:
            for oid, value in varBinds:
                resolvedOid = self._mapOidToHumanReadable(oid) if self.mibViewController is not None else str(oid)
                
                idxPos = -1
                if optionalParam is not None and "idxPos" in optionalParam:
                    idxPos = optionalParam["idxPos"]
                inds = [i for i,c in enumerate(resolvedOid) if c=='.']
                idIndexStart = inds[idxPos] + 1
                idx = resolvedOid[idIndexStart:]
                idx = idx.strip()
                if(not idx in mapping):
                    mapping[idx] = value.prettyPrint()
        except Exception as e:
            logging.error("%s - getIfIdxStringValue Exception occured: %s - %s", self.deviceDisplay["displayName"], e, resolvedOid)

    '''
    Callback method to to be passed into _processIterBulk.
    This method will build a dictionary out of mapping with <key>: <value in float>
    '''	
    def _getIfIdxFloatValueMap(self, varBinds, umbrella, mapping, optionalParam=None):
        try:
            for oid, value in varBinds:
                resolvedOid = self._mapOidToHumanReadable(oid) if self.mibViewController is not None else str(oid)
                idxPos = -1
                inds = [i for i,c in enumerate(resolvedOid) if c=='.']
                if optionalParam is not None and "idxPos" in optionalParam:
                    idxPos = optionalParam["idxPos"]
                idIndexStart = inds[idxPos] + 1
                idx = resolvedOid[idIndexStart:]
                idx = idx.strip()
                if(not idx in mapping):
                    mapping[idx] = float(value.prettyPrint())
        except Exception as e:
            logging.error("%s - Exception occured: %s", self.deviceDisplay["displayName"], e)


    '''
    Method to map oid to human readable form.
    Parameteres: oid (string)
    Return: "<oid representation> ="
    '''
    def _mapOidToHumanReadable(self, oid):
        if(self.mibViewController is None):
            raise ValueError("Cannot resolve oid to human readable form as mib is not used")    
        oType = rfc1902.ObjectType(rfc1902.ObjectIdentity(oid)).resolveWithMib(self.mibViewController).prettyPrint()
        return oType[:-2]	


    def _getStringValueMap(self, varBinds, umbrella, mapping):
        for oid, value in varBinds:
            if self.mibViewController is not None:
                resolvedOid = self._mapOidToHumanReadable(oid)
                idIndexStart = resolvedOid.index(':') + 2
                idx = resolvedOid[idIndexStart:]
                idx = idx.strip()
                if(not idx in mapping):
                    mapping[idx] = value.prettyPrint()

    def _getFloatValueMap(self, varBinds, umbrella, mapping):
        for oid, value in varBinds:
            if self.mibViewController is not None:
                resolvedOid = self._mapOidToHumanReadable(oid)
                idIndexStart = resolvedOid.index(':') + 2
                idx = resolvedOid[idIndexStart:]
                idx = idx.strip()
                if(not idx in mapping):
                    try:
                        mapping[idx] = float(value.prettyPrint())
                    except Exception as e:
                        logging.error("%s - Exception when casting %s | %s: %s",self.deviceDisplay["displayName"], idx, value.prettyPrint(), e)
                        
                        

    def _getMappingWithIdxPosFromCache(self, suffixKey, umbrella, callback):
        mapping, slMap = {}, {}
        idPosCacheKey = self.timeSeriesIdPrefix + "." + suffixKey + ".idxPos"
        optionalParam = {"idxPos": -1}	
        idPosString = self._getValueFromCache(idPosCacheKey)
        if idPosString is not None:
            optionalParam["idxPos"] = int(idPosString)
            iter = self._snmpBulkConnect(umbrella)
            self._processIterBulk(iter, umbrella, mapping, callback, optionalParam=optionalParam)
        else:
            iter = self._snmpBulkConnect(umbrella)
            self._processIterBulk(iter, umbrella, mapping, callback, optionalParam={"idxPos": -1})
            iter = self._snmpBulkConnect(umbrella)
            self._processIterBulk(iter, umbrella, slMap, callback, optionalParam={"idxPos": -2})
            if not len(mapping.keys()) == len(slMap.keys()) and len(slMap.keys()) > len(mapping.keys()):
                mapping = slMap
                optionalParam = {"idxPos": -2}
                self._setValueToCache(idPosCacheKey, -2)
            else:
                self._setValueToCache(idPosCacheKey, -1)   
        return mapping

    def __getSystemProp(self):
        try:
            tmpPropMap, propMap = {}, {}
            iter = self._snmpBulkConnect(self.propsUmbrella)
            self._processIterBulk(iter, self.propsUmbrella, tmpPropMap, self._getIfIdxStringValueMap, optionalParam={"idxPos": -2})
            for k, val in self.propsMap.items():
                if k in tmpPropMap:
                    if self.propsMap[k] == "Up Time":
                        propMap[self.propsMap[k]] = self._tickToString(int(tmpPropMap[k]))
                    else:    
                        propMap[self.propsMap[k]] = tmpPropMap[k]
            if(len(self.deviceDisplay["properties"].keys()) == 0):
                self.deviceDisplay["properties"] = propMap
        except Exception as e:
            logging.debug("%s - Cannot get prop map due to exception : %s", self.deviceDisplay["displayName"], str(e))	    