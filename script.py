import os
from disassemblers.disassembler_x86 import disassemble

def hexview_line_gen ( f, start, limit = -1 ) :
    f.seek(start)
    i = 0
    while 1:
        _hex = ""
        _asc = ""

        for _ in range(16):
            byte = f.read(1)
            if not byte:
                break
            _hex += byte.hex()+" "
            if byte.isalpha() :
                _asc += byte.decode('utf-8', 'replace')
            elif byte == b'\x00':
                _asc += ' '
            else :
                _asc += '.'

        print(f"{start+i:08X}: {_hex:48} {_asc:16}")

        if not byte or (limit != -1 and i > limit):
            break

        i += 16

class Garbage :
    def UNKNOWN_OPCODE ( self, byte ) :
        print(f"Unknown opcode: {byte:02X}")
        self.pos += 1

    def MODE_SWITCH ( self, byte ) :
        address = f"{self.pos:08X}"
        self.pos += 1

        if byte == 0x0F :
            hex = "0F"

            text = "MODE-SWITCH 0F"

            print(f"{address:8}: {hex:50} {text}")

            byte = ord(self.stream.read(1))

            self.parsetable_0F[byte](byte)
        elif byte == 0x38 :
            hex = "0F38"

            text = "MODE-SWITCH 0F38"

            print(f"{address:8}: {hex:50} {text}")

            byte = ord(self.stream.read(1))

            self.parsetable_0F38[byte](byte)
        elif byte == 0x0F3A :
            hex = "0F3A"

            text = "MODE-SWITCH 0F3A"

            print(f"{address:8}: {hex:50} {text}")

            byte = ord(self.stream.read(1))

            self.parsetable_0F3A[byte](byte)
        else :
            print("UNKNOWN MODE SWITCH")

    def PREFIX_66 ( self, byte ) :  # 66
        print("MYEH, stupid prefix")

    def CJMP8       ( self, byte ) : # 70:cjmp   rel8
        address = f"{self.pos:08X}"
        self.pos += 1

        t = byte & 0b00001111
        op = ["JO", "JNO", "JC", "JNC", "JZ", "JNZ", "JNA", "JA", "JS", "JNS", "JP", "JNP", "JL", "JNL", "JNG", "JG"][t]

        dist = int.from_bytes(self.stream.read(1), byteorder='little', signed=True)
        self.pos += 1

        hex = f"70:{t:X}    {dist &0xFFFFFFFF:08X}"
        text = f"{op} {dist} to {self.pos+dist:08X}"

        print(f"{address:8}: {hex:50} {text}")
    def MOVS        ( self, byte ) : # A4:s
        address = f"{self.pos:08X}"
        self.pos += 1

        s = byte & 0b00000001

        hex = f"A4:{s}"

        text = "MOVS"

        print(f"{address:8}: {hex:50} {text}")
    def MOV_CONST   ( self, byte ) : # Bs:reg
        address = f"{self.pos:08X}"
        self.pos += 1

        s   = (byte & 0b00001000) >> 3
        reg =  byte & 0b00000111

        hex = f"Bs:{s}/{reg}"

        regfield = ""
        constant = 0
        if s == 0 :
            const8 = int.from_bytes(self.stream.read(1), byteorder='little', signed=True)
            self.pos += 1
            hex += f" {const8 &0xFF:02X}"
            regfield = self.REGISTER8BIT[reg]
            constant = const8
        else :
            const32 = int.from_bytes(self.stream.read(4), byteorder='little', signed=True)
            self.pos += 4
            hex += f" {const32 &0xFFFFFFFF:08X}"
            regfield = self.REGISTER32BIT[reg]
            constant = const32

        text = f"MOV {regfield}, {constant}"

        print(f"{address:8}: {hex:50} {text}")
    def BITMOVE     ( self, byte ) : # C0:s      modrm
        # C0:s/0  1100 000s r000  | ROL
        # C0:s/1  1100 000s r001  | ROR
        # C0:s/2  1100 000s r010  | RCL
        # C0:s/3  1100 000s r011  | RCR
        # C0:s/4  1100 000s r100  | SHL
        # C0:s/5  1100 000s r101  | SHR
        # C0:s/6  1100 000s r110  | SAL
        # C0:s/7  1100 000s r111  | SAR
        address = f"{self.pos:08X}"
        self.pos += 1

        s =  byte & 0b00000001

        mod, reg, rm, byte, regfield, rmfield, modrmhex = self.MODRM(s)

        hex = f"C0:{s}/{reg} {modrmhex}"

        op = ["ROL", "ROR", "RCL", "RCR", "SHL", "SHR", "SAL", "SAR"][reg]

        constant = int.from_bytes(self.stream.read(1), byteorder='little', signed=True)
        self.pos += 1
        hex += f" {constant &0xFF:02X}"

        text = f"{op} {rmfield}, {constant}"

        print(f"{address:8}: {hex:50} {text}")

    def IMMEDIATE   ( self, byte ) : # 80:xs/r   modrm
        address = f"{self.pos:08X}"
        self.pos += 1

        x = (byte & 0b00000010) >> 1
        s =  byte & 0b00000001

        mod, reg, rm, byte, regfield, rmfield, modrmhex = self.MODRM(s)

        hex =  f"80:{x}{s}/{reg}{modrmhex}"

        op = ["ADD", "OR", "ADC", "SBB", "AND", "SUB", "XOR", "CMP"][reg]

        constant = 0
        if s == 0 :
            const8 = int.from_bytes(self.stream.read(1), byteorder='little', signed=True)
            self.pos += 1
            hex += f" {const8 &0xFF:02X}"
            constant = const8
        elif x == 1 :
            const32 = int.from_bytes(self.stream.read(1), byteorder='little', signed=True) # sign-extended
            self.pos += 1
            hex += f" {const32 &0xFF:02X}"
            constant = const32
        else :
            const32 = int.from_bytes(self.stream.read(4), byteorder='little', signed=True)
            self.pos += 4
            hex += f" {const32 &0xFFFFFFFF:08X}"
            constant = const32

        text = f"{op} {rmfield}, {constant}"

        print(f"{address:8}: {hex:50} {text}")
    def REPE        ( self, byte ) : # F3
        address = f"{self.pos:08X}"
        self.pos += 1

        hex = "F3"
        text = "REPE"

        print(f"{address:8}: {hex:50} {text}")
    def OP_F6s      ( self, byte ) : # F6:s/r
        address = f"{self.pos:08X}"
        self.pos += 1

        s = byte & 0b00000001

        mod, reg, rm, byte, regfield, rmfield, modrmhex = self.MODRM(s)

        hex =  f"F6:{s}/{reg} {modrmhex}"

        if reg == 0 or reg == 1 :
            constant = 0
            if s == 0 :
                const8 = int.from_bytes(self.stream.read(1), byteorder='little', signed=True)
                self.pos += 1
                hex += f" {const8 &0xFF:02X}"
                constant = const8
            else :
                const32 = int.from_bytes(self.stream.read(4), byteorder='little', signed=True)
                self.pos += 4
                hex += f" {const32 &0xFFFFFFFF:08X}"
                constant = const32

            text = f"TEST {rmfield}, {constant}"
        else :
            op = ["-", "-", "NOT", "NEG", "MUL acc", "IMUL acc", "DIV acc", " IDIV acc"][reg]
            text = f"{op} {rmfield}"

        print(f"{address:8}: {hex:50} {text}")
    def OP_FEs      ( self, byte ) : # FE:s
        address = f"{self.pos:08X}"
        self.pos += 1

        s = byte & 0b00000001

        mod, reg, rm, byte, regfield, rmfield, modrmhex = self.MODRM(s)

        hex =  f"FE:{s}/{reg} {modrmhex}"

        if reg == 0b000 : # s/0 INC r/m
            constant = 0
            if s == 0 :
                const8 = int.from_bytes(self.stream.read(1), byteorder='little', signed=True)
                self.pos += 1
                hex += f" {const8 &0xFF:02X}"
                constant = const8
            else :
                const32 = int.from_bytes(self.stream.read(4), byteorder='little', signed=True)
                self.pos += 4
                hex += f" {const32 &0xFFFFFFFF:08X}"
                constant = const32
            text = f"INC [{constant}]"
        elif reg == 0b001 : # s/1 DEC r/m
            constant = 0
            if s == 0 :
                const8 = int.from_bytes(self.stream.read(1), byteorder='little', signed=True)
                self.pos += 1
                hex += f" {const8 &0xFF:02X}"
                constant = const8
            else :
                const32 = int.from_bytes(self.stream.read(4), byteorder='little', signed=True)
                self.pos += 4
                hex += f" {const32 &0xFFFFFFFF:08X}"
                constant = const32
            text = f"DEC [{constant}]"
        elif s == 0 :
            print("Invalid FE:s subselection")
        elif reg == 0b010 : # 1/2 CALL r/m
            text = f"CALL {rmfield}"
        elif reg == 0b011 : # 1/3 CALLF m16:16/32/64
            text = "FE:1/3 CALLF not implemented yet"
        elif reg == 0b100 : # 1/4 JMP r/m
            text = f"JMP {rmfield}"
        elif reg == 0b101 : # 1/5 JMPF m16:16/32/64
            text = "FE:1/5 JMPF not implemented yet"
        elif reg == 0b110 : # 1/6 PUSH r/m
            text = f"PUSH {rmfield}"
        else :
            print("Invalid FE:s subselection")

        print(f"{address:8}: {hex:50} {text}")

    def PUSH_CONST ( self, byte ) : # 68:~s-
        address = f"{self.pos:08X}"
        self.pos += 1

        s = byte & 0b00000010

        hex = f"68:~{s}-"

        constant = 0
        if s == 1 : # YES, THIS IS CORRECT, DONT TOUCH
            const8 = int.from_bytes(self.stream.read(1), byteorder='little', signed=True)
            self.pos += 1
            hex += f" {const8 &0xFF:02X}"
            constant = const8
        else :
            const32 = int.from_bytes(self.stream.read(4), byteorder='little', signed=True)
            self.pos += 4
            hex += f" {const32 &0xFFFFFFFF:08X}"
            constant = const32

        print(f"{address:8}: {hex:50} PUSH {constant}")

    def PG_AO ( self, uid, op, start ) :     # ParseGen acc operation
        def f ( self, byte ) :
            address = f"{self.pos:08X}"
            self.pos += 1

            s = byte & 0b00000001

            hex = f"{start:02X}:{s}"

            regfield = ""
            constant = 0
            if s == 0 :
                const8 = int.from_bytes(self.stream.read(1), byteorder='little', signed=True)
                self.pos += 1
                hex += f" {const8 &0xFF:02X}"
                regfield = "al"
                constant = const8
            else :
                const32 = int.from_bytes(self.stream.read(4), byteorder='little', signed=True)
                self.pos += 4
                hex += f" {const32 &0xFFFFFFFF:08X}"
                regfield = "eax"
                constant = const32

            print(f"{address:8}: {hex:50} {op} {regfield}, {constant}")
        return f
    def PG_DS ( self, uid, op, start ) :     # ParseGen ds operation
        def f ( self, byte ) :
            address = f"{self.pos:08X}"
            self.pos += 1

            d = (byte & 0b00000010) >> 1
            s =  byte & 0b00000001

            mod, reg, rm, byte, regfield, rmfield, modrmhex = self.MODRM(s)

            hex = f"{start:02X}:{d}{s}  {modrmhex}"

            if d == 0 :
                src = regfield
                dest = rmfield
            else :
                src = rmfield
                dest = regfield

            print(f"{address:8}: {hex:50} {op} {dest}, {src}")
        return f
    def PG_RO ( self, uid, op, start ) :     # ParseGen register operation
        def f ( self, byte ) :
            address = f"{self.pos:08X}"
            self.pos += 1

            reg = byte & 0b00000111

            hex = f"{start:02X}:{reg:b}"

            print(f"{address:8}: {hex:50} {op} {self.REGISTER32BIT[reg]}")
        return f
    def PG_S ( self, uid, op, start ) :     # ParseGen s operation
        def f ( self, byte ) :
            address = f"{self.pos:08X}"
            self.pos += 1

            d = (byte & 0b00000010) >> 1
            s =  byte & 0b00000001

            mod, reg, rm, byte, regfield, rmfield, modrmhex = self.MODRM(s)

            hex = f"{start:02X}:{d}{s}  {modrmhex}"

            print(f"{address:8}: {hex:50} {op} {rmfield}, {regfield}")
        return f
    def PG_SO ( self, uid, segment ) :       # ParseGen segment override
        def f ( self, byte ) :
            address = f"{self.pos:08X}"
            self.pos += 1

            print(f"{address:8}: {byte:02X50} {segment} override")
        return f
    def PG_U ( self, op ) :             # ParseGen unibyte operation
        def f ( self, byte ) :
            address = f"{self.pos:08X}"
            self.pos += 1

            print(f"{address:8}: {byte:02X50} {op}")
        return f

