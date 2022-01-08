import datetime
import socket
import struct
import logging
from random import randint
from .utils import device_cmd, datetime_to_bytes, datetime_from_bytes, split_list
from .network_utils import packet, DataBuffer
from . import models, debug


class ClientConnection(object):
    def __init__(self, host: str, port: int):
        self._serial = None
        self._secret_key = None
        self._host = host
        self._port = port
        self._socket = None
        self._request = None
        self._response = None
        self._logger = logging.getLogger("buffer") if debug else None

    def disconnect(self):
        if self._socket:
            self._socket.close()
            self._socket = None

    def connect(self):
        self.disconnect()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(20)
        self._socket.connect((self._host, self._port))
        return self._socket is not None

    def send(self):
        if self._request:
            data = bytes(self._request)
            if debug:
                self._logger.debug("REQ ({} bytes): {}".format(len(data),
                                                               str.join(' ', [hex(char) for char in data])))
            self._socket.sendall(data)

    def receive(self, verify_checksum=True, verify_size=False):
        recv = b''
        buffer_size = 4096
        header = self._socket.recv(8)
        if not header:
            raise Exception("connection is closed by server")
        temp = packet(header)
        while len(recv) < temp.size:
            rem_size = temp.size - len(recv)
            temp_data = self._socket.recv(buffer_size if rem_size > buffer_size else rem_size)
            if not temp_data:
                raise Exception("connection is closed by server")
            recv += temp_data
        data = header + recv
        if debug:
            self._logger.debug("RES ({} bytes): {}".format(len(data),
                                                           str.join(' ', [hex(char) for char in data])))
        self._response = packet(data)
        if not self._response.is_valid(verify_checksum, verify_size):
            raise Exception("invalid packet response")

    def verify_response(self, cmd_name: list = None):
        if cmd_name is None:
            cmd_name = ["ack"]
        if self._response.cmd not in [device_cmd[x] for x in cmd_name]:
            raise Exception("unexpected response cmd: {}".format(self._response.cmd))
        # if isinstance(cmd_name, list):
        # else:
        #     if self._response.cmd != device_cmd[cmd_name]:
        #         raise Exception("unexpected response cmd: {}".format(self._response.cmd))

    def send_cmd(self, cmd_name: str, payload: bytes = b'', res_cmd_name: list = None):
        self._request = packet(cmd=device_cmd[cmd_name], serial=self.serial, secret_key=self._secret_key,
                               payload=payload)
        self.send()
        self.receive()
        self.verify_response(res_cmd_name)


