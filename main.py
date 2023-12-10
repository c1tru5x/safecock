import pymem.process
import keyboard
import time
import win32api
import win32con
from numpy import random
import json

# Specify the path to your JSON file
json_file_path_client = r"C:\Users\c1tru5x\PycharmProjects\pythonProject\venv\Include\client.dll.json"
# Open the JSON file for reading
with open(json_file_path_client, 'r') as json_file:
    # Load the JSON data
    client_data = json.load(json_file)
# Specify the path to your JSON file
json_file_path_offsets = r"C:\Users\c1tru5x\PycharmProjects\pythonProject\venv\Include\offsets.json"
# Open the JSON file for reading
with open(json_file_path_offsets, 'r') as json_file:
    # Load the JSON data
    offs_data = json.load(json_file)

#get offsets from JSON:
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

#### start code
pm = pymem.Pymem("cs2.exe")
client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
player = pm.read_longlong(client + dwLocalPlayerPawn)
def beep(frequency, duration):
    win32api.Beep(frequency, duration)
def trigger():
    for i in range(32):
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
        player_team = pm.read_int(entity_pawn + m_iTeamNum)
        my_team = pm.read_int(player + m_iTeamNum)
        # check only for enemy
        if (player_team != my_team):
            entityID = pm.read_int(player + m_iIDEntIndex)
            if entityID > 0:
                    time.sleep(random.uniform(0.01,0.03))
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    time.sleep(random.uniform(0.01,0.03))
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
def checkDefuse():
    # check if bomb is planted
    planted = pm.read_bool(client + dwPlantedC4 - 0x8)
    # entityList
    for i in range(32):
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
                    beep(350, 150)
                if(isDefusing and hasKit == False):
                    beep(250,300)
def healthCheck():
    time.sleep(0.2)
    # entityList
    for i in range(32):
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
        player_team = pm.read_int(entity_pawn + m_iTeamNum)
        player_health = pm.read_int(entity_pawn + m_iHealth)
        my_team = pm.read_int(player + m_iTeamNum)
        if(player_team == my_team):
            continue
        if(player_health > 0):
            print("------------------------")
            print("Health: ", player_health)
def menu():
    print("SAFECOCK LOADED - WELCOME")
    print("TO CLOSE PRESS F4")
def clear():
    print("\033[H\033[J", end="")
def main():
    menu()
    while(keyboard.is_pressed("F4")==False):
        checkDefuse()
        if keyboard.is_pressed("ALT"):
            trigger()
        if keyboard.is_pressed("H"):
            print("Health Check:")
            healthCheck()
        clear()
main()