
"""
    Reg No.	0	1	2	3	4	5	6	7
byte	AL	CL	DL	BL	AH	CH	DH	BH
word	AX	CX	DX	BX	SP	BP	SI	DI
dword	EAX	ECX	EDX	EBX	ESP	EBP	ESI	EDI
sreg	ES	CS	SS	DS	FS	GS
"""

"""
    XRM (ModRM) Encoding
When an instruction involves two operands, they are usually encoded in the second byte, called the "XRM" byte (officially it's "ModRM" but that doesn't fit neatly into our little ASCII diagrams!) If a memory reference is involved (whether absolute or relative to a register), then we call it the displacement; it can be a full 32 bits, shown as disp32 below, or it can be a "short" 8 bits, shown as disp8.

xxrrrmmm (binary), best viewed as 3 octal digits:
x: modifier flag (indicates one of four cases)
r: register (normally the source operand)
m: reg/mem (normally the destination operand)
Encoding	Reg/Mem Addressing Mode	Notes
0rm	DS:[base]
0r5 disp32	DS:[disp32]	Can't use EBP as Base with no disp
1rm disp8	DS:[base + disp8]
2rm disp32	DS:[base + disp32]
xr4 sib	SIB byte follows (see below)	Can't use ESP as Base
3rm	reg
Note: Special cases are shown in italics.

SIB (Scale*Index+Base) Encoding
More complex memory references are encoded in a second "SIB" byte, which always follows an "XRM" byte.

ssiiibbb (binary), again, best viewed as 3 octal digits:
s: Scale (multiplier for the Index register)
i: Index register
b: Base register
Encoding	Reg/Mem Addressing Mode	Notes
0r4 sib	DS:[base + scale*index]
0r4 si5 disp32	DS:[scale*index + disp32]	Can't use EBP as Base w/o disp
1r4 sib disp8	DS:[base + scale*index + disp8]
2r4 sib disp32	DS:[base + scale*index + disp32]
xr4 04b	DS:[base]	Can't use ESP as Index
xr4 s4b	---	Undefined if s > 0

cc	Mnemonics	Flags	Operation	Long-Winded Name
00	o	OF=1	 	Overflow
01	no	OF=0	 	Not Overflow
02	c b nae	CF=1	< unsigned	u< Carry / Below unsigned
03	nc nb ae	CF=0	> unsigned	Not Carry / Not Below / Above/Equal
04	z e	ZF=1	==	Zero / Equal
05	nz ne	ZF=0	!=	Not Zero / Not Equal
06	be na	CF=1 & ZF=1	<= unsigned	Below/Equal / Not Above
07	nbe a	CF=0 & ZF=0	> unsigned	Above / Not Below/Equal
10	s	SF=1	< 0	Sign bit (Negative)
11	ns	SF=0	>= 0	Not Sign (Positive)
12	p pe	PF=1	 	Parity (Even)
13	np po	PF=0	 	No Parity (Odd)
14	l nge	SF<>OF	<	Less / Not Greater/Equal
15	nl ge	SF==OF	>=	Not Less / Greater/Equal
16	le ng	ZF=1 | SF<>OF	<=	Less/Equal / Not Greater
17	nle g	ZF=0 & SF==OF	>	Not Less/Equal / Greater
"""

"""
    Original set
    0x37 00110111 AAA
    :0P:0ds
    P 0 ADD
        2 ADC
        5 SUB
        3 SBB
        7 CMP
        1 OR
        4 AND
        6 XOR

    :366:s x2m
        NOT L
    :366:s x3m
        NEG L



"""

