import tkinter as tk
from win32api import GetSystemMetrics
import win32api
import win32con
import win32gui
import time
import pymem.process
import json
import struct
import keyboard
from numpy import random
import threading

json_file_path_client = r"C:\Users\c1tru5x\Downloads\cs2-dumper\generated\client.dll.json"
with open(json_file_path_client, 'r') as json_file:
    client_data = json.load(json_file)

json_file_path_offsets = r"C:\Users\c1tru5x\Downloads\cs2-dumper\generated\offsets.json"
with open(json_file_path_offsets, 'r') as json_file:
    offs_data = json.load(json_file)

dwLocalPlayerPawn = offs_data["client_dll"]["data"]["dwLocalPlayerPawn"]["value"]
dwEntityList = offs_data["client_dll"]["data"]["dwEntityList"]["value"]
m_hPlayerPawn = client_data["CCSPlayerController"]["data"]["m_hPlayerPawn"]["value"]
m_iTeamNum = client_data["C_BaseEntity"]["data"]["m_iTeamNum"]["value"]
m_iIDEntIndex = client_data["C_CSPlayerPawnBase"]["data"]["m_iIDEntIndex"]["value"]
m_bIsDefusing = client_data["C_CSPlayerPawnBase"]["data"]["m_bIsDefusing"]["value"]
m_bHasDefuser = client_data["CCSPlayer_ItemServices"]["data"]["m_bHasDefuser"]["value"]
m_iHealth = client_data["C_BaseEntity"]["data"]["m_iHealth"]["value"]
dwPlantedC4 = offs_data["client_dll"]["data"]["dwPlantedC4"]["value"]
m_nBombSite = client_data["C_PlantedC4"]["data"]["m_nBombSite"]["value"]
dwViewMatrix = offs_data["client_dll"]["data"]["dwViewMatrix"]["value"]
m_vOldOrigin = client_data["C_BasePlayerPawn"]["data"]["m_vOldOrigin"]["value"]
m_bDormant = client_data["CGameSceneNode"]["data"]["m_bDormant"]["value"]

lock = threading.Lock
pm = pymem.Pymem("cs2.exe")
client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll

player = pm.read_longlong(client + dwLocalPlayerPawn)
while player is None:  # check for team switch, for example
    player = pm.read_longlong(client + dwLocalPlayerPawn)

playerSize = 16 #number of entities (shrink if mem error)

