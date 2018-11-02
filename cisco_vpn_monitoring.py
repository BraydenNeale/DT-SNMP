from dtmon.dtciscosnmp import DTCiscoMon

def main():
	dtendpoint = {
		"url": "<DT_URL>",
		"apiToken": "<API_TOKEN>"
	}
	
	vpnEndpoint1 = {
		"host": "<IP>",
		"port": 161,
		"snmpAuth": {
			"version": 2,
			"username": "<COMMUNITY_STRING>"
		}
	}
	
	deviceDisplay1 = {
		"id": "domain.cisco.vpn.<HOST_NAME>", 
		"displayName": "<HOST_NAME> | Cisco VPN", 
		"type": "Cisco VPN",
		"ipAddresses":["<IP>"], 
		"listenPorts":["<PORT>"], 
#		"configUrl":"",
		"tags": ["Cisco VPN", "Cisco", "VPN"],
		"favicon":"http://assets.dynatrace.com/global/icons/infographic_rack.png",
		"groupId": "Cisco VPN",
		"properties": {}
	}

	vpnEndpoint2 = {
		"host": "<IP>",
		"port": 161,
		"snmpAuth": {
			"version": 2,
			"username": "<COMMUNITY_STRING>"
		}
	}
	
	deviceDisplay2 = {
		"id": "domain.cisco.vpn.<HOST_NAME", 
		"displayName": "<HOST_NAME> | Cisco VPN", 
		"type": "Cisco VPN",
		"ipAddresses":["<IP>"],
		"listenPorts":["161"], 
#		"configUrl":"",
		"tags": ["Cisco VPN", "Cisco", "VPN"],
		"favicon":"http://assets.dynatrace.com/global/icons/infographic_rack.png",
		"groupId": "Cisco VPN",
		"properties": {}
	}
	
	logDetails = {"level":"error", "location": "./DTCiscoVPNMon.log"}
	
	vpn1 = DTCiscoMon(dtendpoint, vpnEndpoint1, deviceDisplay1, logDetails=logDetails, getLatency=False, mib={"use": False}, tsPrefix="domain.cisco.vpn")
	t_vpn1 = vpn1.dtrun()
	
	vpn2 = DTCiscoMon(dtendpoint, vpnEndpoint2, deviceDisplay2, logDetails=logDetails, getLatency=False, mib={"use": False})
	t_vpn2 = vpn2.dtrun()
	
	vpn3 = DTCiscoMon(dtendpoint, vpnEndpoint3, deviceDisplay3, logDetails=logDetails, getLatency=False, mib={"use": False})
	t_vpn3 = vpn3.dtrun()

	t_vpn1.join()
	t_vpn2.join()
	t_vpn3.join()

	return
	
if __name__ == '__main__':
  main()		