"""
    Original 8086/8088 instruction set
Instruction	Meaning	Notes	Opcode
AAA	ASCII adjust AL after addition	used with unpacked binary coded decimal	0x37
AAD	ASCII adjust AX before division	8086/8088 datasheet documents only base 10 version of the AAD instruction (opcode 0xD5 0x0A), but any other base will work. Later Intel's documentation has the generic form too. NEC V20 and V30 (and possibly other NEC V-series CPUs) always use base 10, and ignore the argument, causing a number of incompatibilities	0xD5
AAM	ASCII adjust AX after multiplication	Only base 10 version (Operand is 0xA) is documented, see notes for AAD	0xD4
AAS	ASCII adjust AL after subtraction		0x3F
ADC	Add with carry	destination := destination + source + carry_flag	0x10…0x15, 0x80/2…0x83/2
ADD	Add	(1) r/m += r/imm; (2) r += m/imm;	0x00…0x05, 0x80/0…0x83/0
AND	Logical AND	(1) r/m &= r/imm; (2) r &= m/imm;	0x20…0x25, 0x80/4…0x83/4
CALL	Call procedure	push eip; eip points to the instruction directly after the call	0x9A, 0xE8, 0xFF/2, 0xFF/3
CBW	Convert byte to word		0x98
CLC	Clear carry flag	CF = 0;	0xF8
CLD	Clear direction flag	DF = 0;	0xFC
CLI	Clear interrupt flag	IF = 0;	0xFA
CMC	Complement carry flag		0xF5
CMP	Compare operands		0x38…0x3D, 0x80/7…0x83/7
CMPSB	Compare bytes in memory		0xA6
CMPSW	Compare words		0xA7
CWD	Convert word to doubleword		0x99
DAA	Decimal adjust AL after addition	(used with packed binary coded decimal)	0x27
DAS	Decimal adjust AL after subtraction		0x2F
DEC	Decrement by 1		0x48…0x4F, 0xFE/1, 0xFF/1
DIV	Unsigned divide	DX:AX = DX:AX / r/m; resulting DX == remainder	0xF6/6, 0xF7/6
ESC	Used with floating-point unit		0xD8..0xDF
HLT	Enter halt state		0xF4
IDIV	Signed divide	DX:AX = DX:AX / r/m; resulting DX == remainder	0xF6/7, 0xF7/7
IMUL	Signed multiply	(1) DX:AX = AX * r/m; (2) AX = AL * r/m	0x69, 0x6B (both since 80186), 0xF6/5, 0xF7/5, 0x0FAF (since 80386)
IN	Input from port	(1) AL = port[imm]; (2) AL = port[DX]; (3) AX = port[imm]; (4) AX = port[DX];	0xE4, 0xE5, 0xEC, 0xED
INC	Increment by 1		0x40…0x47, 0xFE/0, 0xFF/0
INT	Call to interrupt		0xCC, 0xCD
INTO	Call to interrupt if overflow		0xCE
IRET	Return from interrupt		0xCF
Jcc	Jump if condition	(JA, JAE, JB, JBE, JC, JE, JG, JGE, JL, JLE, JNA, JNAE, JNB, JNBE, JNC, JNE, JNG, JNGE, JNL, JNLE, JNO, JNP, JNS, JNZ, JO, JP, JPE, JPO, JS, JZ)	0x70…0x7F, 0x0F80…0x0F8F (since 80386)
JCXZ	Jump if CX is zero		0xE3
JMP	Jump		0xE9…0xEB, 0xFF/4, 0xFF/5
LAHF	Load FLAGS into AH register		0x9F
LDS	Load pointer using DS		0xC5
LEA	Load Effective Address		0x8D
LES	Load ES with pointer		0xC4
LOCK	Assert BUS LOCK# signal	(for multiprocessing)	0xF0
LODSB	Load string byte	if (DF==0) AL = *SI++; else AL = *SI--;	0xAC
LODSW	Load string word	if (DF==0) AX = *SI++; else AX = *SI--;	0xAD
LOOP/LOOPx	Loop control	(LOOPE, LOOPNE, LOOPNZ, LOOPZ) if (x && --CX) goto lbl;	0xE0…0xE2
MOV	Move	copies data from one location to another, (1) r/m = r; (2) r = r/m;	0xA0...0xA3
MOVSB	Move byte from string to string
if (DF==0)
*(byte*)DI++ = *(byte*)SI++;
else
*(byte*)DI-- = *(byte*)SI--;
0xA4
MOVSW	Move word from string to string
if (DF==0)
*(word*)DI++ = *(word*)SI++;
else
*(word*)DI-- = *(word*)SI--;
0xA5
MUL	Unsigned multiply	(1) DX:AX = AX * r/m; (2) AX = AL * r/m;	0xF6/4…0xF7/4
NEG	Two's complement negation	r/m *= -1;	0xF6/3…0xF7/3
NOP	No operation	opcode equivalent to XCHG EAX, EAX	0x90
NOT	Negate the operand, logical NOT	r/m ^= -1;	0xF6/2…0xF7/2
OR	Logical OR	(1) r/m |= r/imm; (2) r |= m/imm;	0x08…0x0D, 0x80…0x83/1
OUT	Output to port	(1) port[imm] = AL; (2) port[DX] = AL; (3) port[imm] = AX; (4) port[DX] = AX;	0xE6, 0xE7, 0xEE, 0xEF
POP	Pop data from stack	r/m = *SP++; POP CS (opcode 0x0F) works only on 8086/8088. Later CPUs use 0x0F as a prefix for newer instructions.	0x07, 0x0F(8086/8088 only), 0x17, 0x1F, 0x58…0x5F, 0x8F/0
POPF	Pop FLAGS register from stack	FLAGS = *SP++;	0x9D
PUSH	Push data onto stack	*--SP = r/m;	0x06, 0x0E, 0x16, 0x1E, 0x50…0x57, 0x68, 0x6A (both since 80186), 0xFF/6
PUSHF	Push FLAGS onto stack	*--SP = FLAGS;	0x9C
RCL	Rotate left (with carry)		0xC0…0xC1/2 (since 80186), 0xD0…0xD3/2
RCR	Rotate right (with carry)		0xC0…0xC1/3 (since 80186), 0xD0…0xD3/3
REPxx	Repeat MOVS/STOS/CMPS/LODS/SCAS	(REP, REPE, REPNE, REPNZ, REPZ)	0xF2, 0xF3
RET	Return from procedure	Not a real instruction. The assembler will translate these to a RETN or a RETF depending on the memory model of the target system.
RETN	Return from near procedure		0xC2, 0xC3
RETF	Return from far procedure		0xCA, 0xCB
ROL	Rotate left		0xC0…0xC1/0 (since 80186), 0xD0…0xD3/0
ROR	Rotate right		0xC0…0xC1/1 (since 80186), 0xD0…0xD3/1
SAHF	Store AH into FLAGS		0x9E
SAL	Shift Arithmetically left (signed shift left)	(1) r/m <<= 1; (2) r/m <<= CL;	0xC0…0xC1/4 (since 80186), 0xD0…0xD3/4
SAR	Shift Arithmetically right (signed shift right)	(1) (signed) r/m >>= 1; (2) (signed) r/m >>= CL;	0xC0…0xC1/7 (since 80186), 0xD0…0xD3/7
SBB	Subtraction with borrow	alternative 1-byte encoding of SBB AL, AL is available via undocumented SALC instruction	0x18…0x1D, 0x80…0x83/3
SCASB	Compare byte string		0xAE
SCASW	Compare word string		0xAF
SHL	Shift left (unsigned shift left)		0xC0…0xC1/4 (since 80186), 0xD0…0xD3/4
SHR	Shift right (unsigned shift right)		0xC0…0xC1/5 (since 80186), 0xD0…0xD3/5
STC	Set carry flag	CF = 1;	0xF9
STD	Set direction flag	DF = 1;	0xFD
STI	Set interrupt flag	IF = 1;	0xFB
STOSB	Store byte in string	if (DF==0) *ES:DI++ = AL; else *ES:DI-- = AL;	0xAA
STOSW	Store word in string	if (DF==0) *ES:DI++ = AX; else *ES:DI-- = AX;	0xAB
SUB	Subtraction	(1) r/m -= r/imm; (2) r -= m/imm;	0x28…0x2D, 0x80…0x83/5
TEST	Logical compare (AND)	(1) r/m & r/imm; (2) r & m/imm;	0x84, 0x84, 0xA8, 0xA9, 0xF6/0, 0xF7/0
WAIT	Wait until not busy	Waits until BUSY# pin is inactive (used with floating-point unit)	0x9B
XCHG	Exchange data	r :=: r/m; A spinlock typically uses xchg as an atomic operation. (coma bug).	0x86, 0x87, 0x91…0x97
XLAT	Table look-up translation	behaves like MOV AL, [BX+AL]	0xD7
XOR	Exclusive OR	(1) r/m ^= r/imm; (2) r ^= m/imm;	0x30…0x35, 0x80…0x83/6
"""

