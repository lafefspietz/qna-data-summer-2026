import asyncio
import json
import websockets
import time
from urllib.request import urlopen

WARM_SWITCHES_1_IP_ADDRESS = '169.254.10.10'
WARM_SWITCHES_2_IP_ADDRESS = '169.254.12.12'

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


async def receive_data(websocket):
    async for message in websocket:
        try:
            json_response = json.loads(message)
            print(f"\nReceived state payload from web panel: {json_response}")
            configure_warm_switches(json_response)
        except Exception as e:
            print(f"Error parsing frontend JSON payload: {e}")

async def main():
    async with websockets.serve(receive_data, "localhost", 8080):
        print("Mock Hardware Controller online.")
        print("WebSocket engine streaming on ws://localhost:8080...")
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMock server shut down cleanly.")
