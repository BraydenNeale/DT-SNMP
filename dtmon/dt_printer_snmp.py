from .dtmonitoringsnmp import DTSNMPMonitoring
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.hlapi import *
from pysnmp.smi import builder, compiler, view, rfc1902
import requests, time, datetime, sched, random
import os
import re
import logging
import threading
import json
import subprocess

class dt_printer_mon(DTSNMPMonitoring):
    # mibBuilder, mibViewController = {}, {}

    # device_model_umbrella = '1.3.6.1.2.1.25.3.2.1.3.1'
    sincepoweron_prints_umbrella = '.1.3.6.1.2.1.43.10.2.1.5'
    uptime_umbrella = '.1.3.6.1.2.1.25.1.1'

    # xerox
    xerox_lifetime_prints_umbrella = '1.3.6.1.4.1.253.8.53.13.2'
    # xerox_map = {}

    # ricoh
    ricoh_umbrella = '1.3.6.1.4.1.367.3.2.1.2.19.5'
    # ricoh_map = {}

    timeSeriesIdPrefix = ""

    metricBulkSize = 100

    def __init__(self,
                    dtEndpoint,
                    deviceAuth,
                    deviceDisplay,
                    timeout={"dtserver": 10, "device": 10},
                    logDetails={"level":"error",
                                "location": "/tmp/dtISAMSNMPMon.log"}):
        super(dt_printer_mon, self).__init__(dtEndpoint,
                                                deviceAuth,
                                                deviceDisplay,
                                                timeout=timeout,
                                                logDetails=logDetails)
        if "Xerox" in self.deviceDisplay["tags"]:
            self.timeSeriesIdPrefix = ("custom:%s" % ("domain.xerox.printer"))
            self.xerox_metric_definitions = {
                self.deviceDisplay["name"]: {
                    # commented out all lifetime print metrics (should be better metrics to report!!!)
                            # unadded oid's
                            # meter1 ().101.20.1)
                            # meter2 ().101.20.2)
                            # meter3 ().101.20.3)
                            # meter4 ().101.20.4)
                            # ===========================================
                            # Total Impressions (.1.20.1)
                        # "total_impressions": {"oid_suffix": ".1.6.1.20.1", "display_name": "Total Impressions", "timeseries_suffix": ".snmp.device.impressions.total"},
                        #     # Power On Impressions (.1.20.2)
                        # "power_on_impressions": {"oid_suffix": ".1.6.1.20.2", "display_name": "Power On Impressions", "timeseries_suffix": ".snmp.device.impressions.poweron"},
                        #     # Black Printed Impressions (.1.20.7)
                        # "black_printed_impressions": {"oid_suffix": ".1.6.1.20.7", "display_name": "Black Printed Impressions", "timeseries_suffix": ".snmp.device.impressions.blackprinted"},
                        #     # Black Printed Sheets (.1.20.8)
                        # "black_printed_sheets": {"oid_suffix": ".1.6.1.20.8", "display_name": "Black Printed Sheets", "timeseries_suffix": ".snmp.device.sheets.blackprinted"},
                        #     # Black Printed 2 Sided Sheets (.1.20.9)
                        # "black_printed_sheets2sided": {"oid_suffix": ".1.6.1.20.9", "display_name": "Black Printed 2 Sided Sheets", "timeseries_suffix": ".snmp.device.sheets2sided.blackprinted"},
                        #     # Black Printed Large Sheets (.1.20.10)
                        # "black_printed_largesheets": {"oid_suffix": ".1.6.1.20.10", "display_name": "Black Printed Large Sheets", "timeseries_suffix": ".snmp.device.largesheets.blackprinted"},
                        #     # Printed Sheets (.1.20.15)
                        # "printed_sheets": {"oid_suffix": ".1.6.1.20.15", "display_name": "Printed Sheets", "timeseries_suffix": ".snmp.device.sheets.printed"},
                        #     # Printed 2 Sided Sheets (.1.20.16)
                        # "printed_sheets2sided": {"oid_suffix": ".1.6.1.20.16", "display_name": "Printed 2 Sided Sheets", "timeseries_suffix": ".snmp.device.sheets2sided.printed"},
                        #     # Color Printed Impressions (.1.20.29)
                        # "color_printed_impressions": {"oid_suffix": ".1.6.1.20.29", "display_name": "Color Printed Impressions", "timeseries_suffix": ".snmp.device.impressions.colorprinted"},
                        #     # Color Printed Sheets (.1.20.30)
                        # "color_printed_sheets": {"oid_suffix": ".1.6.1.20.30", "display_name": "Color Printed Sheets", "timeseries_suffix": ".snmp.device.sheets.colorprinted"},
                        #     # Color Printed 2 Sided Sheets (.1.20.31)
                        # "color_printed_sheets2sided": {"oid_suffix": ".1.6.1.20.31", "display_name": "Color Printed 2 Sided Sheets", "timeseries_suffix": ".snmp.device.sheets2sided.colorprinted"},
                        #     # Color Printed Large Sheets (.1.20.32)
                        # "color_printed_largesheets": {"oid_suffix": ".1.6.1.20.32", "display_name": "Color Printed Large Sheets", "timeseries_suffix": ".snmp.device.largesheets.colorprinted"},
                        #     # Color Impressions (.1.20.33)
                        # "color_impressions": {"oid_suffix": ".1.6.1.20.33", "display_name": "Color Impressions", "timeseries_suffix": ".snmp.device.impressions.color"},
                        #     # Black Impressions  (.1.20.34)
                        # "black_impressions": {"oid_suffix": ".1.6.1.20.34", "display_name": "Black Impressions", "timeseries_suffix": ".snmp.device.impressions.black"},
                        #     # Sheets (.1.20.38)
                        # "sheets": {"oid_suffix": ".1.6.1.20.38", "display_name": "Sheets", "timeseries_suffix": ".snmp.device.sheets"},
                        #     # 2 Sided Sheets (.1.20.39)
                        # "sheets2sided": {"oid_suffix": ".1.6.1.20.39", "display_name": "2 Sided Sheets", "timeseries_suffix": ".snmp.device.sheets2sided"},
                        #     # Color Large Impressions (.1.20.43)
                        # "color_large_impressions": {"oid_suffix": ".1.6.1.20.43", "display_name": "Color Large Impressions", "timeseries_suffix": ".snmp.device.largeimpressions.color"},
                        #     # Black Large Impressions (.1.20.44)
                        # "black_large_impressions": {"oid_suffix": ".1.6.1.20.44", "display_name": "Black Large Impressions", "timeseries_suffix": ".snmp.device.largeimpressions.black"},
                        #     # Large Impressions (.1.20.47)
                        # "large_impressions": {"oid_suffix": ".1.6.1.20.47", "display_name": "Large Impressions", "timeseries_suffix": ".snmp.device.impressions.large"},
                        #     # Fax Impressions (.1.20.71)
                        # "fax_impressions": {"oid_suffix": ".1.6.1.20.71", "display_name": "Fax Impressions", "timeseries_suffix": ".snmp.device.impressions.fax"},
                        #     # Network Scanning Images Sent (.102.20.11)
                        # "network_scanning_images_sent": {"oid_suffix": ".1.6.102.20.11", "display_name": "Network Scanning Images Sent", "timeseries_suffix": ".snmp.device.imagessent.networkscan"},
                        #     # E-mail Images Sent (.102.20.12)
                        # "email_images_sent": {"oid_suffix": ".1.6.102.20.12", "display_name": "E-mail Images Sent", "timeseries_suffix": ".snmp.device.imagessent.email"},
                        #     # Scanned Images Stored (.102.20.21)
                        # "scanned_images_stored": {"oid_suffix": ".1.6.102.20.21", "display_name": "Scanned Images Stored", "timeseries_suffix": ".snmp.device.imagesstored.scan"},
                        #     # Images Sent (.102.20.23)
                        # "images_sent": {"oid_suffix": ".1.6.102.20.23", "display_name": "Images Sent", "timeseries_suffix": ".snmp.device.imagessent"},
                        #     # Fax Images Sent (.102.20.66)
                        # "fax_images_sent": {"oid_suffix": ".1.6.102.20.66", "display_name": "Fax Images Sent", "timeseries_suffix": ".snmp.device.imagessent.fax"},
                        #     # Black Copied Impressions (.103.20.3)
                        # "black_copied_impressions": {"oid_suffix": ".1.6.103.20.3", "display_name": "Black Copied Impressions", "timeseries_suffix": ".snmp.device.impressions.blackcopied"},
                        #     # Black Copied Sheets (.103.20.4)
                        # "black_copied_sheets": {"oid_suffix": ".1.6.103.20.4", "display_name": "Black Copied Sheets", "timeseries_suffix": ".snmp.device.sheets.blackcopied"},
                        #     # Black Copied 2 Sided Sheets (.103.20.5)
                        # "black_copied_sheets2sided": {"oid_suffix": ".1.6.103.20.5", "display_name": "Black Copied 2 Sided Sheets", "timeseries_suffix": ".snmp.device.sheets2sided.blackcopied"},
                        #     # Black Copied Large Sheets (.103.20.6)
                        # "black_copied_largesheets": {"oid_suffix": ".1.6.103.20.6", "display_name": "Black Copied Large Sheets", "timeseries_suffix": ".snmp.device.largesheets.blackcopied"},
                        #     # Copied Sheets (.103.20.15)
                        # "copied_sheets": {"oid_suffix": ".1.6.103.20.15", "display_name": "Copied Sheets", "timeseries_suffix": ".snmp.device.sheets.copied"},
                        #     # Copied 2 Sided Sheets (.103.20.16)
                        # "copied_sheets2sided": {"oid_suffix": ".1.6.103.20.16", "display_name": "Copied 2 Sided Sheets", "timeseries_suffix": ".snmp.device.sheets2sided.copied"},
                        #     # Color Copied Impressions (.103.20.25)
                        # "color_copied_impressions": {"oid_suffix": ".1.6.103.20.25", "display_name": "Color Copied Impressions", "timeseries_suffix": ".snmp.device.impressions.colorcopied"},
                        #     # Color Copied Sheets (.103.20.26)
                        # "color_copied_sheets": {"oid_suffix": ".1.6.103.20.26", "display_name": "Color Copied Sheets", "timeseries_suffix": ".snmp.device.sheets.colorcopied"},
                        #     # Color Copied 2 Sided Sheets (.103.20.27)
                        # "color_copied_sheets2sided": {"oid_suffix": ".1.6.103.20.27", "display_name": "Color Copied 2 Sided Sheets", "timeseries_suffix": ".snmp.device.sheets2sided.colorcopied"},
                        #     # Color Copied Large Sheets (.103.20.28)
                        # "color_copied_largesheets": {"oid_suffix": ".1.6.103.20.28", "display_name": "Color Copied Large Sheets", "timeseries_suffix": ".snmp.device.largesheets.colorcopied"},
                        #     # Embedded Fax Images Sent (.104.20.13)
                        # "embedded_fax_images_sent": {"oid_suffix": ".1.6.104.20.13", "display_name": "Embedded Fax Images Sent", "timeseries_suffix": ".snmp.device.imagessent.embeddedfax"},
                        #     # Embedded Fax Sheets (.104.20.15)
                        # "embedded_fax_sheets": {"oid_suffix": ".1.6.104.20.15", "display_name": "Embedded Fax Sheets", "timeseries_suffix": ".snmp.device.sheets.embeddedfax"},
                        #     # Embedded Fax 2 Sided Sheets (.104.20.16)
                        # "embedded_fax_sheets2sided": {"oid_suffix": ".1.6.104.20.16", "display_name": "Embedded Fax 2 Sided Sheets", "timeseries_suffix": ".snmp.device.sheets2sided.embeddedfax"},
                        #     # Embedded Fax Large Sheets (.104.20.17)
                        # "embedded_fax_largesheets": {"oid_suffix": ".1.6.104.20.17", "display_name": "Embedded Fax Large Sheets", "timeseries_suffix": ".snmp.device.largesheets.embeddedfax"},
                        #     # Internet Fax Images Sent (.138.20.13)
                        # "internet_fax_images_sent": {"oid_suffix": ".1.6.138.20.13", "display_name": "Internet Fax Images Sent", "timeseries_suffix": ".snmp.device.imagessent.internetfax"},
                        #     # Server Fax Images Sent (.139.20.13)
                        # "server_fax_images_sent": {"oid_suffix": ".1.6.139.20.13", "display_name": "Server Fax Images Sent", "timeseries_suffix": ".snmp.device.imagessent.serverfax"},
                            # other dict items
                        # "device_model": {"timeseries_suffix": ".snmp.device.model", "display_name": "Device Model"},
                        "prints_sincepoweron": {"timeseries_suffix": ".snmp.device.prints.sincepoweron", "display_name": "Number of Sheets Printed - since last power cycle"},
                        "uptime": {"timeseries_suffix": ".snmp.device.uptime", "display_name": "Uptime"},
                    }
                }
        else:
            self.timeSeriesIdPrefix = ("custom:%s" % ("domain.ricoh.printer"))
            self.ricoh_metric_definitions = {
                self.deviceDisplay["name"]: {
                    # "device_model": {"timeseries_suffix": ".snmp.device.model", "display_name": "Device Model"},
                    "prints_sincepoweron": {"timeseries_suffix": ".snmp.device.prints.sincepoweron", "display_name": "Number of Sheets Printed - since last power cycle"},
                    "uptime": {"timeseries_suffix": ".snmp.device.uptime", "display_name": "Uptime"}
                }
            }

        # commented due to no mib working for the xerox snmp
        # self.mibBuilder = builder.MibBuilder()
        # compiler.addMibCompiler(self.mibBuilder, sources=['file:///usr/share/snmp/mibs'])
        # self.mibViewController = view.MibViewController(self.mibBuilder)
        # # Pre-load MIB modules we expect to work with
        # self.mibBuilder.loadModules('XEROX-HOST-RESOURCES-EXT-MIB')

    def dtrun(self):
        if self.check_if_machine_up() != 0:
            logging.error(self.deviceAuth["host"] + " is down")
            return
        device = {
            "displayName": self.deviceDisplay["name"],
            "type": self.deviceDisplay["type"],
            "tags": self.deviceDisplay["tags"],
            "properties": {},
            "favicon" : self.deviceDisplay["icon"]
        }
        # if "Xerox" in self.deviceDisplay["tags"]:
        #     self.get_xerox_lifetime_page_counts()
        # else:
        #     pass

        # self.get_device_model()
        self.get_page_counts_sincepoweron()
        self.get_uptime()
        if "Xerox" in self.deviceDisplay["tags"]:
            # register metrics
            self.register_metrics(self.xerox_metric_definitions[self.deviceDisplay["name"]])
            series = self.process_results()
        else:
            # register metrics
            self.register_metrics(self.ricoh_metric_definitions[self.deviceDisplay["name"]])
            series = self.process_results()
        self._sendMetricInBulk(series)
        return

    def get_xerox_lifetime_page_counts(self):
        """ add code here for processing the page count from snmp """

        # =========================================
        # vu suggested since the mibs are not currently
        # working xerox printers snmp calls that it 
        # would be a good idea to call for the snmp data
        # manually.
        # 
        # 
        # =========================================
        # single connection via:
        # bodgey snmpget command running from subprocess (we will get this to work in snmp_connect!!!)
        snmpwalk_result = subprocess.check_output(["snmpwalk", "-v2c", "-On", "-cpublic", self.deviceAuth["host"], self.xerox_lifetime_prints_umbrella])
        for line in snmpwalk_result.splitlines():
            for k,v in self.xerox_metric_definitions[self.deviceDisplay["name"]].items():
                if k != "prints_sincepoweron":
                    if str(v["oid_suffix"]) in str(line):
                        self.xerox_metric_definitions[self.deviceDisplay["name"]][k].update({"snmp_value": int(str(line).split("INTEGER: ")[1].strip("\\n\'"))})
                        # debug for checking correct oid values
                        # print((k, v, str(line)))`
            # ideal call via getCmd (snmp_connect)
            # return_back = self.snmp_connect(self.xerox_umbrella + dict(v)["oid_suffix"])
        # bulk connection via bulkCmd (_snmpBulkConnect)
        # for (errorIndication,
        #     errorStatus,
        #     errorIndex,
        #     varBinds) in self._snmpBulkConnect(self.xerox_umbrella):
        #         if errorIndication or errorStatus:
        #             print(errorIndication or errorStatus)
        #             break
        #         else:
        #             for varBind in varBinds:
        #                 print(' = '.join([x.prettyPrint() for x in varBind]))

    def get_device_model(self):
        # gets device model
        snmpget_device_result = str(subprocess.check_output(["snmpget", "-v2c", "-cpublic", self.deviceAuth["host"], self.device_model_umbrella])).split("STRING: ")[1].strip("\\n\'")
        if "Xerox" in self.deviceDisplay["tags"]:
            self.xerox_metric_definitions[self.deviceDisplay["name"]]["device_model"].update({ "snmp_value": snmpget_device_result })
        else:
            self.ricoh_metric_definitions[self.deviceDisplay["name"]]["device_model"].update({ "snmp_value": snmpget_device_result })

    def get_page_counts_sincepoweron(self):
        # gets get_page_counts_sincepoweron
        snmpget_page_count_result = str(subprocess.check_output(["snmpwalk", "-v2c", "-cpublic", self.deviceAuth["host"], self.sincepoweron_prints_umbrella, "-m", "all"])).split("Counter32: ")[1].strip("\\n\'")
        if "Xerox" in self.deviceDisplay["tags"]:
            self.xerox_metric_definitions[self.deviceDisplay["name"]]["prints_sincepoweron"].update({ "snmp_value": int(snmpget_page_count_result) })
        else:
            self.ricoh_metric_definitions[self.deviceDisplay["name"]]["prints_sincepoweron"].update({ "snmp_value": int(snmpget_page_count_result) })

    def get_uptime(self):
        # gets get_page_counts_sincepoweron
        snmpget_uptime_result = str(subprocess.check_output(["snmpwalk", "-v2c", "-cpublic", self.deviceAuth["host"], self.uptime_umbrella])).split("Timeticks: ")[1].split(")")[0].strip("(")
        # snmpget_result = self.snmp_connect(self.uptime_umbrella)
        # pr(int(snmpget_uptime_result) / 100)
        if "Xerox" in self.deviceDisplay["tags"]:
            self.xerox_metric_definitions[self.deviceDisplay["name"]]["uptime"].update({ "snmp_value": (int(snmpget_uptime_result) / 100) })
        else:
            self.ricoh_metric_definitions[self.deviceDisplay["name"]]["uptime"].update({ "snmp_value": (int(snmpget_uptime_result) / 100) })

    def process_results(self):
        series = []
        if "Xerox" in self.deviceDisplay["tags"]:
            for key, value in self.xerox_metric_definitions[self.deviceDisplay["name"]].items():
                t_series = {
                    "timeseriesId": ("%s%s" % (self.timeSeriesIdPrefix, value["timeseries_suffix"])),
                    "dimensions": {"type": str(key).strip()},
                    "dataPoints": [[int(time.time() * 1000), value["snmp_value"]]]
                }
                series.append(t_series)
        else:
            for key, value in self.ricoh_metric_definitions[self.deviceDisplay["name"]].items():
                t_series = {
                    "timeseriesId": ("%s%s" % (self.timeSeriesIdPrefix, value["timeseries_suffix"])),
                    "dimensions": {"type": str(key).strip()},
                    "dataPoints": [[int(time.time() * 1000), value["snmp_value"]]]
                }
                series.append(t_series)
        return series

    def register_metrics(self, metric_definitions):
        for k, v in metric_definitions.items():
            if "device_model" not in k:
                metric_json = {
                    "displayName": v["display_name"],
                    "unit": "Count",
                    "dimensions": [
                        "type"
                    ],
                    "types": [
                        self.deviceDisplay["type"]
                    ]
                }
            elif "uptime" in k:
                metric_json = {
                    "displayName": v["display_name"],
                    "unit": "Second",
                    "dimensions": [
                        "type"
                    ],
                    "types": [
                        self.deviceDisplay["type"]
                    ]
                }
            else:
                metric_json = {
                    "displayName": v["display_name"],
                    "unit": "String",
                    "dimensions": [
                        "type"
                    ],
                    "types": [
                        self.deviceDisplay["type"]
                    ]
                }
            self._registerDTMetric(("%s%s" % (self.timeSeriesIdPrefix, v["timeseries_suffix"])), json=metric_json)

    def check_if_machine_up(self):
        return os.system("ping -c 1 -w2 " + self.deviceAuth["host"] + " > /dev/null 2>&1")
