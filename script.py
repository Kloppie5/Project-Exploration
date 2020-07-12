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

class Disassembler_x86:

    def __init__ ( self, stream ) :
        self.stream = stream
        self.pos = 0
        self.parsetable = [
            self.PG_DS("ADD", 0x00),    # 00:00   00 0 00 0ds       | ADD
            self.PG_DS("ADD", 0x00),    # 00:01   ^
            self.PG_DS("ADD", 0x00),    # 00:10   ^
            self.PG_DS("ADD", 0x00),    # 00:11   ^
            self.PG_AO("ADD", 0x04),    # 04:0    00 0 00 10s       | ADD acc
            self.PG_AO("ADD", 0x04),    # 04:1    ^
            self.PG_U("PUSH ES"),       # 06      00 0 00 110       | PUSH ES
            self.PG_U("POP ES"),        # 07      00 0 00 111       | POP ES

            self.PG_DS("OR", 0x08),     # 08:00   00 0 01 0ds       | OR
            self.PG_DS("OR", 0x08),     # 08:01   ^
            self.PG_DS("OR", 0x08),     # 08:10   ^
            self.PG_DS("OR", 0x08),     # 08:11   ^              
            self.PG_AO("OR", 0x0C),     # 0C:0    00 0 01 10s       | OR acc
            self.PG_AO("OR", 0x0C),     # 0C:1    ^
            self.PG_U("PUSH CS"),       # 0E      00 0 01 110       | PUSH CS
            self.MODE_SWITCH,           # 0F      00 0 01 111       | Instruction set switch
            
            self.PG_DS("ADC", 0x10),    # 10:00   00 0 10 0ds       | ADC
            self.PG_DS("ADC", 0x10),    # 10:01   ^
            self.PG_DS("ADC", 0x10),    # 10:10   ^
            self.PG_DS("ADC", 0x10),    # 10:11   ^
            self.PG_AO("ADC", 0x14),    # 14:0    00 0 10 10s       | ADC acc
            self.PG_AO("ADC", 0x14),    # 14:1    ^
            self.PG_U("PUSH SS"),       # 16      00 0 10 110       | PUSH SS
            self.PG_U("POP SS"),        # 17      00 0 10 111       | POP SS

            self.PG_DS("SBB", 0x18),    # 18:00   00 0 11 0ds       | SBB
            self.PG_DS("SBB", 0x18),    # 18:01   ^
            self.PG_DS("SBB", 0x18),    # 18:10   ^
            self.PG_DS("SBB", 0x18),    # 18:11   ^
            self.PG_AO("SBB", 0x1C),    # 1C:0    00 0 11 10s       | SBB acc
            self.PG_AO("SBB", 0x1C),    # 1C:1    ^
            self.PG_U("PUSH DS"),       # 1E      00 0 11 110       | PUSH DS
            self.PG_U("POP DS"),        # 1F      00 0 11 111       | POP DS

            self.PG_DS("AND", 0x20),    # 20:00   00 1 00 0ds       | AND
            self.PG_DS("AND", 0x20),    # 20:01   ^
            self.PG_DS("AND", 0x20),    # 20:10   ^
            self.PG_DS("AND", 0x20),    # 20:11   ^
            self.PG_AO("AND", 0x24),    # 24:0    00 1 00 10s       | AND acc
            self.PG_AO("AND", 0x24),    # 24:1    ^
            self.PG_SO("ES"),           # 26      00 1 00 110       | ES override
            self.PG_U("DAA AL"),        # 27      00 1 00 111       | DAA AL

            self.PG_DS("SUB", 0x28),    # 28:00   00 1 01 0ds       | SUB
            self.PG_DS("SUB", 0x28),    # 28:01   ^
            self.PG_DS("SUB", 0x28),    # 28:10   ^
            self.PG_DS("SUB", 0x28),    # 28:11   ^
            self.PG_AO("SUB", 0x2C),    # 2C:0    00 1 01 10s       | SUB acc
            self.PG_AO("SUB", 0x2C),    # 2C:1    ^
            self.PG_SO("CS"),           # 2E      00 1 01 110       | CS override
            self.PG_U("DAS AL"),        # 2F      00 1 01 111       | DAS AL

            self.PG_DS("XOR", 0x30),    # 30:00   00 1 10 0ds       | XOR
            self.PG_DS("XOR", 0x30),    # 30:01   ^
            self.PG_DS("XOR", 0x30),    # 30:10   ^
            self.PG_DS("XOR", 0x30),    # 30:11   ^
            self.PG_AO("XOR", 0x34),    # 34:0    00 1 10 10s       | XOR acc
            self.PG_AO("XOR", 0x34),    # 34:1    ^
            self.PG_SO("SS"),           # 36      00 1 10 110       | SS override
            self.PG_U("AAA AL"),        # 37      00 1 10 111       | AAA AL

            self.PG_DS("CMP", 0x38),    # 38:00   00 1 11 0ds       | CMP
            self.PG_DS("CMP", 0x38),    # 38:01   ^
            self.PG_DS("CMP", 0x38),    # 38:10   ^
            self.PG_DS("CMP", 0x38),    # 38:11   ^
            self.PG_AO("CMP", 0x3C),    # 3C:0    00 1 11 10s       | CMP acc
            self.PG_AO("CMP", 0x3C),    # 3C:1    ^
            self.PG_SO("DS"),           # 3E      00 1 11 110       | DS override
            self.PG_U("AAS AL"),        # 3F      00 1 11 111       | AAS AL

            self.PG_RO("INC", 0x40),    # 40:0    010 00 reg        | INC reg
            self.PG_RO("INC", 0x40),    # 40:1    ^
            self.PG_RO("INC", 0x40),    # 40:2    ^
            self.PG_RO("INC", 0x40),    # 40:3    ^
            self.PG_RO("INC", 0x40),    # 40:4    ^
            self.PG_RO("INC", 0x40),    # 40:5    ^
            self.PG_RO("INC", 0x40),    # 40:6    ^
            self.PG_RO("INC", 0x40),    # 40:7    ^

            self.PG_RO("DEC", 0x48),    # 48:0    010 01 reg        | DEC reg
            self.PG_RO("DEC", 0x48),    # 48:1    ^
            self.PG_RO("DEC", 0x48),    # 48:2    ^
            self.PG_RO("DEC", 0x48),    # 48:3    ^
            self.PG_RO("DEC", 0x48),    # 48:4    ^
            self.PG_RO("DEC", 0x48),    # 48:5    ^
            self.PG_RO("DEC", 0x48),    # 48:6    ^
            self.PG_RO("DEC", 0x48),    # 48:7    ^

            self.PG_RO("PUSH", 0x50),   # 50:0    010 10 reg        | PUSH reg
            self.PG_RO("PUSH", 0x50),   # 50:1    ^
            self.PG_RO("PUSH", 0x50),   # 50:2    ^
            self.PG_RO("PUSH", 0x50),   # 50:3    ^
            self.PG_RO("PUSH", 0x50),   # 50:4    ^
            self.PG_RO("PUSH", 0x50),   # 50:5    ^
            self.PG_RO("PUSH", 0x50),   # 50:6    ^
            self.PG_RO("PUSH", 0x50),   # 50:7    ^
            
            self.PG_RO("POP", 0x58),    # 58:0    010 01 reg        | POP reg
            self.PG_RO("POP", 0x58),    # 58:1    ^
            self.PG_RO("POP", 0x58),    # 58:2    ^
            self.PG_RO("POP", 0x58),    # 58:3    ^
            self.PG_RO("POP", 0x58),    # 58:4    ^
            self.PG_RO("POP", 0x58),    # 58:5    ^
            self.PG_RO("POP", 0x58),    # 58:6    ^
            self.PG_RO("POP", 0x58),    # 58:7    ^

            self.UNKNOWN_OPCODE,        # 60      011000 00         | PUSHA
            self.UNKNOWN_OPCODE,        # 61      011000 01         | POPA
            self.UNKNOWN_OPCODE,        # 62      011000 10         | BOUND
            self.UNKNOWN_OPCODE,        # 63      011000 11         | ARPL

            self.PG_SO("FS"),           # 64      011001 00         | FS override
            self.PG_SO("GS"),           # 65      011001 01         | GS override
            self.PREFIX_66,             # 66      011001 10         | Operand-size override
            self.UNKNOWN_OPCODE,        # 67      011001 11         | Address-size override
            
            self.PUSH_CONST,            # 68:~s-  011010 s0         | PUSH const
            self.UNKNOWN_OPCODE,        # 69:~s-  011010 s1         | IMUL const
            self.PUSH_CONST,            # 68:~s-  011010 s0         | PUSH const
            self.UNKNOWN_OPCODE,        # 69:~s-  011010 s1         | IMUL const
            
            self.UNKNOWN_OPCODE,        # 6C:s    011011 0 s        | INS
            self.UNKNOWN_OPCODE,        # 6C:s    011011 0 s        | INS
            self.UNKNOWN_OPCODE,        # 6E:s    011011 1 s        | OUTS
            self.UNKNOWN_OPCODE,        # 6E:s    011011 1 s        | OUTS

            self.CJMP8,                 # 70      0111 0000         | JO          (OF=1)
            self.CJMP8,                 # 71      0111 0001         | JNO         (OF=0)
            self.CJMP8,                 # 72      0111 0010         | JB JNAE JC  (CF=1)
            self.CJMP8,                 # 73      0111 0011         | JNB JAE JNC (CF=0)
            self.CJMP8,                 # 74      0111 0100         | JZ JE       (ZF=1)
            self.CJMP8,                 # 75      0111 0101         | JNZ JNE     (ZF=0)
            self.CJMP8,                 # 76      0111 0110         | JBE JNA     (CF=1 OR ZF=1)
            self.CJMP8,                 # 77      0111 0111         | JNBE JA     (CF=0 AND ZF=0)
            self.CJMP8,                 # 78      0111 1000         | JS          (SF=1)
            self.CJMP8,                 # 79      0111 1001         | JNS         (SF=0)
            self.CJMP8,                 # 7A      0111 1010         | JP JPE      (PF=1)
            self.CJMP8,                 # 7B      0111 1011         | JNP JPO     (PF=0)
            self.CJMP8,                 # 7C      0111 1100         | JL JNGE     (SF!=OF)
            self.CJMP8,                 # 7D      0111 1101         | JNL JGE     (SF=OF)
            self.CJMP8,                 # 7E      0111 1110         | JLE JNG     ((ZF=1) OR (SF!=OF))
            self.CJMP8,                 # 7F      0111 1111         | JNLE JG     ((ZF=0) AND (SF=OF))

            # 80:xs/0 100000 xs r000    | ADD const
            # 80:xs/1 100000 xs r001    | OR const
            # 80:xs/2 100000 xs r010    | ADC const
            # 80:xs/3 100000 xs r011    | SBB const
            # 80:xs/4 100000 xs r100    | AND const
            # 80:xs/5 100000 xs r101    | SUB const
            # 80:xs/6 100000 xs r110    | XOR const
            # 80:xs/7 100000 xs r111    | CMP const
            self.IMMEDIATE,             # 80
            self.IMMEDIATE,             # 81
            self.IMMEDIATE,             # 82
            self.IMMEDIATE,             # 83

            self.PG_S("TEST", 0x84),    # 84:0    1000010 s         | TEST
            self.PG_S("TEST", 0x84),    # 84:1    ^
            self.PG_S("XCHG", 0x86),    # 86:s    1000011 s         | XCHG
            self.PG_S("XCHG", 0x86),    # 86:1    ^

            self.PG_DS("MOV", 0x88),    # 88:00   100010 ds         | MOV
            self.PG_DS("MOV", 0x88),    # 88:01   ^
            self.PG_DS("MOV", 0x88),    # 88:10   ^
            self.PG_DS("MOV", 0x88),    # 88:11   ^

            self.UNKNOWN_OPCODE,        # 8C:d-   1000 11d0         | MOV sreg
            self.UNKNOWN_OPCODE,        # 8D      1000 1101         | LEA
            self.UNKNOWN_OPCODE,        # 8C:d-   1000 11d0         | MOV sreg
            self.UNKNOWN_OPCODE,        # 8F/0    1000 1111 r000    | POP reg

            self.PG_RO("XCHG eax,", 0x90),  # 90:0    10010 reg         | XCHG reg
            self.PG_RO("XCHG eax,", 0x90),  # 90:1    ^
            self.PG_RO("XCHG eax,", 0x90),  # 90:2    ^
            self.PG_RO("XCHG eax,", 0x90),  # 90:3    ^
            self.PG_RO("XCHG eax,", 0x90),  # 90:4    ^
            self.PG_RO("XCHG eax,", 0x90),  # 90:5    ^
            self.PG_RO("XCHG eax,", 0x90),  # 90:6    ^
            self.PG_RO("XCHG eax,", 0x90),  # 90:7    ^

            self.UNKNOWN_OPCODE,        # 98 CBW
            self.UNKNOWN_OPCODE,        # 99 CWD
            self.UNKNOWN_OPCODE,        # 9A CALLF
            self.UNKNOWN_OPCODE,        # 9B WAIT
            self.PG_U("PUSHF"),         # 9C PUSHF
            self.UNKNOWN_OPCODE,        # 9D POPF
            self.UNKNOWN_OPCODE,        # 9E SAHF
            self.UNKNOWN_OPCODE,        # 9F LAHF

                # A0:ds   1010 00ds       | acc MOV offset
                    self.UNKNOWN_OPCODE,        # A0
                    self.UNKNOWN_OPCODE,        # A1
                    self.UNKNOWN_OPCODE,        # A2
                    self.UNKNOWN_OPCODE,        # A3
                # A4:s    1010 010s       | MOVS
                    self.MOVS,        # A4
                    self.MOVS,        # A5
                # A6:s    1010 011s       | CMPS
                    self.UNKNOWN_OPCODE,        # A6
                    self.UNKNOWN_OPCODE,        # A7
                # A8:s    1010 100s       | acc TEST
                    self.TEST_ACC,        # A8
                    self.TEST_ACC,        # A9
                # AA:s    1010 101s       | STOS
                    self.UNKNOWN_OPCODE,        # AA
                    self.UNKNOWN_OPCODE,        # AB
                # AC:s    1010 110s       | LODS
                    self.UNKNOWN_OPCODE,        # AC
                    self.UNKNOWN_OPCODE,        # AD
                # AE:s    1010 111s       | SCAS
                    self.UNKNOWN_OPCODE,        # AE
                    self.UNKNOWN_OPCODE,        # AF

                # Bs:reg  1011 s reg      | MOV reg
                    self.MOV_CONST,        # B0
                    self.MOV_CONST,        # B1
                    self.MOV_CONST,        # B2
                    self.MOV_CONST,        # B3
                    self.MOV_CONST,        # B4
                    self.MOV_CONST,        # B5
                    self.MOV_CONST,        # B6
                    self.MOV_CONST,        # B7
                    self.MOV_CONST,        # B8
                    self.MOV_CONST,        # B9
                    self.MOV_CONST,        # BA
                    self.MOV_CONST,        # BB
                    self.MOV_CONST,        # BC
                    self.MOV_CONST,        # BD
                    self.MOV_CONST,        # BE
                    self.MOV_CONST,        # BF

                # C0:s/0  1100 000s r000  | ROL
                # C0:s/1  1100 000s r001  | ROR
                # C0:s/2  1100 000s r010  | RCL
                # C0:s/3  1100 000s r011  | RCR
                # C0:s/4  1100 000s r100  | SHL
                # C0:s/5  1100 000s r101  | SHR
                # C0:s/6  1100 000s r110  | SAL
                # C0:s/7  1100 000s r111  | SAR
                    self.BITMOVE,        # C0
                    self.BITMOVE,        # C1

                # C2 RET var
                    self.UNKNOWN_OPCODE,        # C2
                # C3 RET
                    self.UNKNOWN_OPCODE,        # C3
                # C4 LES
                    self.UNKNOWN_OPCODE,        # C4
                # C5 LDS
                    self.UNKNOWN_OPCODE,        # C5

                # C6:s/0  1100 011s r000  | MOV const
                    self.UNKNOWN_OPCODE,        # C6
                    self.UNKNOWN_OPCODE,        # C7

                # C8 ENTER
                    self.UNKNOWN_OPCODE,        # C8
                # C9 LEAVE
                    self.UNKNOWN_OPCODE,        # C9

                # CA RETF var
                    self.UNKNOWN_OPCODE,        # CA
                # CB RETF
                    self.UNKNOWN_OPCODE,        # CB
                # CC INT3
                    self.INT3,                  # CC
                # CD INT
                    self.UNKNOWN_OPCODE,        # CD
                # CE INTO
                    self.UNKNOWN_OPCODE,        # CE
                # CF IRET
                    self.UNKNOWN_OPCODE,        # CF
                
                # D0:xs/0 1101 00xs r000  | ROL 1/x
                # D0:xs/1 1101 00xs r001  | ROR 1/x
                # D0:xs/2 1101 00xs r010  | RCL 1/x
                # D0:xs/3 1101 00xs r011  | RCR 1/x
                # D0:xs/4 1101 00xs r100  | SHL 1/x
                # D0:xs/5 1101 00xs r101  | SHR 1/x
                # D0:xs/6 1101 00xs r110  | SAL 1/x
                # D0:xs/7 1101 00xs r111  | SAR 1/x
                    self.UNKNOWN_OPCODE,        # D0
                    self.UNKNOWN_OPCODE,        # D1
                    self.UNKNOWN_OPCODE,        # D2
                    self.UNKNOWN_OPCODE,        # D3

                # D4 AMX
                    self.UNKNOWN_OPCODE,        # D4
                # D5 ADX
                    self.UNKNOWN_OPCODE,        # D5
                # D6 SALC
                    self.UNKNOWN_OPCODE,        # D6
                # D7 XLAT
                    self.UNKNOWN_OPCODE,        # D7
                # D8/0 FADD
                # D8/1 FMUL
                # D8/2 FCOM
                # D8/3 FCOMP
                # D8/4 FSUB
                # D8/5 FSUBR
                # D8/6 FDIV
                # D8/7 FDIVR
                    self.UNKNOWN_OPCODE,        # D8

                # D9/0 FLD
                # D9/1 FXCH
                # D9/2 FST
                # D9/3 FSTP
                # D9/4 FLDENV
                # D9/5 FLDCW
                # D9/6 FNSTENV
                # D9/7 FSTCW
                    self.UNKNOWN_OPCODE,        # D9

                self.UNKNOWN_OPCODE,        # DA
                self.UNKNOWN_OPCODE,        # DB
                self.UNKNOWN_OPCODE,        # DC
                self.UNKNOWN_OPCODE,        # DD
                self.UNKNOWN_OPCODE,        # DE
                self.UNKNOWN_OPCODE,        # DF

                self.UNKNOWN_OPCODE,        # E0
                self.UNKNOWN_OPCODE,        # E1
                self.UNKNOWN_OPCODE,        # E2
                self.UNKNOWN_OPCODE,        # E3
                self.UNKNOWN_OPCODE,        # E4
                self.UNKNOWN_OPCODE,        # E5
                self.UNKNOWN_OPCODE,        # E6
                self.UNKNOWN_OPCODE,        # E7
                # E8 Call
                    self.CALL,          # E8
                    self.JMP,           # E9
                self.UNKNOWN_OPCODE,        # EA
                self.UNKNOWN_OPCODE,        # EB
                self.UNKNOWN_OPCODE,        # EC
                self.UNKNOWN_OPCODE,        # ED
                self.UNKNOWN_OPCODE,        # EE
                self.UNKNOWN_OPCODE,        # EF

                self.UNKNOWN_OPCODE,        # F0
                self.UNKNOWN_OPCODE,        # F1
                self.UNKNOWN_OPCODE,        # F2
                # F3      11110011        | REPE
                    self.REPE,        # F3
                self.UNKNOWN_OPCODE,        # F4
                self.UNKNOWN_OPCODE,        # F5

                # F6:s/0  1111 011s r000  | TEST
                # F6:s/2  1111 011s r010  | NOT
                # F6:s/3  1111 011s r011  | NEG
                # F6:s/4  1111 011s r100  | MUL
                # F6:s/5  1111 011s r101  | IMUL
                # F6:s/6  1111 011s r110  | DIV
                # F6:s/7  1111 011s r111  | IDIV
                    self.OP_F6s,        # F6
                    self.OP_F6s,        # F7
                self.UNKNOWN_OPCODE,        # F8
                self.UNKNOWN_OPCODE,        # F9
                self.UNKNOWN_OPCODE,        # FA
                self.UNKNOWN_OPCODE,        # FB
                self.UNKNOWN_OPCODE,        # FC
                self.UNKNOWN_OPCODE,        # FD

                # FE:s/0  1111 111s r000  | INC mem
                # FE:s/1  1111 111s r001  | DEC mem
                    self.OP_FEs,        # FE
                # FF/4    1111 1111 r100  | JMP reg
                # FF/5    1111 1111 r101  | JMP mem
                # FF/6    1111 1111 r110  | PUSH reg
                    self.OP_FEs,        # FF
        ]
        self.parsetable_0F = [
            self.UNKNOWN_OPCODE,        # 00
            self.UNKNOWN_OPCODE,        # 01
            self.UNKNOWN_OPCODE,        # 02
            self.UNKNOWN_OPCODE,        # 03
            self.UNKNOWN_OPCODE,        # 04
            self.UNKNOWN_OPCODE,        # 05
            self.UNKNOWN_OPCODE,        # 06
            self.UNKNOWN_OPCODE,        # 07
            self.UNKNOWN_OPCODE,        # 08
            self.UNKNOWN_OPCODE,        # 09
            self.UNKNOWN_OPCODE,        # 0A
            self.UNKNOWN_OPCODE,        # 0B
            self.UNKNOWN_OPCODE,        # 0C
            self.UNKNOWN_OPCODE,        # 0D
            self.UNKNOWN_OPCODE,        # 0E
            self.UNKNOWN_OPCODE,        # 0F
            self.UNKNOWN_OPCODE,        # 10
            self.UNKNOWN_OPCODE,        # 11
            self.UNKNOWN_OPCODE,        # 12
            self.UNKNOWN_OPCODE,        # 13
            self.UNKNOWN_OPCODE,        # 14
            self.UNKNOWN_OPCODE,        # 15
            self.UNKNOWN_OPCODE,        # 16
            self.UNKNOWN_OPCODE,        # 17
            self.UNKNOWN_OPCODE,        # 18
            self.UNKNOWN_OPCODE,        # 19
            self.UNKNOWN_OPCODE,        # 1A
            self.UNKNOWN_OPCODE,        # 1B
            self.UNKNOWN_OPCODE,        # 1C
            self.UNKNOWN_OPCODE,        # 1D
            self.UNKNOWN_OPCODE,        # 1E
            self.UNKNOWN_OPCODE,        # 1F
            self.UNKNOWN_OPCODE,        # 20
            self.UNKNOWN_OPCODE,        # 21
            self.UNKNOWN_OPCODE,        # 22
            self.UNKNOWN_OPCODE,        # 23
            self.UNKNOWN_OPCODE,        # 24
            self.UNKNOWN_OPCODE,        # 25
            self.UNKNOWN_OPCODE,        # 26
            self.UNKNOWN_OPCODE,        # 27
            self.UNKNOWN_OPCODE,        # 28
            self.UNKNOWN_OPCODE,        # 29
            self.UNKNOWN_OPCODE,        # 2A
            self.UNKNOWN_OPCODE,        # 2B
            self.UNKNOWN_OPCODE,        # 2C
            self.UNKNOWN_OPCODE,        # 2D
            self.UNKNOWN_OPCODE,        # 2E
            self.UNKNOWN_OPCODE,        # 2F
            self.UNKNOWN_OPCODE,        # 30
            self.UNKNOWN_OPCODE,        # 31
            self.UNKNOWN_OPCODE,        # 32
            self.UNKNOWN_OPCODE,        # 33
            self.UNKNOWN_OPCODE,        # 34
            self.UNKNOWN_OPCODE,        # 35
            self.UNKNOWN_OPCODE,        # 36
            self.UNKNOWN_OPCODE,        # 37
            self.MODE_SWITCH,        # 38
            self.UNKNOWN_OPCODE,        # 39
            self.MODE_SWITCH,        # 3A
            self.UNKNOWN_OPCODE,        # 3B
            self.UNKNOWN_OPCODE,        # 3C
            self.UNKNOWN_OPCODE,        # 3D
            self.UNKNOWN_OPCODE,        # 3E
            self.UNKNOWN_OPCODE,        # 3F
            self.UNKNOWN_OPCODE,        # 40
            self.UNKNOWN_OPCODE,        # 41
            self.UNKNOWN_OPCODE,        # 42
            self.UNKNOWN_OPCODE,        # 43
            self.UNKNOWN_OPCODE,        # 44
            self.UNKNOWN_OPCODE,        # 45
            self.UNKNOWN_OPCODE,        # 46
            self.UNKNOWN_OPCODE,        # 47
            self.UNKNOWN_OPCODE,        # 48
            self.UNKNOWN_OPCODE,        # 49
            self.UNKNOWN_OPCODE,        # 4A
            self.UNKNOWN_OPCODE,        # 4B
            self.UNKNOWN_OPCODE,        # 4C
            self.UNKNOWN_OPCODE,        # 4D
            self.UNKNOWN_OPCODE,        # 4E
            self.UNKNOWN_OPCODE,        # 4F
            self.UNKNOWN_OPCODE,        # 50
            self.UNKNOWN_OPCODE,        # 51
            self.UNKNOWN_OPCODE,        # 52
            self.UNKNOWN_OPCODE,        # 53
            self.UNKNOWN_OPCODE,        # 54
            self.UNKNOWN_OPCODE,        # 55
            self.UNKNOWN_OPCODE,        # 56
            self.UNKNOWN_OPCODE,        # 57
            self.UNKNOWN_OPCODE,        # 58
            self.UNKNOWN_OPCODE,        # 59
            self.UNKNOWN_OPCODE,        # 5A
            self.UNKNOWN_OPCODE,        # 5B
            self.UNKNOWN_OPCODE,        # 5C
            self.UNKNOWN_OPCODE,        # 5D
            self.UNKNOWN_OPCODE,        # 5E
            self.UNKNOWN_OPCODE,        # 5F
            self.UNKNOWN_OPCODE,        # 60
            self.UNKNOWN_OPCODE,        # 61
            self.UNKNOWN_OPCODE,        # 62
            self.UNKNOWN_OPCODE,        # 63
            self.UNKNOWN_OPCODE,        # 64
            self.UNKNOWN_OPCODE,        # 65
            self.UNKNOWN_OPCODE,        # 66
            self.UNKNOWN_OPCODE,        # 67
            self.UNKNOWN_OPCODE,        # 68
            self.UNKNOWN_OPCODE,        # 69
            self.UNKNOWN_OPCODE,        # 6A
            self.UNKNOWN_OPCODE,        # 6B
            self.UNKNOWN_OPCODE,        # 6C
            self.UNKNOWN_OPCODE,        # 6D
            self.UNKNOWN_OPCODE,        # 6E
            self.UNKNOWN_OPCODE,        # 6F
            self.UNKNOWN_OPCODE,        # 70
            self.UNKNOWN_OPCODE,        # 71
            self.UNKNOWN_OPCODE,        # 72
            self.UNKNOWN_OPCODE,        # 73
            self.UNKNOWN_OPCODE,        # 74
            self.UNKNOWN_OPCODE,        # 75
            self.UNKNOWN_OPCODE,        # 76
            self.UNKNOWN_OPCODE,        # 77
            self.UNKNOWN_OPCODE,        # 7C
            self.UNKNOWN_OPCODE,        # 7D
            self.UNKNOWN_OPCODE,        # 7E
            self.UNKNOWN_OPCODE,        # 7F
            # 80-8F: Jumps
                # 80      1000 0000         | JO          (OF=1)
                    self.CJMP32,                # 80
                # 81      1000 0001         | JNO         (OF=0)
                    self.CJMP32,                # 81
                # 82      1000 0010         | JB JNAE JC  (CF=1)
                    self.CJMP32,                # 82
                # 83      1000 0011         | JNB JAE JNC (CF=0)
                    self.CJMP32,                # 83
                # 84      1000 0100         | JZ JE       (ZF=1)
                    self.CJMP32,                # 84
                # 85      1000 0101         | JNZ JNE     (ZF=0)
                    self.CJMP32,                # 85
                # 86      1000 0110         | JBE JNA     (CF=1 OR ZF=1)
                    self.CJMP32,                # 86
                # 87      1000 0111         | JNBE JA     (CF=0 AND ZF=0)
                    self.CJMP32,                # 87
                # 88      1000 1000         | JS          (SF=1)
                    self.CJMP32,                # 88
                # 89      1000 1001         | JNS         (SF=0)
                    self.CJMP32,                # 89
                # 8A      1000 1010         | JP JPE      (PF=1)
                    self.CJMP32,                # 8A
                # 8B      1000 1011         | JNP JPO     (PF=0)
                    self.CJMP32,                # 8B
                # 8C      1000 1100         | JL JNGE     (SF!=OF)
                    self.CJMP32,                # 8C
                # 8D      1000 1101         | JNL JGE     (SF=OF)
                    self.CJMP32,                # 8D
                # 8E      1000 1110         | JLE JNG     ((ZF=1) OR (SF!=OF))
                    self.CJMP32,                # 8E
                # 8F      1000 1111         | JNLE JG     ((ZF=0) AND (SF=OF))
                    self.CJMP32,                # 8F
            self.UNKNOWN_OPCODE,        # 90
            self.UNKNOWN_OPCODE,        # 91
            self.UNKNOWN_OPCODE,        # 92
            self.UNKNOWN_OPCODE,        # 93
            self.UNKNOWN_OPCODE,        # 94
            self.UNKNOWN_OPCODE,        # 95
            self.UNKNOWN_OPCODE,        # 96
            self.UNKNOWN_OPCODE,        # 97
            self.UNKNOWN_OPCODE,        # 98
            self.UNKNOWN_OPCODE,        # 99
            self.UNKNOWN_OPCODE,        # 9A
            self.UNKNOWN_OPCODE,        # 9B
            self.UNKNOWN_OPCODE,        # 9C
            self.UNKNOWN_OPCODE,        # 9D
            self.UNKNOWN_OPCODE,        # 9E
            self.UNKNOWN_OPCODE,        # 9F
            self.UNKNOWN_OPCODE,        # A0
            self.UNKNOWN_OPCODE,        # A1
            self.UNKNOWN_OPCODE,        # A2
            self.UNKNOWN_OPCODE,        # A3
            self.UNKNOWN_OPCODE,        # A4
            self.UNKNOWN_OPCODE,        # A5
            self.UNKNOWN_OPCODE,        # A6
            self.UNKNOWN_OPCODE,        # A7
            self.UNKNOWN_OPCODE,        # A8
            self.UNKNOWN_OPCODE,        # A9
            self.UNKNOWN_OPCODE,        # AA
            self.UNKNOWN_OPCODE,        # AB
            self.UNKNOWN_OPCODE,        # AC
            self.UNKNOWN_OPCODE,        # AD
            self.UNKNOWN_OPCODE,        # AE
            self.UNKNOWN_OPCODE,        # AF
            self.UNKNOWN_OPCODE,        # B0
            self.UNKNOWN_OPCODE,        # B1
            self.UNKNOWN_OPCODE,        # B2
            self.UNKNOWN_OPCODE,        # B3
            self.UNKNOWN_OPCODE,        # B4
            self.UNKNOWN_OPCODE,        # B5
            self.UNKNOWN_OPCODE,        # B6
            self.UNKNOWN_OPCODE,        # B7
            self.UNKNOWN_OPCODE,        # B8
            self.UNKNOWN_OPCODE,        # B9
            self.UNKNOWN_OPCODE,        # BA
            self.UNKNOWN_OPCODE,        # BB
            self.UNKNOWN_OPCODE,        # BC
            self.UNKNOWN_OPCODE,        # BD
            self.UNKNOWN_OPCODE,        # BE
            self.UNKNOWN_OPCODE,        # BF
            self.UNKNOWN_OPCODE,        # C0
            self.UNKNOWN_OPCODE,        # C1
            self.UNKNOWN_OPCODE,        # C2
            self.UNKNOWN_OPCODE,        # C3
            self.UNKNOWN_OPCODE,        # C4
            self.UNKNOWN_OPCODE,        # C5
            self.UNKNOWN_OPCODE,        # C6
            self.UNKNOWN_OPCODE,        # C7
            self.UNKNOWN_OPCODE,        # C8
            self.UNKNOWN_OPCODE,        # C9
            self.UNKNOWN_OPCODE,        # CA
            self.UNKNOWN_OPCODE,        # CB
            self.UNKNOWN_OPCODE,        # CC
            self.UNKNOWN_OPCODE,        # CD
            self.UNKNOWN_OPCODE,        # CE
            self.UNKNOWN_OPCODE,        # CF
            self.UNKNOWN_OPCODE,        # D0
            self.UNKNOWN_OPCODE,        # D1
            self.UNKNOWN_OPCODE,        # D2
            self.UNKNOWN_OPCODE,        # D3
            self.UNKNOWN_OPCODE,        # D4
            self.UNKNOWN_OPCODE,        # D5
            self.UNKNOWN_OPCODE,        # D6
            self.UNKNOWN_OPCODE,        # D7
            self.UNKNOWN_OPCODE,        # D8
            self.UNKNOWN_OPCODE,        # D9
            self.UNKNOWN_OPCODE,        # DA
            self.UNKNOWN_OPCODE,        # DB
            self.UNKNOWN_OPCODE,        # DC
            self.UNKNOWN_OPCODE,        # DD
            self.UNKNOWN_OPCODE,        # DE
            self.UNKNOWN_OPCODE,        # DF
            self.UNKNOWN_OPCODE,        # E0
            self.UNKNOWN_OPCODE,        # E1
            self.UNKNOWN_OPCODE,        # E2
            self.UNKNOWN_OPCODE,        # E3
            self.UNKNOWN_OPCODE,        # E4
            self.UNKNOWN_OPCODE,        # E5
            self.UNKNOWN_OPCODE,        # E6
            self.UNKNOWN_OPCODE,        # E7
            self.UNKNOWN_OPCODE,        # E8
            self.UNKNOWN_OPCODE,        # E9
            self.UNKNOWN_OPCODE,        # EA
            self.UNKNOWN_OPCODE,        # EB
            self.UNKNOWN_OPCODE,        # EC
            self.UNKNOWN_OPCODE,        # ED
            self.UNKNOWN_OPCODE,        # EE
            self.UNKNOWN_OPCODE,        # EF
            self.UNKNOWN_OPCODE,        # F0
            self.UNKNOWN_OPCODE,        # F1
            self.UNKNOWN_OPCODE,        # F2
            self.UNKNOWN_OPCODE,        # F3
            self.UNKNOWN_OPCODE,        # F4
            self.UNKNOWN_OPCODE,        # F5
            self.UNKNOWN_OPCODE,        # F6
            self.UNKNOWN_OPCODE,        # F7
            self.UNKNOWN_OPCODE,        # F8
            self.UNKNOWN_OPCODE,        # F9
            self.UNKNOWN_OPCODE,        # FA
            self.UNKNOWN_OPCODE,        # FB
            self.UNKNOWN_OPCODE,        # FC
            self.UNKNOWN_OPCODE,        # FD
            self.UNKNOWN_OPCODE,        # FE
            self.UNKNOWN_OPCODE,        # FF
        ]
        self.parsetable_0F38 = [
            self.UNKNOWN_OPCODE,        # 00
            self.UNKNOWN_OPCODE,        # 01
            self.UNKNOWN_OPCODE,        # 02
            self.UNKNOWN_OPCODE,        # 03
            self.UNKNOWN_OPCODE,        # 04
            self.UNKNOWN_OPCODE,        # 05
            self.UNKNOWN_OPCODE,        # 06
            self.UNKNOWN_OPCODE,        # 07
            self.UNKNOWN_OPCODE,        # 08
            self.UNKNOWN_OPCODE,        # 09
            self.UNKNOWN_OPCODE,        # 0A
            self.UNKNOWN_OPCODE,        # 0B
            self.UNKNOWN_OPCODE,        # 0C
            self.UNKNOWN_OPCODE,        # 0D
            self.UNKNOWN_OPCODE,        # 0E
            self.UNKNOWN_OPCODE,        # 0F
            self.UNKNOWN_OPCODE,        # 10
            self.UNKNOWN_OPCODE,        # 11
            self.UNKNOWN_OPCODE,        # 12
            self.UNKNOWN_OPCODE,        # 13
            self.UNKNOWN_OPCODE,        # 14
            self.UNKNOWN_OPCODE,        # 15
            self.UNKNOWN_OPCODE,        # 16
            self.UNKNOWN_OPCODE,        # 17
            self.UNKNOWN_OPCODE,        # 18
            self.UNKNOWN_OPCODE,        # 19
            self.UNKNOWN_OPCODE,        # 1A
            self.UNKNOWN_OPCODE,        # 1B
            self.UNKNOWN_OPCODE,        # 1C
            self.UNKNOWN_OPCODE,        # 1D
            self.UNKNOWN_OPCODE,        # 1E
            self.UNKNOWN_OPCODE,        # 1F
            self.UNKNOWN_OPCODE,        # 20
            self.UNKNOWN_OPCODE,        # 21
            self.UNKNOWN_OPCODE,        # 22
            self.UNKNOWN_OPCODE,        # 23
            self.UNKNOWN_OPCODE,        # 24
            self.UNKNOWN_OPCODE,        # 25
            self.UNKNOWN_OPCODE,        # 26
            self.UNKNOWN_OPCODE,        # 27
            self.UNKNOWN_OPCODE,        # 28
            self.UNKNOWN_OPCODE,        # 29
            self.UNKNOWN_OPCODE,        # 2A
            self.UNKNOWN_OPCODE,        # 2B
            self.UNKNOWN_OPCODE,        # 2C
            self.UNKNOWN_OPCODE,        # 2D
            self.UNKNOWN_OPCODE,        # 2E
            self.UNKNOWN_OPCODE,        # 2F
            self.UNKNOWN_OPCODE,        # 30
            self.UNKNOWN_OPCODE,        # 31
            self.UNKNOWN_OPCODE,        # 32
            self.UNKNOWN_OPCODE,        # 33
            self.UNKNOWN_OPCODE,        # 34
            self.UNKNOWN_OPCODE,        # 35
            self.UNKNOWN_OPCODE,        # 36
            self.UNKNOWN_OPCODE,        # 37
            self.UNKNOWN_OPCODE,        # 38
            self.UNKNOWN_OPCODE,        # 39
            self.UNKNOWN_OPCODE,        # 3A
            self.UNKNOWN_OPCODE,        # 3B
            self.UNKNOWN_OPCODE,        # 3C
            self.UNKNOWN_OPCODE,        # 3D
            self.UNKNOWN_OPCODE,        # 3E
            self.UNKNOWN_OPCODE,        # 3F
            self.UNKNOWN_OPCODE,        # 40
            self.UNKNOWN_OPCODE,        # 41
            self.UNKNOWN_OPCODE,        # 42
            self.UNKNOWN_OPCODE,        # 43
            self.UNKNOWN_OPCODE,        # 44
            self.UNKNOWN_OPCODE,        # 45
            self.UNKNOWN_OPCODE,        # 46
            self.UNKNOWN_OPCODE,        # 47
            self.UNKNOWN_OPCODE,        # 48
            self.UNKNOWN_OPCODE,        # 49
            self.UNKNOWN_OPCODE,        # 4A
            self.UNKNOWN_OPCODE,        # 4B
            self.UNKNOWN_OPCODE,        # 4C
            self.UNKNOWN_OPCODE,        # 4D
            self.UNKNOWN_OPCODE,        # 4E
            self.UNKNOWN_OPCODE,        # 4F
            self.UNKNOWN_OPCODE,        # 50
            self.UNKNOWN_OPCODE,        # 51
            self.UNKNOWN_OPCODE,        # 52
            self.UNKNOWN_OPCODE,        # 53
            self.UNKNOWN_OPCODE,        # 54
            self.UNKNOWN_OPCODE,        # 55
            self.UNKNOWN_OPCODE,        # 56
            self.UNKNOWN_OPCODE,        # 57
            self.UNKNOWN_OPCODE,        # 58
            self.UNKNOWN_OPCODE,        # 59
            self.UNKNOWN_OPCODE,        # 5A
            self.UNKNOWN_OPCODE,        # 5B
            self.UNKNOWN_OPCODE,        # 5C
            self.UNKNOWN_OPCODE,        # 5D
            self.UNKNOWN_OPCODE,        # 5E
            self.UNKNOWN_OPCODE,        # 5F
            self.UNKNOWN_OPCODE,        # 60
            self.UNKNOWN_OPCODE,        # 61
            self.UNKNOWN_OPCODE,        # 62
            self.UNKNOWN_OPCODE,        # 63
            self.UNKNOWN_OPCODE,        # 64
            self.UNKNOWN_OPCODE,        # 65
            self.UNKNOWN_OPCODE,        # 66
            self.UNKNOWN_OPCODE,        # 67
            self.UNKNOWN_OPCODE,        # 68
            self.UNKNOWN_OPCODE,        # 69
            self.UNKNOWN_OPCODE,        # 6A
            self.UNKNOWN_OPCODE,        # 6B
            self.UNKNOWN_OPCODE,        # 6C
            self.UNKNOWN_OPCODE,        # 6D
            self.UNKNOWN_OPCODE,        # 6E
            self.UNKNOWN_OPCODE,        # 6F
            self.UNKNOWN_OPCODE,        # 70
            self.UNKNOWN_OPCODE,        # 71
            self.UNKNOWN_OPCODE,        # 72
            self.UNKNOWN_OPCODE,        # 73
            self.UNKNOWN_OPCODE,        # 74
            self.UNKNOWN_OPCODE,        # 75
            self.UNKNOWN_OPCODE,        # 76
            self.UNKNOWN_OPCODE,        # 77
            self.UNKNOWN_OPCODE,        # 78
            self.UNKNOWN_OPCODE,        # 79
            self.UNKNOWN_OPCODE,        # 7A
            self.UNKNOWN_OPCODE,        # 7B
            self.UNKNOWN_OPCODE,        # 7C
            self.UNKNOWN_OPCODE,        # 7D
            self.UNKNOWN_OPCODE,        # 7E
            self.UNKNOWN_OPCODE,        # 7F
            self.UNKNOWN_OPCODE,        # 80
            self.UNKNOWN_OPCODE,        # 81
            self.UNKNOWN_OPCODE,        # 82
            self.UNKNOWN_OPCODE,        # 83
            self.UNKNOWN_OPCODE,        # 84
            self.UNKNOWN_OPCODE,        # 85
            self.UNKNOWN_OPCODE,        # 86
            self.UNKNOWN_OPCODE,        # 87
            self.UNKNOWN_OPCODE,        # 8C
            self.UNKNOWN_OPCODE,        # 8D
            self.UNKNOWN_OPCODE,        # 8E
            self.UNKNOWN_OPCODE,        # 8F
            self.UNKNOWN_OPCODE,        # 90
            self.UNKNOWN_OPCODE,        # 91
            self.UNKNOWN_OPCODE,        # 92
            self.UNKNOWN_OPCODE,        # 93
            self.UNKNOWN_OPCODE,        # 94
            self.UNKNOWN_OPCODE,        # 95
            self.UNKNOWN_OPCODE,        # 96
            self.UNKNOWN_OPCODE,        # 97
            self.UNKNOWN_OPCODE,        # 98
            self.UNKNOWN_OPCODE,        # 99
            self.UNKNOWN_OPCODE,        # 9A
            self.UNKNOWN_OPCODE,        # 9B
            self.UNKNOWN_OPCODE,        # 9C
            self.UNKNOWN_OPCODE,        # 9D
            self.UNKNOWN_OPCODE,        # 9E
            self.UNKNOWN_OPCODE,        # 9F
            self.UNKNOWN_OPCODE,        # A0
            self.UNKNOWN_OPCODE,        # A1
            self.UNKNOWN_OPCODE,        # A2
            self.UNKNOWN_OPCODE,        # A3
            self.UNKNOWN_OPCODE,        # A4
            self.UNKNOWN_OPCODE,        # A5
            self.UNKNOWN_OPCODE,        # A6
            self.UNKNOWN_OPCODE,        # A7
            self.UNKNOWN_OPCODE,        # A8
            self.UNKNOWN_OPCODE,        # A9
            self.UNKNOWN_OPCODE,        # AA
            self.UNKNOWN_OPCODE,        # AB
            self.UNKNOWN_OPCODE,        # AC
            self.UNKNOWN_OPCODE,        # AD
            self.UNKNOWN_OPCODE,        # AE
            self.UNKNOWN_OPCODE,        # AF
            self.UNKNOWN_OPCODE,        # B0
            self.UNKNOWN_OPCODE,        # B1
            self.UNKNOWN_OPCODE,        # B2
            self.UNKNOWN_OPCODE,        # B3
            self.UNKNOWN_OPCODE,        # B4
            self.UNKNOWN_OPCODE,        # B5
            self.UNKNOWN_OPCODE,        # B6
            self.UNKNOWN_OPCODE,        # B7
            self.UNKNOWN_OPCODE,        # B8
            self.UNKNOWN_OPCODE,        # B9
            self.UNKNOWN_OPCODE,        # BA
            self.UNKNOWN_OPCODE,        # BB
            self.UNKNOWN_OPCODE,        # BC
            self.UNKNOWN_OPCODE,        # BD
            self.UNKNOWN_OPCODE,        # BE
            self.UNKNOWN_OPCODE,        # BF
            self.UNKNOWN_OPCODE,        # C0
            self.UNKNOWN_OPCODE,        # C1
            self.UNKNOWN_OPCODE,        # C2
            self.UNKNOWN_OPCODE,        # C3
            self.UNKNOWN_OPCODE,        # C4
            self.UNKNOWN_OPCODE,        # C5
            self.UNKNOWN_OPCODE,        # C6
            self.UNKNOWN_OPCODE,        # C7
            self.UNKNOWN_OPCODE,        # C8
            self.UNKNOWN_OPCODE,        # C9
            self.UNKNOWN_OPCODE,        # CA
            self.UNKNOWN_OPCODE,        # CB
            self.UNKNOWN_OPCODE,        # CC
            self.UNKNOWN_OPCODE,        # CD
            self.UNKNOWN_OPCODE,        # CE
            self.UNKNOWN_OPCODE,        # CF
            self.UNKNOWN_OPCODE,        # D0
            self.UNKNOWN_OPCODE,        # D1
            self.UNKNOWN_OPCODE,        # D2
            self.UNKNOWN_OPCODE,        # D3
            self.UNKNOWN_OPCODE,        # D4
            self.UNKNOWN_OPCODE,        # D5
            self.UNKNOWN_OPCODE,        # D6
            self.UNKNOWN_OPCODE,        # D7
            self.UNKNOWN_OPCODE,        # D8
            self.UNKNOWN_OPCODE,        # D9
            self.UNKNOWN_OPCODE,        # DA
            self.UNKNOWN_OPCODE,        # DB
            self.UNKNOWN_OPCODE,        # DC
            self.UNKNOWN_OPCODE,        # DD
            self.UNKNOWN_OPCODE,        # DE
            self.UNKNOWN_OPCODE,        # DF
            self.UNKNOWN_OPCODE,        # E0
            self.UNKNOWN_OPCODE,        # E1
            self.UNKNOWN_OPCODE,        # E2
            self.UNKNOWN_OPCODE,        # E3
            self.UNKNOWN_OPCODE,        # E4
            self.UNKNOWN_OPCODE,        # E5
            self.UNKNOWN_OPCODE,        # E6
            self.UNKNOWN_OPCODE,        # E7
            self.UNKNOWN_OPCODE,        # E8
            self.UNKNOWN_OPCODE,        # E9
            self.UNKNOWN_OPCODE,        # EA
            self.UNKNOWN_OPCODE,        # EB
            self.UNKNOWN_OPCODE,        # EC
            self.UNKNOWN_OPCODE,        # ED
            self.UNKNOWN_OPCODE,        # EE
            self.UNKNOWN_OPCODE,        # EF
            self.UNKNOWN_OPCODE,        # F0
            self.UNKNOWN_OPCODE,        # F1
            self.UNKNOWN_OPCODE,        # F2
            self.UNKNOWN_OPCODE,        # F3
            self.UNKNOWN_OPCODE,        # F4
            self.UNKNOWN_OPCODE,        # F5
            self.UNKNOWN_OPCODE,        # F6
            self.UNKNOWN_OPCODE,        # F7
            self.UNKNOWN_OPCODE,        # F8
            self.UNKNOWN_OPCODE,        # F9
            self.UNKNOWN_OPCODE,        # FA
            self.UNKNOWN_OPCODE,        # FB
            self.UNKNOWN_OPCODE,        # FC
            self.UNKNOWN_OPCODE,        # FD
            self.UNKNOWN_OPCODE,        # FE
            self.UNKNOWN_OPCODE,        # FF
        ]
        self.parsetable_0F3A = [
            self.UNKNOWN_OPCODE,        # 00
            self.UNKNOWN_OPCODE,        # 01
            self.UNKNOWN_OPCODE,        # 02
            self.UNKNOWN_OPCODE,        # 03
            self.UNKNOWN_OPCODE,        # 04
            self.UNKNOWN_OPCODE,        # 05
            self.UNKNOWN_OPCODE,        # 06
            self.UNKNOWN_OPCODE,        # 07
            self.UNKNOWN_OPCODE,        # 08
            self.UNKNOWN_OPCODE,        # 09
            self.UNKNOWN_OPCODE,        # 0A
            self.UNKNOWN_OPCODE,        # 0B
            self.UNKNOWN_OPCODE,        # 0C
            self.UNKNOWN_OPCODE,        # 0D
            self.UNKNOWN_OPCODE,        # 0E
            self.UNKNOWN_OPCODE,        # 0F
            self.UNKNOWN_OPCODE,        # 10
            self.UNKNOWN_OPCODE,        # 11
            self.UNKNOWN_OPCODE,        # 12
            self.UNKNOWN_OPCODE,        # 13
            self.UNKNOWN_OPCODE,        # 14
            self.UNKNOWN_OPCODE,        # 15
            self.UNKNOWN_OPCODE,        # 16
            self.UNKNOWN_OPCODE,        # 17
            self.UNKNOWN_OPCODE,        # 18
            self.UNKNOWN_OPCODE,        # 19
            self.UNKNOWN_OPCODE,        # 1A
            self.UNKNOWN_OPCODE,        # 1B
            self.UNKNOWN_OPCODE,        # 1C
            self.UNKNOWN_OPCODE,        # 1D
            self.UNKNOWN_OPCODE,        # 1E
            self.UNKNOWN_OPCODE,        # 1F
            self.UNKNOWN_OPCODE,        # 20
            self.UNKNOWN_OPCODE,        # 21
            self.UNKNOWN_OPCODE,        # 22
            self.UNKNOWN_OPCODE,        # 23
            self.UNKNOWN_OPCODE,        # 24
            self.UNKNOWN_OPCODE,        # 25
            self.UNKNOWN_OPCODE,        # 26
            self.UNKNOWN_OPCODE,        # 27
            self.UNKNOWN_OPCODE,        # 28
            self.UNKNOWN_OPCODE,        # 29
            self.UNKNOWN_OPCODE,        # 2A
            self.UNKNOWN_OPCODE,        # 2B
            self.UNKNOWN_OPCODE,        # 2C
            self.UNKNOWN_OPCODE,        # 2D
            self.UNKNOWN_OPCODE,        # 2E
            self.UNKNOWN_OPCODE,        # 2F
            self.UNKNOWN_OPCODE,        # 30
            self.UNKNOWN_OPCODE,        # 31
            self.UNKNOWN_OPCODE,        # 32
            self.UNKNOWN_OPCODE,        # 33
            self.UNKNOWN_OPCODE,        # 34
            self.UNKNOWN_OPCODE,        # 35
            self.UNKNOWN_OPCODE,        # 36
            self.UNKNOWN_OPCODE,        # 37
            self.UNKNOWN_OPCODE,        # 38
            self.UNKNOWN_OPCODE,        # 39
            self.UNKNOWN_OPCODE,        # 3A
            self.UNKNOWN_OPCODE,        # 3B
            self.UNKNOWN_OPCODE,        # 3C
            self.UNKNOWN_OPCODE,        # 3D
            self.UNKNOWN_OPCODE,        # 3E
            self.UNKNOWN_OPCODE,        # 3F
            self.UNKNOWN_OPCODE,        # 40
            self.UNKNOWN_OPCODE,        # 41
            self.UNKNOWN_OPCODE,        # 42
            self.UNKNOWN_OPCODE,        # 43
            self.UNKNOWN_OPCODE,        # 44
            self.UNKNOWN_OPCODE,        # 45
            self.UNKNOWN_OPCODE,        # 46
            self.UNKNOWN_OPCODE,        # 47
            self.UNKNOWN_OPCODE,        # 48
            self.UNKNOWN_OPCODE,        # 49
            self.UNKNOWN_OPCODE,        # 4A
            self.UNKNOWN_OPCODE,        # 4B
            self.UNKNOWN_OPCODE,        # 4C
            self.UNKNOWN_OPCODE,        # 4D
            self.UNKNOWN_OPCODE,        # 4E
            self.UNKNOWN_OPCODE,        # 4F
            self.UNKNOWN_OPCODE,        # 50
            self.UNKNOWN_OPCODE,        # 51
            self.UNKNOWN_OPCODE,        # 52
            self.UNKNOWN_OPCODE,        # 53
            self.UNKNOWN_OPCODE,        # 54
            self.UNKNOWN_OPCODE,        # 55
            self.UNKNOWN_OPCODE,        # 56
            self.UNKNOWN_OPCODE,        # 57
            self.UNKNOWN_OPCODE,        # 58
            self.UNKNOWN_OPCODE,        # 59
            self.UNKNOWN_OPCODE,        # 5A
            self.UNKNOWN_OPCODE,        # 5B
            self.UNKNOWN_OPCODE,        # 5C
            self.UNKNOWN_OPCODE,        # 5D
            self.UNKNOWN_OPCODE,        # 5E
            self.UNKNOWN_OPCODE,        # 5F
            self.UNKNOWN_OPCODE,        # 60
            self.UNKNOWN_OPCODE,        # 61
            self.UNKNOWN_OPCODE,        # 62
            self.UNKNOWN_OPCODE,        # 63
            self.UNKNOWN_OPCODE,        # 64
            self.UNKNOWN_OPCODE,        # 65
            self.UNKNOWN_OPCODE,        # 66
            self.UNKNOWN_OPCODE,        # 67
            self.UNKNOWN_OPCODE,        # 68
            self.UNKNOWN_OPCODE,        # 69
            self.UNKNOWN_OPCODE,        # 6A
            self.UNKNOWN_OPCODE,        # 6B
            self.UNKNOWN_OPCODE,        # 6C
            self.UNKNOWN_OPCODE,        # 6D
            self.UNKNOWN_OPCODE,        # 6E
            self.UNKNOWN_OPCODE,        # 6F
            self.UNKNOWN_OPCODE,        # 70
            self.UNKNOWN_OPCODE,        # 71
            self.UNKNOWN_OPCODE,        # 72
            self.UNKNOWN_OPCODE,        # 73
            self.UNKNOWN_OPCODE,        # 74
            self.UNKNOWN_OPCODE,        # 75
            self.UNKNOWN_OPCODE,        # 76
            self.UNKNOWN_OPCODE,        # 77
            self.UNKNOWN_OPCODE,        # 78
            self.UNKNOWN_OPCODE,        # 79
            self.UNKNOWN_OPCODE,        # 7A
            self.UNKNOWN_OPCODE,        # 7B
            self.UNKNOWN_OPCODE,        # 7C
            self.UNKNOWN_OPCODE,        # 7D
            self.UNKNOWN_OPCODE,        # 7E
            self.UNKNOWN_OPCODE,        # 7F
            self.UNKNOWN_OPCODE,        # 80
            self.UNKNOWN_OPCODE,        # 81
            self.UNKNOWN_OPCODE,        # 82
            self.UNKNOWN_OPCODE,        # 83
            self.UNKNOWN_OPCODE,        # 84
            self.UNKNOWN_OPCODE,        # 85
            self.UNKNOWN_OPCODE,        # 86
            self.UNKNOWN_OPCODE,        # 87
            self.UNKNOWN_OPCODE,        # 8C
            self.UNKNOWN_OPCODE,        # 8D
            self.UNKNOWN_OPCODE,        # 8E
            self.UNKNOWN_OPCODE,        # 8F
            self.UNKNOWN_OPCODE,        # 90
            self.UNKNOWN_OPCODE,        # 91
            self.UNKNOWN_OPCODE,        # 92
            self.UNKNOWN_OPCODE,        # 93
            self.UNKNOWN_OPCODE,        # 94
            self.UNKNOWN_OPCODE,        # 95
            self.UNKNOWN_OPCODE,        # 96
            self.UNKNOWN_OPCODE,        # 97
            self.UNKNOWN_OPCODE,        # 98
            self.UNKNOWN_OPCODE,        # 99
            self.UNKNOWN_OPCODE,        # 9A
            self.UNKNOWN_OPCODE,        # 9B
            self.UNKNOWN_OPCODE,        # 9C
            self.UNKNOWN_OPCODE,        # 9D
            self.UNKNOWN_OPCODE,        # 9E
            self.UNKNOWN_OPCODE,        # 9F
            self.UNKNOWN_OPCODE,        # A0
            self.UNKNOWN_OPCODE,        # A1
            self.UNKNOWN_OPCODE,        # A2
            self.UNKNOWN_OPCODE,        # A3
            self.UNKNOWN_OPCODE,        # A4
            self.UNKNOWN_OPCODE,        # A5
            self.UNKNOWN_OPCODE,        # A6
            self.UNKNOWN_OPCODE,        # A7
            self.UNKNOWN_OPCODE,        # A8
            self.UNKNOWN_OPCODE,        # A9
            self.UNKNOWN_OPCODE,        # AA
            self.UNKNOWN_OPCODE,        # AB
            self.UNKNOWN_OPCODE,        # AC
            self.UNKNOWN_OPCODE,        # AD
            self.UNKNOWN_OPCODE,        # AE
            self.UNKNOWN_OPCODE,        # AF
            self.UNKNOWN_OPCODE,        # B0
            self.UNKNOWN_OPCODE,        # B1
            self.UNKNOWN_OPCODE,        # B2
            self.UNKNOWN_OPCODE,        # B3
            self.UNKNOWN_OPCODE,        # B4
            self.UNKNOWN_OPCODE,        # B5
            self.UNKNOWN_OPCODE,        # B6
            self.UNKNOWN_OPCODE,        # B7
            self.UNKNOWN_OPCODE,        # B8
            self.UNKNOWN_OPCODE,        # B9
            self.UNKNOWN_OPCODE,        # BA
            self.UNKNOWN_OPCODE,        # BB
            self.UNKNOWN_OPCODE,        # BC
            self.UNKNOWN_OPCODE,        # BD
            self.UNKNOWN_OPCODE,        # BE
            self.UNKNOWN_OPCODE,        # BF
            self.UNKNOWN_OPCODE,        # C0
            self.UNKNOWN_OPCODE,        # C1
            self.UNKNOWN_OPCODE,        # C2
            self.UNKNOWN_OPCODE,        # C3
            self.UNKNOWN_OPCODE,        # C4
            self.UNKNOWN_OPCODE,        # C5
            self.UNKNOWN_OPCODE,        # C6
            self.UNKNOWN_OPCODE,        # C7
            self.UNKNOWN_OPCODE,        # C8
            self.UNKNOWN_OPCODE,        # C9
            self.UNKNOWN_OPCODE,        # CA
            self.UNKNOWN_OPCODE,        # CB
            self.UNKNOWN_OPCODE,        # CC
            self.UNKNOWN_OPCODE,        # CD
            self.UNKNOWN_OPCODE,        # CE
            self.UNKNOWN_OPCODE,        # CF
            self.UNKNOWN_OPCODE,        # D0
            self.UNKNOWN_OPCODE,        # D1
            self.UNKNOWN_OPCODE,        # D2
            self.UNKNOWN_OPCODE,        # D3
            self.UNKNOWN_OPCODE,        # D4
            self.UNKNOWN_OPCODE,        # D5
            self.UNKNOWN_OPCODE,        # D6
            self.UNKNOWN_OPCODE,        # D7
            self.UNKNOWN_OPCODE,        # D8
            self.UNKNOWN_OPCODE,        # D9
            self.UNKNOWN_OPCODE,        # DA
            self.UNKNOWN_OPCODE,        # DB
            self.UNKNOWN_OPCODE,        # DC
            self.UNKNOWN_OPCODE,        # DD
            self.UNKNOWN_OPCODE,        # DE
            self.UNKNOWN_OPCODE,        # DF
            self.UNKNOWN_OPCODE,        # E0
            self.UNKNOWN_OPCODE,        # E1
            self.UNKNOWN_OPCODE,        # E2
            self.UNKNOWN_OPCODE,        # E3
            self.UNKNOWN_OPCODE,        # E4
            self.UNKNOWN_OPCODE,        # E5
            self.UNKNOWN_OPCODE,        # E6
            self.UNKNOWN_OPCODE,        # E7
            self.UNKNOWN_OPCODE,        # E8
            self.UNKNOWN_OPCODE,        # E9
            self.UNKNOWN_OPCODE,        # EA
            self.UNKNOWN_OPCODE,        # EB
            self.UNKNOWN_OPCODE,        # EC
            self.UNKNOWN_OPCODE,        # ED
            self.UNKNOWN_OPCODE,        # EE
            self.UNKNOWN_OPCODE,        # EF
            self.UNKNOWN_OPCODE,        # F0
            self.UNKNOWN_OPCODE,        # F1
            self.UNKNOWN_OPCODE,        # F2
            self.UNKNOWN_OPCODE,        # F3
            self.UNKNOWN_OPCODE,        # F4
            self.UNKNOWN_OPCODE,        # F5
            self.UNKNOWN_OPCODE,        # F6
            self.UNKNOWN_OPCODE,        # F7
            self.UNKNOWN_OPCODE,        # F8
            self.UNKNOWN_OPCODE,        # F9
            self.UNKNOWN_OPCODE,        # FA
            self.UNKNOWN_OPCODE,        # FB
            self.UNKNOWN_OPCODE,        # FC
            self.UNKNOWN_OPCODE,        # FD
            self.UNKNOWN_OPCODE,        # FE
            self.UNKNOWN_OPCODE,        # FF
        ]
        self.REGISTER8BIT  = [ "al",  "cl",  "dl",  "bl",  "ah",  "ch",  "dh",  "bh", "r8l", "r9l", "r10l", "r11l", "r12l", "r13l", "r14l", "r15l"]
        self.REGISTER16BIT = [ "ax",  "cx",  "dx",  "bx",  "sp",  "bp",  "si",  "di", "r8w", "r9w", "r10w", "r11w", "r12w", "r13w", "r14w", "r15w"]
        self.REGISTER32BIT = ["eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi", "r8d", "r9d", "r10d", "r11d", "r12d", "r13d", "r14d", "r15d"]

    def disassemble ( self, start, stop ) :
        self.pos = start
        self.stream.seek(start)

        while self.pos < stop :
            byte = self.stream.read(1)
            if not byte:
                return
            byte = ord(byte)

            self.parsetable[byte](byte)

    def SPLIT233 ( self ) -> (int, int, int, int) :
        byte = self.stream.read(1)
        self.pos += 1

        if not byte:
            print("SPLIT233 ran out of stream")
            return 0, 0, 0
        byte = ord(byte)

        f = (byte & 0b11000000) >> 6
        s = (byte & 0b00111000) >> 3
        t =  byte & 0b00000111

        return f, s, t, byte

    def MODRM ( self, s ) -> (int, int, int, int, str, str, str) :
        regfield = ""
        rmfield = ""

        mod, reg, rm, byte = self.SPLIT233()
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
        rmloc = ""

        scale, index, base, byte = self.SPLIT233()
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

    def PG_AO ( self, op, start ) :     # ParseGen acc operation
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
    def PG_DS ( self, op, start ) :     # ParseGen ds operation
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
    def PG_RO ( self, op, start ) :     # ParseGen register operation
        def f ( self, byte ) :
            address = f"{self.pos:08X}"
            self.pos += 1

            reg = byte & 0b00000111

            hex = f"{start:02X}:{reg:b}"
                
            print(f"{address:8}: {hex:50} {op} {self.REGISTER32BIT[reg]}")
        return f
    def PG_S ( self, op, start ) :     # ParseGen s operation
        def f ( self, byte ) :
            address = f"{self.pos:08X}"
            self.pos += 1

            d = (byte & 0b00000010) >> 1
            s =  byte & 0b00000001

            mod, reg, rm, byte, regfield, rmfield, modrmhex = self.MODRM(s)

            hex = f"{start:02X}:{d}{s}  {modrmhex}"

            print(f"{address:8}: {hex:50} {op} {rmfield}, {regfield}")
        return f 
    def PG_SO ( self, segment ) :       # ParseGen segment override
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
