from datetime import datetime
import struct
# if segment size > 0x2000 shift to stream
device_cmd = {
    'read_db': 0x0007,
    'set_user': 0x0008,
    'get_fp': 0x0009,
    'set_fp': 0x000A,
    'get_data': 0x000B,  # another name "get_sys_option"
    'set_data': 0x000C,  # another name "set_sys_option"
    'read_latest_log': 0x000D,
    'cls_data': 0x000E,
    'del_logs': 0x000F,
    'append_fp': 0x0011,
    'del_user': 0x0012,
    'del_fp': 0x0013,
    'cls_admins': 0x0014,
    'get_user_group': 0x0015,
    'set_user_group': 0x0016,
    'get_user_tz': 0x0017,
    'set_user_tz': 0x0018,
    'get_group_tz': 0x0019,
    'set_group_tz': 0x001A,
    'get_tz': 0x001B,
    'set_tz': 0x001C,
    'get_unlock_group': 0x001D,
    "set_lock_comb": 0x001E,
    "unlock": 0x001F,
    'clear_op_log': 0x0021,
    'read_op_log': 0x0022,
    'ssr_read_att_role': 0x0023,
    'ssr_read_depart': 0x0024,
    'ssr_read_turn': 0x00025,
    'logs_count': 0x0032,
    'end_enroll': 0x003C,
    'start_enroll': 0x003D,
    'cancel_op': 0x003E,
    'query_state': 0x0040,
    'write_LCD': 0x0042,
    'clear_LCD': 0x0043,
    'get_pin_width': 0x0045,
    'get_sms_id': 0x0047,
    'set_user_sms_id': 0x0049,
    'get_door_state': 0x004B,
    'set_workcode': 0x0052,
    'get_workcode': 0x0053,
    'set_fp_ex': 0x0057,
    'get_fp_ex': 0x0058,
    'read_rt_log': 0x005A,
    'get_holiday_tz': 0x005B,
    "set_holiday_tz": 0x005C,
    "send_file": 0x006E,
    'check_hash': 0x0077, 
    'ssr_del_user_ext': 0x0085,
    'del_fp_ex': 0x0086,
    'del_user_fp': 0x0086,
    'get_face': 0x0096,
    "set_face": 0x0097,
    "del_face": 0x0098,
    'get_time': 0x00C9,
    'set_time': 0x00CA,
    'get_holiday': 0x012C,
    'set_holiday': 0x012D,
    'reg_event': 0x01F4,
    'query_sys_op': 0x1F5,
    'connect': 0x03E8,
    'disconnect': 0x03E9,
    'enable': 0x03EA,
    'disable': 0x03EB,
    'reboot': 0x03EC,
    'shutdown': 0x03ED,
    "sleep": 0x03EE,
    'resume': 0x03EF,
    'capture_image': 0x03F4,
    'save_data': 0x03F5,
    'play_voice': 0x03F9,
    'beep': 0x03FC,
    'suspend': 0x03FE,
    'soft_ver': 0x044C,
    'login': 0x044E,
    'recv_buff_header': 0x05DC,
    'recv_buff_content': 0x05DD,
    'end_buff_stream': 0x05DE,
    'start_buff_stream': 0x05DF,
    'buff_stream': 0x05E0,
    'update_lang_by_id': 0x06A5,
    'set_custom_att_state': 0x06A7,
    "set_custom_voice": 0x06A8,
    'enable_custom_voice': 0x06AA,
    "update_file": 0x06AD,
    'ack': 0x07D0,
    'nak': 0x07D1,
    'accept_conn': 0x07D5,
    'get_photo_count': 0x07DD,
    'get_photo_by_name': 0x07DE,
    'clear_photo_by_time': 0x07DF,
    'get_photo_names_by_time': 0x07E0,
    'read_large_tmp': 0x07E1,
    'read_temp_data': 0x08AD,
    'no_pic': 0x1379,
    'no_record': 0x137D,
    'no_fp': 0x137F,
    'no_data': 0x1381,
    'empty_upload_buffer': 0x1383,  # received in set_fp_ex command
    'no_sys_op': 0x1387,
    'get_table_struct': 0x2710,
    'set_user_pic': 0x2719,
    'get_user_pic': 0x271A,
    'del_user_pic': 0x271B,
    'not_support': 0xFFFF
}


def dump(data):
    return [hex(x) for x in data]


def split_list(alist, wanted_parts=1):
    length = len(alist)
    return [alist[i * length // wanted_parts: (i + 1) * length // wanted_parts] for i in range(wanted_parts)]


def datetime_to_number(dt):
    year = dt.year - 2000
    month = dt.month - 1
    day = dt.day - 1
    hour = dt.hour
    minute = dt.minute
    second = dt.second
    temp = year * 12
    temp = temp + month
    temp = (temp << 5) - temp

    temp = ((temp + day) * 24) + hour
    temp = (temp << 4) - temp

    temp = (temp * 4) + minute
    temp = (temp << 4) - temp

    temp = (temp * 4) + second
    return temp


def number_to_datetime(dword_time):
    base_number = dword_time
    temp1 = ((base_number * 0x88888889) >> 32) & 0xFFFFFFFF
    temp2 = temp1 >> 5
    temp3 = temp2 << 4
    second = base_number - ((temp3 - temp2) * 4)
    base_number = temp2
    temp1 = ((base_number * 0x88888889) >> 32) & 0xFFFFFFFF
    temp2 = temp1 >> 5
    temp3 = temp2 << 4
    minute = base_number - ((temp3 - temp2) * 4)

    base_number = temp2
    temp1 = ((base_number * 0xAAAAAAAB) >> 32) & 0xFFFFFFFF
    temp2 = temp1 >> 4
    temp3 = temp2 * 3
    hour = base_number - (temp3 * 8)

    base_number = temp2
    temp1 = ((base_number * 0x8421085) >> 32) & 0xFFFFFFFF
    temp2 = (((base_number - temp1) >> 1) + temp1) >> 4
    temp3 = temp2 << 5
    day = base_number - (temp3 - temp2) + 1

    base_number = temp1
    temp1 = ((base_number * 0xAAAAAAAB) >> 32) & 0xFFFFFFFF
    temp2 = (temp1 >> 3)
    temp3 = temp2 * 12
    month = (base_number - temp3) + 1
    year = temp2 + 0x7D0
    return datetime(year, month, day, hour, minute, second)


def datetime_to_bytes(dt):
    return struct.pack("<I", datetime_to_number(dt))


def datetime_from_bytes(data):
    return number_to_datetime(struct.unpack("<I", data)[0])


def get_null_term_str(data, start, end, encoding):
    temp = data[start:end]
    if 0 in temp:
        temp = bytes(temp[:temp.index(0)])
    else:
        temp = bytes(temp)
    return temp.decode(encoding)
