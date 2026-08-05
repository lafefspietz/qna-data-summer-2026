import asyncio
import json
import time
import websockets
import copy

async def receive_data(websocket, state, previous_state):
    async for message in websocket:
        try:
            incoming_json = json.loads(message)
            
            old_snapshot = copy.deepcopy(previous_state)
            for key, new_value in incoming_json.items():
                old_value = old_snapshot.get(key)
                if old_value != new_value:
                    print(f"Key '{key}' changed from {old_value} to {new_value}")
                    # WHERE ALL THE INSTRUMENTS WILL BE SET ON NETWORK CHANGE

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
    # WHERE ALL THE INSTRUMENTS WILL BE SET ON BOOT (RUN ONCE)
    try:
        asyncio.run(main_loop(state, previous_state))
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nServer shutdown complete.")