def functatasdt () :
    if True :
        if byte == b'\x0F' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x49' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"CMOVNS eax, [eax]")
                _hex = bytearray()
                i += 1
            elif byte == b'\x82' :
                read = f.read(4)
                _hex += read
                dist = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"JB [far] {dist} to {start+i+6+dist:08X}")
                _hex = bytearray()
                i += 4
            elif byte == b'\x87' :
                read = f.read(4)
                _hex += read
                dist = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"JA [far] {dist} to {start+i+6+dist:08X}")
                _hex = bytearray()
                i += 4
            elif byte == b'\xAF' :
                byte = f.read(1)
                _hex += byte
                if byte == b'\xF7' :
                    callback(start+i, _hex, f"IMUL esi, edi")
                    _hex = bytearray()
                i += 1
            i += 1
        if byte == b'\x8D' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x04' :
                byte = f.read(1)
                _hex += byte
                if byte == b'\x0A' :
                    callback(start+i, _hex, f"LEA eax, [edx+ecx]")
                    _hex = bytearray()
                elif byte == b'\x8D' :
                    read = f.read(4)
                    _hex += read
                    number = int.from_bytes(read, byteorder='little', signed=True)
                    callback(start+i, _hex, f"LEA eax, [ecx*4+{number}]")
                    _hex = bytearray()
                    i += 4
                i += 1
            elif byte == b'\x45' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"LEA eax, [ebp+{number}]")
                _hex = bytearray()
                i += 1
            elif byte == b'\x49' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"LEA ecx, [ecx+{number}]")
                _hex = bytearray()
                i += 1
            elif byte == b'\x74' :
                byte = f.read(1)
                _hex += byte
                if byte == b'\x31' :
                    read = f.read(1)
                    _hex += read
                    number = int.from_bytes(read, byteorder='little', signed=True)
                    callback(start+i, _hex, f"LEA esi, [ecx+esi+{number}]")
                    _hex = bytearray()
                    i += 1
                i += 1
            elif byte == b'\x7C' :
                byte = f.read(1)
                _hex += byte
                if byte == b'\x39' :
                    read = f.read(1)
                    _hex += read
                    number = int.from_bytes(read, byteorder='little', signed=True)
                    callback(start+i, _hex, f"LEA edi, [ecx+edi+{number}]")
                    _hex = bytearray()
                    i += 1
                i += 1
            elif byte == b'\xA4' :
                byte = f.read(1)
                _hex += byte
                if byte == b'\x24' :
                    read = f.read(4)
                    _hex += read
                    number = int.from_bytes(read, byteorder='little', signed=True)
                    callback(start+i, _hex, f"LEA esp, [esp+{number}]")
                    _hex = bytearray()
                    i += 4
                i += 1
            i += 1
        if byte == b'\xA1' :
            read = f.read(4)
            _hex += read
            number = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"MOV eax, [{number}]")
            _hex = bytearray()
            i += 4
        elif byte == b'\xA5' :
            callback(start+i, _hex, f"MOVSD")
            _hex = bytearray()
        if byte == b'\xAB' :
            callback(start+i, _hex, f"STOSD")
            _hex = bytearray()
        elif byte == b'\xB8' :
            read = f.read(4)
            _hex += read
            number = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"MOV eax, {number}")
            _hex = bytearray()
            i += 4
        elif byte == b'\xBA' :
            read = f.read(4)
            _hex += read
            number = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"MOV edx, {number}")
            _hex = bytearray()
            i += 4
        elif byte == b'\xBE' :
            read = f.read(4)
            _hex += read
            number = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"MOV esi, {number}")
            _hex = bytearray()
            i += 4
        elif byte == b'\xC1' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\xE0' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"SHL eax, {number}")
                _hex = bytearray()
                i += 1
            elif byte == b'\xE9' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"SHR ecx, {number}")
                _hex = bytearray()
                i += 1
            i += 1
        elif byte == b'\xC3' :
            callback(start+i, _hex, f"RET")
            _hex = bytearray()
        elif byte == b'\xC7' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x00' :
                read = f.read(4)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"MOV [eax], {number}")
                _hex = bytearray()
                i += 5
            elif byte == b'\x45' :
                read = f.read(1)
                _hex += read
                number1 = int.from_bytes(read, byteorder='little', signed=True)
                read = f.read(4)
                _hex += read
                number2 = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"MOV [ebp+{number1}], {number2}")
                _hex = bytearray()
                i += 5
            i += 1
        elif byte == b'\xC9' :
            callback(start+i, _hex, f"LEAVE")
            _hex = bytearray()

        elif byte == b'\xD1' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x88' :
                read = f.read(4)
                _hex += read
                offset = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"ROR [eax+{offset:08X}], 1")
                _hex = bytearray()
                i += 4
            elif byte == b'\x8A' :
                read = f.read(4)
                _hex += read
                offset = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"ROR [edx+{offset:08X}], 1")
                _hex = bytearray()
                i += 4
            i += 1
        elif byte == b'\xD4' :
            read = f.read(1)
            _hex += read
            number = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"AAM {number}") # ascii adjust ax after multiply
            _hex = bytearray()
            i += 1
        elif byte == b'\xD9' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\xEE' :
                callback(start+i, _hex, f"FLDZ")
                _hex = bytearray()
            i += 1
        elif byte == b'\xDB' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x45' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"FILD qword ptr [ebp+{number}]")
                _hex = bytearray()
                i += 1
            i += 1
        elif byte == b'\xDC' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x05' :
                read = f.read(4)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"FADD qword ptr [{number:08X}]")
                _hex = bytearray()
                i += 4
            elif byte == b'\x0D' :
                read = f.read(4)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"FMUL qword ptr [{number:08X}]")
                _hex = bytearray()
                i += 4
            elif byte == b'\x5D' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"FCOMP qword ptr [ebp+{number}]")
                _hex = bytearray()
                i += 1
            i += 1
        elif byte == b'\xDD' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x05' :
                read = f.read(4)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"FLD qword ptr [{number}]")
                _hex = bytearray()
                i += 4
            elif byte == b'\x1C' :
                byte = f.read(1)
                _hex += byte
                if byte == b'\x24' :
                    callback(start+i, _hex, f"FSTP qword ptr [esp]")
                    _hex = bytearray()
                i += 1
            elif byte == b'\x45' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"FLD qword ptr [ebp+{number}]")
                _hex = bytearray()
                i += 1
            elif byte == b'\x5C' :
                byte = f.read(1)
                _hex += byte
                if byte == b'\x24' :
                    read = f.read(1)
                    _hex += read
                    number = int.from_bytes(read, byteorder='little', signed=True)
                    callback(start+i, _hex, f"FSTP qword ptr [esp+{number}]")
                    _hex = bytearray()
                    i += 1
                i += 1
            elif byte == b'\x5D' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"FSTP qword ptr [ebp+{number}]")
                _hex = bytearray()
                i += 1
            i += 1
        elif byte == b'\xDF' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\xE0' :
                callback(start+i, _hex, f"FNSTSW ax")
                _hex = bytearray()
            i += 1
        elif byte == b'\xE4' :
            read = f.read(1)
            _hex += read
            number = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"IN al, {number}")
            _hex = bytearray()
            i += 1


        elif byte == b'\xEB' :
            read = f.read(1)
            _hex += read
            dist = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"JMP [near] {dist} to {start+i+5+dist:08X}")
            _hex = bytearray()
            i += 1

        elif byte == b'\xF4' :
            callback(start+i, _hex, f"HLT")
            _hex = bytearray()

        elif byte == b'\xFC' :
            callback(start+i, _hex, f"CLD")
            _hex = bytearray()
        elif byte == b'\xFD' :
            callback(start+i, _hex, f"STD")
            _hex = bytearray()

        i += 1

        if len(_hex) != 0 :
            callback(start+i, _hex, f"UNKNOWN")



