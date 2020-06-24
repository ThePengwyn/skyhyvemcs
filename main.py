import io
import sys
import os
import signal
import json
import configparser
import ssl
import threading

from http.server import HTTPServer, BaseHTTPRequestHandler

class SkyHyveMemcacheRequestHandler(BaseHTTPRequestHandler):

    def parse_path_index(self):
        return [x for x in self.path.split('/') if x!= '']

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'This is a SkyHyve Memcache Server Instance.')

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(content_length).decode())
        persist = body['PERSIST'] and self.server.persistent
        data = body['DATA']

        path_indexes = self.parse_path_index()
        response_data = self.server.SET(index_list=path_indexes, value=data, persist=persist)

        if response_data['SUCCESS'] == True:
            self.send_response(200)
        else:
            self.send_response(400)

        self.send_response(200)
        self.end_headers()

        response = io.BytesIO()
        response.write(json.dumps(response_data['DATA']).encode())
        self.wfile.write(response.getvalue())

class PathError(Exception):

    pass

class SkyHyveMemcacheServer(HTTPServer):

    def __init__(self, config, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = config
        self.database_params = self.config['Database']

        self.persistent = self.database_params['Persistent']
        self.db_dir = self.database_params['Dir']

        self.memdb = {}

    def set_value(self, memdb, index_list, value, persist, dbpath):

        if len(index_list) == 0:
            pass
        if len(index_list) == 1:
            memdb[index_list[0]] = value
            if persist:
                datafile = open(self.db_dir + dbpath + index_list[0], "w+")
                datafile.truncate(0)
                datafile.write(json.dumps(value))
                datafile.close()
        else:
            if bool(memdb.get(index_list[0])):
                self.set_value(memdb=memdb[index_list[0]], index_list=memdb[1:], value=value, persist=persist, dbpath=dbpath+index_list[0]+'/')
            else:
                memdb[index_list[0]] = {}
                if persist:
                    dir_path = self.db_dir + dbpath + index_list[0] + '/'
                    if not os.path.isdir(dir_path):
                        os.makedirs(dir_path)
                self.set_value(memdb=memdb[index_list[0]], index_list=index_list[1:], value=value, persist=persist, dbpath=dbpath+index_list[0]+'/')

    def GET(self,index_list):

        pass

    def SET(self, index_list, value, persist=True):

        try:
            self.set_value(memdb=self.memdb, index_list=index_list, value=value, persist=persist, dbpath='')
            assert 1 == 2
            return {
                'SUCCESS': True,
                'DATA': None
            }
        except:
            return {
                'SUCCESS': False,
                'DATA': str(sys.exc_info())
            }

class ConfigurationError(Exception):

    def __init__(self, error_message, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_message = error_message

    def __str__(self):
        return self.error_message

class ShutdownWorker:

    def __init__(self, memcache):

        self.memcache = memcache

    def __call__(self):

        self.memcache.server.shutdown()
        self.memcache.server.server_close()
        sys.exit()

class SkyHyveMemcache:

    CONFIG_PATH = './default.conf'
    REQUIRED_SECTIONS = [
        'Server',
        'Database'
    ]

    def __init__(self):

        self.set_signal_handlers()

        self.config = configparser.ConfigParser()
        self.config.read(self.CONFIG_PATH)

        self.validate_config()

    def set_signal_handlers(self):

        signal.signal(signal.SIGINT, self.SIGINT)
        signal.signal(signal.SIGTERM, self.SIGTERM)

    def SIGINT(self, signalNumber, frame):

        print('SIGINT: Shutting Down')
        self.shutdown()

    def SIGTERM(self,signalNumber, frame):

        print('SIGTERM: Shutting Down')
        self.shutdown()

    def shutdown(self):

        shutdown_worker = ShutdownWorker(memcache=self)
        shutdown_thread = threading.Thread(target=shutdown_worker, daemon=False)
        shutdown_thread.start()

    def validate_config(self):

        for section in self.REQUIRED_SECTIONS:
            if not bool(self.config.has_section(section)):
                raise ConfigurationError("Configuration File at " + self.CONFIG_PATH + " is Missing the Section: ''" + section + "'")

    def run(self):

        if self.config.has_option('Server', 'Port'):
            port_param = int(self.config['Server']['Port'])
        else:
            raise ConfigurationError("Configuration File at " + self.CONFIG_PATH + " is Missing the Option: 'Port' in Section: 'Server'")

        self.server = SkyHyveMemcacheServer(
            server_address=('localhost', port_param),
            RequestHandlerClass=SkyHyveMemcacheRequestHandler,
            config=self.config
        )

        if self.config.has_option('Server', 'SSL'):
            ssl_param = self.config['Server']['SSL']
        else:
            raise ConfigurationError("Configuration File at " + self.CONFIG_PATH + " is Missing the Option: 'SSL' in Section: 'Server'")
        try:
            ssl_param = json.loads(ssl_param.strip().lower())
            assert ssl_param in [True, False]
        except:
            raise ConfigurationError("Configuration File at " + self.CONFIG_PATH + " has Invalid Option: 'SSL' in Section: 'Server'. Must be one of 'True', or 'False'")

        if ssl_param:

            if self.config.has_option('Server', 'Keyfile'):
                keyfile_param = self.config['Server']['Keyfile']
            else:
                raise ConfigurationError("Configuration File at " + self.CONFIG_PATH + " is Missing the Option: 'Keyfile' in Section: 'Server'. If SSL is not supposed to be enabled, set Option: 'SSL' = False")
            if not os.path.isfile(keyfile_param):
                raise ConfigurationError("Configuration File at " + self.CONFIG_PATH + " has Invalid Option: 'Keyfile' in Section: 'Server'. File: '" + keyfile_param + "' not does not exist. If SSL is not supposed to be enabled, set Option: 'SSL' = False")

            if self.config.has_option('Server', 'Certfile'):
                certfile_param = self.config['Server']['Certfile']
            else:
                raise ConfigurationError("Configuration File at " + self.CONFIG_PATH + " is Missing the Option: 'Certfile' in Section: 'Server'. If SSL is not supposed to be enabled, set Option: 'SSL' = False")
            if not os.path.isfile(certfile_param):
                raise ConfigurationError("Configuration File at " + self.CONFIG_PATH + " has Invalid Option: 'Certfile' in Section: 'Server'. File: '" + certfile_param + "' not does not exist. If SSL is not supposed to be enabled, set Option: 'SSL' = False")

            self.server.socket = ssl.wrap_socket(
                self.server.socket,
                keyfile=keyfile_param,
                certfile=certfile_param,
                server_side=True
            )

        self.server.serve_forever()

def main():

    skyhyvemc = SkyHyveMemcache()
    skyhyvemc.run()

if __name__ == "__main__":
    main()
