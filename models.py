import struct

from .utils import get_null_term_str, number_to_datetime, datetime_to_number


class UserInfo:
    def __init__(self, encoding):
        self.id = 0
        self.machine_id = 0
        self.name = ""
        self.password = ""
        self.enabled = True
        self.privilege = 0
        self.card_no = 0
        self.person_id = ""
        self.pic = None
        self._data = None
        self._encoding = encoding

    @staticmethod
    def from_bytes(data, encoding):
        model = UserInfo(encoding)
        model._data = data
        if data:
            model.id = struct.unpack("<H", data[:2])[0]
            temp = int(data[2])
            model.enabled = (temp & 1 == 0)
            temp = temp >> 1
            if temp == 1:
                model.privilege = 1
            elif temp == 3:
                model.privilege = 2
            elif temp == 7:
                model.privilege = 3
            else:
                model.privilege = 0
            model.password = get_null_term_str(data, 3, 11, encoding)
            model.name = get_null_term_str(data, 11, 35, encoding)
            model.card_no = struct.unpack("<I", data[35:39])[0]
            model.person_id = get_null_term_str(data, 48, None, encoding)
        return model

    def __bytes__(self):
        output = [0] * 72
        output[0:2] = struct.pack("<H", self.id)
        if self.privilege == 2:
            temp = 3
        elif self.privilege == 3:
            temp = 7
        else:
            temp = self.privilege
        temp = temp << 1
        temp = temp | (0 if self.enabled else 1)
        output[2] = temp
        temp = self.password.encode(self._encoding)
        output[3: 3 + len(temp)] = temp
        temp = self.name.encode(self._encoding)
        output[11: 11 + len(temp)] = temp
        output[35:39] = struct.pack("<I", self.card_no)
        output[39] = 1
        temp = self.person_id.encode(self._encoding)
        output[48: 48 + len(temp)] = temp
        return bytes(output)


class FPInfo:
    def __init__(self, user_id=0, finger_id=0, enabled=True, data=None):
        self.machine_id = 0
        self.user_id = user_id
        self.finger_id = finger_id
        self.enabled = enabled
        self.data = data

    @staticmethod
    def from_bytes(data):
        model = FPInfo()
        if data:
            model.user_id, model.finger_id, model.enabled = struct.unpack("<HBB", data[:4])
            model.data = data[4:]
        return model

    def __bytes__(self):
        return struct.pack("<HBB", self.user_id, self.finger_id, self.enabled) + self.data


class MachineState:
    def __init__(self):
        self.machine_id = 0
        self.user_count = 0
        self.finger_count = 0
        self.face_count = 0
        self.record_count = 0
        self.op_record_count = 0
        self.admin_count = 0
        self.password_count = 0
        self.user_max = 0
        self.finger_max = 0
        self.face_max = 0
        self.record_max = 0
        self.user_rem = 0
        self.finger_rem = 0
        self.face_rem = 0
        self.record_rem = 0

    # machine_id = Column(Integer, ForeignKey(Machine.id), primary_key=True)
    # user_count = Column(Integer)
    # finger_count = Column(Integer)
    # face_count = Column(Integer)
    # record_count = Column(Integer)
    # op_record_count = Column(Integer)
    # admin_count = Column(Integer)
    # password_count = Column(Integer)
    # user_max = Column(Integer)
    # finger_max = Column(Integer)
    # face_max = Column(Integer)
    # record_max = Column(Integer)
    # user_rem = Column(Integer)
    # finger_rem = Column(Integer)
    # face_rem = Column(Integer)
    # record_rem = Column(Integer)

    @staticmethod
    def from_bytes(data):
        model = MachineState()
        model.user_count, \
        model.finger_count, \
        model.record_count, \
        model.op_record_count, \
        model.admin_count, \
        model.password_count, \
        model.finger_max, \
        model.user_max, \
        model.record_max, \
        model.finger_rem, \
        model.user_rem, \
        model.record_rem, \
        model.face_count, \
        model.face_rem, \
        model.face_max = struct.unpack("<16xI4xI4xI4xI4x11I", data[:23 * 4])
        return model

    def __bytes__(self):
        return struct.pack("<16xI4xI4xI4xI4x11I20x",
                           self.user_count,
                           self.finger_count,
                           self.record_count,
                           self.op_record_count,
                           self.admin_count,
                           self.password_count,
                           self.finger_max,
                           self.user_max,
                           self.record_max,
                           self.finger_rem,
                           self.user_rem,
                           self.record_rem,
                           self.face_count,
                           self.face_rem,
                           self.face_max)


class AttLog:
    def __init__(self):
        self.machine_id = 0
        self.att_time = None
        self.person_id = ""
        self.serial = 0
        self.verify_mode = 0
        self.in_out = 0
        self.work_code = 0
        self.encoding = ""

    @staticmethod
    def from_bytes(data, encoding):
        model = AttLog()
        if data:
            model.serial = struct.unpack("<H", data[:2])[0]
            model.person_id = get_null_term_str(data, 2, 26, encoding)
            model.verify_mode, date, model.in_out, model.work_code = struct.unpack("<BIBH", data[26:34])
            model.att_time = number_to_datetime(date)
            model.encoding = encoding
        return model

    def __bytes__(self):
        output = [0] * 40
        output[0:2] = struct.pack("<H", self.serial)
        b_userid = self.person_id.encode(self.encoding)
        output[2:2 + len(b_userid)] = b_userid
        output[26:34] = struct.pack("<BIBH", self.verify_mode, datetime_to_number(self.att_time), self.in_out,
                                    self.work_code)
        return bytes(output)


class OpLog:
    def __init__(self):
        self.machine_id = 0
        self.op_id = 0
        self.op_time = None
        self.admin = 0
        self.param_1 = 0
        self.param_2 = 0
        self.param_3 = 0
        self.param_4 = 0

    @staticmethod
    def from_bytes(data):
        model = OpLog()
        if data:
            model.admin, model.op_id, date, model.param_1, model.param_2, model.param_3, model.param_4 \
                 = struct.unpack("<HHIHHHH", data[:16])
            model.op_time = number_to_datetime(date)
        return model