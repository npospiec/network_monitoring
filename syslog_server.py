# http://ba-gitlab.cisco.com/svs/ba_core_migration/tree/94334298109c85757559d9898470ffae51931d51/nrfu

import socketserver as SocketServer
import threading
import time, datetime


class SyslogUDPHandler(SocketServer.BaseRequestHandler):

    LOG = {}

    def handle(self):
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        data = bytes.decode(self.request[0].strip(), errors='ignore')

        if self.client_address[0] not in self.LOG.keys():
            self.LOG[self.client_address[0]] = []

        self.LOG[self.client_address[0]].append({st:str(data)})

class SyslogUDPServer(SocketServer.UDPServer):
    def return_logfile(self):
        return self.RequestHandlerClass.LOG

    def clear_logs(self):
        self.RequestHandlerClass.LOG = {}
