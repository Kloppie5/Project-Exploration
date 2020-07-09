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

counter = 0
def opcode_print ( pos, hex, text = "" ) :
    global counter
    if not text.startswith("UNKNOWN"):
        print(f"{counter:4} {pos:08X}: {hex:48} {text}")
        counter += 1

def ModRM ( byte ) -> (int, int, int) :
    mod = (ord(byte) & 0b11000000) >> 6
    reg = (ord(byte) & 0b00111000) >> 3
    rm  =  ord(byte) & 0b00000111
    return mod, reg, rm

def SIB ( byte ) -> (int, int, int) : # yes, technically the same as ModRM
    scale = (ord(byte) & 0b11000000) >> 6
    index = (ord(byte) & 0b00111000) >> 3
    base  =  ord(byte) & 0b00000111
    return scale, index, base

def Register ( type, ref ) -> str :
    print(f"Get reg ({type}, {ref})")
    return [
        ["al",   "ax",   "eax",  "rax", "st0", "mmx0", "xmm0",  "ymm0",  "es", "cr0",  "dr0"],
        ["cl",   "cx",   "ecx",  "rcx", "st1", "mmx1", "xmm1",  "ymm1",  "cs", "cr1",  "dr1"],
        ["dl",   "dx",   "edx",  "rdx", "st2", "mmx2", "xmm2",  "ymm2",  "ss", "cr2",  "dr2"],
        ["bl",   "bx",   "ebx",  "rbx", "st3", "mmx3", "xmm3",  "ymm3",  "ds", "cr3",  "dr3"],
        ["ah",   "sp",   "esp",  "rsp", "st4", "mmx4", "xmm4",  "ymm4",  "fs", "cr4",  "dr4"],
        ["ch",   "bp",   "ebp",  "rbp", "st5", "mmx5", "xmm5",  "ymm5",  "gs", "cr5",  "dr5"],
        ["dh",   "si",   "esi",  "rsi", "st6", "mmx6", "xmm6",  "ymm6",  "-",  "cr6",  "dr6"],
        ["bh",   "di",   "edi",  "rdi", "st7", "mmx7", "xmm7",  "ymm7",  "-",  "cr7",  "dr7"],
        ["r8l",  "r8w",  "r8d",  "r8",  "-",   "mmx0", "xmm8",  "ymm8",  "es", "cr8",  "dr8"],
        ["r9l",  "r9w",  "r9d",  "r9",  "-",   "mmx1", "xmm9",  "ymm9",  "cs", "cr9",  "dr9"],
        ["r10l", "r10w", "r10d", "r10", "-",   "mmx2", "xmm10", "ymm10", "ss", "cr10", "dr10"],
        ["r11l", "r11w", "r11d", "r11", "-",   "mmx3", "xmm11", "ymm11", "ds", "cr11", "dr11"],
        ["r12l", "r12w", "r12d", "r12", "-",   "mmx4", "xmm12", "ymm12", "fs", "cr12", "dr12"],
        ["r13l", "r13w", "r13d", "r13", "-",   "mmx5", "xmm13", "ymm13", "gs", "cr13", "dr13"],
        ["r14l", "r14w", "r14d", "r14", "-",   "mmx6", "xmm14", "ymm14", "-",  "cr14", "dr14"],
        ["r15l", "r15w", "r15d", "r15", "-",   "mmx7", "xmm15", "ymm15", "-",  "cr15", "dr15"]
    ][ref][type]

