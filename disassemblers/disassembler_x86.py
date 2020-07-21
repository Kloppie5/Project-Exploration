parsetables = {}

registertable = {
    "sreg" : [ "es",  "cs",  "ss",  "ds"],
    "r8"   : [ "al",  "cl",  "dl",  "bl",  "ah",  "ch",  "dh",  "bh", "r8l", "r9l", "r10l", "r11l", "r12l", "r13l", "r14l", "r15l"],
    "r16"  : [ "ax",  "cx",  "dx",  "bx",  "sp",  "bp",  "si",  "di", "r8w", "r9w", "r10w", "r11w", "r12w", "r13w", "r14w", "r15w"],
    "r32"  : ["eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi", "r8d", "r9d", "r10d", "r11d", "r12d", "r13d", "r14d", "r15d"],
}

ALUOPS = ["ADD", "OR", "ADC", "SBB", "AND", "SUB", "XOR", "CMP"]
ROTOPS = ["ROL", "ROR", "RCL", "RCR", "SHL", "SHR", "SAL", "SAR"]
cctable = ["O", "NO", "C", "NC", "Z", "NZ", "NA", "A", "S", "NS", "P", "NP", "L", "NL", "NG", "G"]
def d0p0dw ( state ) :
    """
        ALU rm reg operations
        0p0+dw xrm
    """
    byte = state["byte"]
    stream = state["stream"]

    p = (byte & 0b00111000) >> 3
    d = (byte & 0b00000010) >> 1
    w =  byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    rmfield = parse_rm(state)
    regfield = parse_reg(state)

    instruction = f"{ALUOPS[p]} {rmfield}, {regfield}"
    if d == 1 :
        instruction = f"{ALUOPS[p]} {regfield}, {rmfield}"

    return instruction
def d0p4w ( state ) :
    """
        ALU acc imm operations
        0p4+w imm
    """
    byte = state["byte"]

    p = (byte & 0b00111000) >> 3
    w =  byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    return f'{ALUOPS[p]} {registertable[state["size"]][p]}, {parse_reg(state)}'
def d0l6d ( state ) :
    """
        Segment register stack operations
        0l6+d
    """
    byte = state["byte"]

    l = (byte & 0b00111000) >> 3
    d =  byte & 0b00000001

    op = ["PUSH", "POP"][d]
    sreg = registertable["sreg"][l]

    return f'{op} {sreg}'
def d0h6 ( state ) :
    """
        Segment override prefix
        0h6
    """
    return "PENDING"
def d0h7 ( state ) :
    """
        BCD conversion
        0p7
    """
    return "PENDING"
def d017 ( state ) :
    stream = state["stream"]
    state["byte"] = int.from_bytes(stream.read(1), byteorder='little', signed=True)
    state["pos"] += 1

    return parsetables["x86_017"][state["byte"]](state)
def d10r ( state ) :
    """
        REG INC
        10r
    """
    byte = state["byte"]

    r = byte & 0b00000111

    return f'INC {registertable["r32"][r]}'
def d11r ( state ) :
    """
        REG DEC
        11r
    """
    byte = state["byte"]

    r = byte & 0b00000111

    return f'DEC {registertable["r32"][r]}'
def d12r ( state ) :
    """
        REG PUSH
        12r
    """
    byte = state["byte"]

    r = byte & 0b00000111

    return f'PUSH {registertable["r32"][r]}'
def d13r ( state ) :
    """
        REG POP
        13r
    """
    byte = state["byte"]

    r = byte & 0b00000111

    return f'POP {registertable["r32"][r]}'
def d14l ( state ) :
    return "PENDING"
def d14h ( state ) :
    return "PENDING"
def d150w0 ( state ) :
    """
        PUSH imm
        150+w0 imm
    """
    byte = state["byte"]
    stream = state["stream"]

    w = (byte & 0b00000010) >> 1

    if w == 1 :
        imm8 = int.from_bytes(stream.read(1), byteorder='little', signed=True)
        state["pos"] += 1
        state["hex"].append(f'{imm8&0xFF:08X}')
        return f"PUSH {imm8}"
    else :
        imm32 = int.from_bytes(stream.read(4), byteorder='little', signed=True)
        state["pos"] += 4
        state["hex"].append(f'{imm32&0xFFFFFFFF:08X}')
        return f"PUSH {imm32}"