LAYOUT_DOS_HEADER = [
    {"name": "e_magic",    "start":  0, "size":  2},
    {"name": "e_cblp",     "start":  2, "size":  2},
    {"name": "e_cp",       "start":  4, "size":  2},
    {"name": "e_crlc",     "start":  6, "size":  2},
    {"name": "e_cparhdr",  "start":  8, "size":  2},
    {"name": "e_minalloc", "start": 10, "size":  2},
    {"name": "e_maxalloc", "start": 12, "size":  2},
    {"name": "e_ss",       "start": 14, "size":  2},
    {"name": "e_sp",       "start": 16, "size":  2},
    {"name": "e_csum",     "start": 18, "size":  2},
    {"name": "e_ip",       "start": 20, "size":  2},
    {"name": "e_cs",       "start": 22, "size":  2},
    {"name": "e_lfarlc",   "start": 24, "size":  2},
    {"name": "e_ovno",     "start": 26, "size":  2},
    {"name": "e_res",      "start": 28, "size":  8},
    {"name": "e_oemid",    "start": 36, "size":  2},
    {"name": "e_oeminfo",  "start": 38, "size":  2},
    {"name": "e_res2",     "start": 40, "size": 20},
    {"name": "e_lfanew",   "start": 60, "size":  4}
]

