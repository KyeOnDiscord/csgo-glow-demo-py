import sys
import pyMeow as pm
from requests import get

class Offsets:
    pass


try:
    # Credits to https://github.com/frk1/hazedumper
    haze = get(
        "https://raw.githubusercontent.com/frk1/hazedumper/master/csgo.json"
    ).json()

    [setattr(Offsets, k, v) for k, v in haze["signatures"].items()]
    [setattr(Offsets, k, v) for k, v in haze["netvars"].items()]
except:
    sys.exit("Unable to fetch Hazedumper's Offsets")

csgo_proc = pm.open_process(processName="csgo.exe")
clientdll = pm.get_module(csgo_proc, "client.dll")["base"]
enginedll = pm.get_module(csgo_proc, "engine.dll")["base"]

while True:
    try:
        LocalPlayer = pm.r_int(csgo_proc, clientdll + Offsets.dwLocalPlayer)
    except:
        continue
    if LocalPlayer:
        
        glowObject = pm.r_int(csgo_proc, clientdll + Offsets.dwGlowObjectManager)
        
        
        # Trying to read this address returns an invalid negative int, idk why
        #ClientState = pm.r_int(csgo_proc,  enginedll + Offsets.dwClientState)
        #Found a workaround by reading the same address as a byte array and converting it to an int
        
        ClientState = pm.r_bytes(csgo_proc, enginedll + Offsets.dwClientState,4) #Read 4 bytes (Int32 is 4 bytes)
        ClientState = int.from_bytes(ClientState, byteorder="little", signed=False) # Convert to int
        MaxPlayers = pm.r_int(csgo_proc, ClientState + Offsets.dwClientState_MaxPlayer)
        
        MyTeam = pm.r_int(csgo_proc, LocalPlayer + Offsets.m_iTeamNum)
        
        for i in range(0, MaxPlayers):
            player = pm.r_int(csgo_proc, clientdll + Offsets.dwEntityList + i * 0x10)
            if player > 0 and player != LocalPlayer:
                player_team = pm.r_int(csgo_proc, player + Offsets.m_iTeamNum)
                player_dormant = pm.r_bool(csgo_proc, player + Offsets.m_bDormant)
                player_health = pm.r_int(csgo_proc, player + Offsets.m_iHealth)
                if not player_dormant and player_health > 0:
                    try:
                        glowIndex = pm.r_int(csgo_proc, player + Offsets.m_iGlowIndex)
                        r, g, b = 0,0,0
                        if player_team == MyTeam:
                            r, g, b = 0, 255, 0
                        else:
                            r, g, b = 255.0, 0, 0
                        
                        pm.w_float(csgo_proc, glowObject + (glowIndex * 0x38) + 0x8, r) # R
                        pm.w_float(csgo_proc, glowObject + (glowIndex * 0x38) + 0xC, g) # G
                        pm.w_float(csgo_proc, glowObject + (glowIndex * 0x38) + 0x10, b) # B
                        pm.w_float(csgo_proc, glowObject + (glowIndex * 0x38) + 0x14, 255.0) # A
                            
                        pm.w_bool(csgo_proc,glowObject + ((glowIndex * 0x38) + 0x28),True) #renderOccluded
                        pm.w_bool(csgo_proc,glowObject + ((glowIndex * 0x38) + 0x28) + 0x1,False) #renderUnoccluded
                        
                        #Create byte array
                        # *255 idea from: https://stackoverflow.com/a/46575472/12897035
                        clrRender_t = bytes([int(r),int(g) ,int(b),255])
                        
                        pm.w_bytes(csgo_proc,player + Offsets.m_clrRender,clrRender_t)
                    except:
                        continue