def d151w0 ( state ) :
    """
        IMUL reg rm imm
        151+w0 xrm imm
    """
    return "PENDING"
def d154dw ( state ) :
    """
        String IO
        154+dw m
    """
    byte = state["byte"]
    stream = state["stream"]

    d = (byte & 0b00000010) >> 1
    w =  byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    mem = 0
    if w == 0 :
        m8 = int.from_bytes(stream.read(1), byteorder='little', signed=True)
        state["pos"] += 1
        state["hex"].append(f'{m8&0xFF:08X}')
        mem = m8
    else :
        m32 = int.from_bytes(stream.read(4), byteorder='little', signed=True)
        state["pos"] += 4
        state["hex"].append(f'{m32&0xFFFFFFFF:08X}')
        mem = m32

    instruction = f"INS {mem}, DX"
    if d == 1 :
        instruction = f"OUTS DX, {mem}"
    return instruction
def d160cc ( state ) :
    """
        Conditional short jump
        160+cc disp8
    """
    byte = state["byte"]
    stream = state["stream"]

    cc = cctable[byte-0o160]

    disp8 = int.from_bytes(stream.read(1), byteorder='little', signed=True)
    state["pos"] += 1
    state["hex"].append(f'{disp8&0xFF:08X}')

    return f'J{cc} {disp8} to {state["pos"]+disp8:08X}'
def d200sw ( state ) :
    """
        ALU rm imm operations
        200+sw xpm imm
    """
    byte = state["byte"]
    stream = state["stream"]

    s = (byte & 0b00000010) >> 1
    w =  byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    rmfield = parse_rm(state)
    p = state["r"]

    if w == 0 :
        imm8 = int.from_bytes(stream.read(1), byteorder='little', signed=True)
        state["pos"] += 1
        state["hex"].append(f'{imm8&0xFF:08X}')
        return f"{ALUOPS[p]} {rmfield}, {imm8}"
    elif s == 0:
        imm32 = int.from_bytes(stream.read(4), byteorder='little', signed=True)
        state["pos"] += 4
        state["hex"].append(f'{imm32&0xFFFFFFFF:08X}')
        return f"{ALUOPS[p]} {rmfield}, {imm32}"
    else : # sign-extend
        imm8 = int.from_bytes(stream.read(1), byteorder='little', signed=True)
        state["pos"] += 1
        state["hex"].append(f'{imm8&0xFF:08X}')
        return f"{ALUOPS[p]} {rmfield}, {imm8}"
def d204w ( state ) :
    """
        TEST reg rm
        204+w xrm
    """
    byte = state["byte"]

    w = byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    rmfield = parse_rm(state)
    regfield = parse_reg(state)

    return f"TEST {rmfield}, {regfield}"
def d206w ( state ) :
    """
        XCHG reg rm
        206+w xrm
    """
    return "PENDING"
def d210dw ( state ) :
    """
        MOV rm reg
        210+dw xrm
    """
    byte = state["byte"]
    stream = state["stream"]

    p = (byte & 0b00111000) >> 3
    d = (byte & 0b00000010) >> 1
    w =  byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    rmfield = parse_rm(state)
    regfield = parse_reg(state)

    instruction = f"MOV {rmfield}, {regfield}"
    if d == 1 :
        instruction = f"MOV {regfield}, {rmfield}"

    return instruction
def d214d0 ( state ) :
    """
        MOV rm sreg
        214+d0 xsm
    """
    return "PENDING"
def d215 ( state ) :
    """
        LEA reg rm
        215 xrm
    """
    state["size"] = "r32"

    rmfield = parse_rm(state)
    regfield = parse_reg(state)

    return f"LEA {regfield}, {rmfield}"
