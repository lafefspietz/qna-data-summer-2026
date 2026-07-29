import asyncio
import json
import time
from urllib.request import urlopen
import hid
import serial
import serial.tools.list_ports
import websockets

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

last_state = {
    "cold_output_switch_1": None,
    "cold_output_switch_2": None,
    "cold_thru_switch_pair": None,
    "measurement_select": None,
    "s_parameter_select": None,
    "twpa_pump_select": None,
    "jpa_pump_select": None,
    "programmable_attenuator": None,
}


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

def configure_warm_switches(json_response):
    measurement_type = json_response["measurement_select"]
    scattering_parameter = json_response["s_parameter_select"]
    twpa_pump = json_response["twpa_pump_select"]
    jpa_pump = json_response["jpa_pump_select"]

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


async def receive_data(websocket):
    async for message in websocket:
        try:
            instrument_data = json.loads(message)
            warm_changed = False
            attenuator_changed = False

            if "cold_switch_states" in instrument_data:
                cold_data = instrument_data["cold_switch_states"]
                for key, val in cold_data.items():
                    if key in last_state and last_state[key] != val:
                        last_state[key] = val
                        print(f"Changed: {key} -> {val}")
                        if key in device_map:
                            device_map[key](val)

            if "warm_switch_states" in instrument_data:
                warm_data = instrument_data["warm_switch_states"]
                for key, val in warm_data.items():
                    if key in last_state and last_state[key] != val:
                        last_state[key] = val
                        print(f"Changed: {key} -> {val}")
                        if key == "programmable_attenuator":
                            attenuator_changed = True
                        else:
                            warm_changed = True

                if warm_changed:
                    configure_warm_switches(warm_data)
                if attenuator_changed:
                    set_programmable_attenuator(abs(warm_data['programmable_attenuator']))

        except Exception as e:
            print(f"Error: {e}")

async def main_loop():
    async with websockets.serve(receive_data, "localhost", 8080):
        while True:
            await asyncio.sleep(0.1)


if __name__ == "__main__":
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

    device_map = {
        "cold_output_switch_1": lambda val: set_cold_output_switch(
            cold_output_switch_1, val
        ),
        "cold_output_switch_2": lambda val: set_cold_output_switch(
            cold_output_switch_2, val
        ),
        "cold_thru_switch_pair": lambda val: set_cold_thru_switch_pair(val),
    }

    print(f"Switch 1 opened on: {cold_output_switch_1.port}")
    print(f"Switch 2 opened on: {cold_output_switch_2.port}")
    print("HID Thru Switch Pair opened successfully.")
    print("Unified Web Instrument server running on ws://localhost:8080...")

    try:
        asyncio.run(main_loop())
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nServer shutdown complete.")
    finally:
        cold_output_switch_1.close()
        cold_output_switch_2.close()
        cold_thru_switch_pair.close()
        print("All hardware ports safely closed and released.")
