from .dtmonitoringbase import DTMonitoringBase
import requests
import time
import datetime
import sched
import random
import re
import ast
import logging
import base64


class DTRestMonitoring(DTMonitoringBase):

    def __init__(self,
                 dtEndpoint,
                 deviceAuth,
                 deviceDisplay,
                 timeout={"dtserver": 10, "device": 10},
                 logDetails={"level": "error",
                             "location": "/tmp/DTRestMonitoring.log"}):
        super(DTRestMonitoring, self).__init__(dtEndpoint,
                                                deviceAuth,
                                                deviceDisplay,
                                                timeout=timeout,
                                                logDetails=logDetails)
        self.__validateInput()

    def __validateInput(self):
        if(not "restAuth" in self.deviceAuth):
            raise ValueError("No auth details for this Restful Device")
        restAuth = self.deviceAuth["restAuth"]
        if(not isinstance(restAuth, dict)):
            raise TypeError('restAuth should be of type dict')
        if not "type" in restAuth:
            raise ValueError("type cannot be empty")
        if restAuth["type"].lower() == "basic":
            if not "username" in restAuth or not "password" in restAuth:
                raise ValueError("username and password need to have value")
        elif restAuth["type"].lower() == "token":
            if not "token" in restAuth:
                raise ValueError("token needs to have value")

    def __authHeader(self):
        restAuth = self.deviceAuth["restAuth"]
        authHeader = {}
        if(restAuth["type"].lower() == "basic"):
            authHeader["Authorization"] = "Basic " + \
                base64.b64encode((restAuth['username'] + ":" + restAuth['password']).encode('ascii')).decode('utf-8')
        return authHeader

    def makeRequest(self, method, uri, json={}, verify=None, timeout=None):
        url = self.deviceAuth["host"]
        if (("port" in self.deviceAuth)
                and (self.deviceAuth["port"].strip() != "")):
            url += ":" + str(self.deviceAuth["port"])
        url += uri
        logging.debug("\n\turl: %s \n\tjson: %s \n\tauthHeader: %s",
                      url, json, self.__authHeader())
        return self._makeRequest(method,
                                 url,
                                 json=json,
                                 headers=self.__authHeader(),
                                 verify=verify,
                                 timeout=timeout)
