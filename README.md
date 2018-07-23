Simple monitoring server.

Author: npospiec@cisco.com

The application has been created to simplify the testing of network monitoring on various devices.

## Currently supported services:
    - SYSLOG receiver
    - SNMP Management station that includes Trap receiver and SNMP GET functionality.

## Usage
1. Configuring the services
    a. Default configuration:
        The default configuration is included in the database of server module (simple dict variable):
        DB = {
        "services" : {
            "syslogServer" : {
                "listenerAddress" : "0.0.0.0",
                "listenerPort" : 1514,
                "running": "no"
        },
            "snmpServer" : {
                "listenerAddress" : "0.0.0.0",
                "listenerPort": 1993,
                "community" : "public",
                "running" : "no"
        }
        },
        "logs" : {
            "syslogServer" : {},
            "snmpServer" :{}
            }
        }
        This configuration is also returned via API call:
        http GET 127.0.0.1:5000/api/v2/services

    b. Changing the configuration.
        Use API POST method call to change the default configuration:
        http POST 127.0.0.1:5000/api/v2/services/<service> payload
        where:
            service - is one of the available services as described in 1.b.
            payload - json representation of the service arguments as shown in the default configuration (1.b.) e.g.
            {
                "listenerAddress" : "0.0.0.0",
                "port" : 1514
            }
2. Starting/stopping the services
    To start or stop any of the available servcies use POST method outlined in the 1.b., including argument `running`
    with value `yes` or `no' in the request payload. Example:
        http POST 127.0.0.1:5000/api/v2/services/snmpServer running=yes

3. SNMP GET
    First, start the SNMP server using instructions in point 2. To send SNMP get message to device use:
    http POST 127.0.0.1:5000/api/v1/services/snmpServer/snmpGet
        Payload: {
                    "ip" :
                    "port" :
                    "oid" :
                }
4. Logs
    The syslog and trap receiver services keep log of the incoming requestes. The logs are kept in the database under
    `logs\<service>'.
    - To view all log messages use: GET /api/v2/logs
    - To view all log messages for a service use: GET /api/v2/logs/<service>
    - To view all messages for a service and a given IP address use: GET /api/v2/logs/<service>/<ip_address>

    To clear logs use DELETE on /api/v2/logs

5. Return data.
    In most cases the data returned is as seen in the server isntance database. The return codes for valid request: 200
    The error codes can be found in the the code below...