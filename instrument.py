import asyncio
import json
import time
import websockets
import copy
from urllib.request import urlopen
import hid
import serial
import serial.tools.list_ports
from windfreak import SynthHD
from RsInstrument import RsInstrument, BinFloatFormat
import skrf as rf
import matplotlib.pyplot as plt
import numpy as np
import pyvisa


states = {
    "short": [0, 0, 0x00, 0x08, 0x00, 0x00, 0x08, 0x00],
    "open": [0, 0, 0x00],
    "load": [0, 0, 0x00, 0x00, 0x01, 0x00, 0x00, 0x01],
    "port1": [0, 0, 0x14, 0x20, 0x04, 0x14, 0x20, 0x04],
    "port2": [0, 0, 0x04, 0x10, 0x44, 0x04, 0x10, 0x44],
    "port3": [0, 0, 0x01, 0x01, 0x82, 0x01, 0x01, 0x82],
    "port4": [0, 0, 0x00, 0x82, 0x82, 0x00, 0x82, 0x82],
    "port5": [0, 0, 0x02, 0x04, 0x82, 0x02, 0x04, 0x82],
    "port6": [0, 0, 0x0C, 0x40, 0x04, 0x0C, 0x40, 0x04],
}

commands = {
    "short": b"s",
    "open": b"o",
    "load": b"l",
    "port1": b"1",
    "port2": b"2",
    "port3": b"3",
    "port4": b"4",
    "port5": b"5",
    "port6": b"6",
}

WARM_SWITCHES_1_IP_ADDRESS = '169.254.10.10'
WARM_SWITCHES_2_IP_ADDRESS = '169.254.12.12'
PROGRAMMABLE_ATTENUATOR_IP_ADDRESS = '169.254.11.11'

def send_url_command(ip_address, cmd_to_send):
    url = f"http://{ip_address}/:{cmd_to_send}"
    for attempt in range(3):
        try:
            with urlopen(url, timeout=3) as response:
                pte_return = response.read()
            if len(pte_return) > 100:
                print(f"Error, command not found: {url}")
                return "Invalid Command!"
            return pte_return.decode('utf-8').strip()
        except Exception as network_err:
            if attempt == 2:
                print(f"Hardware Network Warning: No response from {ip_address}. Error: {network_err}")
                return "No Response!"
            time.sleep(0.05)
            
def set_warm_switches_by_ip(ip_address, A, B, C, D):
    state_byte = 128 + int(A) + (2 * int(B)) + (4 * int(C)) + (8 * int(D))
    return send_url_command(ip_address, f"SETP={state_byte}")
    
def set_warm_switches(A1, B1, C1, D1, A2, B2, C2, D2):
    response_1 = set_warm_switches_by_ip(WARM_SWITCHES_1_IP_ADDRESS, A1, B1, C1, D1)
    response_2 = set_warm_switches_by_ip(WARM_SWITCHES_2_IP_ADDRESS, A2, B2, C2, D2)
    return response_1, response_2