"""
    Disassembler x86
    up to 4 legacy prefixes
    1,2 or 3-byte opcode
    optional modrm
    optional sib
    optional 1,2 or 4-byte displacement
    optional 1,2 or 4-byte immediate
"""

parsetables = {}
parsetables["x86"] = [
    d0p0dw, d0p0dw, d0p0dw, d0p0dw, d0p4w,  d0p4w,  d0l6d,  d0l6d,
    d0p0dw, d0p0dw, d0p0dw, d0p0dw, d0p4w,  d0p4w,  d0l6d,  dx0F,
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
    d340,   d341,   d342,   d343,   d344w,  d344w,  d346w,  d346w,
    d350,   d351,   d352,   d353,   d354w,  d354w,  d356w,  d356w,
    d360,   d361,   d362,   d363,   d364,   d365,   d366,   d367,
    d370,   d371,   d372,   d373,   d374,   d375,   d376wr01,d377,
]

ROTOPS = ["ROL", "ROR", "RCL", "RCR", "SHL", "SHR", "SAL", "SAR"]


ALUOPS = ["ADD", "OR", "ADC", "SBB", "AND", "SUB", "XOR", "CMP"]
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

    xrm = state["xrm"] = ord(stream.read(1))

    size = w

    dis = f"{ALUOPS[p]} {rm} {reg}"

    print(dis)
