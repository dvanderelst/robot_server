import logging
import os
import socket
import sys
import threading
import time
from library import Misc


def default_function(*args):
    return args


class Server:
    def __init__(self):
        # create logger with
        self.logger = logging.getLogger('server')
        self.logger.setLevel(logging.INFO)
        # create file handler which logs even debug messages
        file_logger = logging.FileHandler('server.log', mode='w')
        file_logger.setLevel(logging.INFO)
        # create console handler with a higher log level
        console_logger = logging.StreamHandler(sys.stdout)
        console_logger.setLevel(logging.INFO)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_logger.setFormatter(formatter)
        console_logger.setFormatter(formatter)
        # add the handlers to the logger
        self.logger.addHandler(file_logger)
        self.logger.addHandler(console_logger)

        # some defaults
        self.break_character = '*'

        host = socket.gethostname()
        self.buffer = 1024
        self.host = host
        self.log = []
        self.sockets = []
        self.print_log('Starting server at ' + host)
        self.print_log('Server working directory: ' + os.getcwd())

        # Bind functions
        self.open_connection(12345, self.shutdown)
        self.open_connection(10000, bind_function=self.test_communiction)

    ########################################
    # ROBOT FUNCTIONS
    ########################################

    def test_communiction(self, args):
        if not type(args) == list: args = [args]
        return 'success'

    ########################################
    # SERVER FUNCTIONS
    ########################################

    def print_log(self, text, level='i'):
        text = Misc.lst2str(text)
        if level == 'i': self.logger.info(text)
        if level == 'w': self.logger.warning(text)
        if level == 'c': self.logger.critical(text)

    def open_socket(self, port_number):
        self.sockets.append(port_number)
        skt = socket.socket()
        skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        skt.bind(('', port_number))
        skt.listen(1)
        return skt

    def receive_data(self, connection):
        data = ''
        while 1:
            packet = connection.recv(self.buffer)
            packet = packet.decode()
            if not packet: break
            data += packet
            if data.endswith(self.break_character): break
        data = data.rstrip(self.break_character + '\n')
        return data

    def open_connection(self, port_number, bind_function=default_function):
        t = threading.Thread(target=self.open_single_connection, args=(port_number, bind_function))
        t.start()

    def close_connection(self, port_number):
        message = 'close' + self.break_character
        message = message.encode()
        self.print_log(['Closing', port_number])
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('', port_number)
        sock.connect(server_address)
        sock.sendall(message)
        sock.close()

    def shutdown(self):
        ports = self.sockets
        self.print_log(['Shutting down Ports'] + ports)
        if 12345 in ports: ports.remove(12345)
        for port_number in ports: self.close_connection(port_number)
        self.close_connection(12345)
        self.print_log(['Finished shutting down'])
        self.sockets = []

    def open_single_connection(self, port_number, bind_function=default_function):
        function_name = bind_function.__name__
        self.print_log(['Opening connection for', function_name, 'on port', port_number])
        skt = self.open_socket(port_number)
        while 1:
            self.print_log(['Listening for', function_name, 'on port', port_number])
            connection, address = skt.accept()
            start = time.time()
            arguments = self.receive_data(connection)
            arguments = arguments.split(',')
            if function_name == 'shutdown':
                self.shutdown()
                break
            if 'close' in arguments[0]: break
            results = bind_function(arguments)
            results = str(results)
            if not results.endswith(self.break_character): results += self.break_character
            results = str(results)
            results = results.encode()
            connection.sendall(results)
            connection.close()
            stop = time.time()
            delta = round((stop - start) * 1000)
            self.print_log(['Response time for', function_name, ':', delta, 'ms'])
        self.print_log(['Closing connection for', function_name, 'on port', port_number])
        if 'close' in arguments[0]: connection.sendall('closed ' + str(port_number) + self.break_character)
        connection.close()
        skt.close()
