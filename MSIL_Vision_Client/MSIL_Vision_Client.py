import snap7,os,sys,psutil
from snap7.util import get_bool,set_bool
import time,threading,queue,socket

name_list=os.path.basename(__file__).split('.')
name_list[-1]="exe"
exe_name_list=[".".join(name_list),"_visible.".join(name_list)]
print(exe_name_list)
process_count=0
for p in psutil.process_iter():
    # print(p.name())
    if p.name() in exe_name_list:
        process_count=process_count+1
        # print
    if process_count>2:
        print(process_count)
        print("Already execution file ran")
        sys.exit()       

setting_file=open('msil_client_settings.txt','r')
print("MT: I am a Server of MSIL vision")

filedic={}
for line in setting_file:
    file_data=line.strip().split('===')
    a=file_data[0]
    b=file_data[1]
    filedic[a]=b
setting_file.close()

ipaddress_of_plc=filedic.pop('ipaddress_of_plc')
db_number=int(filedic.pop('data_block_number_of_plc'))
rack_number=int(filedic.pop('rack_number_of_plc'))
slot_number=int(filedic.pop('slot_number_of_plc'))
ipaddress_of_server=filedic.pop('ipaddress_of_server_system')
port_of_server=int(filedic.pop('port_of_server_system'))
max_size_server_queue=int(filedic.pop('maximum_size_server_queue'))
plc_db_read_delay=int(filedic.pop('plc_db_read_delay_in_milliseconds'))/1000
server_reconnect_delay=int(filedic.pop('server_reconnect_delay_in_milliseconds'))/1000
server_queue=queue.Queue(maxsize=max_size_server_queue)

def send_data_server():
    last_data_sent=True
    while True:
        try:
            client_socket=socket.socket()
            try: 
                client_socket.connect((ipaddress_of_server,port_of_server))
                print("connected")
            except socket.error as e:
                print(e)
                client_socket.close()
                continue
            while True:
                if last_data_sent:
                    s_data=server_queue.get()
                client_socket.send(s_data)
                last_data_sent=True
                print("Data sent")
        except Exception as e:
            last_data_sent=False
            print(e)
            client_socket.close()
            time.sleep(server_reconnect_delay)

def snap7_thread():
    connection_flag=False
    while True:
        try:
            if not connection_flag:
                client=snap7.client.Client()
                client.connect(ipaddress_of_plc,rack_number,slot_number)
                connection_flag=True
            prim_data=client.db_read(db_number,0,1)
            #print(prim_data)
            register_flag=get_bool(prim_data,0,0)
            if register_flag:
                camera_status=get_bool(prim_data,0,1)
                # print(camera_status)
                elr_bc_data_byte=client.db_read(db_number,2,42)
                print(elr_bc_data_byte)
                elr_barcode_data=elr_bc_data_byte[2:2+elr_bc_data_byte[1]].decode()
                sensor_cover_bc_data_byte=client.db_read(db_number,44,42)
                print(sensor_cover_bc_data_byte)
                sensor_cover_barcode_data=sensor_cover_bc_data_byte[2:2+sensor_cover_bc_data_byte[1]].decode()
                print(camera_status,"elr :", elr_barcode_data,"sc: ",sensor_cover_barcode_data)
                set_bool(prim_data,0,0,0)
                client.db_write(db_number,0,prim_data)
                if server_queue.full():
                    server_queue.get()
                server_queue.put(camera_status.to_bytes(1,'big')+elr_bc_data_byte+sensor_cover_bc_data_byte)
            time.sleep(plc_db_read_delay)
        except Exception as e:
            if str(e)=="b' TCP : Unreachable peer'":
                print(f' Unable to connect PLC')
                connection_flag=False
            if str(e)=="b' ISO : An error occurred during send TCP : Connection reset by peer'":
                print(f' Unable to connect PLC')
                connection_flag=False
            if str(e)=="b' ISO : An error occurred during recv TCP : Connection timed out'":
                print(f' Unable to connect PLC')
                connection_flag=False
            else:
                print(e)
            time.sleep(2)

snap7_th=threading.Thread(target=snap7_thread,daemon=True)
snap7_th.start()
print("MT: Snap7_thread thread started")
send_data_ser=threading.Thread(target=send_data_server,daemon=True)
send_data_ser.start()
print("MT: Send_data_server thread started")

while True:
    time.sleep(60)
