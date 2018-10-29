from dtmon.dtsandblast import DTSandblastMon

def main():
	# PROD
	dtendpoint = {
		"url": "<URL>",
		"apiToken": "<API>"
    }
	
	dlpEndpoint1 = {
		"host": "<HOST_NAME>",
		"port": 161,
		"snmpAuth": {
			"version": 3,
			"username": "<USWR>",
			"authKey": "<AUTH_KEY>",
			"privKey": "<PRIV_KEY>",
			"authProtocol": "<AUTH_PROT>",
			"privProtocol": "<PRIV_PROT>"
		}
	}
	
	deviceDisplay1 = {
		"id": "<DOMAIN>.checkpoint.dlp.<HOST_NAME>", 
		"displayName": "<HOST_NAME> | DLP", 
		"type": "Checkpoint-DLP",
		"ipAddresses":["<IP>"], 
		"listenPorts":["<PORT>"], 
#		"configUrl":"",
		"tags": ["Checkpoint", "DLP"],
		"favicon":"http://assets.dynatrace.com/global/icons/infographic_rack.png",
		"groupId": "Checkpoint-DLP",
		"properties": {}
	}

	dlpEndpoint2 = {
		"host": "<HOST_NAME>",
		"port": 161,
		"snmpAuth": {
			"version": 3,
			"username": "<USER>",
			"authKey": "<AUTH_KEY>",
			"privKey": "<PRIV_KEY>",
			"authProtocol": "<AUTH_PROT>",
			"privProtocol": "<PRIV_PROT>"
		}
	}
	
	deviceDisplay2 = {
		"id": "<DOMAIN>.checkpoint.dlp.<HOST_NAME>", 
		"displayName": "<HOST_NAME> | DLP", 
		"type": "Checkpoint-DLP",
		"ipAddresses":["<IP>"], 
		"listenPorts":["<PORT>"], 
#		"configUrl":"",
		"tags": ["Checkpoint", "DLP"],
		"favicon":"http://assets.dynatrace.com/global/icons/infographic_rack.png",
		"groupId": "Checkpoint-DLP",
		"properties": {}
	}

	logDetails = {"level":"error", "location": "./DTDLPSNMPMon.log"}
	
	dlp1 = DTSandblastMon(dtendpoint, dlpEndpoint1, deviceDisplay1, logDetails=logDetails, getLatency=False, mib={"use": False})
	t_dlp1 = dlp1.dtrun()

	dlp2 = DTSandblastMon(dtendpoint, dlpEndpoint2, deviceDisplay2, logDetails=logDetails, getLatency=False, mib={"use": False})
	t_dlp2 = dlp2.dtrun()

	t_dlp1.join()
	t_dlp2.join()

	return
	
if __name__ == '__main__':
  main()		