def d0p4w ( state ) :
    """
        ALU acc imm operations
        0p4+w imm
    """
    p = (byte & 0b00111000) >> 3
    w =  byte & 0b00000001
def d0l6d ( state ) :
    """
        Segment register stack operations
        0l6+d
    """
    pass
def d0h6 ( state ) :
    """
        Segment override prefix
        0h6
    """
    pass
def d0h7 ( state ) :
    """
        BCD conversion
        0p7
    """
    pass
def d10r ( state ) :
    """
        REG INC
        10r
    """
    pass
def d11r ( state ) :
    """
        REG DEC
        11r
    """
    pass
def d12r ( state ) :
    """
        REG PUSH
        12r
    """
    pass
def d13r ( state ) :
    """
        REG POP
        13r
    """
    pass
def d150w0 ( state ) :
    """
        PUSH imm
        150+w0 imm
    """
    pass
def d151w0 ( state ) :
    """
        IMUL reg rm imm
        151+w0 xrm imm
    """
    pass
def d154dw ( state ) :
    """
        String IO
        154+dw
    """
    pass
def d160cc ( state ) :
    """
        Conditional short jump
        160+cc disp8
    """
    pass
def d200sw ( state ) :
    """
        ALU rm imm operations
        200+sw xpm imm
    """
    pass
def d204w ( state ) :
    """
        ALU reg rm test
        204+w xrm
    """
    pass
def d206w ( state ) :
    """
        XCHG reg rm
        206+w xrm
    """
    pass
def d210dw ( state ) :
    """
        MOV rm reg
        210+dw xrm
    """
    pass
def d214d0 ( state ) :
    """
        MOV rm sreg
        214+d0 xsm
    """
    pass
def d215 ( state ) :
    """
        LEA reg rm
        215 xrm
    """
    pass
def d22r ( state ) :
    """
        XCHG EAX reg
        22r
    """
    pass
def d230 ( state ) :
    """
        CWDE
        230
    """
    pass
def d231 ( state ) :
    """
        CDQ
        231
    """
    pass
def d234 ( state ) :
    """
        PUSHF
        234
    """
    pass
def d235 ( state ) :
    """
        POPF
        235
    """
    pass
def d236 ( state ) :
    """
        SAHF
        236
    """
    pass
def d237 ( state ) :
    """
        LAHF
        237
    """
    pass
def d240dw ( state ) :
    """
        MOV acc mem
        240+dw disp
    """
    pass
def d244w ( state ) :
    """
        MOVS
        244+w
    """
    pass
