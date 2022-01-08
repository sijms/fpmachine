# fpmachine
python driver for fingerprint machine (ZKTeco biometrics)
# support
until now 2 model supported and tested ZMM100_TFT and ZMM220_TFT
# install
```bash
pip3 install --upgrade fpmachine
```
# usage
```python
from fpmachine.devices import ZMM220_TFT

# create a device with ip, port and encoding
dev = ZMM220_TFT("192.168.1.3", 4370, "latin-1")

# connect and pass commkey default=0
dev.connect(2020)

# get users
users = dev.get_users()

# get attendance logs
att_logs = dev.get_att_logs()

# get fingerprints
fps = dev.get_fps()

# get face data passing person_id
face = dev.get_user_face("34002")

# get user picture passing person_id
pic = dev.get_user_pic("34002")

# get machine state
state = dev.get_state()

# set user pic passing person_id and bytes (pic data)
dev.set_user_pic("34002", pic_data)

# set user face passing person_id and bytes (face data)
dev.set_user_face("34002", face_data)

# set user at specific serial (id) passing UserInfo that 
dev.set_user(user_info)

# set fingerprint passing FPInfo struct that contain user serial and finger id
dev.set_fp(fp_info)

# set all fingerprints
dev.set_fps(fp_info_list)

# use delete function with caution

# delete user passing user serial (id) not person id
dev.del_user(id)

# delete user pic passing person_id
dev.del_user_pic("34002")

# delete user face passing person_id
dev.del_user_face("34002")

# delete fingerprint passing person_id and finger_id
dev.del_fp("34002", 5)
# delete all users
dev.del_users()

# delete all admins
dev.del_admins()

# delete all fingerprints
dev.del_fps()

# delete all attendance logs
dev.del_att_logs()

# disconnect
dev.disconnect()

# note the device object has properties some of them are readonly:
#.    id, name, product_time, serial_number, language, finger_fun_on, face_fun_on, zk_face_version, biometric_type, 
#.    build_version, bin_width, vendor, platform, os, software_version, ...
# others are read/write:
#.    work_code, mac_address, ip_address, password (commkey), port, device_time
