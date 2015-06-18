"""
File: insert_code.py
Authors: Daniel Chen and Homa Alemzadeh
Created: 2015/2/3

Overall Idea
1. copy entire folder from backup to origion
2. Read the target file and determine what to insert
3. Insert to the source code file
4. Compile the source code file

Modified: 2015/2/5
1. Now checks if make was successful, if not restores and quits
2. Added a quit function to be called on Ctrl+C and compilation errors
3. Fixed the R matrix value assignment
4. Added different assignment scenarios for position, rotation, and joint variables
"""

import os
import subprocess
import random
import sys
from math import cos, sin, sqrt, acos, asin, pow as pow_f
import socket
import sys
from db import Mysql
from collections import OrderedDict
import numpy as np
import struct
import time
import signal

src = '/home/junjie/homa_wksp/raven_2/src/raven'
master_file = './selected_injection.txt'
raven_home = '/home/junjie/homa_wksp/raven_2'
root_dir = '/home/junjie/homa_wksp'
cur_inj = -1
saved_param = []
surgeon_simulator = 1;
UDP_IP = "127.0.0.1"
UDP_PORT = 34000
injection_summary = open('/home/junjie/homa_wksp/raven_2/injection_summary.txt','w')
injection_detail = open('/home/junjie/homa_wksp/raven_2/injection_detail.txt','w')

env = os.environ.copy()
'''splits = env['ROS_PACKAGE_PATH'].split(':')
splits[-1] = '/home/junjie/homa_wksp/raven_2'
os.environ['ROS_PACKAGE_PATH']=':'.join(splits)
print os.environ['ROS_PACKAGE_PATH'] '''

goldenRavenTask= 'xterm -e roslaunch raven_2 raven_2.launch'
ravenTask = 'xterm -hold -e roslaunch raven_2 raven_2.launch inject_mode:='
if (surgeon_simulator == 1):
    packetTask = 'xterm -hold -e python '+raven_home+'/Real_Packet_Generator_Surgeon.py'
else:
    packetTask = 'xterm -e python '+raven_home+'/Real_Packet_Generator.py'


def str_to_nums(out_str):
    out_num = [];
    param = out_str.split(',')
    for p in param:
        out_num.append(int_or_float(p))
    return out_num

# Convert rotation matrix to yaw (rz), pitch (ry), roll (rx) 
def to_ypr(R_str):
    param = R_str.split(',')
    R00 = float(param[0]);
    R02 = float(param[2]);
    R22 = float(param[8]);

    ry = asin(min(1,max(R02,-1)));
    rx = acos(min(1,max(R22/cos(ry),-1)));
    rz = acos(min(1,max(R00/cos(ry),-1)));

    ypr_str = str(rz)+', '+str(ry)+', '+str(rx);

    return ypr_str

# Convert yaw (rz), pitch (ry), roll (rx) to rotation matrix
def generate_rotation(a, b):
    rx = random.uniform(a, b)
    ry = random.uniform(a, b)
    rz = random.uniform(a, b)

    R00 = cos(ry)*cos(rz)
    R01 = -cos(ry)*sin(rz)
    R02 = sin(ry)

    R10 = cos(rx)*sin(rz)+cos(rz)*sin(rx)*sin(ry)
    R11 = cos(rx)*cos(rz)-sin(rx)*sin(ry)*sin(rz)
    R12 = -cos(ry)*sin(rx)

    R20 = sin(rx)*sin(rz)-cos(rx)*cos(rz)*sin(ry)
    R21 = cos(rz)*sin(rx)+cos(rx)*sin(ry)*sin(rz)
    R22 = cos(rx)*cos(ry)
    R = '%5f;%5f;%5f;%5f;%5f;%5f;%5f;%5f;%5f' % \
            (R00, R01, R02, R10, R11, R12, R20, R21, R22)

    return R

def int_or_float(s):
    try:
        return int(s, 0)
    except ValueError:
        return float(s)

# generate_target_r(param)
# Format of param:
#   <type> <min> <max>

def generate_target_r(param):
    for item in param:
        p = item.lstrip()
        param2 = p.split(' ')
        newline = ''
        if param2[1] == 'rand_float':
            new_val = random.uniform(int_or_float(param2[2]), int_or_float(param2[3]))
            newline = "%s %5f" % (param2[0], new_val)
        elif param2[1] == 'rand_int':
            new_val = random.randint(int(param2[2]), int(param2[3]))
            newline = "%s %d" % (param2[0], new_val)
        elif param2[1] == 'rand_rotation':
            new_val = generate_rotation(int_or_float(param2[2]), int_or_float(param2[3]))
            newline = "%s %s" % (param2[0], new_val)
        else:
            newline = item
    return newline;

