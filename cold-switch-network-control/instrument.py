import asyncio
import json
import time
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

last_state = {
    "cold_output_switch_1": None,
    "cold_output_switch_2": None,
    "cold_thru_switch_pair": None,
}


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

            for key, val in instrument_data.items():
                if key in last_state and last_state[key] != val:
                    last_state[key] = val
                    print(f"Changed: {key} -> {val}")

                    if key in device_map:
                        device_map[key](val)

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
    print("Starting WebSocket server on ws://localhost:8080...")

    try:
        asyncio.run(main_loop())
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nServer shutdown complete.")
    finally:
        cold_output_switch_1.close()
        cold_output_switch_2.close()
        cold_thru_switch_pair.close()
        print("All hardware ports safely closed and released.")
