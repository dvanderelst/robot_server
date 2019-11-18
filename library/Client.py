import socket
import paramiko
import logging
import threading
import sys
import os
import errno
import time
import easygui
from library import Misc


def read_filelist():
    current_dir = os.path.dirname(__file__)
    list_file = os.path.join(current_dir, 'filelist.txt')
    f = open(list_file, 'r')
    files = f.readlines()
    f.close()
    while '\n' in files: files.remove('\n')
    new = []
    for x in files: new.append(x.rstrip('\n'))
    return new


class Client:
    def __init__(self, do_upload=True, run_locally=False):
        # create logger with
        self.logger = logging.getLogger('client')
        self.logger.setLevel(logging.INFO)
        # create file handler which logs even debug messages
        self.file_logger = logging.FileHandler('client.log', mode='w')
        self.file_logger.setLevel(logging.INFO)
        # create console handler with a higher log level
        self.console_logger = logging.StreamHandler(sys.stdout)
        self.console_logger.setLevel(logging.INFO)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.file_logger.setFormatter(formatter)
        self.console_logger.setFormatter(formatter)
        # add the handlers to the logger
        self.logger.addHandler(self.file_logger)
        self.logger.addHandler(self.console_logger)
        self.run_locally = run_locally

        self.logging = False
        self.logfile = None
        self.__stop_loop = False

        if not self.run_locally:
            self.remote = '192.168.0.109'
            self.remote_python = '/home/batman/anaconda2/bin/python'
            self.remote_dir = '/home/batman/Desktop/server/'
            self.remote_script = 'start_server.py'
            self.local_dir = os.getcwd()
            self.user = 'batman'
            self.password = 'robin'

        if self.run_locally:
            self.remote = 'localhost'
            self.remote_python = '/home/dieter/anaconda3/envs/default/bin/python'
            self.remote_dir = '/home/dieter/Desktop/testing/'
            self.remote_script = 'start_server.py'
            self.local_dir = os.getcwd()
            self.user = 'dieter'
            self.password = None

        if self.password is None: self.password = easygui.passwordbox('password for the remote computer')

        # Open Ssh
        # self.start_logging()
        self.print_log('Starting Client')
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.remote, username=self.user, password=self.password, timeout=3)
        # Open FTP
        transport = paramiko.Transport((self.remote, 22))
        transport.default_window_size = 10 * 1024 * 1024
        transport.connect(username=self.user, password=self.password)
        self.sftp = paramiko.SFTPClient.from_transport(transport)

        # Do Upload
        if do_upload: self.upload_files(verbose=True)

    def __del__(self):
        self.ssh.close()
        self.sftp.close()

    ##################################
    # ROBOT CONTROL FUNCTIONS
    ##################################
    def test_communication(self, message=[]):
        arguments = ['Test communication', 1, 2, 3] + message
        command = Misc.lst2command(arguments)
        reply = self.send_command(command, 10000)
        self.print_log([reply])

    ##################################
    # SUPPORT FUNCTIONS
    ##################################

    # def start_logging(self, filename='client.log', erase=False):
    #     # create file handler which logs even debug messages
    #     mode = 'a'
    #     if erase: mode = 'w'
    #     self.file_logger = logging.FileHandler(filename, mode=mode)
    #     self.file_logger.setLevel(logging.INFO)
    #     formatter = logging.Formatter('%(asctime)s - %(cluttered_name)s - %(levelname)s - %(message)s')
    #     self.file_logger.setFormatter(formatter)
    #     self.logger.addHandler(self.file_logger)

    def stop_logging(self):
        self.file_logger.close()

    def print_log(self, text, level='i'):
        text = Misc.lst2str(text)
        text = Misc.lst2str(text)
        if level == 'i': self.logger.info(text)
        if level == 'w': self.logger.warning(text)
        if level == 'c': self.logger.critical(text)

    ##################################
    # SERVER CONTROL FUNCTIONS
    ##################################

    def send_command(self, command, port, answer=True):
        if not command.endswith('*'): command += '*'
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.remote, port)
        sock.connect(server_address)
        sock.send(command.encode())
        data = ''
        if not answer: return data
        while 1:
            packet = sock.recv(1024)
            packet = packet.decode()
            data += packet
            if data.endswith('*'): break
        data = data.rstrip('*')
        return data

    def stop_remote_server(self):
        a = self.send_command('close', 12345, answer=True)
        self.print_log([a])
        self.__stop_loop = True

    def start_remote_server(self):
        if not self.run_locally: self.stop_remote_python()
        t = threading.Thread(target=self.remote_server_process)
        t.start()
        time.sleep(5)

    def stop_remote_python(self):
        stdin, stdout, stderr = self.ssh.exec_command('killall python')
        time.sleep(2.5)
        self.print_log(['Stopping Remote Python'])
        a = stdout.read()
        b = stderr.read()
        output = a + b
        output = output.replace('\n', '')
        self.print_log([output])

    def remote_server_process(self):
        command = self.remote_python + ' ' + self.remote_dir + self.remote_script
        channel = self.ssh.get_transport()
        channel = channel.open_session()
        channel.get_pty()
        channel.exec_command(command)
        while True:
            if channel.recv_ready():
                data = channel.recv(10)
                data = data.decode()
                sys.stdout.write(data)
            else:
                # only break if there is no more data to be read from the remote session
                if self.__stop_loop: break
        self.__stop_loop = False
        if not self.run_locally: self.stop_remote_python()
        self.ssh.close()

    ##################################
    # SFTP FUNCTIONS
    ##################################

    def remote_folder_exists(self, folder):
        try:
            self.sftp.stat(folder)
        except IOError as e:
            if e.errno == errno.ENOENT: return False
            raise
        else:
            return True

    def delete_remote_folder(self, folder):
        files = self.sftp.listdir(folder)
        for file_name in files:
            file_path = os.path.join(folder, file_name)
            try:
                self.sftp.remove(file_path)
            except IOError:
                self.delete_remote_folder(file_path)
        self.sftp.rmdir(folder)

    def upload_files(self, verbose=False):
        if verbose: print('Uploading files')
        if self.remote_folder_exists(self.remote_dir): self.delete_remote_folder(self.remote_dir)
        if not self.remote_folder_exists(self.remote_dir): self.sftp.mkdir(self.remote_dir)
        files = read_filelist()
        for local_file in files:
            parts = os.path.split(local_file)
            remote_file = os.path.join(self.remote_dir, parts[0], parts[1])
            remote_dir = os.path.join(self.remote_dir, parts[0])
            if not self.remote_folder_exists(remote_dir): self.sftp.mkdir(remote_dir)
            self.sftp.put(local_file, remote_file)
            if verbose: print(local_file, '---->', remote_file)


if __name__ == '__main__':
    c = Client()