def configure_warm_switches(state_dict):
    measurement_type = state_dict["measurement_select"]
    scattering_parameter = state_dict["s_parameter_select"]
    twpa_pump = state_dict["twpa_pump_select"]
    jpa_pump = state_dict["jpa_pump_select"]

    warm_switch_1_A = 0
    warm_switch_1_B = 0
    warm_switch_1_C = 0
    warm_switch_1_D = 0
    warm_switch_2_A = 0
    warm_switch_2_B = 0
    warm_switch_2_C = 0
    warm_switch_2_D = 0

    if measurement_type == "vna":
        warm_switch_2_B = 0
        warm_switch_2_C = 0
    elif measurement_type == "spectrum_analyzer_fridge":
        warm_switch_2_B = 0
        warm_switch_2_C = 1
    elif measurement_type == "spectrum_analyzer_diode":
        warm_switch_2_B = 1
        warm_switch_2_C = 1

    if scattering_parameter in ["s11", "s12", "s13", "s14"]:
        warm_switch_2_A = 0
    elif scattering_parameter in ["s21", "s22", "s23", "s24"]:
        warm_switch_2_A = 1

    if scattering_parameter in ["s11", "s21"]:
        warm_switch_1_A = 0
        warm_switch_1_B = 0
    elif scattering_parameter in ["s12", "s22"]:
        warm_switch_1_A = 0
        warm_switch_1_B = 1
        warm_switch_1_C = 0
    elif scattering_parameter in ["s13", "s23"]:
        warm_switch_1_A = 1
        warm_switch_1_B = 0
        warm_switch_1_C = 0
    elif scattering_parameter in ["s14", "s24"]:
        warm_switch_1_A = 1
        warm_switch_1_B = 0
        warm_switch_1_C = 1

    if twpa_pump == "twpa_pump_1":
        warm_switch_1_D = 0
    elif twpa_pump == "twpa_pump_2":
        warm_switch_1_D = 1

    if jpa_pump == "jpa_pump_1":
        warm_switch_2_D = 0
    elif jpa_pump == "jpa_pump_2":
        warm_switch_2_D = 1

    set_warm_switches(
        warm_switch_1_A,
        warm_switch_1_B,
        warm_switch_1_C,
        warm_switch_1_D,
        warm_switch_2_A,
        warm_switch_2_B,
        warm_switch_2_C,
        warm_switch_2_D,
    )

    
def set_programmable_attenuator(attenuation):
    send_url_command(PROGRAMMABLE_ATTENUATOR_IP_ADDRESS, f"SETATT={attenuation}")

def get_port_by_serial(serial_num):
    for p in serial.tools.list_ports.comports():
        if p.serial_number == serial_num:
            return p.device
    raise RuntimeError(f"Switch with serial {serial_num} not found!")

def set_cold_thru_switch_pair(state_string):
    if state_string in states:
        data = states[state_string]
        cold_thru_switch_pair.write(data)
        cold_thru_switch_pair.write([0, 2])
        print(state_string)

def set_cold_output_switch(switch_device, state_string):
    if state_string in commands:
        switch_device.write(commands[state_string])
        print(f"{state_string}")

switch_1_serial = "342393133353518022E0"
switch_2_serial = "3423232363135150A1D2"

cold_output_switch_1 = serial.Serial(
    get_port_by_serial(switch_1_serial), 9600, write_timeout=0
)
cold_output_switch_2 = serial.Serial(
    get_port_by_serial(switch_2_serial), 9600, write_timeout=0
)

VID = 0x04D8
PID = 0xEDFB

cold_thru_switch_pair = hid.device()
cold_thru_switch_pair.open(VID, PID)


rm = pyvisa.ResourceManager()
instruments = rm.list_resources()

vna = None
for instrument in instruments:
    if 'Rohde' in instrument:
        # Initialize instrument
        vna = RsInstrument(instrument, id_query=True, reset=False) 
        break

spa = None
for instrument in instruments:
    if '7405' in instrument:
        spa = rm.open_resource(instrument) 
        break

