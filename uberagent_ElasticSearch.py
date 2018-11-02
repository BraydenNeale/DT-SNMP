from dtmon.dtuberagentesmon import DTUbserAgentESMon

def main():
	dtendpoint = {
		"url": "<DT_URL>",
		"apiToken": "<API>"
	}
	esEndpoint = {
		"host": "<HOSTNAME>",
		"port": "<PORT>",
		"restAuth": {
			"type": "basic",
			"username": "<USER>",
			"password": "<PASSWORD>"
		}
	}

	deviceDisplay = {
		"id": "domain.uberagent.DPT NAME", 
		"displayName": "DPT NAME Uber Agent", 
		"type": "DPT NAME Uber Agent",
#		"ipAddresses":["10.2.244.95"], 
#		"listenPorts":["161"], 
#		"configUrl":"",
		"tags": ["DPT NAME", "Uber Agent"],
		"favicon":"http://assets.dynatrace.com/global/icons/infographic_rack.png",
		"groupId": "DPT NAME Uber Agent",
		"properties": {}
	}

	timeQuery = { #in seconds
		"shiftBy":60 ,
		"interval": 60
	}

	logDetails = {"level":"error", "location": "./DTDPT NAMEUberAgentESMon.log"}
	vpn = DTUbserAgentESMon(dtendpoint, esEndpoint, "uberagent", deviceDisplay, sites=["ELZA", "HBAR", "GELO"], logDetails=logDetails, timeQueryInSec=timeQuery)
	vpn.dtrun()

	return
	
if __name__ == '__main__':
  main()		
