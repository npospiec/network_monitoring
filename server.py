from syslog_server import SyslogUDPHandler, SyslogUDPServer
from snmp_server import SNMPserver
import threading
from copy import deepcopy

# TODO: read config from json file

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
# Listener to adjust state of the server
class ServerInterface():
    """This class serves as a common interfaces between different server fucntion
    Design: Facade pattern
    """

    def __init__(self):
        self.snmpServer = None
        self.snmpTrapReceiverThread = None
        self.syslogServer = None
        self.syslogThread = None
        self.db = DB
        self._state = {
            # if False - service not running
            "syslogServer" : False,
            "snmpServer" : False
        }

    def return_log(self, service):
        self.update_logs()

    def update_logs(self):
        if self.snmpServer is not None:
            self.db['logs']['snmpServer'] = self.snmpServer.traps
        if self.syslogServer is not None:
            self.db['logs']['syslogServer'] = self.syslogServer.return_logfile()

    def clear_logs(self):
        if self.snmpServer is not None:
            self.snmpServer.traps = {}
        if self.syslogServer is not None:
            self.syslogServer.clear_logs()
    def service_handler(self,):
        # this function updates the services state to align with the configuration
        states = {}
        # check syslogService
        # is it running?
        for service in self.db['services']:

            cfg_state = self.db['services'][service]['running'].lower() # will be string - yes/no
            act_state = self._state[service] # bool
            # is it configured to run?

            # if running and connfigured to run - change in state
            if act_state and cfg_state == 'yes':
                states[service] = 'Service is running'

            # if running and configured NOT to run - shutting down
            if act_state and cfg_state == 'no':
                states[service] = 'Shutting down {}'.format(service)
                self.__getattribute__(service + '_stop')()

            # if not running and configured to run - starting
            if not act_state and cfg_state == 'yes':
                states[service] = '{} is staring.'.format(service)
                self.__getattribute__(service + '_start')()
            # if not running and configured NOT to run - no change in state
        return states
    def _syslogServer_initialize(self):
        # starts server with the settings from self.config
        ip = self.db['services']['syslogServer']['listenerAddress']
        port = int(self.db['services']['syslogServer']['listenerPort'])

        self.syslogServer = SyslogUDPServer((ip, port), SyslogUDPHandler)

    def syslogServer_start(self):

        if not self.syslogServer:
            self._syslogServer_initialize()

        if self.syslogThread:
            print('Syslog Server is already running.')
        else:
            # Start Server in a Thread
            self.syslogThread = threading.Thread(target=self.syslogServer.serve_forever)
            self.syslogThread.daemon = True

            self.syslogThread.start()
            self._state['syslogServer'] = True

    def syslogServer_stop(self):
        self.syslogServer.shutdown()
        self.syslogThread.join()
        self.syslogThread = None
        self._state['syslogServer'] = False


    def _snmpServer_initialize(self):
        # starts server with the settings from self.config
        ip = self.db['services']['snmpServer']['listenerAddress']
        port = self.db['services']['snmpServer']['listenerPort']
        community = self.db['services']['snmpServer']['community']

        self.snmpServer = SNMPserver(ip, port, community)


    def snmpServer_start(self):

        if not self.snmpServer:
            self._snmpServer_initialize()

        if self.snmpTrapReceiverThread:
            print('Trap receiver is already running.')
        else:
            self.snmpTrapReceiverThread = threading.Thread(target=self.snmpServer.trap_receiver)
            self.snmpTrapReceiverThread.daemon = True
            self.snmpTrapReceiverThread.start()
            self._state['snmpServer'] = True

    def snmpServer_stop(self):

        self.snmpServer.snmpEngine.transportDispatcher.jobFinished(1)
        self.snmpServer.unregister_ntfrcv()
        self.snmpTrapReceiverThread = None

        self._state['snmpServer'] = False

    # TODO: pysnmp.smi.error.NoSuchObjectError
    # TODO: Exception: No SNMP response received before timeout
    def snmpServer_get(self, ip, port, oid):
        if not self.snmpServer:
            self._snmpServer_initialize()
        rtn_msg = self.snmpServer.snmpget(ip, port, oid)
        return rtn_msg


def merge_config(a, b):
    if not isinstance(b, dict):
        return b
    result = deepcopy(a)
    for k, v in b.items():
        if k in result and isinstance(result[k], dict):
            result[k] = merge_config(result[k], v)
        else:
            result[k] = deepcopy(v)
    return result