def d217r0 ( state ) :
    read_xrm(state)
    r = state["r"]
    if r != 0 :
        return "INVALID"

    state["size"] = "r32"

    rmfield = parse_rm(state)

    return f"POP {rmfield}"
def d22r ( state ) :
    """
        XCHG EAX reg
        22r
    """
    byte = state["byte"]

    r = byte & 0b00000111

    reg = registertable["r32"][r]

    return f"XCHG EAX, {reg}"
def d230 ( state ) :
    """
        CWDE
        230
    """
    return "CWDE"
def d231 ( state ) :
    """
        CDQ
        231
    """
    return "PENDING"
def d232 ( state ) :
    return "PENDING"
def d233 ( state ) :
    return "PENDING"
def d234 ( state ) :
    """
        PUSHF
        234
    """
    return "PENDING"
def d235 ( state ) :
    """
        POPF
        235
    """
    return "PENDING"
def d236 ( state ) :
    """
        SAHF
        236
    """
    return "PENDING"
def d237 ( state ) :
    """
        LAHF
        237
    """
    return "PENDING"
def d240dw ( state ) :
    """
        MOV acc mem
        240+dw disp
    """
    byte = state["byte"]
    stream = state["stream"]

    d = (byte & 0b00000010) >> 1
    w =  byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    acc = registertable[state["size"]][0]

    mem = 0
    if w == 0 :
        moff8 = int.from_bytes(stream.read(1), byteorder='little', signed=True)
        state["pos"] += 1
        state["hex"].append(f'{moff8&0xFF:08X}')
        mem = moff8
    else :
        moff32 = int.from_bytes(stream.read(4), byteorder='little', signed=True)
        state["pos"] += 4
        state["hex"].append(f'{moff32&0xFFFFFFFF:08X}')
        mem = moff32

    instruction = f"MOV {acc}, {mem}"
    if d == 1 :
        instruction = f"MOV {mem}, {acc}"

    return instruction
def d244w ( state ) :
    """
        MOVS
        244+w
    """
    byte = state["byte"]

    w = byte & 0b00000001

    return ["MOVS", "MOVSD"][w]
def d246w ( state ) :
    """
        CMPS
        246+w
    """
    byte = state["byte"]

    w = byte & 0b00000001

    return ["CMPS", "CMPSD"][w]
def d250w ( state ) :
    """
        ALU acc imm test
        250+w imm
    """
    return "PENDING"
def d252w ( state ) :
    """
        STOS
        252+w
    """
    byte = state["byte"]

    w = byte & 0b00000001

    return ["STOS", "STOSD"][w]
def d254w ( state ) :
    """
        LODS
        254+w
    """
    return "PENDING"
def d256w ( state ) :
    """
        SCAS
        256+w
    """
    return "PENDING"
def d26wr ( state ) :
    """
        MOV reg imm
        2[6+w]r imm
    """
    byte = state["byte"]
    stream = state["stream"]

    w = (byte & 0b00001000) >> 3
    r =  byte & 0b00000111

    state["size"] = ["r8", "r32"][w]

    reg = registertable[state["size"]][r]

    if w == 0 :
        imm8 = int.from_bytes(stream.read(1), byteorder='little', signed=True)
        state["pos"] += 1
        state["hex"].append(f'{imm8&0xFF:08X}')
        return f"MOV {reg}, {imm8}"
    if w == 1 :
        imm32 = int.from_bytes(stream.read(4), byteorder='little', signed=True)
        state["pos"] += 4
        state["hex"].append(f'{imm32&0xFFFFFFFF:08X}')
        return f"MOV {reg}, {imm32}"

    return "INVALID"