# generate_target_r(param)
# Format of param:
#   <type> <min> <max>
# Example: generate_target_r_stratified(['sequence rand_float 0.1 10.5'], 10, 9)

def generate_target_r_stratified(param, num_of_bin, current_bin):
    for item in param:
        p = item.lstrip()
        param2 = p.split(' ')
        print param2[0]
        print param2[1]
        print param2[2]
        print param2[3]
        newline = ''
        if param2[1] == 'rand_float':
            min_val = int_or_float(param2[2])
            max_val = int_or_float(param2[3])
            total_range = max_val - min_val
            increment = total_range / num_of_bin
            lower_bound = min_val + current_bin * increment
            upper_bound = min_val + (current_bin+1) * increment
            if upper_bound > max_val:
                upper_bound = max_val
            new_val = random.uniform(lower_bound, upper_bound)
            newline = "%s %5f" % (param2[0], new_val)
        elif param2[1] == 'rand_int':
            min_val = int(param2[2])
            max_val = int(param2[3])
            total_range = max_val - min_val
            increment = total_range / num_of_bin
            lower_bound = min_val + current_bin * increment
            upper_bound = min_val + (current_bin+1) * increment
            if upper_bound > max_val:
                upper_bound = max_val
            new_val = random.randint(lower_bound, upper_bound)
            newline = "%s %d" % (param2[0], new_val)
        elif param2[1] == 'rand_rotation':
            new_val = generate_rotation(int_or_float(param2[2]), int_or_float(param2[3]))
            newline = "%s %s" % (param2[0], new_val)
        else:
            newline = item
        print "debug: " + newline
    return newline;

# Format of the list dictionary my_dict.
# my_dict[index]{key, value}
# index = packet number
# key(str) = "FK_Pos_Arm0", "FK_Pos_Arm1", ...
# value(?) = 
# [0] Packet #
# [1:4] FK_Pos_Arm0
# [4:7] FK_Ori_Arm0
# [7:14] IK_Thetas_Arm0
# [14-17] FK_Pos_Arm1
# [17-20] FK_Ori_Arm1
# [20-27] IK_Thetas_Arm1
# [28] Error_Msg
def parse_log_file2(fd):
    my_list = []
    error_str = ''
    dt=np.dtype([('packet', 'i4'),
            ('arm0_pos', '3f4'),
            ('arm0_ori', '3f4'),
            ('arm0_thetas', '7f4'),
            ('arm1_pos', '3f4'),
            ('arm1_ori', '3f4'),
            ('arm1_thetas', '7f4'),
            ('error_msg','a2000')])

    # Build dictionary
    for line in fd:
        # Strip '\n' from each line then split by ','
        line = line.strip('\n')
        param = line.split(':')
        # Skip empty lines
        if param[0] == '': 
            continue
        # End of Packet => Store it in the list
        elif param[0].startswith('_'):
            my_list.append(array)
        # New Packet => Create a new array
        elif param[0] == 'Packet':
            array = np.zeros(1, dt)
            array['packet'] = int(param[1])
        elif param[0] == 'FK_Pos_Arm0':
            array['arm0_pos'] = str_to_nums(param[1])
        elif param[0] == 'FK_Ori_Arm0':
            array['arm0_ori'] = str_to_nums(to_ypr(param[1]))
        elif param[0] == 'IK_Thetas_Arm0':
            array['arm0_thetas'] = str_to_nums(param[1])
        elif param[0] == 'FK_Pos_Arm1':
            array['arm1_pos'] = str_to_nums(param[1])
        elif param[0] == 'FK_Ori_Arm1':
            array['arm1_ori'] = str_to_nums(to_ypr(param[1]))
        elif param[0] == 'IK_Thetas_Arm1':
            array['arm1_thetas'] = str_to_nums(param[1])
        elif param[0] == 'Error':
            error_str = str(param[1])+';'+error_str
            array['error_msg'] = str(error_str);
    return my_list

def quit(): 
    try:
        r2_control_pid = subprocess.check_output("pgrep r2_control", 
                shell=True)
        os.killpg(int(r2_control_pid), signal.SIGINT)
        time.sleep(1)
    except:
        pass
    try:
        roslaunch_pid = subprocess.check_output("pgrep roslaunch", 
                shell=True)
        os.killpg(int(roslaunch_pid), signal.SIGINT)
        time.sleep(1)
    except:
        pass
    try:
        os.killpg(raven_proc.pid, signal.SIGINT)
        time.sleep(1)
    except:
        pass
    try:
        os.killpg(packet_proc.pid, signal.SIGINT)
        time.sleep(1)
    except:
        pass

    os.system("killall xterm")
    #os.system("killall python")
    os.system("killall roslaunch")
    os.system("killall r2_control")

