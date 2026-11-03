import pymem
import re

offsets = {}

def load_offsets():
    with open("src/offsets.hpp", "r") as f:
        content = f.read()
        pattern = r"namespace (\w+) \{([^}]+)\}"
        for match in re.finditer(pattern, content):
            ns = match.group(1)
            block = match.group(2)
            offset_pattern = r"inline constexpr uintptr_t (\w+) = (0x[0-9a-fA-F]+);"
            for off_match in re.finditer(offset_pattern, block):
                name = off_match.group(1)
                value = int(off_match.group(2), 16)
                offsets[f"{ns}.{name}"] = value

def attach_to_roblox():
    load_offsets()
    return pymem.Pymem("RobloxPlayerBeta.exe")

class MemFunctions:
    def __init__(self, pm):
        self.pm = pm
        self.dm = None
        self.players = None
        self.workspace = None
    
    def get_datamodel(self):
        if self.dm:
            return self.dm
        base = self.pm.base_address
        fake_ptr = base + offsets["FakeDataModel.Pointer"]
        fake_dm = self.pm.read_longlong(fake_ptr)
        self.dm = self.pm.read_longlong(fake_dm + offsets["FakeDataModel.RealDataModel"])
        return self.dm
    
    def get_children(self, parent):
        try:
            start_ptr = self.pm.read_longlong(parent + offsets["Instance.ChildrenStart"])
            end_ptr = self.pm.read_longlong(start_ptr + offsets["Instance.ChildrenEnd"])
            current = self.pm.read_longlong(start_ptr)
            children = []
            for addr in range(current, min(end_ptr, current + 0x4000000), 0x10):
                try:
                    child = self.pm.read_longlong(addr)
                    if child:
                        children.append(child)
                except:
                    continue
            return children
        except:
            return []
    
    def get_classname(self, inst):
        try:
            cd = self.pm.read_longlong(inst + offsets["Instance.ClassDescriptor"])
            name_ptr = self.pm.read_longlong(cd + offsets["Instance.ClassName"])
            return self.pm.read_string(name_ptr, 64)
        except:
            return ""
    
    def find_service(self, name):
        dm = self.get_datamodel()
        for child in self.get_children(dm):
            if self.get_classname(child) == name:
                return child
        return None
    
    def get_local_player(self):
        if not self.players:
            self.players = self.find_service("Players")
        return self.pm.read_longlong(self.players + offsets["Player.LocalPlayer"])
    
    def get_character(self):
        lp = self.get_local_player()
        return self.pm.read_longlong(lp + offsets["Player.ModelInstance"])
    
    def get_humanoid(self):
        char = self.get_character()
        for child in self.get_children(char):
            if self.get_classname(child) == "Humanoid":
                return child
        return None
    
    def speed(self, value):
        hum = self.get_humanoid()
        self.pm.write_float(hum + offsets["Humanoid.Walkspeed"], float(value))
        self.pm.write_float(hum + offsets["Humanoid.WalkspeedCheck"], float(value))
        print(f"Speed set to {value}")
    
    def noclip(self, enabled):
        char = self.get_character()
        count = 0
        for child in self.get_children(char):
            classname = self.get_classname(child)
            if classname in ["Part", "MeshPart", "UnionOperation"]:
                try:
                    primitive = self.pm.read_longlong(child + offsets["BasePart.Primitive"])
                    flags = self.pm.read_ushort(primitive + offsets["Primitive.Flags"])
                    if enabled:
                        flags &= ~0x8
                    else:
                        flags |= 0x8
                    self.pm.write_ushort(primitive + offsets["Primitive.Flags"], flags)
                    count += 1
                except:
                    pass
        print(f"Noclip {'enabled' if enabled else 'disabled'} on {count} parts")
    
    def fov(self, value):
        if not self.workspace:
            self.workspace = self.find_service("Workspace")
        camera = self.pm.read_longlong(self.workspace + offsets["Workspace.CurrentCamera"])
        self.pm.write_float(camera + offsets["Camera.FieldOfView"], float(value))
        print(f"FOV set to {value}")
    
    def gravity(self, value):
        if not self.workspace:
            self.workspace = self.find_service("Workspace")
        world_ptr = self.pm.read_longlong(self.workspace + offsets["Workspace.World"])
        self.pm.write_float(world_ptr + offsets["World.Gravity"], float(value))
        print(f"Gravity set to {value}")
    
    def fullbright(self):
        lighting = self.find_service("Lighting")
        self.pm.write_float(lighting + offsets["Lighting.Brightness"], 2.0)
        self.pm.write_float(lighting + offsets["Lighting.Ambient"], 1.0)
        self.pm.write_float(lighting + offsets["Lighting.Ambient"] + 4, 1.0)
        self.pm.write_float(lighting + offsets["Lighting.Ambient"] + 8, 1.0)
        self.pm.write_float(lighting + offsets["Lighting.OutdoorAmbient"], 1.0)
        self.pm.write_float(lighting + offsets["Lighting.OutdoorAmbient"] + 4, 1.0)
        self.pm.write_float(lighting + offsets["Lighting.OutdoorAmbient"] + 8, 1.0)
        self.pm.write_float(lighting + offsets["Lighting.FogEnd"], 100000.0)
        self.pm.write_float(lighting + offsets["Lighting.FogStart"], 100000.0)
        print("Fullbright enabled")
    
    def gethealth(self):
        hum = self.get_humanoid()
        health = self.pm.read_float(hum + offsets["Humanoid.Health"])
        max_health = self.pm.read_float(hum + offsets["Humanoid.MaxHealth"])
        print(f"Health: {health:.1f} / {max_health:.1f}")
    
    def getpos(self):
        char = self.get_character()
        hrp = None
        for child in self.get_children(char):
            if self.get_classname(child) == "Part":
                try:
                    name_container = self.pm.read_longlong(child + offsets["Instance.NameContainer"])
                    name_ptr = self.pm.read_longlong(name_container + offsets["Instance.Name"])
                    name = self.pm.read_string(name_ptr, 64)
                    if name == "HumanoidRootPart":
                        hrp = child
                        break
                except:
                    pass
        
        primitive = self.pm.read_longlong(hrp + offsets["BasePart.Primitive"])
        x = self.pm.read_float(primitive + offsets["Primitive.Position"])
        y = self.pm.read_float(primitive + offsets["Primitive.Position"] + 4)
        z = self.pm.read_float(primitive + offsets["Primitive.Position"] + 8)
        print(f"Position: ({x:.2f}, {y:.2f}, {z:.2f})")
    
    def userid(self):
        lp = self.get_local_player()
        user_id = self.pm.read_longlong(lp + offsets["Player.UserId"])
        print(f"UserId: {user_id}")
    
    def accountage(self):
        lp = self.get_local_player()
        age = self.pm.read_longlong(lp + offsets["Player.AccountAge"])
        print(f"AccountAge: {age} days")