def d300w ( state ) :
    """
        ROT rm imm
        300+w xpm imm8
    """
    byte = state["byte"]
    stream = state["stream"]

    read_xrm(state)

    p = state["r"]

    w = byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    rmfield = parse_rm(state)

    if w == 0 :
        imm8 = int.from_bytes(stream.read(1), byteorder='little', signed=True)
        state["pos"] += 1
        state["hex"].append(f'{imm8&0xFF:08X}')
        return f"{ROTOPS[p]} {rmfield}, {imm8}"
    if w == 1 :
        imm32 = int.from_bytes(stream.read(4), byteorder='little', signed=True)
        state["pos"] += 4
        state["hex"].append(f'{imm32&0xFFFFFFFF:08X}')
        return f"{ROTOPS[p]} {rmfield}, {imm32}"

    return "INVALID"
def d302 ( state ) :
    """
        RET imm
        302 imm16
    """
    return "PENDING"
def d303 ( state ) :
    """
        RET
        303
    """
    return "RET"
def d304 ( state ) :
    """
        LES
        304
    """
    return "PENDING"
def d305 ( state ) :
    """
        LDS
        305
    """
    return "PENDING"
def d306w ( state ) :
    """
        MOV rm imm
        306+w xrm imm
    """
    byte = state["byte"]
    stream = state["stream"]

    w = byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    rmfield = parse_rm(state)

    if w == 0 :
        imm8 = int.from_bytes(stream.read(1), byteorder='little', signed=True)
        state["pos"] += 1
        state["hex"].append(f'{imm8&0xFF:08X}')
        return f"MOV {rmfield}, {imm8}"
    else :
        imm32 = int.from_bytes(stream.read(4), byteorder='little', signed=True)
        state["pos"] += 4
        state["hex"].append(f'{imm32&0xFFFFFFFF:08X}')
        return f"MOV {rmfield}, {imm32}"
def d310 ( state ) :
    """
        ENTER locals, nesting
        310 imm32 imm8
    """
    stream = state["stream"]

    imm32 = int.from_bytes(stream.read(4), byteorder='little', signed=True)
    imm8 = int.from_bytes(stream.read(1), byteorder='little', signed=True)
    state["pos"] += 5
    state["hex"].append(f'{imm32&0xFFFFFFFF:08X}')
    state["hex"].append(f'{imm8&0xFF:08X}')

    return f"ENTER {imm32}, {imm8}"
def d311 ( state ) :
    """
        LEAVE
        311
    """
    return "LEAVE"
def d312 ( state ) :
    """
        RET FAR imm
        312 imm16
    """
    return "PENDING"
def d313 ( state ) :
    """
        RET FAR
        313
    """
    return "PENDING"
def d314 ( state ) :
    """
        INT3
        314
    """
    return "INT3"
def d315 ( state ) :
    """
        INT imm8
        315 imm8
    """
    return "PENDING"
def d316 ( state ) :
    """
        INT0
        316
    """
    return "PENDING"
def d317 ( state ) :
    """
        IRET
        317
    """
    return "PENDING"
def d320w ( state ) :
    """
        ROT rm 1
        320+w xpm
    """
    byte = state["byte"]
    stream = state["stream"]

    read_xrm(state)

    p = state["r"]

    w = byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    rmfield = parse_rm(state)

    return f"{ROTOPS[p]} {rmfield}, 1"
def d322w ( state ) :
    """
        ROT rm CL
        322+w xpm
    """
    byte = state["byte"]
    stream = state["stream"]

    read_xrm(state)

    p = state["r"]

    w = byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    rmfield = parse_rm(state)

    return f"{ROTOPS[p]} {rmfield}, CL"
def d324 ( state ) :
    """
        AMX imm8
        324 imm8
    """
    stream = state["stream"]

    imm8 = int.from_bytes(stream.read(1), byteorder='little', signed=True)
    state["pos"] += 1
    state["hex"].append(f'{imm8&0xFF:08X}')
    return f"AMX {imm8}"
def d325 ( state ) :
    """
        ADX imm8
        325 imm8
    """
    return "PENDING"
def d326 ( state ) :
    """
        SALC
        326
    """
    return "PENDING"
def d327 ( state ) :
    """
        XLAT
        327
    """
    return "PENDING"
def d33 ( state ) :
    """
        FPU instruction
        33m xrm
    """
    return "PENDING"