class ZMM100_TFT(ClientConnection):
    def __init__(self, host: str, port: int, encoding: str, secret_key: int = 0, serial: int = 0):
        super().__init__(host, port)
        self._encoding = encoding
        self._connected = (self._socket is not None)
        self._secret_key: int = secret_key
        self._serial: int = serial
        self._enabled: bool = True

    def connect(self, comm_key=0):
        # if self._socket:
        #     self.disconnect()
        super().connect()
        self._connected = False
        self._secret_key = 0
        self._serial = 0
        self.send_cmd("connect")
        self._secret_key = self._response.secret_key
        if comm_key > 0:
            payload = self.hash_commkey(comm_key)
            self.send_cmd("login", payload)
        self._connected = True
        return self._connected

    def disconnect(self):
        try:
            if self._connected:
                self.send_cmd("disconnect")
        except Exception as ex:
            if self._logger:
                self._logger.error("disconnection with error:")
                self._logger.error(str(ex))
        finally:
            super().disconnect()
            self._connected = False

    def hash_commkey(self, comm_key: int):
        index = 1
        num = 0
        for _ in range(0x20):
            num *= 2
            num = num & 0xFFFFFFFF
            if comm_key & index > 0:
                num = num | 1
            index = index << 1
            if index > 0xFFFFFFFF:
                index = 1
        num += self._secret_key
        # y1 = (num & 0xFF) ^ 0x5A
        y2 = (num >> 8 & 0xFF) ^ 0x4B
        y3 = (num >> 16 & 0xFF) ^ 0x53
        y4 = (num >> 24 & 0xFF) ^ 0x4F
        y5 = randint(1, 0x100)
        y2 = y2 ^ y5
        y3 = y3 ^ y5
        y4 = y4 ^ y5
        ret = [y2, y5, y4, y3]
        ret.reverse()
        return bytes(ret)

    def reboot(self):
        self.send_cmd("reboot")

    def shutdown(self):
        self.send_cmd("shutdown")

    def set_device_prop(self, new_value: bytes, prop_cmd="set_data"):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        self.send_cmd(prop_cmd, new_value)
        self.send_cmd("save_data")
        # return True

    @property
    def id(self):
        return self.get_device_prop(b"DeviceID\x00")

    @id.setter
    def id(self, val):
        payload = "DeviceID={}".format(val)
        self.set_device_prop(payload.encode(self._encoding))

    @property
    def name(self):
        return self.get_device_prop(b"~DeviceName\x00")

    @property
    def type(self):
        return self.get_device_prop(b"DeviceType\x00")

    @property
    def product_time(self):
        return self.get_device_prop(b"~ProductTime")

    @property
    def serial_number(self):
        return self.get_device_prop(b"~SerialNumber\x00")

    @property
    def language(self):
        return self.get_device_prop(b"Language\x00")

    @property
    def compat_old_firmware(self):
        return self.get_device_prop(b"CompatOldFirmware\x00")

    @property
    def is_support_pull(self):
        return self.get_device_prop(b"IsSupportPull\x00")

    @property
    def camera_open(self):
        return self.get_device_prop(b"CameraOpen\x00")

    @property
    def finger_fun_on(self):
        return self.get_device_prop(b"FingerFunOn")

    @property
    def face_fun_on(self):
        return self.get_device_prop(b"FaceFunOn\x00")

    @property
    def zk_face_version(self):
        return self.get_device_prop(b"ZKFaceVersion")

    @property
    def biometric_type(self):
        return self.get_device_prop(b"BiometricType")

    @property
    def build_version(self):
        return self.get_device_prop(b"BuildVersion\x00")

    @property
    def att_photo_for_sdk(self):
        return self.get_device_prop(b"AttPhotoForSDK\x00")

    @property
    def is_only_rf_machine(self):
        return self.get_device_prop(b"~IsOnlyRFMachine\x00")

    @property
    def ssr(self):
        return self.get_device_prop(b"~SSR\x00")

    @property
    def pin_width(self):
        return self.get_device_prop(b"~PIN2Width\x00")

    @property
    def vendor(self):
        return self.get_device_prop(b"~OEMVendor\x00")

    @property
    def platform(self):
        return self.get_device_prop(b"~Platform\x00")

    @property
    def os(self):
        return self.get_device_prop(b"~OS")

    @property
    def extend_fmt_1(self):
        return self.get_device_prop(b"~ExtendFmt")

    @property
    def extend_fmt_2(self):
        return self.get_device_prop(b"ExtendFmt\x00")

    @property
    def extend_oplog_1(self):
        return self.get_device_prop(b"~ExtendOPLog\x00")

    @property
    def user_ext_fmt(self):
        return self.get_device_prop(b"~UserExtFmt\x00")

    @property
    def extend_oplog_2(self):
        return self.get_device_prop(b"ExtendOPLog")

    @property
    def software_version(self):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        self.send_cmd("soft_ver")
        msg = self._response.payload.decode('latin-1')
        return msg.strip(' \x00')

    @property
    def fp_version(self):
        return self.get_device_prop(b"~ZKFPVersion\x00")

    @property
    def work_code(self):
        return self.get_device_prop(b"WorkCode\x00")

    @work_code.setter
    def work_code(self, val: str):
        temp = "WorkCode=" + val
        self.set_device_prop(temp.encode('latin-1'))

    @property
    def mac_address(self):
        return self.get_device_prop(b"MAC\x00")

    @mac_address.setter
    def mac_address(self, val: str):
        temp = "MAC=" + val
        self.set_device_prop(temp.encode('latin-1'))

    @property
    def ip_address(self):
        return self.get_device_prop(b"IPAddress\x00")

    @ip_address.setter
    def ip_address(self, val: str):
        temp = "IPAddress=" + val
        self.set_device_prop(temp.encode('latin-1'))

    @property
    def password(self):
        return self.get_device_prop(b"COMKey\x00")

    @password.setter
    def password(self, val):
        payload = "COMKey={}".format(val)
        self.set_device_prop(payload.encode('latin-1'))

    @property
    def port(self):
        return int(self.get_device_prop(b"UDPPort\x00"))

    @port.setter
    def port(self, val: int):
        payload = "UDPPort={}".format(val)
        self.set_device_prop(payload.encode('latin-1'))

    @property
    def daylight_saving_timeon(self):
        return self.get_device_prop(b"DaylightSavingTimeOn\x00")

    @daylight_saving_timeon.setter
    def daylight_saving_timeon(self, val: str):
        payload = "DaylightSavingTimeOn=" + val
        self.set_device_prop(payload.encode('latin-1'))

    @property
    def daylight_saving_time(self):
        return self.get_device_prop(b"DaylightSavingTime\x00")

    @daylight_saving_time.setter
    def daylight_saving_time(self, val: str):
        payload = "DaylightSavingTime=" + val
        self.set_device_prop(payload.encode('latin-1'))

    @property
    def standard_time(self):
        return self.get_device_prop(b"StandardTime\x00")

    @standard_time.setter
    def standard_time(self, val: str):
        payload = "StandardTime=" + val
        self.set_device_prop(payload.encode('latin-1'))

    @property
    def device_time(self):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        self.send_cmd("get_time")
        return datetime_from_bytes(self._response.payload[:4])

    @device_time.setter
    def device_time(self, new_time: datetime.datetime):
        self.set_device_prop(datetime_to_bytes(new_time), "set_time")

    def query_system_option(self,
                            query_string="~OS=?,ExtendFmt=?,~ExtendFmt=?,ExtendOPLog=?,~ExtendOPLog=?,~Platform=?,"
                                         "~ZKFPVersion=?,WorkCode=?,~SSR=?,~PIN2Width=?,~UserExtFmt=?,BuildVersion=?,"
                                         "AttPhotoForSDK=?,~IsOnlyRFMachine=?,CameraOpen=?,CompatOldFirmware=?,"
                                         "IsSupportPull=?,Language=?,~SerialNumber=?,FaceFunOn=?,~DeviceName=?"):
        self.send_cmd("query_sys_op", query_string.encode('latin-1'))
        return self._response.payload.decode("latin-1")

    def get_device_prop(self, prop_payload: bytes):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        self.send_cmd("get_data", prop_payload, ["ack", "no_sys_op"])
        if self._response.cmd == device_cmd["no_sys_op"]:
            return None
        msg = self._response.payload.decode('latin-1')
        return msg.split("=")[1].strip(' \x00')

    def get_tz_info(self, tz_index: int):
        if not self._connected:
            raise Exception("you need to connect to machine first")

        self.send_cmd("get_tz", struct.pack("<I", tz_index))
        index = struct.unpack("<H", self._response.payload[:2])[0]
        if index == tz_index:
            tz = self._response.payload[2:-2]
            return ''.join(['{0:02d}'.format(x) for x in tz])

    def set_tz_info(self, tz_index: int, str_val):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        if len(str_val) % 2 > 0:
            return False
        vals = split_list(str_val, len(str_val) // 2)
        payload = struct.pack("<H", tz_index) + bytes([int(x) for x in vals])
        self.send_cmd("set_tz", payload)
        return True

    def clear_data(self, data_id: int):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        self.send_cmd("cls_data", payload=struct.pack("<B", data_id))
        self.send_cmd("save_data")

    def del_user(self, _id: int, disable_device=True):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        if disable_device:
            self.disable_device()
        try:
            self.send_cmd("del_user", payload=struct.pack("<H", _id))
        except Exception as ex:
            raise ex
        finally:
            if disable_device:
                self.enable_device()

    @property
    def database_structure(self):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        self.send_cmd("get_table_struct", res_cmd_name=["recv_buff_header"])
        self.receive()
        self.verify_response(["recv_buff_content"])
        data = self._response
        self.receive()
        self.verify_response()
        # footer = self._response
        return data.payload.decode('latin-1')

    def get_fp_data(self, user_id: int, finger_id: int, disable_device=True):
        """
        return byte data of the fingerprint
        """
        if not self._connected:
            raise Exception("you need to connect to machine first")
        if disable_device:
            self.disable_device()
        try:
            self.send_cmd("get_fp", struct.pack("<HB", user_id, finger_id), ["recv_buff_header", "nak", "no_data"])
            if self._response.cmd == device_cmd["nak"]:
                return b''
            elif self._response.cmd == device_cmd["no_data"]:
                return b''
            else:
                self.receive()
                self.verify_response(["recv_buff_content"])
                data = self._response
                self.receive()
                self.verify_response()
                # footer = self._response
                return data.payload[:-6]
        except Exception as ex:
            raise ex
        finally:
            if disable_device:
                self.enable_device()

    def send_file(self, file_name: str, file_data: bytes, disable_device=True):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        if disable_device:
            self.disable_device()
        try:
            self._upload_data(file_data)
            file_name = file_name.encode(self._encoding)
            file_name = file_name + struct.pack("<{}x".format(39 - len(file_name)))
            payload = struct.pack("<I", 0x6A4) + file_name
            self.send_cmd("send_file", payload, ["ack", "nak"])
            ret = self._response.cmd == device_cmd["ack"]
            self.send_cmd("end_buff_stream")
            if not ret:
                raise Exception("operation failed")
        finally:
            if disable_device:
                self.enable_device()
        self.send_cmd("save_data")

    def set_user_pic(self, person_id: str, pic_data: bytes, disable_device=True):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        if disable_device:
            self.disable_device()
        try:
            self._upload_data(pic_data)
            file_name = person_id.encode(self._encoding) + b".jpg"
            file_name = file_name + struct.pack("<{}x".format(39 - len(file_name)))
            payload = file_name + bytes([0] * 4)
            self.send_cmd("set_user_pic", payload)
            self.send_cmd("end_buff_stream")
        finally:
            if disable_device:
                self.enable_device()
        self.send_cmd("save_data")

    def del_user_pic(self, person_id: str, disable_device=True):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        if disable_device:
            self.disable_device()
        try:
            self.send_cmd("del_user_pic", person_id.encode(self._encoding) + b".jpg\x00", ["ack", "no_pic"])
            if self._response.cmd == device_cmd["no_pic"]:
                return False
            return True
        finally:
            if disable_device:
                self.enable_device()
            self.send_cmd("save_data")

    def get_user_pic(self, person_id: str):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        self.send_cmd("get_user_pic", person_id.encode(self._encoding) + b".jpg\x00",
                      ["recv_buff_header", "nak", "no_pic"])
        if self._response.cmd != device_cmd["recv_buff_header"]:
            return b''
        data_size, _ = struct.unpack("<II", self._response.payload[:8])
        self.receive()
        self.verify_response(["recv_buff_content"])
        data = self._response
        self.receive()
        self.verify_response()
        _ = self._response
        if len(data.payload) != data_size:
            raise Exception("data integrity is incorrect")
        return data.payload

    def del_op_logs(self):
        self.send_cmd("clear_op_log")
        self.send_cmd("save_data")

    def del_users(self):
        self.clear_data(0x05)

    def del_fps(self):
        self.clear_data(0x02)

    def del_admins(self):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        self.send_cmd("cls_admins")
        self.send_cmd("save_data")

    def get_photo_count(self):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        self.send_cmd("get_photo_count")
        if len(self._response.payload) == 1:
            return struct.unpack("<B", self._response.payload)[0]
        elif len(self._response.payload) == 2:
            return struct.unpack("<H", self._response.payload)[0]
        elif len(self._response.payload) == 4:
            return struct.unpack("<I", self._response.payload)[0]
        else:
            raise Exception("unknown response format for photo count")

    def get_state(self, disable_device=True):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        if disable_device:
            self.disable_device()
        try:
            self.send_cmd("logs_count")

            if len(self._response.payload or b'') < (23 * 4):
                raise Exception("error in logs_count command")
            return models.MachineState.from_bytes(self._response.payload)
        except Exception as ex:
            raise ex
        finally:
            if disable_device:
                self.enable_device()

    def del_att_logs(self, disable_device=True):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        if disable_device:
            self.disable_device()
        try:
            self.send_cmd("del_logs")
        except Exception as ex:
            raise ex
        finally:
            if disable_device:
                self.enable_device()
        self.send_cmd("save_data")

    def disable_device(self, time_out_in_sec=0):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        self.send_cmd("disable", struct.pack("<I", time_out_in_sec))

    def enable_device(self):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        self.send_cmd("enable")

    def check_hash(self):
        """
        use as follows after send data from client to machine using header-content-footer
        use this function optionally to return the hash of the buffer received by device and
        compare it with hash you make from buffer before send
        """
        if not self._connected:
            raise Exception("you need to connect to machine first")
        self.send_cmd("check_hash")
        return struct.unpack("<I", self._response.payload)

    def get_fps(self, disable_device=True):
        ret = self._get_data_buffer(0x02000701, disable_device)
        if ret is not None:
            ret.remove_leading()
            return ret.fps

    def del_user_face(self, person_id: str, face_id=50, disable_device=True):
        # ret = False
        if not self._connected:
            raise Exception("you need to connect to machine first")
        if disable_device:
            self.disable_device()
        try:
            payload = [0] * 28
            temp = person_id.encode(self._encoding)
            length = len(temp)
            if length > 24:
                length = 24
            payload[:length] = temp[:length]
            payload[25] = face_id
            self.send_cmd("del_face", bytes(payload))
        finally:
            if disable_device:
                self.enable_device()
        self.send_cmd("save_data")

    def get_user_face(self, person_id: str, face_id=50, disable_device=True):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        if disable_device:
            self.disable_device()
        try:
            # payload = [0] * 28
            person_id = person_id.encode(self._encoding)
            payload = person_id + struct.pack("<{}xxB2x".format(24 - len(person_id)), face_id)
            self.send_cmd("get_face", payload, ["recv_buff_header", "nak", "no_data"])
            if self._response.cmd == device_cmd["nak"]:
                return b''
            elif self._response.cmd == device_cmd["no_data"]:
                return b''
            else:
                self.receive()
                self.verify_response(["recv_buff_content"])
                data = self._response
                self.receive()
                self.verify_response()
                _ = self._response
                return data.payload
        finally:
            if disable_device:
                self.enable_device()

    def set_user_face(self, person_id: str, face_data: bytes, face_index=50, disable_device=True):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        if disable_device:
            self.disable_device()
        try:
            self._upload_data(face_data)
            person_id = person_id.encode(self._encoding)
            payload = person_id + struct.pack("<{}xxBH".format(24 - len(person_id)), face_index, len(face_data))
            self.send_cmd("set_face", payload)
            self.send_cmd("end_buff_stream")
        finally:
            if disable_device:
                self.enable_device()
        self.send_cmd("save_data")

    # old function
    # def delFP(self, user_id, finger_id, disable_device=True):
    #     if not self._connected:
    #         raise Exception("you need to connect to machine first")
    #     if disable_device:
    #         self.disableDevice()
    #     try:
    #         self.sendCmd("del_fp", struct.pack("<HB", user_id, finger_id), ["ack", "nak", "no_fp"])
    #         ret = self._response.cmd == device_cmd["ack"]
    #         self.sendCmd("save_data")
    #         return ret
    #     finally:
    #         if disable_device:
    #             self.enableDevice()
    def set_user(self, user_info: models.UserInfo):
        """
        It is very important to identify the serial of the user_info object
        because the machine use this serial to store data thus avoid overriding
        on user over another one thus please use correct index (serial)
        """
        if not self._connected:
            raise Exception("you need to connect to machine first")
        self.send_cmd("set_user", bytes(user_info))

    def del_fp(self, person_id: str, finger_id: int, disable_device=True):
        # ret = False
        if not self._connected:
            raise Exception("you need to connect to machine first")
        if disable_device:
            self.disable_device()
        try:
            payload = [0] * 25
            temp = person_id.encode(self._encoding)
            length = len(temp)
            if length > 24:
                length = 24
            payload[:length] = temp[:length]
            payload[24] = finger_id
            # if len(temp) >= 24:
            #     payload = temp[:24] + struct.pack("<B", finger_id)
            # else:
            #     remain = 24 - len(temp)
            #     fmt = "<{}xB".format(remain)
            #     payload = temp + struct.pack(fmt, finger_id)
            self.send_cmd("del_fp_ex", bytes(payload), ["ack", "nak", "no_fp"])
            ret = self._response.cmd == device_cmd["ack"]
        finally:
            if disable_device:
                self.enable_device()
        if ret:
            self.send_cmd("save_data")
        return ret

    def _upload_data(self, data: bytes):
        self.send_cmd("recv_buff_header", struct.pack("<I", len(data)))
        self.send_cmd("recv_buff_content", data)
        buffer = DataBuffer(self._encoding, data)
        hash_code = hash(buffer)
        self.send_cmd("check_hash")
        if hash_code != struct.unpack("<I", self._response.payload)[0]:
            raise Exception("problem in data sending")

    def set_fp(self, fp_info: models.FPInfo, disable_device=True):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        if disable_device:
            self.disable_device()
        try:
            self._upload_data(fp_info.data)
            # self.sendCmd("recv_buff_header", struct.pack("<I", len(fp_info.data)))
            # self.sendCmd("recv_buff_content", fp_info.data)
            # buffer = DataBuffer(fp_info.data)
            # hash_code = hash(buffer)
            # self.sendCmd("check_hash")
            # if hash_code != struct.unpack("<I", self._response.payload)[0]:
            #     raise Exception("problem in data sending")
            payload = struct.pack("<HBBH", fp_info.user_id, fp_info.finger_id, fp_info.enabled, len(fp_info.data))
            self.send_cmd("set_fp_ex", payload)
            self.send_cmd("end_buff_stream")
        finally:
            if disable_device:
                self.enable_device()
        self.send_cmd("save_data")

    def set_fps(self, fp_infos: list, disable_device=True):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        if disable_device:
            self.disable_device()
        try:
            for fp_info in fp_infos:
                self.send_cmd("recv_buff_header", struct.pack("<I", len(fp_info.data)))
                self.send_cmd("recv_buff_content", fp_info.data)
                buffer = DataBuffer(self._encoding, fp_info.data)
                hash_code = hash(buffer)
                self.send_cmd("check_hash")
                if hash_code != struct.unpack("<I", self._response.payload)[0]:
                    raise Exception("problem in data sending")
                payload = struct.pack("<HBBH", fp_info.user_id, fp_info.finger_id, fp_info.enabled, len(fp_info.data))
                self.send_cmd("set_fp_ex", payload)
                self.send_cmd("end_buff_stream")
        finally:
            if disable_device:
                self.enable_device()
        self.send_cmd("save_data")

    def get_fp(self, user_id: int, finger_id: int, disable_device=True):
        """
        return FPInfo record
        """
        if not self._connected:
            raise Exception("you need to connect to machine first")
        if disable_device:
            self.disable_device()
        try:
            self.send_cmd("get_fp_ex", struct.pack("<HB", user_id, finger_id), ["recv_buff_header", "nak", "no_data"])
            if self._response.cmd == device_cmd["nak"]:
                return
            elif self._response.cmd == device_cmd["no_data"]:
                return
            else:
                self.receive()
                self.verify_response(["recv_buff_content"])
                data = self._response
                self.receive()
                self.verify_response()
                # footer = self._response
                return models.FPInfo(user_id=user_id, finger_id=finger_id, enabled=data.payload[-1],
                                     data=data.payload[:-7])
        except Exception as ex:
            raise ex
        finally:
            if disable_device:
                self.enable_device()

    def get_users(self, disable_device=True):
        ret = self._get_data_buffer(0x05000901, disable_device)
        if ret is not None:
            ret.remove_leading()
            return ret.users

    def get_op_logs(self, disable_device=True):
        ret = self._get_data_buffer(0x2201, disable_device)
        if ret is not None:
            ret.remove_leading()
            return ret.op_logs

    def get_att_logs(self, disable_device=True):
        ret = self._get_data_buffer(0x0D01, disable_device)
        if ret is not None:
            ret.remove_leading()
            return ret.att_logs

    def _get_data_buffer(self, data_id: int, disable_device=True):
        if not self._connected:
            raise Exception("you need to connect to machine first")
        if disable_device:
            self.disable_device()
        try:

            data_buffer = DataBuffer(self._encoding)
            payload = struct.pack("<I7x", data_id)
            self.send_cmd("start_buff_stream", payload, ["ack", "nak", "recv_buff_content", "no_record"])
            if self._response.cmd == device_cmd["recv_buff_content"]:
                data_buffer.append(self._response.payload)
                return data_buffer
            elif self._response.cmd in [device_cmd["nak"], device_cmd["no_record"]]:
                return data_buffer
            else:
                data_size = struct.unpack("<I", self._response.payload[1:5])[0]
                packet_size = 0xFFC0
                packets = data_size // packet_size
                rem_size = data_size
                if (data_size % packet_size) > 0:
                    packets += 1
                # has_error = False
                for _ in range(0, packets):
                    # payload = DwordToBytes(data_size - rem_size) + DwordToBytes(rem_size if rem_size < packet_size
                    # else packet_size)
                    payload = struct.pack("<I", data_size - rem_size) + \
                              struct.pack("<I", rem_size if rem_size < packet_size else packet_size)
                    self.send_cmd("buff_stream", payload, ["recv_buff_header"])
                    recv_size = struct.unpack("<I", self._response.payload[:4])[0]
                    self.receive()
                    self.verify_response(["recv_buff_content"])
                    data = self._response
                    self.receive()
                    self.verify_response()
                    # footer = self._response
                    data_buffer.append(data.payload)
                    rem_size -= recv_size
                self.send_cmd("end_buff_stream")
                # if not has_error:
                return data_buffer
        except Exception as ex:
            raise ex
        finally:
            if disable_device:
                self.enable_device()

    @property
    def connected(self):
        return self._connected

    @property
    def serial(self):
        self._serial += 1
        return self._serial - 1


class ZMM220_TFT(ZMM100_TFT):
    def __init__(self, host, port, encoding, secret_key=0, serial=0):
        super().__init__(host, port, encoding, secret_key, serial)

    def connect(self, comm_key=0):
        if self._socket:
            self.disconnect()
        super(ZMM100_TFT, self).connect()
        self._connected = False
        self._secret_key = 0
        self._serial = 0
        self.send_cmd("connect", res_cmd_name=["accept_conn"])
        self._secret_key = self._response.secret_key
        if comm_key > 0:
            payload = self.hash_commkey(comm_key)
            self.send_cmd("login", payload)
        self._connected = True
        return self._connected
