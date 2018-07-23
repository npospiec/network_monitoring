import socketserver as SocketServer
import threading
import time
import datetime
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import ntfrcv
from pysnmp.hlapi import *
from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.carrier.asyncore.dgram import udp, udp6, unix
from pyasn1.codec.ber import decoder
from pysnmp.proto import api



class SNMPserver():


    def __init__(self, ip, port, community='public'):

        self.LISTENER = ip
        self.LISTENER_PORT = port
        self.snmpEngine = engine.SnmpEngine()
        self.trap_sources = []
        self.community = community
        self.traps = {}
        config.addTransport(
            self.snmpEngine,
            udp.domainName + (1,),
            udp.UdpTransport().openServerMode((self.LISTENER, self.LISTENER_PORT))
        )
        print('Starting SNMP server on %s port %s with community %s.' % (
        self.LISTENER, self.LISTENER_PORT, community))
        config.addV1System(self.snmpEngine, 'testindex', community)
        self.stopped = False

    def cbFun(self, snmpEngine,
              stateReference,
              contextEngineId, contextName,
              varBinds,
              cbCtx):
        transportDomain, transportAddress = snmpEngine.msgAndPduDsp.getTransportInfo(stateReference)

        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        if transportAddress[0] not in self.trap_sources:
            self.trap_sources.append(transportAddress[0])
            print(transportAddress[0])
            # for name, val in varBinds:
            #     print('%s = %s' % (name.prettyPrint(), val.prettyPrint()))
        if transportAddress[0] not in self.traps.keys():
            self.traps[transportAddress[0]] = {}

        print('Notification from %s, SNMP Engine %s, Context %s' % (
            transportAddress, contextEngineId.prettyPrint(),
            contextName.prettyPrint()
        )
              )
        trap_args = []
        for name, val in varBinds:
            trap_args.append('%s = %s' % (name.prettyPrint(), val.prettyPrint()))
            print('%s = %s' % (name.prettyPrint(), val.prettyPrint()))
        self.traps[transportAddress[0]][st] = trap_args

    def trap_receiver(self):

        self.ntfrcv = ntfrcv.NotificationReceiver(self.snmpEngine, self.cbFun)

        self.snmpEngine.transportDispatcher.jobStarted(1)  # this job would never finish

        try:
            self.snmpEngine.transportDispatcher.runDispatcher()
        except:
            self.snmpEngine.transportDispatcher.closeDispatcher()
            raise
        if self.stopped:
            return
    def unregister_ntfrcv(self):

        self.ntfrcv.close(self.snmpEngine)

    def snmpget(self, ip, port, oid='1.3.6.1.2.1.1.5.0'):
        rtn_data = {}
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   CommunityData(self.community),
                   UdpTransportTarget((ip, int(port))),
                   ContextData(),
                   ObjectType(ObjectIdentity(oid)))
        )
        if errorIndication:
            raise Exception(errorIndication)
        elif errorStatus:

            rtn_data['error'] = '%s at %s' % (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?')
        else:

            for varBind in varBinds:
                data =  [x.prettyPrint() for x in varBind]
                rtn_data[data[0]] = data[1:]

        return rtn_data