def d340 ( state ) :
    """
        LOOPNE
        340 disp8
    """
    return "PENDING"
def d341 ( state ) :
    """
        LOOPE
        341 disp8
    """
    return "PENDING"
def d342 ( state ) :
    """
        LOOP
        342 disp8
    """
    return "PENDING"
def d343 ( state ) :
    """
        JCXZ
        343 disp8
    """
    return "PENDING"
def d344dw ( state ) :
    """
        Acc IO
        344+dw imm8
    """
    byte = state["byte"]
    stream = state["stream"]

    d = (byte & 0b00000010) >> 1
    w =  byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    acc = registertable[state["size"]][0]

    imm8 = int.from_bytes(stream.read(1), byteorder='little', signed=True)
    state["pos"] += 1
    state["hex"].append(f'{imm8&0xFF:08X}')

    instruction = f"IN {acc}, {imm8}"
    if d == 1 :
        instruction = f"OUT {imm8}, {acc}"
    return instruction
def d350 ( state ) :
    """
        CALL disp
        350 disp
    """
    byte = state["byte"]
    stream = state["stream"]

    disp32 = int.from_bytes(stream.read(4), byteorder='little', signed=True)
    state["pos"] += 4
    state["hex"].append(f'{disp32&0xFFFFFFFF:08X}')

    return f'CALL {disp32} to {state["pos"]+disp32:08X}'
def d351w0 ( state ) :
    """
        JMP disp
        351 disp
    """
    byte = state["byte"]
    stream = state["stream"]

    w = (byte & 0b00000010) >> 1

    if w == 1 :
        disp8 = int.from_bytes(stream.read(4), byteorder='little', signed=True)
        state["pos"] += 4
        state["hex"].append(f'{disp8&0xFF:08X}')
        return f'JMP {disp8} to {state["pos"]+disp8:08X}'
    else :
        disp32 = int.from_bytes(stream.read(4), byteorder='little', signed=True)
        state["pos"] += 4
        state["hex"].append(f'{disp32&0xFFFFFFFF:08X}')
        return f'JMP {disp32} to {state["pos"]+disp32:08X}'
def d352 ( state ) :
    """
        JMPF
        352
    """
    return "PENDING"
def d354w ( state ) :
    """
        IN acc DX
        354+w
    """
    return "PENDING"
def d356w ( state ) :
    """
        OUT DX acc
        356+w
    """
    return "PENDING"
def d360 ( state ) :
    """
        LOCK
        360
    """
    return "PENDING"
def d361 ( state ) :
    """
        ICEBP
        361
    """
    return "PENDING"
def d362 ( state ) :
    """
        REPNE
        362
    """
    return "PENDING"
def d363 ( state ) :
    """
        REPE
        363
    """
    return "REPE"
def d364 ( state ) :
    """
        HLT
        364
    """
    return "HLT"
def d365 ( state ) :
    """
        CMC
        365
    """
    return "PENDING"
def d366w ( state ) :
    """
        366 instruction
    """
    read_xrm(state)
    r = state["r"]
    return [
        d366wr0,
        miss,
        d366wr2,
        d366wr3,
        d366wr4,
        d366wr5,
        d366wr6,
        d366wr7
    ][r](state)
def d366wr0 ( state ) :
    """
        TEST rm imm
        366+w x0m imm
    """
    byte = state["byte"]
    stream = state["stream"]

    w = byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    rmfield = parse_rm(state)

    if w == 0 :
        imm8 = int.from_bytes(stream.read(1), byteorder='little', signed=True)
        state["pos"] += 1
        state["hex"].append(f'{imm8&0xFF:08X}')
        return f"TEST {rmfield}, {imm8}"
    if w == 1 :
        imm32 = int.from_bytes(stream.read(4), byteorder='little', signed=True)
        state["pos"] += 4
        state["hex"].append(f'{imm32&0xFFFFFFFF:08X}')
        return f"TEST {rmfield}, {imm32}"

    return "INVALID"
