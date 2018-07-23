from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from server import ServerInterface, merge_config

# TODO add bad request validation for json data
app = Flask(__name__)
api = Api(app)

# Server Facade
SERVER = ServerInterface()


def resource_doesnt_exist(resource, dictionary):
    if resource not in dictionary.keys():
        abort(404, message="Resource {} doesn't exist".format(resource))

parser = reqparse.RequestParser()
parser.add_argument('task')


class Services(Resource):
    """ Returns list of services and configuration

    Example:
        `http GET 127.0.0.1:5000/api/v2/services`
    """

    def get(self):
        return SERVER.db['services'], 200


class ServiceAPI(Resource):
    """ Using GET returns configuration of the service defined in the DB of the Server Instance
    POST takes JSON data as inputs. The arguments are different depending of the service and are validated
    against the Server Instance database. e.g:
    {
            "listenerAddress" : "0.0.0.0",
            "listenerPort": 1993,
            "community" : "public",
            "running" : "no"
    }

    Examples:
        GET:
        `http GET 127.0.0.1:5000/api/v2/services/snmpServer`

        POST:
        `http POST 127.0.0.1:5000/api/v2/services/syslogServer listenerAddress=0.0.0.0 listenerPort=1993 running=yes`

    """
    def get(self, service):
        """ Response payload: {
                                service configuration arguments as defined in Server Instance DB
                            }

                 """
        resource_doesnt_exist(service, SERVER.db['services'])
        return SERVER.db['services'][service]

    def post(self, service):
        """Response payload if service is found
                {
                    "syslogServer": "syslogServer is staring."
                }
            If service is not found it will return 404.
        """
        resource_doesnt_exist(service, SERVER.db['services']) # verify if service exists on the server, 404 if not.
        parser = reqparse.RequestParser()
        for arg in SERVER.db['services'][service].keys():
            parser.add_argument(arg, type=str,
                                     required=False,
                                     default=SERVER.db['services'][service][arg],
                                     help='Valid arguments for {} are {}'.format(service, '; '.join(
                                         list(SERVER.db['services'][service].keys()))))
        merged_services = merge_config(SERVER.db['services'], {service: parser.parse_args()})
        SERVER.db['services'] = merged_services # apply the arguments to the db on the Server Instance

        # now push the argument to the server and update the running services accordingly
        states = SERVER.service_handler()
        return states, 200

class snmpGet(Resource):

    def post(self):
        # verify if the snmpService is running.
        parser = reqparse.RequestParser()
        parser.add_argument('ip', type=str, required=True, help='Valid IP address is required!')
        parser.add_argument('port', required=True, help='Valid port is required!')
        parser.add_argument('oid', required=True, help='Valid SNMP OID is required!')
        call_args = parser.parse_args()
        return SERVER.snmpServer_get(call_args['ip'], call_args['port'], call_args['oid']), 200

class Logs(Resource):
    """ Returns all services' logs."""
    def get(self):
        SERVER.update_logs()
        return SERVER.db['logs'], 200

    def delete(self):
        SERVER.clear_logs()
        return SERVER.db['logs'], 200
class LogAPI(Resource):
    """ Using GET returns log for a specified service.
    Using DELETE, clears logs for the specified service."""
    def get(self, service):
        resource_doesnt_exist(service, SERVER.db['logs'])
        SERVER.update_logs()
        return SERVER.db['logs'][service]

    # def delete(self, service):
    #     resource_doesnt_exist(service, SERVER.db['logs'])
    #     SERVER.update_logs()
    #     SERVER.db['logs'][service] = {}
    #     return SERVER.db['logs'][service], 200


class LogAPIip(Resource):
    """ Using GET returns the log for the IP address inside of the service.
    Using DELETE, clears log sourced with the IP as specified in the argument."""
    def get(self, service, ip):
        resource_doesnt_exist(service, SERVER.db['logs'])
        SERVER.update_logs()
        if ip not in SERVER.db['logs'][service]:
            return {ip: 'Log not found'}, 404
        else:
            return {SERVER.db['logs']['service'][ip]}, 200

    # def delete(self, service, ip):
    #     resource_doesnt_exist(service, SERVER.db['logs'])
    #     SERVER.update_logs()
    #     SERVER.db['logs'][service].pop(ip, None)
    #     return {}, 200

## Actually setup the Api resource routing here
##
api.add_resource(Services, '/api/v2/services')
api.add_resource(ServiceAPI, '/api/v2/services/<service>')
api.add_resource(snmpGet, '/api/v1/services/snmpServer/snmpGet')
api.add_resource(Logs, '/api/v2/logs')
api.add_resource(LogAPI, '/api/v2/logs/<service>')
api.add_resource(LogAPIip, '/api/v2/logs/<service>/<ip>')

if __name__ == '__main__':
    app.run(debug=True)