class Disassembler_x86 :

    # init: stream |- read(size:int) -> byte
    #              |- seek(dist:int)
    # state:{pos:int}

    opcode_tree = [
        [   [   [   [   [                                                       # 00-07: ADD, ES
                                        {'name': 'ADD'},                            # 00:ds   00 0 00 0ds       | ADD
                            [           {'name': 'acc ADD'},                        # 04:s    00 0 00 10s       | acc ADD
                                [       {'name': 'PUSH ES'},                        # 06      00 0 00 110       | PUSH ES
                                        {'name': 'POP ES'}]]                        # 07      00 0 00 111       | POP ES
                        ],[                                                     # 08-0F: OR, CS
                                        {'name': 'OR'},                             # 08:ds   00 0 01 0ds       | OR
                            [           {'name': 'acc OR'},                         # 0C:s    00 0 01 10s       | acc OR
                                [       {'name': 'PUSH CS'},                        # 0E      00 0 01 110       | PUSH CS
                                        {'name': 'IS 0F'}]]]                        # 0F      00 0 01 111       | Instruction set switch
                    ],[ [                                                       # 10-17: ADC, SS
                                        {'name': 'ADC'},                            # 10:ds   00 0 10 0ds       | ADC
                            [           {'name': 'acc ADC'},                        # 14:s    00 0 10 10s       | acc ADC
                                [       {'name': 'PUSH SS'},                        # 16      00 0 10 110       | PUSH SS
                                        {'name': 'POP SS'}]]                        # 17      00 0 10 111       | POP SS
                        ],[                                                 # 18-1F: SBB, DS
                                        {'name': 'SBB'},                            # 18:ds   00 0 11 0ds       | SBB
                            [           {'name': 'acc SBB'},                        # 1C:s    00 0 11 10s       | acc SSB
                                [       {'name': 'PUSH DS'},                        # 1E      00 0 11 110       | PUSH DS
                                        {'name': 'POP DS'}]]]]                      # 1F      00 0 11 111       | POP DS
                ],[ [   [                                                       # 20-27: AND, ESo DDA
                                        {'name': 'AND'},                            # 20:ds   00 1 00 0ds       | AND
                            [           {'name': 'acc AND'},                        # 24:s    00 1 00 10s       | acc AND
                                [       {'name': 'ES override'},                    # 26      00 1 00 110       | ES override
                                        {'name': 'acc DAA'}]]                       # 27      00 1 00 111       | DAA AL
                        ],[                                                     # 28-2F: SUB, CSo DAS
                                        {'name': 'SUB'},                            # 28:ds   00 1 01 0ds       | SUB
                            [           {'name': 'acc SUB'},                        # 2C:s    00 1 01 10s       | acc SUB
                                [       {'name': 'CS override'},                    # 2E      00 1 01 110       | CS override
                                        {'name': 'acc DAS'}]]]                      # 2F      00 1 01 111       | DAS AL
                    ],[ [                                                       # 30-37: XOR, SSo AAA
                                        {'name': 'XOR'},                            # 30:ds   00 1 10 0ds       | XOR
                            [           {'name': 'acc XOR'},                        # 34:s    00 1 10 10s       | acc XOR
                                [       {'name': 'SS override'},                    # 36      00 1 10 110       | SS override
                                        {'name': 'acc AAA'}]]                       # 37      00 1 10 111       | AAA AL
                        ],[                                                     # 38-3F: CMP, DSo AAS
                                        {'name': 'CMP'},                            # 38:ds   00 1 11 0ds       | CMP
                            [           {'name': 'acc CMP'},                        # 3C:s    00 1 11 10s       | acc CMP
                                [       {'name': 'DS override'},                    # 3E      00 1 11 110       | DS override 
                                        {'name': 'acc AAS'}]]]]]                    # 3F      00 1 11 111       | AAS AL
            ],[ [                                                               # 40-5F: reg operations
                            [           {'name': 'INC reg'},                        # 40:reg  010 00 reg        | INC reg
                                        {'name': 'DEC reg'}                         # 48:reg  010 01 reg        | DEC reg
                            ],[         {'name': 'PUSH reg'},                       # 50:reg  010 10 reg        | PUSH reg
                                        {'name': 'POP reg'}]                        # 58:reg  010 11 reg        | POP reg
                ],[ [   [   [   [                                               # 60-67
                                        {'name': 'PUSHA'},                          # 60      011000 00         | PUSHA
                                        {'name': 'POPA'}                            # 61      011000 01         | POPA
                                ],[     {'name': 'BOUND'},                          # 62      011000 10         | BOUND
                                        {'name': 'ARPL'}]                           # 63      011000 11         | ARPL
                            ],[ [                                               # 64-67: Prefixes
                                        {'name': 'FS override'},                    # 64      011001 00         | FS override
                                        {'name': 'GS override'}                     # 65      011001 01         | GS override
                                ],[
                                        {'name': 'Operand-size override'},          # 66      011001 10         | Operand-size override
                                        {'name': 'Address-size override'}]]         # 67      011001 11         | Address-size override
                        ],[                                                     # 68-6B
                                        # 68:~s-  011010 s0         | PUSH const
                                        # 69:~s-  011010 s1         | IMUL const
                                    # 6C-6F: Port IO
                                        # 6C:s    011011 0 s        | INS
                                        # 6E:s    011011 1 s        | OUTS
                        ]
                    ],                  {'name': 'COND JMP'}        # 70-7F: Jumps
                                                                        # 70      0111 0000         | JO          (OF=1)
                                                                        # 71      0111 0001         | JNO         (OF=0)
                                                                        # 72      0111 0010         | JB JNAE JC  (CF=1)			
                                                                        # 73      0111 0011         | JNB JAE JNC (CF=0)
                                                                        # 74      0111 0100         | JZ JE       (ZF=1)
                                                                        # 75      0111 0101         | JNZ JNE     (ZF=0)
                                                                        # 76      0111 0110         | JBE JNA     (CF=1 OR ZF=1)
                                                                        # 77      0111 0111         | JNBE JA     (CF=0 AND ZF=0)
                                                                        # 78      0111 1000         | JS          (SF=1)
                                                                        # 79      0111 1001         | JNS         (SF=0)
                                                                        # 7A      0111 1010         | JP JPE      (PF=1)
                                                                        # 7B      0111 1011         | JNP JPO     (PF=0)
                                                                        # 7C      0111 1100         | JL JNGE     (SF!=OF)
                                                                        # 7D      0111 1101         | JNL JGE     (SF=OF)
                                                                        # 7E      0111 1110         | JLE JNG     ((ZF=1) OR (SF!=OF))
                                                                        # 7F      0111 1111         | JNLE JG     ((ZF=0) AND (SF=OF))
                ]
            ]
        ], # 1
            [   [   [            # 100
                    
                ], [         # 101

                ]
            ],  [   [            # 110
                
                ], [         # 111
                
                ]
            ]
        ]


        # 80-83: Immediate
            # 80:xs/0 100000 xs r000   | ADD const
            # 80:xd/1 100000 xs r001   | OR const
            # 80:xs/2 100000 xs r010   | ADC const
            # 80:xs/3 100000 xs r011   | SBB const
            # 80:xs/4 100000 xs r100   | AND const
            # 80:xs/5 100000 xs r101   | SUB const
            # 80:xs/6 100000 xs r110   | XOR const
            # 80:xs/7 100000 xs r111   | CMP const

        # 84:s    1000010 s       | TEST
        # 86:s    1000011 s       | XCHG
        # 88:ds   100010 ds       | MOV
        # 8C:d-   1000 11d0       | MOV segreg
        # 8D      1000 1101       | LEA
        # 8F/0    1000 1111 r000  | POP reg
        # 90:reg  10010 reg       | XCHG reg

        # 98 CBW
        # 99 CWD
        # 9A CALLF
        # 9B WAIT
        # 9C PUSHF
        # 9D POPF
        # 9E SAHF
        # 9F LAHF

        # A0:ds   1010 00ds  | acc MOV offset

        # A4:s    1010 010s       | MOVS
        # A6:s    1010 011s       | CMPS
        # A8:s    1010 100s       | acc TEST
        # AA:s    1010 101s       | STOS
        # AC:s    1010 110s       | LODS
        # AE:s    1010 111s       | SCAS

        # Bs:reg  1011 s reg      | MOV reg

        # C0:s/0  1100 000s r000  | ROL
        # C0:s/1  1100 000s r001  | ROR
        # C0:s/2  1100 000s r010  | RCL
        # C0:s/3  1100 000s r011  | RCR
        # C0:s/4  1100 000s r100  | SHL
        # C0:s/5  1100 000s r101  | SHR
        # C0:s/6  1100 000s r110  | SAL
        # C0:s/7  1100 000s r111  | SAR

        # C2 RET var
        # C3 RET

        # C4 LES
        # C5 LDS

        # C6:s/0  1100 011s r000  | MOV const

        # C8 ENTER
        # C9 LEAVE

        # CA RETF var
        # CB RETF
        # CC INT3
        # CD INT
        # CE INTO
        # CD IRET

        # D0:xs/0 1101 00xs r000  | ROL 1/x
        # D0:xs/1 1101 00xs r001  | ROR 1/x
        # D0:xs/2 1101 00xs r010  | RCL 1/x
        # D0:xs/3 1101 00xs r011  | RCR 1/x
        # D0:xs/4 1101 00xs r100  | SHL 1/x
        # D0:xs/5 1101 00xs r101  | SHR 1/x
        # D0:xs/6 1101 00xs r110  | SAL 1/x
        # D0:xs/7 1101 00xs r111  | SAR 1/x

        # D4 AMX
        # D5 ADX
        # D6 SALC
        # D7 XLAT
        # D8/0 FADD
        # D8/1 FMUL
        # D8/2 FCOM
        # D8/3 FCOMP
        # D8/4 FSUB
        # D8/5 FSUBR
        # D8/6 FDIV
        # D8/7 FDIVR

        # D9/0 FLD
        # D9/1 FXCH
        # D9/2 FST
        # D9/3 FSTP
        # D9/4 FLDENV
        # D9/5 FLDCW
        # D9/6 FNSTENV
        # D9/7 FSTCW


        # F6:s/0  1111 011s r000  | TEST
        # F6:s/2  1111 011s r010  | NOT
        # F6:s/3  1111 011s r011  | NEG
        # FE:s/0  1111 111s r000  | INC mem
        # FE:s/1  1111 111s r001  | DEC mem
        # FF/4    1111 1111 r100  | JMP reg
        # FF/5    1111 1111 r101  | JMP mem
        # FF/6    1111 1111 r110  | PUSH reg
    ]

    def __init__ ( self, stream ) :
        self.stream = stream
        self.state = {'pos': 0}
    
    def disassemble ( self, start, stop ) :
        stream.seek(start)
        self.state.pos = start

        while self.state.pos < stop :
            byte = ord(f.read(1))