def d366wr2 ( state ) :
    """
        NOT rm
        366+w x2m
    """
    byte = state["byte"]

    w = byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    rmfield = parse_rm(state)

    return f"NOT {rmfield}"
def d366wr3 ( state ) :
    """
        NEG rm
        366+w x3m
    """
    byte = state["byte"]

    w = byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    rmfield = parse_rm(state)

    return f"NEG {rmfield}"
def d366wr4 ( state ) :
    """
        MUL rm
        366+w x4m
    """
    byte = state["byte"]

    w = byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    rmfield = parse_rm(state)

    return f"MUL {rmfield}"
def d366wr5 ( state ) :
    """
        IMUL rm
        366+w x5m
    """
    byte = state["byte"]

    w = byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    rmfield = parse_rm(state)

    return f"IMUL {rmfield}"
def d366wr6 ( state ) :
    """
        DIV rm
        366+w x6m
    """
    byte = state["byte"]

    w = byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    rmfield = parse_rm(state)

    return f"DIV {rmfield}"
def d366wr7 ( state ) :
    """
        IDIV rm
        366+w x7m
    """
    byte = state["byte"]

    w = byte & 0b00000001

    state["size"] = ["r8", "r32"][w]

    rmfield = parse_rm(state)

    return f"IDIV {rmfield}"
def d370 ( state ) :
    """
        CLC
        370
    """
    return "PENDING"
def d371 ( state ) :
    """
        STC
        371
    """
    return "PENDING"
def d372 ( state ) :
    """
        CLI
        372
    """
    return "CLI"
def d373 ( state ) :
    """
        STI
        373
    """
    return "PENDING"
def d374 ( state ) :
    """
        CLD
        374
    """
    return "CLD"
def d375 ( state ) :
    """
        STD
        375
    """
    return "STD"
def d376wr01 ( state ) :
    """
        376+w x0m INC
        376+w x1m DEC
    """
    return "PENDING"
def d377 ( state ) :
    """
        377 instruction
    """
    read_xrm(state)
    r = state["r"]
    return [
        d376wr01,
        d376wr01,
        d377r2,
        d377r3,
        d377r4,
        d377r5,
        d377r6,
        miss
    ][r](state)
def d377r2 ( state ) :
    """
        CALL rm
        377 x2m
    """
    state["size"] = "r32"
    rm = parse_rm(state)
    return f"CALL {rm}"
def d377r3 ( state ) :
    """

        377 x3m
    """
    return "PENDING"
def d377r4 ( state ) :
    """
        JMP rm
        377 x4m
    """

    state["size"] = "r32"

    rm = parse_rm(state)

    return f"JMP {rm}"
def d377r5 ( state ) :
    """

        377 x5m
    """
    return "PENDING"
def d377r6 ( state ) :
    """
        PUSH rm
        377 x6m
    """
    state["size"] = "r32"
    rm = parse_rm(state)
    return f"PUSH {rm}"

def d017100cc ( state ) :
    """
        CMOVcc reg rm
        017 100+cc
    """
    byte = state["byte"]
    stream = state["stream"]

    cc = cctable[byte&0xFF-0o100]

    state["size"] = "r32"

    rmfield = parse_rm(state)
    regfield = parse_reg(state)

    return f'CMOV{cc} {regfield}, {rmfield}'
def d017200cc ( state ) :
    """
        Jcc disp32
        017 200+cc disp32
    """
    byte = state["byte"]
    stream = state["stream"]

    cc = cctable[byte&0xFF-0o200]

    disp32 = int.from_bytes(stream.read(4), byteorder='little', signed=True)
    state["pos"] += 4
    state["hex"].append(f'{disp32&0xFFFFFFFF:08X}')

    return f'J{cc} {disp32} to {state["pos"]+disp32:08X}'

def miss ( state ) :
    return f'MISSING {state["byte"]&0xFF:03o}/{state["byte"]&0xFF:02X}'