class MoveableOverlay(tk.Tk):
    def __init__(self):
        super().__init__()
        self.crosshair_radius_cm = 7  # Desired crosshair radius in centimeters
        self.crosshair_length = int(self.crosshair_radius_cm * 2)  # Set line length to twice the desired radius

        self.geometry(f"{GetSystemMetrics(0)}x{GetSystemMetrics(1)}+0+0")
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.attributes('-transparentcolor', 'black')
        self.overrideredirect(True)

        self.canvas = tk.Canvas(self, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click) #dont loose focus on click of drawn objects

        self.crosshair_h = None
        self.crosshair_v = None
        self.snap_line = None
        self.text_id = None

        # Start the periodic update
        self.update_crosshair()

        # Bind to window resize events
        self.old_window_proc = win32gui.SetWindowLong(self.winfo_id(), win32con.GWL_WNDPROC, self.on_size)

        # Bind to the Destroy event
        self.bind("<Destroy>", self.on_destroy)
    def on_canvas_click(self, event):
        # Release the grab to allow click-through
        self.grab_release()

    def on_canvas_click(self, event):
        # Check if the click occurred within the region occupied by the drawn elements
        x, y = event.x, event.y
        if self.canvas.find_overlapping(x, y, x, y):
            # Click occurred on the drawn elements, ignore it
            return "break"

    def draw_crosshair(self, enemy_coordinates):
        for x, y, z, player_health in enemy_coordinates:
            if z < 0.01: #no div 0 error
                return
            # Adjust rectangle size based on Z-distance and screen size
            rect_size = 100000 / z
            rect_width = rect_size / 3.3
            rect_height = rect_size / 1.9

            # Calculate rectangle coordinates
            rect_x1 = x - rect_width / 2
            rect_y1 = y
            rect_x2 = x + rect_width / 2
            rect_y2 = y + rect_height * -1

            # Draw rectangle with outline
            self.canvas.create_rectangle(rect_x1, rect_y1, rect_x2, rect_y2, outline="#00ff00" if player_health > 30 else "#ff0000", width=max(2, int(rect_size / 100)))
            # Draw line from bottom center to crosshair middle
            bottom_center_x = GetSystemMetrics(0) // 2
            bottom_center_y = GetSystemMetrics(1)
            snap_line = self.canvas.create_line(bottom_center_x, bottom_center_y, x, y, fill="#0000bb" if player_health > 30 else "#ff0000", width=2)
            health_text = "{}".format(player_health)  # Replace with the actual health value for each enemy
            health_text_id = self.canvas.create_text(x , rect_y2 - 10, text=health_text,
                                                    font=("sans-serif", 10, "bold"), fill="#00ff00" if player_health > 30 else "#ff0000")
    def draw_hud_text(self, lines):
        screen_width = GetSystemMetrics(0)
        screen_height = GetSystemMetrics(1)
        text = "\n".join(lines)
        self.text_id = self.canvas.create_text(screen_width - 300, screen_height - 20, text=text, font=("sans-serif", 8, "bold"),
                                              fill="#ffff00")
    def update_crosshair(self):
        self.canvas.delete("all")  # Clear all drawings
        # Get enemy coordinates and player health
        enemy_positions = do_esp()
        # Draw crosshair, snap line, HUD text and Health for each enemy
        self.draw_crosshair(enemy_positions)
        # Draw HUD text with multiple lines
        lines = [
            "--safec0ck-- v1.3 by c1tru5x"
        ]
        self.draw_hud_text(lines)
        self.after(50, self.update_crosshair)

    def on_size(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_SIZE:
            self.update_crosshair()
        return win32gui.CallWindowProc(self.old_window_proc, hwnd, msg, wparam, lparam)
    
    def on_destroy(self, event):
        print("Application is closing. Clean up resources here.")

def do_esp():
    enemy_coordinates = []
    for i in range(playerSize): #set lower if memory problems
        entity = pm.read_ulonglong(client + dwEntityList)
        list_entity = pm.read_ulonglong(entity + ((8 * (i & 0x7FFF) >> 9) + 16))
        if list_entity == 0:
            continue
        entity_controller = pm.read_ulonglong(list_entity + (120) * (i & 0x1FF))
        if entity_controller == 0:
            continue
        entity_controller_pawn = pm.read_ulonglong(entity_controller + m_hPlayerPawn)
        if entity_controller_pawn == 0:
            continue
        list_entity = pm.read_ulonglong(entity + (0x8 * ((entity_controller_pawn & 0x7FFF) >> 9) + 16))
        if list_entity == 0:
            continue
        entity_pawn = pm.read_ulonglong(list_entity + (120) * (entity_controller_pawn & 0x1FF))
        #extra
        dormantState = pm.read_bool(entity_pawn + m_bDormant)
        player_team = pm.read_int(entity_pawn + m_iTeamNum)
        my_team = pm.read_int(player + m_iTeamNum)
        player_health = pm.read_int(entity_pawn + m_iHealth)
        if entity_pawn == 0 or entity_pawn == player or dormantState == True or player_team == my_team or player_health < 1:  # do not render self and teammates
            continue
        positions = pm.read_bytes(entity_pawn + m_vOldOrigin, 12)
        pos = struct.unpack("3f", positions)  # x, y, z
        view_matrix = pm.read_bytes(client + dwViewMatrix, 64)
        matrix = struct.unpack("16f", view_matrix)  # 4x4 ViewMatrix
        screen_cords = world_to_screen(matrix, pos)
        if screen_cords is not None:
            enemy_coordinates.append((int(screen_cords[0]), int(screen_cords[1]), int(screen_cords[2]), player_health)) #x,y,z,health
    return enemy_coordinates

def world_to_screen(matrix, pos):
    z = pos[0] * matrix[12] + pos[1] * matrix[13] + pos[2] * matrix[14] + matrix[15]
    # person behind us
    if z < 0.01:
        return None
    x = pos[0] * matrix[0] + pos[1] * matrix[1] + pos[2] * matrix[2] + matrix[3]
    y = pos[0] * matrix[4] + pos[1] * matrix[5] + pos[2] * matrix[6] + matrix[7]
    xx = x / z
    yy = y / z
    _x = (GetSystemMetrics(0) / 2 * xx) + (xx + GetSystemMetrics(0) / 2)
    _y = (GetSystemMetrics(1) / 2) - (GetSystemMetrics(1) / 2 * yy)
    return _x, _y, z  # screen coordinates and distance

def beep(frequency, duration):
    win32api.Beep(frequency, duration)

def checkDefuse():# check if bomb is planted
            planted = pm.read_bool(client + dwPlantedC4 - 0x8)
            for i in range(playerSize):
                entity = pm.read_ulonglong(client + dwEntityList)
                list_entity = pm.read_ulonglong(entity + ((8 * (i & 0x7FFF) >> 9) + 16))
                if list_entity == 0:
                    continue
                entity_controller = pm.read_ulonglong(list_entity + (120) * (i & 0x1FF))
                if entity_controller == 0:
                    continue
                entity_controller_pawn = pm.read_ulonglong(entity_controller + m_hPlayerPawn)
                if entity_controller_pawn == 0:
                    continue
                list_entity = pm.read_ulonglong(entity + (0x8 * ((entity_controller_pawn & 0x7FFF) >> 9) + 16))
                if list_entity == 0:
                    continue
                entity_pawn = pm.read_ulonglong(list_entity + (120) * (entity_controller_pawn & 0x1FF))
                if entity_pawn == 0:
                    continue
                isDefusing = pm.read_bool(entity_pawn + m_bIsDefusing)
                hasKit = pm.read_bool(entity_pawn + m_bHasDefuser)
                player_team = pm.read_int(entity_pawn + m_iTeamNum)
                my_team = pm.read_int(player + m_iTeamNum)
                if planted:
                    #check only for enemy and only if planted
                    if(player_team != my_team):
                        if(isDefusing and hasKit):
                            beep(350, 70)
                        if(isDefusing and hasKit == False):
                            beep(250, 150)
                time.sleep(0.01)
def trigger():
            entityID = pm.read_int(player + m_iIDEntIndex)
            my_team = pm.read_int(player + m_iTeamNum)
            if entityID > 0:
                time.sleep(random.uniform(0.01,0.03))
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(random.uniform(0.01,0.03))
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            time.sleep(0.1)

def run_check_defuse():
    while True:
        checkDefuse()
        time.sleep(0.1)

def run_trigger():
    while True:
        if keyboard.is_pressed("ALT"):
            trigger()
        time.sleep(0.05)

# Start additional threads for continuous functions
threading.Thread(target=run_check_defuse, daemon=True).start()
threading.Thread(target=run_trigger, daemon=True).start()
if __name__ == "__main__":
    moveable_overlay = MoveableOverlay()
    moveable_overlay.mainloop()
    run_trigger()
    run_check_defuse()