def disassembled_view ( f, start, callback, limit = -1 ) :
    f.seek(start)
    i = 0

    _hex = ""

    while 1:
        if limit != -1 and i > limit:
            callback(start+i, _hex)
            return
        
        byte = f.read(1)
        if not byte:
            callback(start+i, _hex)
            return

        byte = ord(byte)


        # 0F 0000 1111
        #  A0:p   1010 000p       | PUSH/POP FS
        #  A8:p   1010 100p       | PUSH/POP GS





        # 00-07: ADD, ES
            # 00:ds   00 0 00 0ds       | ADD
            # 04:s    00 0 00 10s       | acc ADD
            # 06      00 0 00 110       | PUSH ES
            # 07      00 0 00 111       | POP ES
        # 08-0F: OR, CS
            # 08:ds   00 0 01 0ds       | OR
            # 0C:s    00 0 01 10s       | acc OR
            # 0E      00 0 01 110       | PUSH CS
            # 0F      0000 1111         | Instruction set switch
        # 10-17: ADC, SS
            # 10:ds   00 0 10 0ds       | ADC
            # 14:s    00 0 10 10s       | acc ADC
            # 16      00 0 10 110       | PUSH SS
            # 17      00 0 10 111       | POP SS
        # 18-1F: SBB, DS
            # 18:ds   00 0 11 0ds       | SBB
            # 1C:s    00 0 11 10s       | acc SSB
            # 1E      00 0 11 110       | PUSH DS
            # 1F      00 0 11 111       | POP DS
        # 20-27: AND, ESo DDA
            # 20:ds   00 1 00 0ds       | AND
            # 24:s    00 1 00 10s       | acc AND
            # 26      00 1 00 110       | ES override
            # 27      00 1 00 111       | DAA AL
        # 28-2F: SUB, CSo DAS
            # 28:ds   00 1 01 0ds       | SUB
            # 2C:s    00 1 01 10s       | acc SUB
            # 2E      00 1 01 110       | CS override
            # 2F      00 1 01 111       | DAS AL
        # 30-37: XOR, SSo AAA
            # 30:ds   00 1 10 0ds       | XOR
            # 34:s    00 1 10 10s       | acc XOR
            # 36      00 1 10 110       | SS override
            # 37      00 1 10 111       | AAA AL
        # 38-3F: CMP, DSo AAS
            # 38:ds   00 1 11 0ds       | CMP
            # 3C:s    00 1 11 10s       | acc CMP
            # 3E      00 1 11 110       | DS override 
            # 3F      00 1 11 111       | AAS AL
        # 40-5F: reg operations
            # 40:reg  010 00 reg        | INC reg
            # 48:reg  010 01 reg        | DEC reg
            # 50:reg  010 10 reg        | PUSH reg
            # 58:reg  010 11 reg        | POP reg
        # 60-67
            # 60      011000 00         | PUSHA
            # 61      011000 01         | POPA
            # 62      011000 10         | BOUND
            # 63      011000 11         | ARPL
        # 64-67: Prefixes
            # 64      011001 00         | FS override
            # 65      011001 01         | GS override
            # 66      011001 10         | Operand-size override
            # 67      011001 11         | Address-size override
        # 68-6B
            # 68:~s-  011010 s0         | PUSH const
            # 69:~s-  011010 s1         | IMUL const
        # 6C-6F: Port IO
            # 6C:s    011011 0 s        | INS
            # 6E:s    011011 1 s        | OUTS
        # 70-7F: Jumps
        	# 70      0111 0000         | JO          (OF=1)
            # 71      0111 0001         | JNO         (OF=0)
            # 72      0111 0010         | JB JNAE JC  (CF=1)			
            # 73      0111 0011         | JNB JAE JNC (CF=0)
            # 74      0111 0100         | JZ JE       (ZF=1)
            # 75      0111 0101         | JNZ JNE     (ZF=0)
            # 76      0111 0110         | JBE JNA     (CF=1  OR ZF=1)
            # 77      0111 0111         | JNBE JA     (CF=0 AND ZF=0)
            # 78      0111 1000         | JS          (SF=1)
            # 79      0111 1001         | JNS         (SF=0)
            # 7A      0111 1010         | JP JPE      (PF=1)
            # 7B      0111 1011         | JNP JPO     (PF=0)
            # 7C      0111 1100         | JL JNGE     (SF!=OF)
            # 7D      0111 1101         | JNL JGE     (SF=OF)
            # 7E      0111 1110         | JLE JNG     ((ZF=1) OR (SF!=OF))
            # 7F      0111 1111         | JNLE JG     ((ZF=0) AND (SF=OF))
        # 80-83: Immediate
            # 80:xs/0 100000 xs r000   | ADD const
            # 80:xd/1 100000 xs r001   | OR const
            # 80:xs/2 100000 xs r010   | ADC const
            # 80:xs/3 100000 xs r011   | SBB const
            # 80:xs/4 100000 xs r100   | AND const
            # 80:xs/5 100000 xs r101   | SUB const
            # 80:xs/6 100000 xs r110   | XOR const
            # 80:xs/7 100000 xs r111   | CMP const

        # 84:s    1000010 s       | TEST
        # 86:s    1000011 s       | XCHG
        # 88:ds   100010 ds       | MOV
        # 8C:d-   1000 11d0       | MOV segreg
        # 8D      1000 1101       | LEA
        # 8F/0    1000 1111 r000  | POP reg
        # 90:reg  10010 reg       | XCHG reg

        # 98 CBW
        # 99 CWD
        # 9A CALLF
        # 9B WAIT
        # 9C PUSHF
        # 9D POPF
        # 9E SAHF
        # 9F LAHF

        # A0:ds   1010 00ds  | acc MOV offset

        # A4:s    1010 010s       | MOVS
        # A6:s    1010 011s       | CMPS
        # A8:s    1010 100s       | acc TEST
        # AA:s    1010 101s       | STOS
        # AC:s    1010 110s       | LODS
        # AE:s    1010 111s       | SCAS

        # Bs:reg  1011 s reg      | MOV reg

        # C0:s/0  1100 000s r000  | ROL
        # C0:s/1  1100 000s r001  | ROR
        # C0:s/2  1100 000s r010  | RCL
        # C0:s/3  1100 000s r011  | RCR
        # C0:s/4  1100 000s r100  | SHL
        # C0:s/5  1100 000s r101  | SHR
        # C0:s/6  1100 000s r110  | SAL
        # C0:s/7  1100 000s r111  | SAR

        # C2 RET var
        # C3 RET

        # C4 LES
        # C5 LDS

        # C6:s/0  1100 011s r000  | MOV const

        # C8 ENTER
        # C9 LEAVE

        # CA RETF var
        # CB RETF
        # CC INT3
        # CD INT
        # CE INTO
        # CD IRET

        # D0:xs/0 1101 00xs r000  | ROL 1/x
        # D0:xs/1 1101 00xs r001  | ROR 1/x
        # D0:xs/2 1101 00xs r010  | RCL 1/x
        # D0:xs/3 1101 00xs r011  | RCR 1/x
        # D0:xs/4 1101 00xs r100  | SHL 1/x
        # D0:xs/5 1101 00xs r101  | SHR 1/x
        # D0:xs/6 1101 00xs r110  | SAL 1/x
        # D0:xs/7 1101 00xs r111  | SAR 1/x

        # D4 AMX
        # D5 ADX
        # D6 SALC
        # D7 XLAT
        # D8/0 FADD
        # D8/1 FMUL
        # D8/2 FCOM
        # D8/3 FCOMP
        # D8/4 FSUB
        # D8/5 FSUBR
        # D8/6 FDIV
        # D8/7 FDIVR

        # D9/0 FLD
        # D9/1 FXCH
        # D9/2 FST
        # D9/3 FSTP
        # D9/4 FLDENV
        # D9/5 FLDCW
        # D9/6 FNSTENV
        # D9/7 FSTCW


        # F6:s/0  1111 011s r000  | TEST
        # F6:s/2  1111 011s r010  | NOT
        # F6:s/3  1111 011s r011  | NEG
        # FE:s/0  1111 111s r000  | INC mem
        # FE:s/1  1111 111s r001  | DEC mem
        # FF/4    1111 1111 r100  | JMP reg
        # FF/5    1111 1111 r101  | JMP mem
        # FF/6    1111 1111 r110  | PUSH reg

        if ord(byte) & 0b11111100 == 0b00000000 : # ADD 000000ds
            d = (ord(byte) & 0b00000010) >> 1 # 0: add reg to r/m, 1: add r/m to reg
            s =  ord(byte) & 0b00000001       # 0: 8-bit,          1: 16- or 32-bit
            _hex += f"000000 {d}{s}"
            
            modrm = f.read(1) 
            mod, reg, rm = ModRM(modrm)
            _hex += f" {mod:02b} {reg:03b} {rm:03b}"

            regfield = Register(s*2, reg)
            rmfield = Register(2, rm)

            if mod == 0b00 :
                if rm == 0b100 : # SIB mode
                    sib = f.read(1)
                    scale, index, base = SIB(sib)
                    _hex += f" {scale:02b} {index:03b} {base:03b}"

                    rmfield = f"{Register(2, index)}*{1<<scale}"

                    if base == 0b101 : # displacement-only mode
                        disp32 = int.from_bytes(f.read(4), byteorder='little', signed=True)
                        _hex += f" {disp32:08X}"
                        rmfield += f"{disp32:+08X}"
                        i += 4
                    else :
                        print()
                    
                    i += 1
            if mod == 0b01 : # one-byte displacement mode
                disp8 = int.from_bytes(f.read(1), byteorder='little', signed=True)
                _hex += f" {disp8:02X}"
                rmfield += f"{disp8:+02X}"
                i += 1
            if mod == 0b10 : # four-byte displacement mode
                disp32 = int.from_bytes(f.read(4), byteorder='little', signed=True)
                _hex += f" {disp32:08X}"
                rmfield += f"{disp32:+08X}"
                i += 4
            if mod == 0b11 : # direct mode (r/m is a register field)
                rmfield = Register(s*2, rm)
            else :
                rmfield = f"[{rmfield}]"
            
            if d == 0b0 :
                callback(start+i, _hex, f"ADD {rmfield}, {regfield}")
            else :
                callback(start+i, _hex, f"ADD {regfield}, {rmfield}")
            _hex = ""
            i += 1

        elif ord(byte) & 0b11111100 == 0b10000000 : # immediate mode 100000xs
            x = (ord(byte) & 0b00000010) >> 1 # 0: same size as s, 1: sign-extended
            s =  ord(byte) & 0b00000001       # 0: 8-bit,          1: 32-bit
            _hex += f"100000 {x}{s}"
            print("immediate mode")

            modrm = f.read(1) 
            mod, reg, rm = ModRM(modrm)
            _hex += f" {mod:02b} {reg:03b} {rm:03b}"

            if reg == 0b000 :
                print("immediate add")
            if reg == 0b111:
                print("immediate cmp")

        if ord(byte) & 0b11111110 == 0b00000100 : # ADD 0000010s
            print("accumulator add")

        elif xs == 0b01 :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x11 101 100' :
                read = f.read(4)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"SUB esp, {number}")
                _hex = bytearray()
                i += 4
            elif byte == b'\x11 111 001' :
                read = f.read(4)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"CMP ecx, {number}")
                _hex = bytearray()
                i += 4
            elif byte == b'\x11 111 010' :
                read = f.read(4)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"CMP edx, {number}")
                _hex = bytearray()
                i += 4
            i += 1

        elif byte == b'\x100000 11' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x00 111 101' :
                read = f.read(4)
                _hex += read
                number1 = int.from_bytes(read, byteorder='little', signed=True)
                read = f.read(1)
                _hex += read
                number2 = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"CMP dword ptr [{number1:08X}], {number2}")
                _hex = bytearray()
                i += 5
            elif byte == b'\x01 100 101' :
                read = f.read(1)
                _hex += read
                number1 = int.from_bytes(read, byteorder='little', signed=True)
                read = f.read(1)
                _hex += read
                number2 = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"AND dword ptr [ebp+{number1}], {number2}")
                _hex = bytearray()
                i += 2
            elif byte == b'\x01 111 101' :
                read = f.read(1)
                _hex += read
                number1 = int.from_bytes(read, byteorder='little', signed=True)
                read = f.read(1)
                _hex += read
                number2 = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"CMP dword ptr [ebp+{number1}], {number2}")
                _hex = bytearray()
                i += 2
            elif byte == b'\x11 000 100' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"AND esp, {number}")
                _hex = bytearray()
                i += 1
            elif byte == b'\x11 000 110' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"AND esi, {number}")
                _hex = bytearray()
                i += 1
            elif byte == b'\xC7' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"AND edi, {number}")
                _hex = bytearray()
                i += 1
            elif byte == b'\x11 100 000' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"AND eax, {number}")
                _hex = bytearray()
                i += 1
            elif byte == b'\xE1' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"AND ecx, {number}")
                _hex = bytearray()
                i += 1
            elif byte == b'\xE2' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"AND edx, {number}")
                _hex = bytearray()
                i += 1
            elif byte == b'\xE6' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"AND esi, {number}")
                _hex = bytearray()
                i += 1
            elif byte == b'\xE7' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"AND edi, {number}")
                _hex = bytearray()
                i += 1
            elif byte == b'\xE9' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"SUB ecx, {number}")
                _hex = bytearray()
                i += 1
            elif byte == b'\xEA' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"SUB edx, {number}")
                _hex = bytearray()
                i += 1
            elif byte == b'\xEC' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"SUB esp, {number}")
                _hex = bytearray()
                i += 1
            elif byte == b'\xEE' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"SUB esi, {number}")
                _hex = bytearray()
                i += 1
            elif byte == b'\xEF' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"SUB edi, {number}")
                _hex = bytearray()
                i += 1
            elif byte == b'\xF8' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"CMP eax, {number}")
                _hex = bytearray()
                i += 1
            elif byte == b'\xF9' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"CMP ecx, {number}")
                _hex = bytearray()
                i += 1
            elif byte == b'\xFA' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"CMP edx, {number}")
                _hex = bytearray()
                i += 1
            elif byte == b'\xFE' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"CMP esi, {number}")
                _hex = bytearray()
                i += 1
            i += 1





        elif byte == b'\x04' :
            read = f.read(1)
            _hex += read
            number = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"ADD al, {number}")
            _hex = bytearray()
            i += 1
        elif byte == b'\x05' :
            read = f.read(4)
            _hex += read
            number = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"ADD eax, {number}")
            _hex = bytearray()
            i += 4
        elif byte == b'\x08' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x5E' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"OR [esi+{number}], bl")
                _hex = bytearray()
                i += 1
            i += 1
        elif byte == b'\x0E' :
            callback(start+i, _hex, f"PUSH cs")
            _hex = bytearray()
        elif byte == b'\x0F' :
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
        elif byte == b'\x10' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x49' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"ADC [ecx+{number}], cl")
                _hex = bytearray()
                i += 1
            i += 1
        elif byte == b'\x11' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x49' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"ADC [ecx+{number}], ecx")
                _hex = bytearray()
                i += 1
            i += 1
        elif byte == b'\x23' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\xC8' :
                callback(start+i, _hex, f"AND ecx, eax")
                _hex = bytearray()
            elif byte == b'\xD1' :
                callback(start+i, _hex, f"AND edx, ecx")
                _hex = bytearray()
            i += 1
        elif byte == b'\x2B' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\xC8' :
                callback(start+i, _hex, f"SUB ecx, eax")
                _hex = bytearray()
            elif byte == b'\xCF' :
                callback(start+i, _hex, f"SUB ecx, edi")
                _hex = bytearray()
            elif byte == b'\xD0' :
                callback(start+i, _hex, f"SUB edx, eax")
                _hex = bytearray()
            elif byte == b'\xD1' :
                callback(start+i, _hex, f"SUB edx, ecx")
                _hex = bytearray()
            elif byte == b'\xF9' :
                callback(start+i, _hex, f"SUB edi, ecx")
                _hex = bytearray()
            i += 1
        elif byte == b'\x30' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x11' :
                callback(start+i, _hex, f"XOR [ecx], dl")
                _hex = bytearray()
            i += 1
        elif byte == b'\x33' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\xC0' :
                callback(start+i, _hex, f"XOR eax, eax")
                _hex = bytearray()
            i += 1
        elif byte == b'\x34' :
            read = f.read(1)
            _hex += read
            number = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"XOR al, {number}")
            _hex = bytearray()
            i += 1
        elif byte == b'\x39' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x05' :
                read = f.read(4)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"CMP [{number}], eax")
                _hex = bytearray()
                i += 4
            i += 1
        elif byte == b'\x3B' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x0D' :
                read = f.read(4)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"CMP ecx, [{number:08X}]")
                _hex = bytearray()
                i += 4
            elif byte == b'\x35' :
                read = f.read(4)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"CMP esi, [{number:08X}]")
                _hex = bytearray()
                i += 4
            elif byte == b'\xC1' :
                callback(start+i, _hex, f"CMP eax, ecx")
                _hex = bytearray()
            elif byte == b'\xCA' :
                callback(start+i, _hex, f"CMP ecx, edx")
                _hex = bytearray()
            elif byte == b'\xDF' :
                callback(start+i, _hex, f"CMP ebx, edi")
                _hex = bytearray()
            elif byte == b'\xF7' :
                callback(start+i, _hex, f"CMP esi, edi")
                _hex = bytearray()
            elif byte == b'\xF8' :
                callback(start+i, _hex, f"CMP edi, eax")
                _hex = bytearray()
            elif byte == b'\xFA' :
                callback(start+i, _hex, f"CMP edi, edx")
                _hex = bytearray()
            elif byte == b'\xFE' :
                callback(start+i, _hex, f"CMP edi, esi")
                _hex = bytearray()
            i += 1
        elif byte == b'\x3D' :
            read = f.read(4)
            _hex += read
            number = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"CMP eax, {number}")
            _hex = bytearray()
            i += 4
        elif byte == b'\x40' :
            callback(start+i, _hex, f"INC eax")
            _hex = bytearray()
        elif byte == b'\x41' :
            callback(start+i, _hex, f"INC ecx")
            _hex = bytearray()
        elif byte == b'\x46' :
            callback(start+i, _hex, f"INC esi")
            _hex = bytearray()
        elif byte == b'\x48' :
            callback(start+i, _hex, f"DEC eax")
            _hex = bytearray()
        elif byte == b'\x49' :
            callback(start+i, _hex, f"DEC ecx")
            _hex = bytearray()
        elif byte == b'\x4E' :
            callback(start+i, _hex, f"DEC esi")
            _hex = bytearray()
        elif byte == b'\x50' :
            callback(start+i, _hex, f"PUSH eax")
            _hex = bytearray()
        elif byte == b'\x51' :
            callback(start+i, _hex, f"PUSH ecx")
            _hex = bytearray()
        elif byte == b'\x53' :
            callback(start+i, _hex, f"PUSH ebx")
            _hex = bytearray()
        elif byte == b'\x55' :
            callback(start+i, _hex, f"PUSH ebp")
            _hex = bytearray()
        elif byte == b'\x56' :
            callback(start+i, _hex, f"PUSH esi")
            _hex = bytearray()
        elif byte == b'\x57' :
            callback(start+i, _hex, f"PUSH edi")
            _hex = bytearray()
        elif byte == b'\x59' :
            callback(start+i, _hex, f"POP ecx")
            _hex = bytearray()
        elif byte == b'\x5B' :
            callback(start+i, _hex, f"POP ebx")
            _hex = bytearray()
        elif byte == b'\x5C' :
            callback(start+i, _hex, f"POP esp")
            _hex = bytearray()
        elif byte == b'\x5D' :
            callback(start+i, _hex, f"POP ebp")
            _hex = bytearray()
        elif byte == b'\x5E' :
            callback(start+i, _hex, f"POP esi")
            _hex = bytearray()
        elif byte == b'\x5F' :
            callback(start+i, _hex, f"POP edi")
            _hex = bytearray()
        elif byte == b'\x66' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x3B' :
                byte = f.read(1)
                _hex += byte
                if byte == b'\xC8' :
                    callback(start+i, _hex, f"CMP cx ax")
                    _hex = bytearray()
                i += 1
            i += 1
        elif byte == b'\x68' :
            read = f.read(4)
            _hex += read
            number = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"PUSH {number}")
            _hex = bytearray()
            i += 4
        elif byte == b'\x6A' :
            read = f.read(1)
            _hex += read
            number = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"PUSH {number}")
            _hex = bytearray()
            i += 1
        elif byte == b'\x72' :
            read = f.read(1)
            _hex += read
            dist = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"JB [near] {dist} to {start+i+2+dist:08X}")
            _hex = bytearray()
            i += 1
        elif byte == b'\x74' :
            read = f.read(1)
            _hex += read
            dist = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"JE [near] {dist} to {start+i+2+dist:08X}")
            _hex = bytearray()
            i += 1
        elif byte == b'\x75' :
            read = f.read(1)
            _hex += read
            dist = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"JNE [near] {dist} to {start+i+2+dist:08X}")
            _hex = bytearray()
            i += 1
        elif byte == b'\x76' :
            read = f.read(1)
            _hex += read
            dist = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"JNA [near] {dist} to {start+i+2+dist:08X}")
            _hex = bytearray()
            i += 1
        elif byte == b'\x77' :
            read = f.read(1)
            _hex += read
            dist = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"JA [near] {dist} to {start+i+2+dist:08X}")
            _hex = bytearray()
            i += 1
        elif byte == b'\x7B' :
            read = f.read(1)
            _hex += read
            dist = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"JNP [near] {dist} to {start+i+2+dist:08X}")
            _hex = bytearray()
            i += 1
        elif byte == b'\x7C' :
            read = f.read(1)
            _hex += read
            dist = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"JL [near] {dist} to {start+i+2+dist:08X}")
            _hex = bytearray()
            i += 1
        elif byte == b'\x7D' :
            read = f.read(1)
            _hex += read
            dist = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"JNL [near] {dist} to {start+i+2+dist:08X}")
            _hex = bytearray()
            i += 1
        elif byte == b'\x7E' :
            read = f.read(1)
            _hex += read
            dist = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"JLE [near] {dist} to {start+i+2+dist:08X}")
            _hex = bytearray()
            i += 1
        elif byte == b'\x7F' :
            read = f.read(1)
            _hex += read
            dist = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"JG [near] {dist} to {start+i+2+dist:08X}")
            _hex = bytearray()
            i += 1
        elif byte == b'\x84' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\xC0' :
                callback(start+i, _hex, f"TEST al, al")
                _hex = bytearray()
            i += 1
        elif byte == b'\x85' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\xC0' :
                callback(start+i, _hex, f"TEST eax, eax")
                _hex = bytearray()
            if byte == b'\xC9' :
                callback(start+i, _hex, f"TEST ecx, ecx")
                _hex = bytearray()
            elif byte == b'\xD2' :
                callback(start+i, _hex, f"TEST edx, edx")
                _hex = bytearray()
            elif byte == b'\xDB' :
                callback(start+i, _hex, f"TEST ebx, ebx")
                _hex = bytearray()
            elif byte == b'\xF6' :
                callback(start+i, _hex, f"TEST esi, esi")
                _hex = bytearray()
            elif byte == b'\xFF' :
                callback(start+i, _hex, f"TEST edi, edi")
                _hex = bytearray()
            i += 1
        elif byte == b'\x88' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x07' :
                callback(start+i, _hex, f"MOV [edi], al")
                _hex = bytearray()
            elif byte == b'\x10' :
                callback(start+i, _hex, f"MOV [eax], dl")
                _hex = bytearray()
            elif byte == b'\x11' :
                callback(start+i, _hex, f"MOV [ecx], dl")
                _hex = bytearray()
            elif byte == b'\x18' :
                callback(start+i, _hex, f"MOV [eax], bl")
                _hex = bytearray()
            elif byte == b'\x1C' :
                byte = f.read(1)
                _hex += byte
                if byte == b'\x01' :
                    callback(start+i, _hex, f"MOV [ecx+eax], bl")
                    _hex = bytearray()
                i += 1
            elif byte == b'\x47' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"MOV [edi+{number}], al")
                _hex = bytearray()
                i += 1
            i += 1
        elif byte == b'\x89' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x06' :
                callback(start+i, _hex, f"MOV [esi], eax")
                _hex = bytearray()
            elif byte == b'\x30' :
                callback(start+i, _hex, f"MOV [eax], esi")
                _hex = bytearray()
            elif byte == b'\x44' :
                byte = f.read(1)
                _hex += byte
                if byte == b'\x8F' :
                    read = f.read(1)
                    _hex += read
                    number = int.from_bytes(read, byteorder='little', signed=True)
                    callback(start+i, _hex, f"MOV [edi+ecx*4+{number}], eax")
                    _hex = bytearray()
                    i += 1
                i += 1
            elif byte == b'\x45' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"MOV [ebp+{number}], eax")
                _hex = bytearray()
                i += 1
            i += 1
        elif byte == b'\x8A' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x06' :
                callback(start+i, _hex, f"MOV al, [esi]")
                _hex = bytearray()
            elif byte == b'\x10' :
                callback(start+i, _hex, f"MOV dl, [eax]")
                _hex = bytearray()
            elif byte == b'\x14' :
                byte = f.read(1)
                _hex += byte
                if byte == b'\x01' :
                    callback(start+i, _hex, f"MOV bl, [eax]")
                    _hex = bytearray()
                i += 1
            elif byte == b'\x18' :
                callback(start+i, _hex, f"MOV bl, [eax]")
                _hex = bytearray()
            elif byte == b'\x19' :
                callback(start+i, _hex, f"MOV bl, [ecx]")
                _hex = bytearray()
            elif byte == b'\x44' :
                byte = f.read(1)
                _hex += byte
                if byte == b'\x24' :
                    read = f.read(1)
                    _hex += read
                    number = int.from_bytes(read, byteorder='little', signed=True)
                    callback(start+i, _hex, f"MOV al, [esp+{number}]")
                    _hex = bytearray()
                    i += 1
                i += 1
            elif byte == b'\x46' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"MOV al, [esi+{number}]")
                _hex = bytearray()
                i += 1
            i += 1
        elif byte == b'\x8B' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x3D' :
                read = f.read(4)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"MOV edi, [{number}]")
                _hex = bytearray()
                i += 4
            elif byte == b'\x44' :
                byte = f.read(1)
                _hex += byte
                if byte == b'\x24' :
                    read = f.read(1)
                    _hex += read
                    number = int.from_bytes(read, byteorder='little', signed=True)
                    callback(start+i, _hex, f"MOV eax, [esp+{number}]")
                    _hex = bytearray()
                    i += 1
                elif byte == b'\x8E' :
                    read = f.read(1)
                    _hex += read
                    number = int.from_bytes(read, byteorder='little', signed=True)
                    callback(start+i, _hex, f"MOV eax, [esi+ecx*4+{number}]")
                    _hex = bytearray()
                    i += 1
                i += 1
            elif byte == b'\x45' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"MOV eax, [ebp+{number}]")
                _hex = bytearray()
                i += 1
            elif byte == b'\x4C' :
                byte = f.read(1)
                _hex += byte
                if byte == b'\x24' :
                    read = f.read(1)
                    _hex += read
                    number = int.from_bytes(read, byteorder='little', signed=True)
                    callback(start+i, _hex, f"MOV ecx, [esp+{number}]")
                    _hex = bytearray()
                    i += 1
                i += 1
            elif byte == b'\x4D' :
                read = f.read(1)
                _hex += read
                dist = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"MOV ecx, [ebp + {dist}]")
                _hex = bytearray()
                i += 1
            elif byte == b'\x54' :
                byte = f.read(1)
                _hex += byte
                if byte == b'\x24' :
                    read = f.read(1)
                    _hex += read
                    number = int.from_bytes(read, byteorder='little', signed=True)
                    callback(start+i, _hex, f"MOV edx, [esp+{number}]")
                    _hex = bytearray()
                    i += 1
                i += 1
            elif byte == b'\x55' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"MOV edx, [ebp+{number}]")
                _hex = bytearray()
                i += 1
            elif byte == b'\x5D' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"MOV ebx, [ebp+{number}]")
                _hex = bytearray()
                i += 1
            elif byte == b'\x75' :
                read = f.read(1)
                _hex += read
                dist = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"MOV esi, [ebp + {dist}]")
                _hex = bytearray()
                i += 1
            elif byte == b'\x7D' :
                read = f.read(1)
                _hex += read
                dist = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"MOV edi, [ebp + {dist}]")
                _hex = bytearray()
                i += 1
            elif byte == b'\xC1' :
                callback(start+i, _hex, f"MOV eax, ecx")
                _hex = bytearray()
            elif byte == b'\xC3' :
                callback(start+i, _hex, f"MOV eax, ebx")
                _hex = bytearray()
            elif byte == b'\xC6' :
                callback(start+i, _hex, f"MOV eax, esi")
                _hex = bytearray()
            elif byte == b'\xC7' :
                callback(start+i, _hex, f"MOV eax, edi")
                _hex = bytearray()
            elif byte == b'\xC8' :
                callback(start+i, _hex, f"MOV ecx, eax")
                _hex = bytearray()
            elif byte == b'\xCA' :
                callback(start+i, _hex, f"MOV ecx, edx")
                _hex = bytearray()
            elif byte == b'\xCB' :
                callback(start+i, _hex, f"MOV ecx, ebx")
                _hex = bytearray()
            elif byte == b'\xD1' :
                callback(start+i, _hex, f"MOV edx, ecx")
                _hex = bytearray()
            elif byte == b'\xD8' :
                callback(start+i, _hex, f"MOV ebx, eax")
                _hex = bytearray()
            elif byte == b'\xDA' :
                callback(start+i, _hex, f"MOV ebx, eax")
                _hex = bytearray()
            elif byte == b'\xDE' :
                callback(start+i, _hex, f"MOV ebx, esi")
                _hex = bytearray()
            elif byte == b'\xE5' :
                callback(start+i, _hex, f"MOV esp, ebp")
                _hex = bytearray()
            elif byte == b'\xEC' :
                callback(start+i, _hex, f"MOV ebx, edx")
                _hex = bytearray()
            elif byte == b'\xF0' :
                callback(start+i, _hex, f"MOV esi, eax")
                _hex = bytearray()
            elif byte == b'\xF1' :
                callback(start+i, _hex, f"MOV esi, ecx")
                _hex = bytearray()
            elif byte == b'\xF2' :
                callback(start+i, _hex, f"MOV esi, edx")
                _hex = bytearray()
            elif byte == b'\xF8' :
                callback(start+i, _hex, f"MOV edi, eax")
                _hex = bytearray()
            elif byte == b'\xF9' :
                callback(start+i, _hex, f"MOV edi, ecx")
                _hex = bytearray()
            elif byte == b'\xFF' :
                callback(start+i, _hex, f"nop <2>")
                _hex = bytearray()
            i += 1
        elif byte == b'\x8D' :
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
        elif byte == b'\x90' :
            callback(start+i, _hex, f"nop <1>")
            _hex = bytearray()
        elif byte == b'\x94' :
            callback(start+i, _hex, f"XCHG eax, esp")
            _hex = bytearray()
        elif byte == b'\x9C' :
            callback(start+i, _hex, f"PUSHFD")
            _hex = bytearray()
        elif byte == b'\xA1' :
            read = f.read(4)
            _hex += read
            number = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"MOV eax, [{number}]")
            _hex = bytearray()
            i += 4
        elif byte == b'\xA5' :
            callback(start+i, _hex, f"MOVSD")
            _hex = bytearray()
        elif byte == b'\xA8' :
            read = f.read(1)
            _hex += read
            number = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"TEST al, {number}")
            _hex = bytearray()
            i += 1
        elif byte == b'\xAB' :
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
        elif byte == b'\xCC' :
            callback(start+i, _hex, f"INT3")
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
        elif byte == b'\xE8' :
            read = f.read(4)
            _hex += read
            dist = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"CALL {dist} to {start+i+5+dist:08X}")
            _hex = bytearray()
            i += 4
        elif byte == b'\xE9' :
            read = f.read(4)
            _hex += read
            dist = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"JMP [called near?] {dist} to {start+i+5+dist:08X}")
            _hex = bytearray()
            i += 4
        elif byte == b'\xEB' :
            read = f.read(1)
            _hex += read
            dist = int.from_bytes(read, byteorder='little', signed=True)
            callback(start+i, _hex, f"JMP [near] {dist} to {start+i+5+dist:08X}")
            _hex = bytearray()
            i += 1
        elif byte == b'\xF3' :
            callback(start+i, _hex, f"REPE prefix")
            _hex = bytearray()
        elif byte == b'\xF4' :
            callback(start+i, _hex, f"HLT")
            _hex = bytearray()
        elif byte == b'\xF6' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\xC4' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"TEST ah, {number}")
                _hex = bytearray()
                i += 1
            i += 1
        elif byte == b'\xF7' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\xC7' :
                read = f.read(4)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"TEST edi, {number}")
                _hex = bytearray()
                i += 4
            elif byte == b'\xD9' :
                callback(start+i, _hex, f"NEG ecx")
                _hex = bytearray()
            i += 1
        elif byte == b'\xFC' :
            callback(start+i, _hex, f"CLD")
            _hex = bytearray()
        elif byte == b'\xFD' :
            callback(start+i, _hex, f"STD")
            _hex = bytearray()
        elif byte == b'\xFF' :
            byte = f.read(1)
            _hex += byte
            if byte == b'\x15' :
                read = f.read(4)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"CALL dword ptr [{number:08X}]")
                _hex = bytearray()
                i += 4
            elif byte == b'\x24' :
                byte = f.read(1)
                _hex += byte
                if byte == b'\x85' :
                    read = f.read(4)
                    _hex += read
                    offset = int.from_bytes(read, byteorder='little', signed=True)
                    callback(start+i, _hex, f"JMP dword ptr [eax*4+{offset:08X}]")
                    _hex = bytearray()
                    i += 4
                elif byte == b'\x8D' :
                    read = f.read(4)
                    _hex += read
                    offset = int.from_bytes(read, byteorder='little', signed=True)
                    callback(start+i, _hex, f"JMP dword ptr [ecx*4+{offset:08X}]")
                    _hex = bytearray()
                    i += 4
                elif byte == b'\x95' :
                    read = f.read(4)
                    _hex += read
                    offset = int.from_bytes(read, byteorder='little', signed=True)
                    callback(start+i, _hex, f"JMP dword ptr [edx*4+{offset:08X}]")
                    _hex = bytearray()
                    i += 4
                i += 1
            elif byte == b'\x35' :
                read = f.read(4)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"PUSH [{number}]")
                _hex = bytearray()
                i += 4
            elif byte == b'\x55' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"CALL dword ptr [ebp+{number}]")
                _hex = bytearray()
                i += 1
            elif byte == b'\x75' :
                read = f.read(1)
                _hex += read
                number = int.from_bytes(read, byteorder='little', signed=True)
                callback(start+i, _hex, f"PUSH [ebp+{number}]")
                _hex = bytearray()
                i += 1
            elif byte == b'\xD7' :
                callback(start+i, _hex, f"CALL edi")
                _hex = bytearray()
            i += 1
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
                file_disassembler.disassemble(EntryPoint, EntryPoint+3000)
        print()
        break
ModRM(b'\xC7')