parsetables["x86"] = [
    d0p0dw, d0p0dw, d0p0dw, d0p0dw, d0p4w,  d0p4w,  d0l6d,  d0l6d,
    d0p0dw, d0p0dw, d0p0dw, d0p0dw, d0p4w,  d0p4w,  d0l6d,  d017,
    d0p0dw, d0p0dw, d0p0dw, d0p0dw, d0p4w,  d0p4w,  d0l6d,  d0l6d,
    d0p0dw, d0p0dw, d0p0dw, d0p0dw, d0p4w,  d0p4w,  d0l6d,  d0l6d,
    d0p0dw, d0p0dw, d0p0dw, d0p0dw, d0p4w,  d0p4w,  d0h6,   d0h7,
    d0p0dw, d0p0dw, d0p0dw, d0p0dw, d0p4w,  d0p4w,  d0h6,   d0h7,
    d0p0dw, d0p0dw, d0p0dw, d0p0dw, d0p4w,  d0p4w,  d0h6,   d0h7,
    d0p0dw, d0p0dw, d0p0dw, d0p0dw, d0p4w,  d0p4w,  d0h6,   d0h7,

    d10r,   d10r,   d10r,   d10r,   d10r,   d10r,   d10r,   d10r,
    d11r,   d11r,   d11r,   d11r,   d11r,   d11r,   d11r,   d11r,
    d12r,   d12r,   d12r,   d12r,   d12r,   d12r,   d12r,   d12r,
    d13r,   d13r,   d13r,   d13r,   d13r,   d13r,   d13r,   d13r,
    d14l,   d14l,   d14l,   d14l,   d14h,   d14h,   d14h,   d14h,
    d150w0, d151w0, d150w0, d151w0, d154dw, d154dw, d154dw, d154dw,
    d160cc, d160cc, d160cc, d160cc, d160cc, d160cc, d160cc, d160cc,
    d160cc, d160cc, d160cc, d160cc, d160cc, d160cc, d160cc, d160cc,

    d200sw, d200sw, d200sw, d200sw, d204w,  d204w,  d206w,  d206w,
    d210dw, d210dw, d210dw, d210dw, d214d0, d215,   d214d0, d217r0,
    d22r,   d22r,   d22r,   d22r,   d22r,   d22r,   d22r,   d22r,
    d230,   d231,   d232,   d233,   d234,   d235,   d236,   d237,
    d240dw, d240dw, d240dw, d240dw, d244w,  d244w,  d246w,  d246w,
    d250w,  d250w,  d252w,  d252w,  d254w,  d254w,  d256w,  d256w,
    d26wr,  d26wr,  d26wr,  d26wr,  d26wr,  d26wr,  d26wr,  d26wr,
    d26wr,  d26wr,  d26wr,  d26wr,  d26wr,  d26wr,  d26wr,  d26wr,

    d300w,  d300w,  d302,   d303,   d304,   d305,   d306w,  d306w,
    d310,   d311,   d312,   d313,   d314,   d315,   d316,   d317,
    d320w,  d320w,  d322w,  d322w,  d324,   d325,   d326,   d327,
    d33,    d33,    d33,    d33,    d33,    d33,    d33,    d33,
    d340,   d341,   d342,   d343,   d344dw, d344dw, d344dw, d344dw,
    d350,   d351w0, d352,   d351w0, d354w,  d354w,  d356w,  d356w,
    d360,   d361,   d362,   d363,   d364,   d365,   d366w,  d366w,
    d370,   d371,   d372,   d373,   d374,   d375,   d376wr01, d377,
]
parsetables["x86_017"] = [
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,

    d017100cc,  d017100cc,  d017100cc,  d017100cc,  d017100cc,  d017100cc,  d017100cc,  d017100cc,
    d017100cc,  d017100cc,  d017100cc,  d017100cc,  d017100cc,  d017100cc,  d017100cc,  d017100cc,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,

    d017200cc,  d017200cc,  d017200cc,  d017200cc,  d017200cc,  d017200cc,  d017200cc,  d017200cc,
    d017200cc,  d017200cc,  d017200cc,  d017200cc,  d017200cc,  d017200cc,  d017200cc,  d017200cc,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,

    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
    miss,   miss,   miss,   miss,   miss,   miss,   miss,   miss,
]