LAYOUT_COFF_HEADER = [
    {"name": "Machine",              "start":  0, "size": 2},
    {"name": "NumberOfSections",     "start":  2, "size": 2},
    {"name": "TimeDateStamp",        "start":  4, "size": 4},
    {"name": "PointerToSymbolTable", "start":  8, "size": 4},
    {"name": "NumberOfSymbols",      "start": 12, "size": 4},
    {"name": "SizeOfOptionalHeader", "start": 16, "size": 2},
    {"name": "Characteristics",      "start": 18, "size": 2}
]

LAYOUT_OPTIONAL_HEADER32 = [
    {"name": "Signature",                   "start":  0, "size":   2},
    {"name": "MajorLinkerVersion",          "start":  2, "size":   1},
    {"name": "MinorLinkerVersion",          "start":  3, "size":   1},
    {"name": "SizeOfCode",                  "start":  4, "size":   4},
    {"name": "SizeOfInitializedData",       "start":  8, "size":   4},
    {"name": "SizeOfUninitializedData",     "start": 12, "size":   4},
    {"name": "AddressOfEntryPoint",         "start": 16, "size":   4},
    {"name": "BaseOfCode",                  "start": 20, "size":   4},
    {"name": "BaseOfData",                  "start": 24, "size":   4},
    {"name": "ImageBase",                   "start": 28, "size":   4},
    {"name": "SectionAlignment",            "start": 32, "size":   4},
    {"name": "FileAlignment",               "start": 36, "size":   4},
    {"name": "MajorOperatingSystemVersion", "start": 40, "size":   2},
    {"name": "MinorOperatingSystemVersion", "start": 42, "size":   2},
    {"name": "MajorImageVersion",           "start": 44, "size":   2},
    {"name": "MinorImageVersion",           "start": 46, "size":   2},
    {"name": "MajorSubsystemVersion",       "start": 48, "size":   2},
    {"name": "MinorSubsystemVersion",       "start": 50, "size":   2},
    {"name": "Win32VersionValue",           "start": 52, "size":   4},
    {"name": "SizeOfImage",                 "start": 56, "size":   4},
    {"name": "SizeOfHeaders",               "start": 60, "size":   4},
    {"name": "CheckSum",                    "start": 64, "size":   4},
    {"name": "Subsystem",                   "start": 68, "size":   2},
    {"name": "DllCharacteristics",          "start": 70, "size":   2},
    {"name": "SizeOfStackReserve",          "start": 72, "size":   4},
    {"name": "SizeOfStackCommit",           "start": 76, "size":   4},
    {"name": "SizeOfHeapReserve",           "start": 80, "size":   4},
    {"name": "SizeOfHeapCommit",            "start": 84, "size":   4},
    {"name": "LoaderFlags",                 "start": 88, "size":   4},
    {"name": "NumberOfRvaAndSizes",         "start": 92, "size":   4}
]