async def receive_data(websocket, state, previous_state):
    async for message in websocket:
        try:
            incoming_json = json.loads(message)
            
            old_snapshot = copy.deepcopy(previous_state)
            for key, new_value in incoming_json.items():
                old_value = old_snapshot.get(key)
                if old_value != new_value:
                    print(f"Key '{key}' changed from {old_value} to {new_value}")
                    # set all instrument states here:
                    if key == 'programmable_attenuator':
                        set_programmable_attenuator(incoming_json['programmable_attenuator'])
                    if key == 's_parameter_select' or key == 'measurement_select' or key == 'twpa_pump_select' or key == 'jpa_pump_select':
                        configure_warm_switches(incoming_json)
                    if key == 'cold_output_switch_1':
                         set_cold_output_switch(cold_output_switch_1,incoming_json["cold_output_switch_1"])
                    if key == 'cold_output_switch_2':
                         set_cold_output_switch(cold_output_switch_2,incoming_json["cold_output_switch_2"])
                    if key == 'cold_thru_switch_pair':
                        set_cold_thru_switch_pair(incoming_json['cold_thru_switch_pair'])
                    if key == 'vna_start_frequency':
                        vna.write(f":SENS1:FREQ:START {incoming_json['vna_start_frequency']}")
                        vna.go_to_local()
                    if key == 'vna_stop_frequency':
                        vna.write(f":SENS1:FREQ:STOP {incoming_json['vna_stop_frequency']}")
                        vna.go_to_local()
                    if key == 'vna_number_of_points':
                        vna.write(f":SENS1:SWEep:POINts {incoming_json['vna_number_of_points']}")
                        vna.go_to_local()
                    if key == 'vna_if_bandwidth':
                        vna.write(f":SENS1:BANDwidth {incoming_json['vna_if_bandwidth']}")
                        vna.go_to_local()
                    if key == 'vna_source_power':
                        vna.write(f":SOUR1:POW {incoming_json['vna_source_power']}")
                        vna.go_to_local()
                    if key == 'spa_start_frequency':    
                        spa.write(f":SENS1:FREQ:START {incoming_json['spa_start_frequency']}")
                    if key == 'spa_stop_frequency':
                        spa.write(f":SENS1:FREQ:STOP {incoming_json['spa_stop_frequency']}")
                    if key == 'spa_number_of_points':
                        spa.write(f":SENS1:SWEep:POINts {incoming_json['spa_number_of_points']}")
                    if key == 'spa_resolution_bandwidth':
                        spa.write(f":SENS:BAND {incoming_json['spa_resolution_bandwidth']}")
                    if key == 'spa_video_bandwidth':
                        spa.write(f":SENS:BAND:VID {incoming_json['spa_video_bandwidth']}")

            state.clear()
            state.update(incoming_json)
            if state != previous_state:
                previous_state.clear()
                previous_state.update(copy.deepcopy(state))
        except Exception as e:
            print(f"Error parsing data: {e}")


async def main_loop(state, previous_state):
    async def connection_handler(ws):
        await receive_data(ws, state, previous_state)
    async with websockets.serve(connection_handler, "localhost", 8080):
        while True:
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    with open("state.json", "r") as f:
        state = json.load(f)
    previous_state = copy.deepcopy(state)
    time.sleep(1) 
    # WHERE ALL THE INSTRUMENTS WILL BE SET ON BOOT (RUN ONCE):
    set_cold_output_switch(cold_output_switch_1,state["cold_output_switch_1"])
    set_cold_output_switch(cold_output_switch_2,state["cold_output_switch_2"])
    set_cold_thru_switch_pair(state['cold_thru_switch_pair'])
    configure_warm_switches(state)
    set_programmable_attenuator(state['programmable_attenuator'])

    vna.write(f":SENS1:FREQ:START {state['vna_start_frequency']}")
    vna.write(f":SENS1:FREQ:STOP {state['vna_stop_frequency']}")
    vna.write(f":SENS1:SWEep:POINts {state['vna_number_of_points']}")
    vna.write(f":SENS1:BANDwidth {state['vna_if_bandwidth']}")
    vna.write(f":SOUR1:POW {state['vna_source_power']}")
    vna.go_to_local()
    
    spa.write(f":SENS1:FREQ:START {state['spa_start_frequency']}")
    spa.write(f":SENS1:FREQ:STOP {state['spa_stop_frequency']}")
    spa.write(f":SENS1:SWEep:POINts {state['spa_number_of_points']}")
    spa.write(f":SENS:BAND {state['spa_resolution_bandwidth']}")
    spa.write(f":SENS:BAND:VID {state['spa_video_bandwidth']}")

    try:
        asyncio.run(main_loop(state, previous_state))
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nServer shutdown complete.")
    finally:
        cold_output_switch_1.close()
        cold_output_switch_2.close()
        cold_thru_switch_pair.close()
        print("All switch hardware ports safely closed and released.")
    