def disassemble ( stream, start, stop ) :
    stream.seek(start)

    state = {
        "stream" : stream,
        "pos" : start,
    }

    pos = start

    while pos < stop :
        state = {
            "stream" : stream,
            "byte" : ord(stream.read(1)),
            "pos" : pos,
        }
        state["hex"] = [
            f'{state["pos"]:08X}',
            f'{state["byte"]:03o}'
        ]
        state["pos"] += 1

        parse = parsetables["x86"][state["byte"]](state)
        if parse.startswith("PENDING") or parse.startswith("MISSING") :
            print(f'{" ".join(state["hex"]):50} {parse}')
        pos = state["pos"]

def read_xrm ( state ) :
    if "xrm" in state :
        return
    xrm = state["xrm"] = ord(state["stream"].read(1))
    state["pos"] += 1

    state["x"]  = (xrm & 0b11000000) >> 6
    state["r"]  = (xrm & 0b00111000) >> 3
    state["rm"] =  xrm & 0b00000111

    state["hex"].append(f"{xrm:03o}")

def parse_rm ( state ) -> str :
    read_xrm(state)
    stream = state["stream"]
    x = state["x"]
    rm = state["rm"]
    base = registertable[state["size"]][rm]

    if x == 3 : # 3rm | register direct mode
        return base

    if rm == 4 : # xr4 | sib
        base = parse_sib(state)

    if x == 0 : # 0rm
        if rm == 5 : # 0r5 disp32 | displacement only
            disp32 = int.from_bytes(stream.read(4), byteorder='little', signed=True)
            state["pos"] += 4
            state["hex"].append(f'{disp32&0xFFFFFFFF:08X}')
            return f"DS:[{disp32:08X}]"
        return f"DS:[{base}]"

    if x == 1 : # 1rm disp8
        disp8 = int.from_bytes(stream.read(1), byteorder='little', signed=True)
        state["pos"] += 1
        state["hex"].append(f'{disp8&0xFF:08X}')
        return f"DS:[{base}{disp8:+08X}]"

    if x == 2 : # 2rm disp32
        disp32 = int.from_bytes(stream.read(4), byteorder='little', signed=True)
        state["pos"] += 4
        state["hex"].append(f'{disp32&0xFFFFFFFF:08X}')
        return f"DS:[{base}{disp32:+08X}]"

def parse_reg ( state ) -> str :
    read_xrm(state)
    stream = state["stream"]
    reg = state["r"]
    return registertable[state["size"]][reg]

def parse_sib ( state ) -> str :
    read_xrm(state)
    stream = state["stream"]
    x = state["x"]
    if "sib" in state :
        return state["sibaddress"]
    sib = state["sib"] = ord(state["stream"].read(1))
    state["pos"] += 1

    scale = state["scale"] = (sib & 0b11000000) >> 6
    index = state["index"] = (sib & 0b00111000) >> 3
    base = state["base"]  =  sib & 0b00000111

    state["hex"].append(f"{sib:03o}")

    baseaddress = registertable[state["size"]][base]
    if base == 5 : # si5 | no base
        baseaddress = 0

    indexaddress = registertable[state["size"]][index]
    if base == 5 : # s4b | no index
        indexaddress = 0

    offset = 0
    if x == 1 : # 1rm | +disp8
        offset = int.from_bytes(stream.read(1), byteorder='little', signed=True)
        state["pos"] += 1
        state["hex"].append(f'{offset&0xFF:08X}')
    if x == 2 : # 2rm | +disp32
        offset = int.from_bytes(stream.read(4), byteorder='little', signed=True)
        state["pos"] += 4
        state["hex"].append(f'{offset&0xFFFFFFFF:08X}')

    state["sibaddress"] = sibaddress = f"{baseaddress}+{indexaddress}^{1<<scale}+{offset}"
    return sibaddress
