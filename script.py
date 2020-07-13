import os

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

class ParseRule :

    # byte : uint8
    # pattern : str
    # op : str
    # params : [str]

    def __init__ ( self, line ) :
        byte, pattern, op, params = line.split()
        byte = int(byte, 16)
        params = params.split('_')
        print(f"Created ParseRule({pattern}): {op} {params}")
        self.byte = byte
        self.pattern = pattern
        self.op = op
        self.params = params

    def parse ( self, disassembler ) :
        print(f"{disassembler.pos:08X}", end=' ')

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



        for param in self.params :
            if param == "AL" :
                print(param)
        print(f"{self.pattern} {self.op} {self.params}")

class Disassembler_x86:

    def __init__ ( self, stream ) :
        self.stream = stream
        self.pos = 0
        self.parsetable_gen()

        self.REGISTER8BIT  = [ "al",  "cl",  "dl",  "bl",  "ah",  "ch",  "dh",  "bh", "r8l", "r9l", "r10l", "r11l", "r12l", "r13l", "r14l", "r15l"]
        self.REGISTER16BIT = [ "ax",  "cx",  "dx",  "bx",  "sp",  "bp",  "si",  "di", "r8w", "r9w", "r10w", "r11w", "r12w", "r13w", "r14w", "r15w"]
        self.REGISTER32BIT = ["eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi", "r8d", "r9d", "r10d", "r11d", "r12d", "r13d", "r14d", "r15d"]

    def parsetable_gen ( self ) :
        UNKNOWN_OPCODE = ParseRule ( "-1 x UNKNOWN_OPCODE -" )
        self.parsetable = [ UNKNOWN_OPCODE ] * 256
        s = """
            00 00:00  ADD    RM8_R8
            01 00:01  ADD    RM32_R32
            02 00:10  ADD    RR8_M8
            03 00:11  ADD    R32_RM32
            04 04:0   ADD    AL_I8
            05 04:1   ADD    EAX_I32
            06 06     PUSH   ES
            07 07     POP    ES

            08 08:00  OR     RM8_R8
            09 08:01  OR     RM32_R32
            0A 08:10  OR     R8_RM8
            0B 08:11  OR     R32_RM32
            0C 0C:0   OR     AL_I8
            0D 0C:1   OR     EAX_I32
            0E 0E     PUSH   CS
            0F 0F     p0F    -

            10 10:00  ADC    RM8_R8
            11 10:01  ADC    RM32_R32
            12 10:10  ADC    R8_RM8
            13 10:11  ADC    R32_RM32
            14 14:0   ADC    AL_I8
            15 14:1   ADC    EAX_I32
            16 16     PUSH   SS
            17 17     POP    SS

            18 18:00  SBB    RM8_R8
            19 18:01  SBB    RM32_R32
            1A 18:10  SBB    R8_RM8
            1B 18:11  SBB    R32_RM32
            1C 1C:0   SBB    AL_I8
            1D 1C:1   SBB    EAX_I32
            1E 1E     PUSH   DS
            1F 1F     POP    DS

            20 20:00  AND    RM8_R8
            21 20:01  AND    RM32_R32
            22 20:10  AND    R8_RM8
            23 20:11  AND    R32_RM32
            24 24:0   AND    AL_I8
            25 24:1   AND    EAX_I32
            26 26     pES    ES
            27 27     DAA    -

            28 28:00  SUB    RM8_R8
            29 28:01  SUB    RM32_R32
            2A 28:10  SUB    R8_RM8
            2B 28:11  SUB    R32_RM32
            2C 2C:0   SUB    AL_I8
            2D 2C:1   SUB    EAX_I32
            2E 2E     pCS    CS
            2F 2F     DAS    -

            30 30:00  XOR    RM8_R8
            31 30:01  XOR    RM32_R32
            32 30:10  XOR    R8_RM8
            33 30:11  XOR    R32_RM32
            34 34:0   XOR    AL_I8
            35 34:1   XOR    EAX_I32
            36 36     pSS    SS
            37 37     AAA    -

            38 38:00  CMP    RM8_R8
            39 38:01  CMP    RM32_R32
            3A 38:10  CMP    R8_RM8
            3B 38:11  CMP    R32_RM32
            3C 3C:0   CMP    AL_I8
            3D 3C:1   CMP    EAX_I32
            3E 3E     pDS    DS
            3F 3F     AAS    -

            40 40+0   INC    R32
            41 40+1   INC    R32
            42 40+2   INC    R32
            43 40+3   INC    R32
            44 40+4   INC    R32
            45 40+5   INC    R32
            46 40+6   INC    R32
            47 40+7   INC    R32

            48 48+0   DEC    R32
            49 48+1   DEC    R32
            4A 48+2   DEC    R32
            4B 48+3   DEC    R32
            4C 48+4   DEC    R32
            4D 48+5   DEC    R32
            4E 48+6   DEC    R32
            4F 48+7   DEC    R32

            50 50+0   PUSH   R32
            51 50+1   PUSH   R32
            52 50+2   PUSH   R32
            53 50+3   PUSH   R32
            54 50+4   PUSH   R32
            55 50+5   PUSH   R32
            56 50+6   PUSH   R32
            57 50+7   PUSH   R32

            58 58+0   POP    R32
            59 58+1   POP    R32
            5A 58+2   POP    R32
            5B 58+3   POP    R32
            5C 58+4   POP    R32
            5D 58+5   POP    R32
            5E 58+6   POP    R32
            5F 58+7   POP    R32

            60 60     PUSHA  -
            61 61     POPA   -
            62 62     BOUND  R32_M32&32
            63 63     ARPL   RM16_R16

            64 64     pFS    -
            65 65     pGS    -
            66 66     p66    -
            67 67     p67    -

            68 68:0-  PUSH   I32
            69 69:0-  IMUL   R32_RM32_I32
            6A 68:1-  PUSH   I8
            6B 69:1-  IMUL   R8_RM8_I8

            6C 6C:0   INS    M8
            6D 6C:1   INS    M32
            6E 6E:0   OUTS   M8
            6F 6F:1   OUTS   M32

            70 7|0    JO     REL8
            71 7|1    JNO    REL8
            72 7|2    JC     REL8
            73 7|3    JNC    REL8
            74 7|4    JZ     REL8
            75 7|5    JNZ    REL8
            76 7|6    JNA    REL8
            77 7|7    JA     REL8
            78 7|8    JS     REL8
            79 7|9    JNS    REL8
            7A 7|A    JP     REL8
            7B 7|B    JNP    REL8
            7C 7|C    JL     REL8
            7D 7|D    JNL    REL8
            7E 7|E    JNG    REL8
            7F 7|F    JG     REL8

            80 80:00  IMM    RT_RM8_I8
            81 80:01  IMM    RT_RM32_I32
            82 80:10  IMM    RT_RM8_I8
            83 80:11  IMM    RT_RM32_I8

            84 84:0   TEST   RM8_R8
            85 84:1   TEST   RM32_R32
            86 86:0   XCHG   R8_RM8
            87 86:1   XCHG   R32_RM32
            88 88:00  MOV    RM8_R8
            89 88:01  MOV    RM32_R32
            8A 88:10  MOV    R8_RM8
            8B 88:11  MOV    R32_RM32

            8C 8C:0-  MOV    RM16_S
            8D 8D     LEA    R32_M
            8E 8C:1-  MOV    S_RM16
            8F 8F/0   POP    RM32

            90 90+0   XCHG   R32_EAX
            91 90+1   XCHG   R32_EAX
            92 90+2   XCHG   R32_EAX
            93 90+3   XCHG   R32_EAX
            94 90+4   XCHG   R32_EAX
            95 90+5   XCHG   R32_EAX
            96 90+6   XCHG   R32_EAX
            97 90+7   XCHG   R32_EAX

            98 98     CWDE   -
            99 99     CDQ    -
            9A 9A     CALLF  PTR16:32
            9B 9B     pWAIT  -
            9C 9C     PUSHF  -
            9D 9D     POPF   -
            9E 9E     SAHF   -
            9F 9F     LAHF   -

            A0 A0:00  MOV    AL_MO8
            A1 A0:01  MOV    EAX_MO32
            A2 A0:10  MOV    MO8_AL
            A3 A0:11  MOV    MO32_EAX
            A4 A4:0   MOVS   M8_M8
            A5 A4:1   MOVS   M32_M32
            A6 A6:0   CMPS   M8_M8
            A7 A6:1   CMPS   M32_M32
            A8 A8:0   TEST   AL_I8
            A9 A8:1   TEST   EAX_I32

            AA AA:0   STOS   M8_AL
            AB AA:1   STOS   M32_EAX
            AC AC:0   LODS   AL_M8
            AD AC:1   LODS   EAX_M32
            AE AE:0   SCAS   M8_AL
            AF AE:1   SCAS   M32_EAX

            B0 B0+0   MOV    R8_I8
            B1 B0+1   MOV    R8_I8
            B2 B0+2   MOV    R8_I8
            B3 B0+3   MOV    R8_I8
            B4 B0+4   MOV    R8_I8
            B5 B0+5   MOV    R8_I8
            B6 B0+6   MOV    R8_I8
            B7 B0+7   MOV    R8_I8
            B8 B8+0   MOV    R32_I32
            B9 B8+1   MOV    R32_I32
            BA B8+2   MOV    R32_I32
            BB B8+3   MOV    R32_I32
            BC B8+4   MOV    R32_I32
            BD B8+5   MOV    R32-I32
            BE B8+6   MOV    R32_I32
            BF B8+7   MOV    R32_I32

            C0 C0:0   BIT    RT_RM8_I8
            C1 C0:1   BIT    RT_RM32_I32

            C2 C2     RET    I16
            C3 C3     RET    -

            C4 C4     LES    R32_M16:32
            C5 C5     LDS    R32_M16:32

            C6 C6/0   MOV    RM8_I8
            C7 C7/0   MOV    RM32_I32

            C8 C8     ENTER  I16_I8
            C9 C9     LEAVE  -

            CA CA     RET    I16
            CB CB     RET    -

            CC CC     INT3   -
            CD CD     INT    I8
            CE CE     INTO   -
            CF CF     IRET   -

            D0 D0:00  BIT    RT_RM8
            D1 D0:01  BIT    RT_RM32
            D2 D0:10  BIT    RT_RM8_CL
            D3 D0:11  BIT    RT_RM32_CL

            D4 D4     AMX    I8
            D5 D5     ADX    I8
            D6 D6     SALC   -
            D7 D7     XLAT   M8

            D8 D8-DF  FFUN   ign
            D9 D8-DF  FFUN   ign
            DA D8-DF  FFUN   ign
            DB D8-DF  FFUN   ign
            DC D8-DF  FFUN   ign
            DD D8-DF  FFUN   ign
            DE D8-DF  FFUN   ign
            DF D8-DF  FFUN   ign

            E0 E0     LOOPNZ ECX_REL8
            E1 E1     LOOPZ  ECX_REL8
            E2 E2     LOOP   ECX_REL8
            E3 E3     JECXZ  REL8_ECX

            E4 E4     IN     AL_I8
            E5 E5     IN     EAX_I8
            E6 E6     OUT    I8_AL
            E7 E7     OUT    I8_EAX

            E8 E8     CALL   REL32
            E9 E9     JMP    REL32
            EA EA     JMPF   PTR16:32
            EB EB     JMP    REL8

            EC EC:00  IN     AL_DX
            ED EC:01  IN     EAX_DX
            EE EC:10  OUT    DX_AL
            EF EC:11  OUT    DX_EAX

            F0 F0     pLOCK  -
            F1 F1     INT1   -
            F2 F2     pREPNZ -
            F3 F3     pREPZ  -
            F4 F4     HLT    -
            F5 F5     CMC    -
            F6 F6     F6     ign
            F7 F7     F7     ign
            F8 F8     CLC    -
            F9 F9     STC    -
            FA FA     CLI    -
            FB FB     STI    -
            FC FC     CLD    -
            FD FD     STD    -
            FE FE     FE     ign
            FF FF     FF     ign
        """
        for line in s.splitlines() :
            if line.strip() == "" :
                continue

            parserule = ParseRule(line)

            self.parsetable[parserule.byte] = parserule

        self.parsetable_0F = [ UNKNOWN_OPCODE ] * 256
        self.parsetable_0F38 = [ UNKNOWN_OPCODE ] * 256
        self.parsetable_0F3A = [ UNKNOWN_OPCODE ] * 256

    def disassemble ( self, start, stop ) :
        self.pos = start
        self.stream.seek(start)

        while self.pos < stop :
            byte = self.stream.read(1)
            if not byte:
                return
            byte = ord(byte)

            self.parsetable[byte].parse(self)

    def MODRM ( self, s ) -> (int, int, int, int, str, str, str) :
        byte = self.stream.read(1)
        self.pos += 1

        regfield = ""
        rmfield = ""

        if not byte:
            print("SPLIT233 ran out of stream")
            return 0, 0, 0
        byte = ord(byte)

        mod = (byte & 0b11000000) >> 6
        reg = (byte & 0b00111000) >> 3
        rm  =  byte & 0b00000111

        hex = f" {byte:02X}[{mod:02b} {reg:03b} {rm:03b}]"

        if s == 0 :
            regfield = self.REGISTER8BIT[reg]
        else :
            regfield = self.REGISTER32BIT[reg]

        if mod == 0b00 and rm == 0b101 : # displacement-only mode
            disp32 = int.from_bytes(self.stream.read(4), byteorder='little', signed=True)
            self.pos += 4
            hex += f" {disp32:08X}"
            rmfield = f"[{disp32:+08X}]"
        elif mod == 0b11 : # direct mode
            rmfield = self.REGISTER32BIT[rm]
        else :
            rmloc = ""
            if rm == 0b100 : # SIB mode
                scale, index, base, sibbyte, rmloc, sibhex = self.SIB(mod)
                hex += sibhex
            else :
                rmloc = self.REGISTER32BIT[rm]

            offset = ""
            if mod == 0b01 : # one-byte displacement mode
                disp8 = int.from_bytes(self.stream.read(1), byteorder='little', signed=True)
                self.pos += 1
                hex += f" {disp8 &0xFF:02X}"
                offset = f"{disp8:+02X}"
            elif mod == 0b10 : # four-byte displacement mode
                disp32 = int.from_bytes(self.stream.read(4), byteorder='little', signed=True)
                self.pos += 4
                hex += f" {disp32 &0xFFFFFFFF:08X}"
                offset = f"{disp32:+08X}"

            rmfield = f"[{rmloc}{offset}]"

        return mod, reg, rm, byte, regfield, rmfield, hex

    def SIB ( self, mod ) -> (int, int, int, int, str, str) :
        byte = self.stream.read(1)
        self.pos += 1

        rmloc = ""

        if not byte:
            print("SPLIT233 ran out of stream")
            return 0, 0, 0
        byte = ord(byte)

        scale = (byte & 0b11000000) >> 6
        index = (byte & 0b00111000) >> 3
        base  =  byte & 0b00000111

        hex = f" {byte:02X}[{scale:02b} {index:03b} {base:03b}]"

        rmloc = f"{self.REGISTER32BIT[index]}*{1<<scale}"
        if base == 0b101 :
            if mod == 0b00 : # displacement-only mode
                disp32 = int.from_bytes(self.stream.read(4), byteorder='little', signed=True)
                self.pos += 4
                hex += f" {disp32 &0xFFFFFFFF:08X}"
                rmloc += f"{disp32:+}"
        else :
            rmloc = f"{self.REGISTER32BIT[base]}+{rmloc}"

        return scale, index, base, byte, rmloc, hex

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
    def INT3        ( self, byte ) : # CC
        address = f"{self.pos:08X}"
        self.pos += 1

        hex = "CC"
        text = "INT3"

        print(f"{address:8}: {hex:50} {text}")
    def CALL        ( self, byte ) : # E8        rel16/32
        address = f"{self.pos:08X}"
        self.pos += 1

        dist = int.from_bytes(self.stream.read(4), byteorder='little', signed=True)
        self.pos += 4

        hex = f"E8      {dist &0xFFFFFFFF:08X}"
        text = f"CALL {dist} to {self.pos+dist:08X}"

        print(f"{address:8}: {hex:50} {text}")
    def JMP         ( self, byte ) : # E9        rel16/32
        address = f"{self.pos:08X}"
        self.pos += 1

        dist = int.from_bytes(self.stream.read(4), byteorder='little', signed=True)
        self.pos += 4

        hex = f"E9      {dist &0xFFFFFFFF:08X}"
        text = f"JMP {dist} to {self.pos+dist:08X}"

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
    def CJMP32      ( self, byte ) : # 0F 70:cjmp   rel16/32
        address = f"{self.pos:08X}"
        self.pos += 1

        t = byte & 0b00001111
        op = ["JO", "JNO", "JC", "JNC", "JZ", "JNZ", "JNA", "JA", "JS", "JNS", "JP", "JNP", "JL", "JNL", "JNG", "JG"][t]

        dist = int.from_bytes(self.stream.read(4), byteorder='little', signed=True)
        self.pos += 4

        hex = f"70:{t:X}    {dist &0xFFFFFFFF:08X}"
        text = f"{op} {dist} to {self.pos+dist:08X}"

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
                file_disassembler = Disassembler_x86(f)
                file_disassembler.disassemble(EntryPoint, EntryPoint+300)
        print()
        break
