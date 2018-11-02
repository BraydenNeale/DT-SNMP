from dtmon.dtsandblast import DTSandblastMon

def main():
	dtendpoint = {
		"url": "<DT_URL>",
		"apiToken": "<API_TOKEN>"
	}
	
	sandblastEndpoint = {
		"host": "<IP>",
		"port": 161,
		"snmpAuth": {
			"version": 3,
			"username": "<USEER>",
			"authKey": "<AUTH_KEY>",
			"privKey": "<PRIV_KEY>",
			"authProtocol": "<AUTH_PROT>",
			"privProtocol": "<PRIV_PROT>"
		}
	}
	
	deviceDisplay = {
		"id": "domain.checkpoint.sandblast.<HOST_NAME>", 
		"displayName": "<HOST_NAME> | Sandblast", 
		"type": "Checkpoint-Sandblast",
		"ipAddresses":["<IP>"], 
		"listenPorts":["<PORT>"], 
#		"configUrl":"",
		"tags": ["Checkpoint", "Sandblast"],
		"favicon":"http://assets.dynatrace.com/global/icons/infographic_rack.png",
		"groupId": "Checkpoint-Sandblast",
		"properties": {}
	}

	
	
	logDetails = {"level":"debug", "location": "./DTSandblastSNMPMon.log"}
	
	sandblast = DTSandblastMon(dtendpoint, sandblastEndpoint, deviceDisplay, logDetails=logDetails, getLatency=True, mib={"use": False})
	t_sandblast = sandblast.dtrun()
	t_sandblast.join()

	return
	
if __name__ == '__main__':
  main()		