LAYOUT_OPTIONAL_HEADER64 = [
    {"name": "Signature",                   "start":   0, "size":   2},
    {"name": "MajorLinkerVersion",          "start":   2, "size":   1},
    {"name": "MinorLinkerVersion",          "start":   3, "size":   1},
    {"name": "SizeOfCode",                  "start":   4, "size":   4},
    {"name": "SizeOfInitializedData",       "start":   8, "size":   4},
    {"name": "SizeOfUninitializedData",     "start":  12, "size":   4},
    {"name": "AddressOfEntryPoint",         "start":  16, "size":   4},
    {"name": "BaseOfCode",                  "start":  20, "size":   4},
    {"name": "ImageBase",                   "start":  24, "size":   8},
    {"name": "SectionAlignment",            "start":  32, "size":   4},
    {"name": "FileAlignment",               "start":  36, "size":   4},
    {"name": "MajorOperatingSystemVersion", "start":  40, "size":   2},
    {"name": "MinorOperatingSystemVersion", "start":  42, "size":   2},
    {"name": "MajorImageVersion",           "start":  44, "size":   2},
    {"name": "MinorImageVersion",           "start":  46, "size":   2},
    {"name": "MajorSubsystemVersion",       "start":  48, "size":   2},
    {"name": "MinorSubsystemVersion",       "start":  50, "size":   2},
    {"name": "Win32VersionValue",           "start":  52, "size":   4},
    {"name": "SizeOfImage",                 "start":  56, "size":   4},
    {"name": "SizeOfHeaders",               "start":  60, "size":   4},
    {"name": "CheckSum",                    "start":  64, "size":   4},
    {"name": "Subsystem",                   "start":  68, "size":   2},
    {"name": "DllCharacteristics",          "start":  70, "size":   2},
    {"name": "SizeOfStackReserve",          "start":  72, "size":   8},
    {"name": "SizeOfStackCommit",           "start":  80, "size":   8},
    {"name": "SizeOfHeapReserve",           "start":  88, "size":   8},
    {"name": "SizeOfHeapCommit",            "start":  96, "size":   8},
    {"name": "LoaderFlags",                 "start": 104, "size":   4},
    {"name": "NumberOfRvaAndSizes",         "start": 108, "size":   4},
]

