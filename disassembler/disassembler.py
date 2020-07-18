
disassembler = {
    'Prefix': {
        0xF0: 'LOCK prefix',
        0xF2: 'REPNE/REPNZ prefix',
        0xF3: 'REP or REPE/REPZ prefix',

        0x2E: 'CS segment override',
        0x36: 'SS segment override',
        0x3E: 'DS segment override',
        0x26: 'ES segment override',
        0x64: 'FS segment override',
        0x65: 'GS segment override',

        0x66: 'Operand-size override prefix',

        0x67: 'Address-size override prefix',
    },
    'REX' : {
        0b01000001: 'B',
        0b01000010: 'X',
        0b01000100: 'R',
        0b01001000: 'W',
    },
    'VEX': {
        'Dont, just dont': ''
    },
    'Opcode' : {

    },
    'ModRM',
    'SIB',
    'Displacement',
    'Immediate'
}

def disassemble ( stream, offset ) -> (String, String, int) :
    prettyprint = ''
    assembly = ''
    fed = 0
    state = { 'progress' : 'prefixes' }

    while 1 :
        switch ( state.progress) :
        print("hi")

    '\xF0' 'lock '
    '\xF2' 'repne '
    '\xF3' 'repe '

    Prefix group 1

    return "";