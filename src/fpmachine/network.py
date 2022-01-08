from .devices import ZMM100_TFT, ZMM220_TFT


# from .virtual import VirtualDevice


class Client(object):
    def __init__(self, device):
        self._device = device

    def __enter__(self):
        if self._device.connect():
            return self._device
        else:
            raise Exception("connection error")
    
    def __exit__(self, _type, value, traceback):
        self._device.disconnect()


class ZMM100Client(Client):
    def __init__(self, ip, port, encoding):
        super().__init__(ZMM100_TFT(ip, port, encoding))


class ZMM220Client(Client):
    def __init__(self, ip, port, encoding):
        super().__init__(ZMM220_TFT(ip, port, encoding))

# class ServerConnection(threading.Thread):
#     def __init__(self, thread_id, conn, server):
#         threading.Thread.__init__(self)
#         self._conn = conn
#         self._threads = server.threads
#         self._remove_lock = server.thread_remove_lock
#         self._server = server
#         self._machine_id = server._machine_id
#         self._id = thread_id
#         self._buffer = None
#         self._connected = False
#         # self._stopEx = threading.Event()
#         self._logger = logging.getLogger("server")
#         self._blogger = logging.getLogger("buffer")
#         self._virtual = VirtualDevice(server._machine_id, server._database_url)
#         self._last_op = ""
#         try:
#             self._virtual.connect()
#             self._client = ClientConnection(self._virtual.host, self._virtual.port)
#         except Exception as ex:
#             self._logger.error(str(ex))
#             self._client = None
#
#     def clean(self):
#         self._remove_lock.acquire()
#         while self in self._threads:
#             self._threads.remove(self)
#         self._remove_lock.release()
#         self._logger.info("removing thread {0} and remaining thread {1}".format(self._id, len(self._threads)))
#
#     def stop(self):
#         self._connected = False
#         # self._stopEx.set()
#
#     def stopped(self):
#         return not self._connected # self._stopEx.isSet()
#
#     def createPck(self, copy_from, payload=b'', cmd_name="ack", secret_key=None):
#         return packet(cmd=device_cmd[cmd_name],
#                       serial=copy_from.serial,
#                       secret_key=copy_from.secret_key if secret_key is None else secret_key,
#                       payload=payload)
#
#     def _readPck(self):
#         data = b''
#         seg_len = 0x1000
#         header = self._conn.recv(8)
#         pck = packet(header)
#         if not pck.isValid(False, False):
#             raise Exception("received packet is not valid")
#         rem_size = pck.size - len(data)
#         while rem_size > 0:
#             temp_data = self._conn.recv(seg_len if rem_size > seg_len else rem_size)
#             if not temp_data:
#                 raise Exception("connection is closed by the client")
#             data += temp_data
#             rem_size = pck.size - len(data)
#         data = header + data
#         # if debug:
#         #     self._blogger.debug("REQ ({} bytes): {}".format(len(data),
#         #         str.join(' ', [hex(char) for char in data])))
#         return packet(data)
#
#     def readPcks(self):
#         pcks = []
#         pck = self._readPck()
#         pcks.append(pck)
#         # if pck.cmd == device_cmd["recv_buff_header"]:
#         #     pck = self._readPck()
#         #     pcks.append(pck)
#         # while pck.cmd == device_cmd["recv_buff_content"]:
#         #     pck = self._readPck()
#         #     pcks.append(pck)
#         # pcks.append(self._readPck())
#         return pcks
#
#
#     def run(self):
#         # att_offset = 0
#         # att_size = 0
#         idle = 0
#         # connect to machine
#         self._connected = self._client and self._client.connect()
#         try:
#             while self._connected:
#                 command_processed = False
#                 ready = select([self._conn], [], [], 3)
#                 # data = b''
#                 if not ready[0]:
#                     idle += 3
#                     # print(idle)
#                 else:
#                     idle = 0
#                     pcks = self.readPcks()
#                     # print("{}: {}".format(hex(pcks[0].cmd), len(pcks)))
#                     pck = pcks[0]
#
#                     if pck.cmd == device_cmd["recv_buff_header"]:
#                         # print(dump(pck.payload))
#                         self._buffer = DataBuffer()
#                     elif pck.cmd == device_cmd["recv_buff_content"]:
#                         self._buffer.append(pck.payload)
#                     # elif pck.cmd == device_cmd["check_hash"]:
#                         # if not self._buffer:
#                         #     recv = bytes(self.createPck(pck, struct.pack("<I", 0)))
#                         # else:
#                         #     recv = bytes(self.createPck(pck, struct.pack("<I", hash(self._buffer))))
#                         # command_processed = False
#                     elif pck.cmd == device_cmd["del_face"]:
#                         person_id = get_null_term_str(pck.payload, 0, 24)
#                         face_id = pck.payload[25]
#                         self._virtual.delFP(person_id, face_id)
#                     elif pck.cmd == device_cmd["set_face"]:
#                         person_id = get_null_term_str(pck.payload, 0, 24)
#                         face_index, buffer_len = struct.unpack("<BH", pck.payload[25:28])
#                         if buffer_len == len(self._buffer.data):
#                             self._virtual.setUserFace(person_id, self._buffer.data, face_index)
#
# elif pck.cmd == device_cmd["get_face"]: person_id = get_null_term_str(pck.payload, 0, 24) face_id = pck.payload[25]
# face_id = struct.unpack("<BB", pck.payload[24:26])[0] data = self._virtual.getUserFace(person_id, face_id) if not
# data: recv = bytes(self.createPck(pck, cmd_name="no_data")) else: payload = struct.pack("<II", len(data),
# 0x10000) recv = bytes(self.createPck(pck, payload=payload, cmd_name="recv_buff_header")) recv += bytes(
# self.createPck(pck, payload=data, cmd_name="recv_buff_content",secret_key=0)) recv += bytes(self.createPck(pck))
# command_processed = True elif pck.cmd == device_cmd["get_fp_ex"]: user_id, finger_id = struct.unpack("<HB",
# pck.payload[:3]) fp = self._virtual.getFP(user_id, finger_id) # print("fp len: {}".format(len(fp.data))) if not fp:
# recv = bytes(self.createPck(pck, cmd_name="no_data")) else: data = fp.data + struct.pack("<6xB", fp.enabled)
# payload = struct.pack("<II", len(data), 0x10000) recv = bytes(self.createPck(pck, payload=payload,
# cmd_name="recv_buff_header")) recv += bytes(self.createPck(pck, payload=data, cmd_name="recv_buff_content",
# secret_key=0)) recv += bytes(self.createPck(pck)) command_processed = True elif pck.cmd == device_cmd["set_fp_ex"]:
# fp_info = models.FPInfo() fp_info.user_id, fp_info.finger_id, fp_info.enabled, buffer_len = struct.unpack("<HBBH",
# pck.payload) fp_info.data = self._buffer.data # update fp in virtual device self._virtual.setFP(fp_info) #
# self._last_op = "set_fp_ex" # recv = bytes(self.createPck(pck)) command_processed = False elif pck.cmd ==
# device_cmd["del_fp_ex"]: # delete fp in virtual device person_id = get_null_term_str(pck.payload, 0, 24) finger_id =
# pck.payload[24] self._virtual.delFP(person_id, finger_id)
#
#                     elif pck.cmd == device_cmd["set_user"]:
#                         user_info = models.UserInfo.from_bytes(pck.payload)
#                         self._virtual.setUser(user_info)
#                         # print(dump(pck.payload))
#                         # recv = bytes(self.createPck(pck))
#                         # command_processed = True
#                     # elif pck.cmd == device_cmd["save_data"]:
#                     #     if self._last_op:
#                     #         recv = bytes(self.createPck(pck))
#                     #         command_processed = True
#                     #         self._last_op = ""
#
# elif pck.cmd == device_cmd["disconnect"]: self._connected = False elif pck.cmd == device_cmd["logs_count"]: # st =
# self._db_session.query(models.MachineState).filter_by(machine_id=self._machine_id).first() recv = bytes(
# self.createPck(pck, bytes(self._virtual.getState()))) command_processed = True
#
#                     elif pck.cmd == device_cmd["del_logs"]:
#                         self._virtual.delAttLogs()
#                         recv = bytes(self.createPck(pck))
#                         command_processed = True
#
#                     elif pck.cmd == device_cmd["start_buff_stream"]:
#                         buffer_type = struct.unpack("<I", pck.payload[:4])[0]
#                         self._buffer = DataBuffer()
#                         # buffer_data = b''
#                         if buffer_type == 0xD01:
#                             # att_log_set = 0
#                             # att_size = 0
#                             logs = self._virtual.getAttLogs()
#                             for log in logs:
#                                 self._buffer.append(bytes(log)) # += bytes(log)
#                             self._last_op = "true"
#                         elif buffer_type == 0x05000901:
#                             users = self._virtual.getUsers()
#                             for user in users:
#                                 self._buffer.append(bytes(user)) # += bytes(user)
#                             self._last_op = "true"
#                         elif buffer_type == 0x02000701:
#                             fps = self._virtual.getFPS()
#                             for fp in fps:
#                                 temp = bytes(fp)
#                                 self._buffer.append(struct.pack("<H", len(temp) + 2) + temp)
#                             self._last_op = "true"
#
#                         else:
#                             self._buffer = None
#                             self._last_op = ""
#                         if not self._buffer or not self._buffer.data:
#                             recv = bytes(self.createPck(pck, cmd_name="no_data"))
#                         else:
#                             # self._buffer = DataBuffer(buffer_data)
#                             self._buffer.add_leading_len()
#                             # self._buffer = DataBuffer(struct.pack("<I", len(buffer_data)) + buffer_data)
#                             buffer_len = struct.pack("<I", len(self._buffer))
#                             payload = b'\x00' + buffer_len + buffer_len + struct.pack("<I", hash(self._buffer))
#                             recv = bytes(self.createPck(pck, payload))
#                             command_processed = True
#
#                     elif pck.cmd == device_cmd["buff_stream"] and self._buffer is not None:
#                         offset, size = struct.unpack("<II", pck.payload[:8])
#                         # size = struct.unpack("<I", pck.payload[4:8])[0]
#                         # payload = struct.pack("<II", size, 0x10000) # pck.payload[4:] + struct.pack("<I", 0x10000)
#                         recv = bytes(self.createPck(pck, struct.pack("<II", size, 0x10000), "recv_buff_header"))
#
#                         # self._conn.sendall(recv)
#                         # payload = bytes(self._buffer)[att_offset: att_size]
#                         recv += bytes(self.createPck(pck, self._buffer.segment(offset, size), "recv_buff_content", 0))
#                         # recv += bytes(packet(cmd=device_cmd[],
#                         #                     serial=pck.serial,
#                         #                     secret_key=0, payload=))
#                         recv += bytes(self.createPck(pck))
#                         command_processed = True
#                     elif pck.cmd == device_cmd["end_buff_stream"] and self._buffer is not None:
#                         if self._last_op:
#                             self._last_op = ""
#                             recv = bytes(self.createPck(pck))
#                             command_processed = True
#                         self._buffer = None
#
#                     # elif pck.cmd == device_cmd["connect"]:
#                     #     recv = bytes(self.createPck(pck, cmd_name="accept_conn"))
#                     elif pck.cmd == device_cmd["soft_ver"]:
#                         recv = bytes(self.createPck(pck, self._virtual.SoftwareVersion.encode('latin-1'), ))
#                         command_processed = True
#                     elif pck.cmd == device_cmd["del_user_pic"]:
#                         person_id = pck.payload.decode('cp1256').strip('.jpg\x00')
#                         self._virtual.delUserPic(person_id)
#                     elif pck.cmd == device_cmd["set_user_pic"]:
#                         person_id = get_null_term_str(pck.payload, 0, -1).strip(".jpg")
#                         self._virtual.setUserPic(person_id, self._buffer.data)
#                     elif pck.cmd == device_cmd["get_user_pic"]:
#                         person_id = pck.payload.decode('cp1256').strip('.jpg\x00')
#                         pic = self._virtual.getUserPic(person_id)
#                         if not pic:
#                             recv = bytes(self.createPck(pck, cmd_name="no_pic"))
#                         else:
#                             payload = struct.pack("<II", len(pic), 0xFFF8)
#                             recv = bytes(self.createPck(pck, payload, "recv_buff_header"))
#                             recv += bytes(self.createPck(pck, pic, "recv_buff_content", 0))
#                             recv += bytes(self.createPck(pck))
#                         command_processed = True
#                     elif pck.cmd == device_cmd["get_table_struct"]:
#                         temp = self._virtual.DatabaseStructure.encode('latin-1')
#                         payload = struct.pack("<II", len(temp), 0xFFF8)
#                         recv = bytes(self.createPck(pck, payload, "recv_buff_header"))
#                         recv += bytes(self.createPck(pck, temp, "recv_buff_content", 0))
#                         recv += bytes(self.createPck(pck))
#                         command_processed = True
#
# elif pck.cmd == device_cmd["get_data"]: option_name = pck.payload.decode('latin-1').strip(' \x00') opt =
# self._virtual.getSysOption(option_name) if not opt: recv = bytes(self.createPck(pck, cmd_name="no_sys_op")) else:
# recv = bytes(self.createPck(pck, "{}={}\x00".format(opt.prop_name, opt.prop_val).encode('latin-1')))
# command_processed = True
#
#                     elif pck.cmd == device_cmd["query_sys_op"]:
#                         query_string = pck.payload.decode('latin-1')
#                         output_string = self._virtual.querySysOption(query_string)
#                         recv = bytes(self.createPck(pck, output_string.encode('latin-1')))
#                         command_processed = True
#
#                     # elif pck.cmd == device_cmd["ex_op_log_recv"]:
#                     #     recv = bytes(self.createPck(pck, cmd_name="ex_op_log_recv"))
#                     #     command_processed = True
#
#                     elif pck.cmd == device_cmd["get_pin_width"]:
#                         recv = bytes(self.createPck(pck, struct.pack("<B", 9)))
#                         command_processed = True
#                     # else:
#                     #     recv = bytes(self.createPck(pck))
#                     #     command_processed = True
#                     # default behaviour is to send the request to the machine
#                     # and bypass response to the client
#                     if not command_processed:
#                         # print("send to machine")
#                         self._client._request = b''
#                         for pck in pcks:
#                             self._client._request += bytes(pck)
#                         # self._client._request = data
#                         self._client.send()
#                         self._client.receive()
#                         recv = bytes(self._client._response)
#                         if self._client._response.cmd == device_cmd["recv_buff_header"]:
#                             self._client.receive()
#                             recv += bytes(self._client._response)
#                             self._client.receive()
#                             recv += bytes(self._client._response)
#
#                         # recv = self._client.generic_receive()
#                     if len(recv) > 0:
#                         # if debug:
#                         #     self._blogger.debug("RES ({} bytes): {}".format(len(recv),
#                         #         str.join(' ', [hex(char) for char in recv])))
#                         self._conn.sendall(recv)
#                     # connected = not self.stopped()
#                 if idle >= 1800:
#                     self._logger.info("idle reach limit for thread {}".format(self._id))
#                     self._connected = False
#
#                 # if not connected or self.stopped():
#                 #     break
#         except Exception as ex:
#             self._logger.error(str(ex))
#         finally:
#             self._conn.close()
#             # close machine socket
#             if self._client:
#                 self._client.disconnect()
#             self.clean()

                
# class Server(object):
#     def __init__(self, machine_id, host="0.0.0.0", port=4370, database_url=""):
#         self._machine_id = machine_id
#         self._host = host
#         self._port = port
#         self._socket = None
#         self.threads = []
#         self.thread_remove_lock = threading.Lock()
#         self._logger = logging.getLogger("server")
#         self._database_url = database_url
#
#     def cleanup(self):
#         self._socket.close()
#         for th in self.threads:
#             th.stop()
#         while len(self.threads) > 0:
#             self.threads[0].join()
#
#     def create_thread_id(self):
#         id = randint(0x1000, 0xFFFF)
#         while id in [x._id for x in self.threads]:
#             id = randint(0x1000, 0xFFFF)
#         return id
#
#     def run(self):
#         self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         self._socket.bind((self._host, self._port))
#         self._socket.listen(10)
#         try:
#             if not self._database_url:
#                 raise Exception("database_url cannot be empty")
#             while True:
#                 conn, addr = self._socket.accept()
#                 self._logger.info("machine with ip ({}) is connected to system".format(addr))
#                 th_id = self.create_thread_id()
#                 th = ServerConnection(th_id, conn, self)
#                 th.start()
#                 self.threads.append(th)
#                 self._logger.info("thread {} added with total thread {}".format(th_id, len(self.threads)))
#         except Exception as ex:
#             self._logger.error(str(ex))
#         finally:
#             self.cleanup()