def signal_handler(signal, frame):
    print "Ctrl+C Pressed!"
    quit()
    sys.exit(0)

def inject(idx):
    # Fault ID to be used with the output filenames.
    fault_id = str(1)#str(idx);

    #raven_proc = subprocess.Popen(ravenTask+'1', env=env, shell=True, preexec_fn=os.setsid)
    time.sleep(2)   
    #packet_proc = subprocess.Popen(packetTask, shell=True, preexec_fn=os.setsid)
    #Wait for a response from the robot
    data = ''
    while not data:
        print("Waiting for Raven to be done...")
        data = sock.recvfrom(100)
        if data[0].find('Done!') > -1:
            print("Raven is done, shutdown everything...")  
        elif data[0].find('Stopped') > -1:
            print("Raven is stopped, shutdown everything...")  
        else:
            data = ''
    quit()

"""
Example: if (x > 3 && x < 5) {x = 40}
"""
def insert_code(file_name, line_num, trigger, target):

    # Compute all the variable
    src_file = src + "/" + file_name
    bkup_file = src + "/" + file_name + '.bkup'
    chk_file = src + "/" + file_name + '.chk'
    trigger_line = ' && '.join(trigger)
    # target[0] variable name, target[1] value

    # For R matrices injected values are based on absolute values of yaw, roll, pitch
    if ((target[0] == 'u.R_l') or (target[0] == 'u.R_r')):
        code = 'if (' + trigger_line + ') { '; 
        elems = target[1].split(';');
        for i in range(0,3):
            for j in range(0,3):
                code =code+target[0]+'['+str(i)+']['+str(j)+']='+ elems[i*3+j]+'; '; 
        code = code + '}\n';  
        print code
    # For thetas and USBs the injected value is absolute 
    elif (target[0].find('jpos') > -1) or (file_name.find('USB') > -1):
        code = 'if (' + trigger_line + ') { ' + target[0] + ' = ' + target[1] + ';}\n'
    # For position the injected value is incremental
    else:
        code = 'if (' + trigger_line + ') { ' + target[0] + '+= ' + target[1] + ';}\n'
    print file_name + ':' + line_num + '\n' + code
    #save a backup file
    cmd = 'cp ' + src_file + ' ' + bkup_file
    os.system(cmd)

    #open files
    src_fp = open(src_file, 'w')
    bkup_fp = open(bkup_file, 'r')
    
    for i, line in enumerate(bkup_fp):
        if i == int(line_num)-1:
            src_fp.write(code)
        src_fp.write(line)
    src_fp.close()
    bkup_fp.close()

    cmd = 'cd ' + raven_home + ';make -j > compile.output'
    make_ret = os.system(cmd)
 
    #save a check file
    cmd = 'cp ' + src_file + ' ' + chk_file
    os.system(cmd)

    #restore file
    cmd = 'chmod 777 '+bkup_file;
    os.system(cmd);
    cmd = 'cp ' + bkup_file + ' ' + src_file

    # delete backup
    if (os.system(cmd) == 0): 
        cmd = 'rm ' + bkup_file;
        os.system(cmd);   

    if (make_ret != 0):
        print "Make Error: Compilation Failed..\n"
        quit()
        sys.exit(0)