LAYOUT_DATA_DIRECTORY = [
    {"name": "ExportDirectoryVirtualAddress",               "start":   0, "size": 4},
    {"name": "ExportDirectorySize",                         "start":   4, "size": 4},
    {"name": "ImportDirectoryVirtualAddress",               "start":   8, "size": 4},
    {"name": "ImportDirectorySize",                         "start":  12, "size": 4},
    {"name": "ResourceDirectoryVirtualAddress",             "start":  16, "size": 4},
    {"name": "ResourceDirectorySize",                       "start":  20, "size": 4},
    {"name": "ExceptionDirectoryVirtualAddress",            "start":  24, "size": 4},
    {"name": "ExceptionDirectorySize",                      "start":  28, "size": 4},
    {"name": "SecurityDirectoryVirtualAddress",             "start":  32, "size": 4},
    {"name": "SecurityDirectorySize",                       "start":  36, "size": 4},
    {"name": "BaseRelocationTableVirtualAddress",           "start":  40, "size": 4},
    {"name": "BaseRelocationTableSize",                     "start":  44, "size": 4},
    {"name": "DebugDirectoryVirtualAddress",                "start":  48, "size": 4},
    {"name": "DebugDirectorySize",                          "start":  52, "size": 4},
    {"name": "ArchitectureSpecificDataVirtualAddress",      "start":  56, "size": 4},
    {"name": "ArchitectureSpecificDataSize",                "start":  60, "size": 4},
    {"name": "RVAofGPVirtualAddress",                       "start":  64, "size": 4},
    {"name": "RVAofGPSize",                                 "start":  68, "size": 4},
    {"name": "TLSDirectoryVirtualAddress",                  "start":  72, "size": 4},
    {"name": "TLSDirectorySize",                            "start":  76, "size": 4},
    {"name": "LoadConfigurationDirectoryVirtualAddress",    "start":  80, "size": 4},
    {"name": "LoadConfigurationDirectorySize",              "start":  84, "size": 4},
    {"name": "BoundImportDirectoryinheadersVirtualAddress", "start":  88, "size": 4},
    {"name": "BoundImportDirectoryinheadersSize",           "start":  92, "size": 4},
    {"name": "ImportAddressTableVirtualAddress",            "start":  96, "size": 4},
    {"name": "ImportAddressTableSize",                      "start": 100, "size": 4},
    {"name": "DelayLoadImportDescriptorsVirtualAddress",    "start": 104, "size": 4},
    {"name": "DelayLoadImportDescriptorsSize",              "start": 108, "size": 4},
    {"name": "COMRuntimedescriptorVirtualAddress",          "start": 112, "size": 4},
    {"name": "COMRuntimedescriptorSize",                    "start": 116, "size": 4},
    {"name": "Padding",                                     "start": 120, "size": 8}
]

