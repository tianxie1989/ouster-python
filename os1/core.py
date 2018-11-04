import socket
from functools import partial

from os1.server import SynchronousRequestHandler, UDPServer


class OS1ConfigurationError(Exception):
    pass


class OS1(object):
    def __init__(self, host, dest_host, port=7502, mode=16):
        self.dest_host = dest_host
        self.port = port
        self.mode = mode
        self.api = OS1API(host)

    def start(self):
        self.api.set_config_param("udp_ip", self.dest_host)
        self.api.raise_for_error()

        self.api.reinitialize()
        self.api.raise_for_error()

    def run_forever(self, handler):
        request_handler = partial(SynchronousRequestHandler, handler)
        with UDPServer((self.dest_host, self.port), request_handler) as server:
            server.serve_forever()

    def __getattr__(self, name):
        return getattr(self.api, name)


class OS1API(object):
    def __init__(self, host, port=7501):
        self.address = (host, port)
        self._error = None

    def get_config_txt(self):
        return self._send("get_config_txt")

    def get_sensor_info(self):
        return self._send("get_sensor_info")

    def get_beam_intrinsics(self):
        return self._send("get_beam_intrinsics")

    def get_imu_intrinsics(self):
        return self._send("get_imu_intrinsics")

    def get_lidar_intrinsics(self):
        return self._send("get_lidar_intrinsics")

    def get_config_param(self, *args):
        command = "get_config_param {}".format(" ".join(args))
        return self._send(command)

    def set_config_param(self, *args):
        command = "set_config_param {}".format(" ".join(args))
        return self._send(command)

    def reinitialize(self):
        return self._send("reinitialize")

    def raise_for_error(self):
        if self.has_error:
            raise OS1ConfigurationError(self._error)

    @property
    def has_error(self):
        if self._error is not None:
            return True
        return False

    def _send(self, command, *args):
        self._error = None
        payload = " ".join([command] + list(args)).encode("utf-8") + b"\n"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(self.address)
            sock.sendall(payload)
            response = sock.recv(8192)
        return response

    def _error_check(self, response):
        response = response.decode("utf-8")
        if response.startswith("error"):
            self._error = response
        else:
            self._error = None