def write_fault_log_to_db(db, inj_param=''):
    print "Writing to the database..."
    # Open fault log
    if (inj_param == 'Golden run'):
        fault_log_name = root_dir+'/raven_2/sim_log.txt'
    else:    
        fault_log_name = root_dir+'/raven_2/fault_log_1.txt'
    fault_fd = open(fault_log_name,'r')
    my_list = parse_log_file2(fault_fd)
    fault_fd.close()
    g_err_msg = '';

    # Connect to DB
    db._open()

    # Insert to DB
    try:
        if ('Golden run' in inj_param):  
            last_id = 0;
        else:      
            injection_summary.write(my_ip+','+time.strftime('%Y-%m-%d %H:%M:%S')+','+inj_param+'\n');
            last_id = db._insert('injection_summary', machine=my_ip, timestamp=time.strftime('%Y-%m-%d %H:%M:%S'), parameter=inj_param)
        
        for item in my_list:
            db._insert('injection_detail',
                    injection_id=last_id,
                    packet=item['packet'][0],
                    x_0=item['arm0_pos'][0][0],
                    y_0=item['arm0_pos'][0][1],
                    z_0=item['arm0_pos'][0][2],
                    yaw_0=item['arm0_ori'][0][0],
                    pitch_0=item['arm0_ori'][0][1],
                    roll_0=item['arm0_ori'][0][2],
                    th1_0=item['arm0_thetas'][0][0],
                    th2_0=item['arm0_thetas'][0][1],
                    th3_0=item['arm0_thetas'][0][2],
                    th4_0=item['arm0_thetas'][0][3],
                    th5_0=item['arm0_thetas'][0][4],
                    th6_0=item['arm0_thetas'][0][5],
                    th7_0=item['arm0_thetas'][0][6],
                    x_1=item['arm1_pos'][0][0],
                    y_1=item['arm1_pos'][0][1],
                    z_1=item['arm1_pos'][0][2],
                    yaw_1=item['arm1_ori'][0][0],
                    pitch_1=item['arm1_ori'][0][1],
                    roll_1=item['arm1_ori'][0][2],
                    th1_1=item['arm1_thetas'][0][0],
                    th2_1=item['arm1_thetas'][0][1],
                    th3_1=item['arm1_thetas'][0][2],
                    th4_1=item['arm1_thetas'][0][3],
                    th5_1=item['arm1_thetas'][0][4],
                    th6_1=item['arm1_thetas'][0][5],
                    th7_1=item['arm1_thetas'][0][6],
                    error_msg=str(item['error_msg'][0]))
            g_err_msg = g_err_msg + ';'+ str(item['error_msg'][0]);
        injection_detail.write(str(last_id)+','+g_err_msg+'\n');
        db._commit()
    except:
        db._rollback()
        print "Error: _insert()"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print sys.exc_info()
        print '\nFile name: '+ str(fname)+' - Line no:'+str(exc_tb.tb_lineno)+'\n'
        exit()
    db._close()


# Main code Starts
if len(sys.argv) < 2:
    print("Error: missing parameter")
    print("Usage: python %s <start_number>" % sys.argv[0])
    exit()
sock = socket.socket(socket.AF_INET, # Internet
                      socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP,UDP_PORT))

# Find my own IP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("gmail.com", 80))
my_ip = s.getsockname()[0]
print my_ip
s.close()

cur_inj = -1 
saved_param= []

# Open and close to clear the results from previous run.py
try:
    os.remove(result_file)
except:
    pass

# Connect to database
db = Mysql(host='130.126.140.209', user='root', password='Netlab1',database='raven')
#db = Mysql(host='127.0.0.1', user='root', password='yans1988',database='raven')
# Add the golden run to database
if (int(sys.argv[1]) == 1):
    print 'Writing Golden Results to Database..'
    write_fault_log_to_db(db, '0: Golden run')

signal.signal(signal.SIGINT, signal_handler)

# Start Injections
with open(master_file) as fp:
    target_file = ''
    line_num = 0
    trigger = []
    target = []

    for line in fp:
        # Strip '\n' from each line then split by ','
        line = line.strip('\n')
        param = line.split(',')

        # Skip lines begin with # or empty line
        if param[0] == '' or param[0] == '#':
            continue
       
        # Read location info
        elif param[0] == 'location':
            location_info = param[1].split(':')
            target_file = location_info[0].lstrip()
            line_num = location_info[1]

        # Read trigger info
        elif param[0] == 'trigger':
            param.pop(0)
            trigger = [item.strip() for item in param]

        elif param[0] == 'target_r':
            param.pop(0)
            saved_param = param
            target = (generate_target_r(saved_param)).split(' ')

        elif param[0] == 'injection':
            if cur_inj != int(param[1]):
                cur_inj = int(param[1])
                print("setup param for %d" % cur_inj)
            else:
                # Injection starts at argv[1]
                # Example starting_inj_num is 3.2
                starting_inj_num = (sys.argv[1]).split('.')
                if int(param[1]) >= int(starting_inj_num[0]):
                    # If param == 3, indicate do random injection param[2] times.
                    if len(param) == 3:
                        for x in xrange(int(param[2])):
                            if len(starting_inj_num) > 1:
                                if x < int(starting_inj_num):
                                    next
                            #target = (generate_target_r(saved_param)).split(' ')
                            target = (generate_target_r_stratified(saved_param, int(param[2]), x)).split(' ')
                            insert_code(target_file, line_num, trigger, target)

                            print("injecting to %d.%d" % (cur_inj, x))
                            inject(str(cur_inj)+'.'+str(x))
                            write_fault_log_to_db(db, str(cur_inj)+': '+target_file+';'+ line_num+';'+';'.join(trigger)+';'+';'.join(target))
                    else:
                        print("injecting to %d" % (cur_inj))
                        insert_code(target_file, line, trigger, target)
                        inject(str(cur_inj))
                        write_fault_log_to_db(db, str(cur_inj)+': '+target_file+';'+ line_num+';'+';'.join(trigger)+';'+';'.join(target))