LAYOUT_SECTION_HEADER = [
    {"name": "Name",                 "start":  0, "size": 8},
    {"name": "VirtualSize",          "start":  8, "size": 4},
    {"name": "VirtualAddress",       "start": 12, "size": 4},
    {"name": "SizeOfRawData",        "start": 16, "size": 4},
    {"name": "PointerToRawData",     "start": 20, "size": 4},
    {"name": "PointerToRelocations", "start": 24, "size": 4},
    {"name": "PointerToLinenumbers", "start": 28, "size": 4},
    {"name": "NumberOfRelocations",  "start": 32, "size": 2},
    {"name": "NumberOfLinenumbers",  "start": 34, "size": 2},
    {"name": "Characteristics",      "start": 36, "size": 4}
]

LAYOUT_PE32_PLUS = [
    {"name": "MS-DOS Header",   "start":   0, "size":  64, "layout": LAYOUT_DOS_HEADER},
    {"name": "Signature",       "start": 200, "size":   4},
    {"name": "COFF Header",     "start": 204, "size":  20, "layout": LAYOUT_COFF_HEADER},
    {"name": "Optional Header", "start": 224, "size": 112, "layout": LAYOUT_OPTIONAL_HEADER64},
    {"name": "Data Directory",  "start": 336, "size": 128, "layout": LAYOUT_DATA_DIRECTORY},
    {"name": "Section Table",   "start": 464, "size":  40, "layout": LAYOUT_SECTION_HEADER}
]