def d246w ( state ) :
    """
        CMPS
        246+w
    """
    pass
def d250w ( state ) :
    """
        ALU acc imm test
        250+w imm
    """
    pass
def d252w ( state ) :
    """
        STOS
        252+w
    """
    pass
def d254w ( state ) :
    """
        LODS
        254+w
    """
    pass
def d256w ( state ) :
    """
        SCAS
        256+w
    """
    pass
def d26wr ( state ) :
    """
        MOV reg imm
        2[6+w]r imm
    """
    pass
def d300w ( state ) :
    """
        ROT rm imm
        300+w xpm imm8
    """
    pass
def d302 ( state ) :
    """
        RET imm
        302 imm16
    """
    pass
def d303 ( state ) :
    """
        RET
        303
    """
    pass
def d304 ( state ) :
    """
        LES
        304
    """
    pass
def d305 ( state ) :
    """
        LDS
        305
    """
    pass
def d306w ( state ) :
    """
        MOV rm imm
        306+w xrm imm
    """
    pass
def d310 ( state ) :
    """
        ENTER locals, nesting
        310 imm32 imm8
    """
    pass
def d311 ( state ) :
    """
        LEAVE
        311
    """
    pass
def d312 ( state ) :
    """
        RET FAR imm
        312 imm16
    """
    pass
def d313 ( state ) :
    """
        RET FAR
        313
    """
    pass
def d314 ( state ) :
    """
        INT3
        314
    """
    pass
def d315 ( state ) :
    """
        INT imm8
        315 imm8
    """
    pass
def d316 ( state ) :
    """
        INT0
        316
    """
    pass
def d317 ( state ) :
    """
        IRET
        317
    """
    pass
def d320w ( state ) :
    """
        ROT rm 1
        320+w xpm
    """
    pass
def d322w ( state ) :
    """
        ROT rm CL
        322+w xpm
    """
    pass
def d324 ( state ) :
    """
        AMX imm8
        324 imm8
    """
    pass
def d325 ( state ) :
    """
        ADX imm8
        325 imm8
    """
    pass
def d326 ( state ) :
    """
        SALC
        326
    """
    pass
def d327 ( state ) :
    """
        XLAT
        327
    """
    pass
def d33 ( state ) :
    """
        FPU instruction
        33m xrm
    """
    pass
def d340 ( state ) :
    """
        LOOPNE
        340 disp8
    """
    pass
def d341 ( state ) :
    """
        LOOPE
        341 disp8
    """
    pass
def d342 ( state ) :
    """
        LOOP
        342 disp8
    """
    pass
def d343 ( state ) :
    """
        JCXZ
        343 disp8
    """
    pass
def d344w ( state ) :
    """
        IN acc port
        344+w imm8
    """
    pass
def d346w ( state ) :
    """
        OUT port acc
        346+w imm8
    """
    pass
def d350 ( state ) :
    """
        CALL disp
        350 disp
    """
    pass
def d351 ( state ) :
    """
        JUMP disp
        351 disp
    """
    pass
def d352 ( state ) :
    """
        JMPF
        352
    """
    pass
def d353 ( state ) :
    """
        JMP rel8
        353 rel8
    """
    pass
def d354w ( state ) :
    """
        IN acc DX
        354+w
    """
    pass
def d356w ( state ) :
    """
        OUT DX acc
        356+w
    """
    pass
def d360 ( state ) :
    """
        LOCK
        360
    """
    pass
def d361 ( state ) :
    """
        ICEBP
        361
    """
    pass
def d362 ( state ) :
    """
        REPNE
        362
    """
    pass
def d363 ( state ) :
    """
        REPE
        363
    """
    pass
def d364 ( state ) :
    """
        HLT
        364
    """
    pass
def d365 ( state ) :
    """
        CMC
        365
    """
    pass
def d366 ( state ) :
    """
        366 instruction
    """
    pass
def d366wr0 ( state ) :
    """
        ALU rm imm test
        366+w x0m imm
    """
    pass
def d366wr2 ( state ) :
    """
        NOT rm
        366 x2m
    """
    pass
