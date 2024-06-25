import tkinter as tk
import asyncio
from aiocoap import *

async def coap_client(payload):
    server_ip = "169.254.117.139"
    server_port = 5683
    resource_path = "resource"
    
    context = await Context.create_client_context()
    uri = f'coap://{server_ip}:{server_port}/{resource_path}'
    request = Message(code=POST, payload=payload.encode('utf-8'), uri=uri)

    try:
        response = await context.request(request).response
        print('Response: %s\n%r' % (response.code, response.payload))
    except Exception as e:
        print('Failed to fetch resource:')
        print(e)

class CoAPClient:
    def _init_(self, app):
        self.app = app

    async def send_values(self):
        first_value = self.app.key_values.get(1200, 0)
        values = [first_value] + [0] * 7  # Sende nur den ersten Wert, die anderen sind 0
        payload = ','.join(map(str, values))
        await coap_client(payload)

class PianoApp:
    def _init_(self, root):
        self.root = root
        self.root.title("Grafisches Klavier")

        self.keys = []
        self.key_values = {1200: 0}

        self.notes = ["C0", "D", "E", "F", "G", "A", "H", "C1"]
        self.key_map = {
            'a': 1200, 's': 1100, 'd': 1000, 'f': 900, 
            'g': 800, 'h': 700, 'j': 600, 'k': 500
        }

        self.coap_client = CoAPClient(self)
        self.create_piano()
        self.bind_keys()

    def create_piano(self):
        key_width = 50
        key_height = 100

        for i, note in enumerate(self.notes):
            key = tk.Canvas(self.root, width=key_width, height=key_height, bg="white", borderwidth=1, relief="solid")
            key.create_text(key_width//2, key_height//2, text=note, font=("Arial", 24))
            key.grid(row=0, column=i, padx=2, pady=2)
            key.bind("<ButtonPress-1>", self.press_key(1200 - i * 100))
            key.bind("<ButtonRelease-1>", self.release_key(1200 - i * 100))

            self.keys.append(key)

    def press_key(self, key_value):
        def on_press(event):
            key_index = (1200 - key_value) // 100
            self.keys[key_index].configure(bg="gray")
            self.key_values[1200] = key_value
            print(f"Taste {self.notes[key_index]} gedrückt, Wert: {self.key_values[1200]}")
            asyncio.create_task(self.coap_client.send_values())

        return on_press

    def release_key(self, key_value):
        def on_release(event):
            key_index = (1200 - key_value) // 100
            self.keys[key_index].configure(bg="white")
            self.key_values[1200] = 100
            print(f"Taste {self.notes[key_index]} losgelassen, Wert: {self.key_values[1200]}")
            asyncio.create_task(self.coap_client.send_values())

        return on_release

    def bind_keys(self):
        for key, value in self.key_map.items():
            self.root.bind(f'<{key}>', self.press_key(value))
            self.root.bind(f'<KeyRelease-{key}>', self.release_key(value))

async def tkinter_loop(root):
    while True:
        root.update()
        await asyncio.sleep(0.01)

async def main():
    root = tk.Tk()
    app = PianoApp(root)

    # Starte die tkinter-Ereignisschleife in einer asyncio-Schleife
    await tkinter_loop(root)

if _name_ == "_main_":
    asyncio.run(main())