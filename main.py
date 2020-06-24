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

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        print(self.path.split('/'))
        self.wfile.write(b'This is a SkyHyve Memcache Server Instance.')

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        self.send_response(200)
        self.end_headers()
        response = io.BytesIO()
        response.write(b'This is POST request. ')
        response.write(b'Received: ')
        response.write(body)
        self.wfile.write(response.getvalue())

class PathError(Exception):

    

class SkyHyveMemcacheServer(HTTPServer):

    def __init__(self, config, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = config
        database_params = self.config['Database']

        self.memdb = {}

    def set_value(self, target_dict, index_list, value):

        if len(index_list) == 0:

        if len(index_list) == 1:
            target_dict[index_list[0]] = value
        else:
            if bool(target_dict.get(index_list[0])):
                set_value(target_dict=target_dict[index_list[0]], index_list=index_list[1:], value=value)
            else:
                target_dict[index_list[0]] = {}
                set_value(target_dict=target_dict[index_list[0]], index_list=index_list[1:], value=value)


    def GET(index_list):



    def SET(index_list, persist=True):

        self.set_value(target_dict=self.memdb, index_list=index_list, )

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

    CONFIG_PATH = './skyhyvemc.conf'
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