def d366wr3 ( state ) :
    """
        NEG rm
        366 x3m
    """
    pass
def d366wr4 ( state ) :
    """
        MUL rm
        366 x4m
    """
    pass
def d366wr5 ( state ) :
    """
        IMUL rm
        366 x5m
    """
    pass
def d366wr6 ( state ) :
    """
        DIV rm
        366 x6m
    """
    pass
def d366wr7 ( state ) :
    """
        IDIV rm
        366 x7m
    """
    pass
def d370 ( state ) :
    """
        CLC
        370
    """
    pass
def d371 ( state ) :
    """
        STC
        371
    """
    pass
def d372 ( state ) :
    """
        CLI
        372
    """
    pass
def d373 ( state ) :
    """
        STI
        373
    """
    pass
def d374 ( state ) :
    """
        CLD
        374
    """
    pass
def d375 ( state ) :
    """
        STD
        375
    """
    pass
def d376wr01 ( state ) :
    """
        376+w x0m INC
        376+w x1m DEC
    """
    pass
def d377 ( state ) :
    """
        377 instruction
    """
    pass
def d377r2 ( state ) :
    """
        CALL rm
        377 x2m
    """
    pass
def d377r4 ( state ) :
    """
        JMP rm
        377 x4m
    """
    pass
def d377r6 ( state ) :
    """
        PUSH rm
        377 x6m
    """
    pass

def disassemble ( stream, start, stop ) :
    pos = start

    state = {
        "stream" : stream,
        "pos" : pos,
        "byte" : -1,
    }

    while pos < stop :
        state["byte"] = ord(stream.read(1))
        parsetables["x86"][state["byte"]](state)

def read_xrm ( state ) :
    byte = ord(state["stream"].read(1))
    state["pos"] += 1
    state["xrm"] = byte

    mod = (byte & 0b11000000) >> 6
    reg = (byte & 0b00111000) >> 3
    rm  =  byte & 0b00000111

    if mod == 0b00 and rm == 0b101 : # displacement-only mode
        disp32 = int.from_bytes(state.stream.read(4), byteorder='little', signed=True)
        state.pos += 4
        rmfield = f"[{disp32:+08X}]"
    elif mod == 0b11 : # direct mode
        rmfield = state.REGISTER32BIT[rm]
    else :
        rmloc = ""
        if rm == 0b100 : # SIB mode
            scale, index, base, sibbyte, rmloc, sibhex = state.SIB(mod)
        else :
            rmloc = state.REGISTER32BIT[rm]

        offset = ""
        if mod == 0b01 : # one-byte displacement mode
            disp8 = int.from_bytes(state.stream.read(1), byteorder='little', signed=True)
            state.pos += 1
            offset = f"{disp8:+02X}"
        elif mod == 0b10 : # four-byte displacement mode
            disp32 = int.from_bytes(state.stream.read(4), byteorder='little', signed=True)
            state.pos += 4
            offset = f"{disp32:+08X}"

        rmfield = f"[{rmloc}{offset}]"

    return mod, reg, rm, byte, regfield, rmfield, hex

def SIB ( state, mod ) -> (int, int, int, int, str, str) :
    byte = state.stream.read(1)
    state.pos += 1

    rmloc = ""

    if not byte:
        print("SPLIT233 ran out of stream")
        return 0, 0, 0
    byte = ord(byte)

    scale = (byte & 0b11000000) >> 6
    index = (byte & 0b00111000) >> 3
    base  =  byte & 0b00000111

    hex = f" {byte:02X}[{scale:02b} {index:03b} {base:03b}]"

    rmloc = f"{state.REGISTER32BIT[index]}*{1<<scale}"
    if base == 0b101 :
        if mod == 0b00 : # displacement-only mode
            disp32 = int.from_bytes(state.stream.read(4), byteorder='little', signed=True)
            state.pos += 4
            hex += f" {disp32 &0xFFFFFFFF:08X}"
            rmloc += f"{disp32:+}"
    else :
        rmloc = f"{state.REGISTER32BIT[base]}+{rmloc}"

    return scale, index, base, byte, rmloc, hex

    callback(state.pos, "ADD", "RM8", "R8")
    pass
