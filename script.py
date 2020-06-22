
with open("E:\SteamLibrary\steamapps\common\Monster Hunter World\MonsterHunterWorld.exe", "rb") as f:
    i = 0
    line = ""
    while 1:
        _hex = ""
        _asc = ""

        for _ in range(16):
            byte = f.read(1)
            if not byte:
                break 
            _hex += byte.hex()+" "
            _asc += byte.decode('utf-8', 'replace').replace(u'\ufffd', '.')
        
        print(f"{i:08d}: {_hex:48} {_asc:16}")
        
        if not byte:
            break
        
        i += 1

print("Hello again~")