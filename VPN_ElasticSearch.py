from dtmon.dtvpnesmon import DTVPNESMon

def main():
	dtendpoint = {
		"url": "<URL>",
		"apiToken": "<API_TOKEN>"
	}
	esEndpoint = {
		"host": "<HOST_NAME>",
		"port": "<PORT>",
		"restAuth": {
			"type": "basic",
			"username": "<USER>",
			"password": "<PASSWORD>"
		}
	}

	deviceDisplay = {
		"id": "domain.vpn", 
		"displayName": "VPN", 
		"type": "DHS VPN",
#		"ipAddresses":["<IP>"], 
#		"listenPorts":["<PORT>"], 
#		"configUrl":"",
		"tags": ["DHS VPN"],
		"favicon":"http://assets.dynatrace.com/global/icons/infographic_rack.png",
		"groupId": "DHS VPN",
		"properties": {}
	}

	timeQuery = { #in seconds
		"shiftBy":0 ,
		"interval": 270
	}

	logDetails = {"level":"debug", "location": "./DTVPNESMon.log"}
	vpn = DTVPNESMon(dtendpoint, esEndpoint, "logstash_vpnsessions", deviceDisplay, logDetails=logDetails, timeQueryInSec=timeQuery)
	vpn.dtrun()

	return
	
if __name__ == '__main__':
  main()		
