import struct

from .models import UserInfo, AttLog, FPInfo, OpLog
from .utils import split_list


class packet(object):
    def __init__(self, data=None, cmd=0, serial=0, payload=b"", secret_key=0xC31E):
        """
        initialize network packet either from bytes data or by filling other parameters
        :param data: packet data in form of bytes
        :param cmd: command number
        :param serial: serial number for packet
        :param payload: payload data carried by packet
        :param secret_key: session key
        """
        self._header = b"\x50\x50\x82\x7D"
        self._cmd = cmd
        self._checksum = 0x00
        self._secret_key = secret_key  # generate random word key
        self._serial = serial
        self._payload = payload
        self._size = len(self._payload) + 8
        if data is not None:
            if len(data) >= 8:
                self._header = data[0:4]
                self._size = struct.unpack("<I", data[4:8])[0]
            if len(data) >= 16:
                self._cmd, self._checksum, self._secret_key, self._serial = struct.unpack("<HHHH", data[8:16])
            if len(data) > 16:
                self._payload = data[16:]

    def is_valid(self, check_sum=True, check_size=False):
        """
        validate packet response
        :param check_sum: validate checksum
        :param check_size: validate size
        :return: True if valid
        """
        ret = self._header == b"\x50\x50\x82\x7D"
        if check_size:
            ret &= self._size == len(self._payload) + 8
        if check_sum:
            data = bytes(self)
            ret &= self._checksum == struct.unpack("<H", data[10:12])[0]
        return ret

    @property
    def secret_key(self):
        return self._secret_key

    @property
    def size(self):
        return self._size

    @property
    def serial(self):
        return self._serial

    @property
    def cmd(self):
        return self._cmd

    @property
    def payload(self):
        return self._payload

    def __bytes__(self):
        """
        return packet in form of data bytes
        :return: packet as data bytes
        """
        self._size = len(self.payload or b'') + 8
        output = self._header
        checksum = 0
        output += struct.pack("<IHHHH", self._size, self._cmd, checksum, self._secret_key, self._serial)
        if self.payload:
            output += self.payload
        checksum = self.calculate_checksum(output)
        return self._header + struct.pack("<IHHHH", self._size, self._cmd, checksum,
                                          self._secret_key, self._serial) + self.payload

    @staticmethod
    def calculate_checksum(input_list):
        """
        calculate checksum for input packet data bytes
        :param input_list: packet in form of bytes
        :return: 2 byte number
        """
        _sum = 0
        size = (len(input_list) // 2) * 2
        for x in range(8, size, 2):
            if x == 10:
                continue
            _sum += struct.unpack("<H", input_list[x:x+2])[0]
            if (_sum >> 31) & 1 == 1:
                _sum = (_sum & 0xFFFF) + (_sum >> 0x10)
        if len(input_list) % 2 > 0:
            _sum += input_list[-1]
        num = _sum
        while num > 0:
            num = _sum >> 0x10
            _sum = (_sum & 0xFFFF) + num
        return (~_sum) & 0xFFFF


class DataBuffer(object):
    def __init__(self, encoding: str, raw_buffer: bytes = None):
        """
        initialize network data buffer from raw_buffer
        :param encoding: default encoding
        :param raw_buffer: data buffer
        """
        self._data = raw_buffer or b''
        self._encoding = encoding

    def add_leading_len(self, size: int = 4):
        """
        add length in front of the raw_buffer
        :param size: size used to represent size either 1, 2, 4
        :return:
        """
        if size == 2:
            fmt = "<H"
        elif size == 1:
            fmt = "<B"
        else:
            fmt = "<I"
        self._data = struct.pack(fmt, len(self._data)) + self._data
    
    def add_leading(self, val: int, size: int = 4):
        """
        add leading val in front of raw_buffer
        :param val: value to add in front of the buffer
        :param size: size of the value either 1, 2, 4
        :return:
        """
        if size == 2:
            fmt = "<H"
        elif size == 1:
            fmt = "<B"
        else:
            fmt = "<I"
        self._data = struct.pack(fmt, val) + self._data

    def remove_leading(self, size=4):
        if len(self._data) > size:
            self._data = self._data[size:]

    def __len__(self):
        """
        return actual length of the internal _data
        :return: internal _data length
        """
        return len(self._data)

    @property
    def data(self):
        """
        get internal data
        :return: internal _data
        """
        return self._data
        # return self._data[self._start:] if len(self._data) > self._start else []
        # return self._data[self._input_leading:] if len(self._data) > self._input_leading else []

    def segment(self, offset, size):
        """
        return segment from internal _data as [offset: offset + size]
        :param offset: start of segment
        :param size: length of segment
        :return: segment of the data in form of bytes
        """
        return self._data[offset: offset + size]
        # return bytes(self)[offset: offset + size]
    # @property
    # def attLogs(self):
    #     if (len(self) % 40) > 0:
    #         return None
    #     return [AttLog.from_bytes(x) for x in split_list(self.data, len(self) // 40)]

    @property
    def op_logs(self):
        """
        convert internal buffer to segment each segment represent OpLog object
        :return: list of OpLog object
        """
        if len(self) % 16 > 0:
            return None
        return [OpLog.from_bytes(x) for x in split_list(self.data, len(self) // 16)]

    @property
    def att_logs(self):
        """
        convert internal buffer into segments each segment represent AttLog object
        :return: list of AttLog object
        """
        if len(self) % 40 > 0:
            return None
        return [AttLog.from_bytes(x, self._encoding) for x in split_list(self.data, len(self) // 40)]

    @property
    def users(self):
        """
        convert internal buffer into segments each segment represent UserInfo object
        :return: list of UserInfo object
        """
        if len(self.data) % 72 > 0:
            return None
        return [UserInfo.from_bytes(x, self._encoding) for x in split_list(self.data, len(self) // 72)]
    
    @property
    def fps(self):
        """
        convert internal buffer into segments each segment represent FpInfo object
        :return: list of FpInfo object
        """
        index = 0
        ret = []
        while index < len(self.data):
            seg_len = struct.unpack("<H", self.data[index: index + 2])[0]
            index += 2
            seg_len -= 2
            ret.append(FPInfo.from_bytes(self.data[index: index + seg_len]))
            index += seg_len
        return ret

    def append(self, part):
        """
        append more segment to internal buffer
        :param part:
        :return:
        """
        self._data += part

    def __bytes__(self):
        """
        return internal data buffer
        :return:
        """
        return self._data
        # return struct.pack("<I", len(self.data)) + self.data

    def __hash__(self):
        """
        create hash from data buffer
        :return: hash value in form of number
        """
        a = 0
        # for x in bytes(self):
        for x in self._data:
            a = (a << 0x4) + x
            b = a & 0xF0000000
            if b > 0:
                c = b >> 0x18
                if (c & 0x80) > 0:
                    c = c | 0xFFFFFF00
                c = c ^ b
                a = a ^ c
            a = a & 0xFFFFFFFF
        b = ((((a * 0x40404081) >> 32) & 0xFFFFFFFF) >> 0x16) * 0xFEFFFF
        return a - (b & 0xFFFFFFFF) if len(self) > 0 else 0
