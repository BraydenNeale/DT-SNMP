from dtmon.dtf5snmp import DTF5Mon
import configparser

def main():
	config = configparser.ConfigParser()
	config_path = './config.ini'
	config.read(config_path)

	DT_URL = config.get('dynatrace','DT_URL_SAAS')
	DT_API_TOKEN = config.get('dynatrace','DT_API_TOKEN')
	DEFAULT_ICON = config.get('dynatrace','DEFAULT_ICON')
	DOMAIN = config.get('environment','DOMAIN')

	dtendpoint = {
		"url": DT_URL,
		"apiToken": DT_API_TOKEN
	}

	F5_IP = config.get('f5-swg','IP')
	F5_HOSTNAMENAME = config.get('f5-swg','HOSTNAME')
	F5_PORT = int(config.get('f5-swg', 'PORT'))
	F5_SNMP_VERSION = int(config.get('f5-swg', 'SNMP_VERSION'))
	F5_SNMP_COMMUNITY = config.get('f5-swg', 'SNMP_COMMUNITY')

	f5Endpoint = {
		"host": F5_IP,
		"port": F5_PORT,
		"snmpAuth": {
			"version": F5_SNMP_VERSION,
			"username": F5_SNMP_COMMUNITY
		}
	}
	
	deviceDisplay = {
		"id": "{0}.f5.{1}".format(DOMAIN,F5_HOSTNAMENAME),
		"displayName": "{0} | F5".format(F5_HOSTNAMENAME),
		"type": "F5",
		"ipAddresses":[F5_IP], 
		"listenPorts":[F5_PORT], 
#		"configUrl":"",
		"tags": ["F5"],
		"favicon": DEFAULT_ICON,
		"groupId": "F5",
		"properties": {}
	}

	logDetails = {"level":"debug", "location": "./DTF5SNMPMon.log"}
	
	f5 = DTF5Mon(dtendpoint, f5Endpoint, deviceDisplay, logDetails=logDetails, getLatency=True, mib={"use": False})
	t_f5 = f5.dtrun()
	t_f5.join()

	return
	
if __name__ == '__main__':
  main()		