def read_int ( f, start, size, printtext = "" ) :
    f.seek(start)
    read = int.from_bytes(f.read(size), byteorder='little', signed=True)
    if printtext != "" :
        print(f"Reading '{printtext}' at [{start}, {size}]: {read}")
    return read

def read_bytes ( f, start, size, printtext = "" ) :
    f.seek(start)
    read = f.read(size)
    if printtext != "" :
        print(f"Reading '{printtext}' at [{start}, {size}]: {read}")
    return read

def stream_dir_exe_gen () :
    for dir in [
        "C:/Program Files (x86)/Steam/steamapps/common/",
        "E:/SteamLibrary/steamapps/common/",
        "F:/SteamLibrary/steamapps/common/",
    ] :
        for subdir in os.scandir(dir) :
            if not subdir.is_dir() :
                continue
            for file in os.scandir(subdir) :
                if not file.name.endswith(".exe") :
                    continue
                yield file

for file in stream_dir_exe_gen() :
    print(f"{file.path}")
    with open(file, "rb") as f:
        # DOS Header
        e_magic = read_bytes(f, 0, 2)
        if e_magic != b'MZ' :
            print(f"(!) File {file.path} does not have a valid MS-DOS Header Magic Number")
            continue

        # PE Signature
        PTR_pe_signature = read_int(f, 60, 4)
        PE_Signature = read_bytes(f, PTR_pe_signature, 4)
        if PE_Signature != b'PE\x00\x00' :
            print(f"(!) File {file.path} does not have a valid PE Header Signature")
            continue

        # COFF Header
        PTR_coff_header = PTR_pe_signature + 4
        SIZE_coff_header = 20
        Machine = read_int(f, PTR_coff_header, 2)
        NumberOfSections = read_int(f, PTR_coff_header + 2, 2)
        if Machine == 0x14c: # I386
            print("> I386")
        elif Machine == 0x8664: # AMD64
            print("> AMD64")
        else :
            print(f"(!) Unknown Machine {Machine}")

        # Optional Header (though usually nonoptional)
        PTR_optional_header = PTR_coff_header + SIZE_coff_header
        SIZE_optional_header = -1
        OptionalHeaderSignature = read_int(f, PTR_optional_header, 2)
        AddressOfEntryPoint = read_int(f, PTR_optional_header + 16, 4)
        if OptionalHeaderSignature == 0x010b: # PE32
            print("> PE32")
            SIZE_optional_header = 96
        elif OptionalHeaderSignature == 0x020b: # PE32+
            print("> PE32+")
            SIZE_optional_header = 112
        else :
            print(f"(!) Unknown OptionalHeaderSignature {OptionalHeaderSignature}")

        # Data Directories (though technically part of the optional header)
        PTR_data_directories = PTR_optional_header + SIZE_optional_header
        SIZE_data_directories = 128

        # Sections
        PTR_sections = PTR_data_directories + SIZE_data_directories
        SIZE_section = 40
        for i in range(NumberOfSections) :
            PTR_section = PTR_sections + SIZE_section * i
            Name = read_bytes(f, PTR_section, 8)
            VirtualSize = read_int(f, PTR_section + 8, 4)
            VirtualAddress = read_int(f, PTR_section + 12, 4)
            SizeOfRawData = read_int(f, PTR_section + 16, 4)
            PointerToRawData = read_int(f, PTR_section + 20, 4)
            if AddressOfEntryPoint >= VirtualAddress and AddressOfEntryPoint <= VirtualAddress+VirtualSize :
                EntryPoint = AddressOfEntryPoint-VirtualAddress+PointerToRawData
                print(f"> Found Entrypoint {EntryPoint:X} in section '{Name}' ({VirtualAddress}-{VirtualAddress+VirtualSize})")
                disassemble(f, EntryPoint, EntryPoint+300)
        print()
        break
