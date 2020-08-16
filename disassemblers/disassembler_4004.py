"""
ACC<4>  CY<1>
R0-15 <4>
data ptr<8>
code ptr<12>
"""
class disassembler_4004 :
    """
        0000 0000           NOP
        0001 CCCC AAAA AAAA JCN
        0010 RRR0 DDDD DDDD FIM
        0010 RRR1           SRC
        0011 RRR0           FIN
        0011 RRR1           JIN
        0100 AAAA AAAA AAAA JUN
        0101 AAAA AAAA AAAA JMS
        0110 RRRR           INC
        0111 RRRR AAAA AAAA ISZ
        1000 RRRR           ADD
        1001 RRRR           SUB
        1010 RRRR           LD
        1011 RRRR           XCH
        1100 DDDD           BBL
        1101 DDDD           LDM

        1110 0000           WRM
        1110 0001           WMP
        1110 0010           WRR
        1110 0011           WPM
        1110 0100           WR0
        1110 0101           WR1
        1110 0110           WR2
        1110 0111           WR3
        1110 1000           SBM
        1110 1001           RDM
        1110 1010           RDR
        1110 1011           ADM
        1110 1100           RD0
        1110 1101           RD1
        1110 1110           RD2
        1110 1111           RD3

        1111 0000           CLB
        1111 0001           CLC
        1111 0010           IAC
        1111 0011           CMC
        1111 0100           CMA
        1111 0101           RAL
        1111 0110           RAR
        1111 0111           TCC
        1111 1000           DAC
        1111 1001           TCS
        1111 1010           STC
        1111 1011           DAA
        1111 1100           KBP
        1111 1101           DCL
    """
    def assemble ( self, stream, start, stop ) :
        print("4004 assemble not yet supported")
    def disassemble ( self, stream, start, stop ) :
        pos = start
        while pos < stop :
            p_raw, p_instr, p_arg, p_comment, pos = self.ISA_MATCH_RTI ( stream, pos )
            print(f'{p_raw:19} {p_instr:3} {p_arg:3} {p_comment}')
    def emulate_opcodes ( self, stream, start, stop ) :
        print("4004 emulate_opcodes not yet supported")
    def emulate_raw ( self, stream, start, stop ) :
        print("4004 emulate_raw not yet supported")
    


    def ISA_MATCH_RTI ( self, stream, pos ) :
        def I_INV ( stream, pos, byte ) :
            return f'{byte:b}', "UNK", "", "Unknown instruction", pos+1

        def I_0000_0000 (s,p,b) :
            """
                0000 0000           NOP
                no operation
            """
            return "0000 0000", "NOP", "", "", p+1
        # 0001 CCCC AAAA AAAA JCN
        def I_0001 (s,p,b) :
            pass
        # 0010 RRR0 DDDD DDDD FIM
        def I_0010_RRR0 (s,p,b) :
            pass
        def I_0010_RRR1 (s,p,b) :
            """
                0010 RRR1           SRC
                send register control
            """
            r = (b & 0b1110) >> 1
            return f'0010 {r:3b}1', "SRC", f'r{r}-r{r+1}', "", p+1
        def I_0011_RRR0 (s,p,b) :
            """
                0011 RRR0           FIN
                fetch indirect from rom
            """
            r = (b & 0b1110) >> 1
            return f'0011 {r:3b}0', "FIN", f'r{r}-r{r+1}', "", p+1
        def I_0011_RRR1 (s,p,b) :
            """
                0011 RRR1           JIN
                jump indirect
            """
            r = (b & 0b1110) >> 1
            return f'0011 {r:3b}1', "JIN", f'r{r}-r{r+1}', "", p+1
        def I_0100 (s,p,b) :
            """
                0100 AAAA AAAA AAAA JUN
                jump unconditionally
            """
            b2 = ord(stream.read(1))

            a3 = b & 0b1111
            a2 = b2 >> 4
            a1 = b2 & 0b1111
            return f'0100 {a3:4b} {a2:4b} {a1:4b}', "JUN", f'{a3:4b}{a2:4b}{a1:4b}', "", p+2
        # 0101 AAAA AAAA AAAA JMS
        def I_0101 (s,p,b) :
            pass
        def I_0110 (s,p,b) :
            """
                0110 RRRR           INC
                increment index register
            """
            r = b & 0b1111
            return f'0110 {r:4b}', "INC", f'r{r}', "", p+1
        # 0111 RRRR AAAA AAAA ISZ
        def I_0111 (s,p,b) :
            pass
        def I_1000 (s,p,b) :
            """
                1000 RRRR           ADD
                add index register to accumulator with carry
            """
            r = b & 0b1111
            return f'1000 {r:4b}', "ADD", f'r{r}', "", p+1
        def I_1001 (s,p,b) :
            """
                1001 RRRR           SUB
                subtract index register from accumulator with borrow
            """
            r = b & 0b1111
            return f'1001 {r:4b}', "SUB", f'r{r}', "", p+1
        def I_1010 (s,p,b) :
            """
                1010 RRRR           LD
                load index register to accumulator
            """
            r = b & 0b1111
            return f'1010 {r:4b}', "LD", f'r{r}', "", p+1
        def I_1011 (s,p,b) :
            """
                1011 RRRR           XCH
                exchange index register and accumulator
            """
            r = b & 0b1111
            return f'1011 {r:4b}', "XCH", f'r{r}', "", p+1
        def I_1100 (s,p,b) :
            """
                1100 DDDD           BBL
                branch back and load data to accumulator
            """
            d = b & 0b1111
            return f'1011 {d:4b}', "BBL", f'{d}', "", p+1
        def I_1101 (s,p,b) :
            """
                1101 DDDD           LDM
                load data to accumulator
            """
            d = b & 0b1111
            return f'1101 {d:4b}', "LDM", f'{d}', "", p+1

        # 1110 0000           WRM
        # 1110 0001           WMP
        # 1110 0010           WRR
        # 1110 0011           WPM
        # 1110 0100           WR0
        # 1110 0101           WR1
        # 1110 0110           WR2
        # 1110 0111           WR3
        # 1110 1000           SBM
        # 1110 1001           RDM
        # 1110 1010           RDR
        # 1110 1011           ADM
        # 1110 1100           RD0
        # 1110 1101           RD1
        # 1110 1110           RD2
        # 1110 1111           RD3

        # 1111 0000           CLB
        # 1111 0001           CLC
        # 1111 0010           IAC
        # 1111 0011           CMC
        # 1111 0100           CMA
        # 1111 0101           RAL
        # 1111 0110           RAR
        # 1111 0111           TCC
        # 1111 1000           DAC
        # 1111 1001           TCS
        # 1111 1010           STC
        # 1111 1011           DAA
        # 1111 1100           KBP
        # 1111 1101           DCL


        stream.seek(pos)
        byte = ord(stream.read(1))
        return [
            # 0000 0000           NOP
            I_0000_0000,    I_INV,          I_INV,          I_INV,
            I_INV,          I_INV,          I_INV,          I_INV,
            I_INV,          I_INV,          I_INV,          I_INV,
            I_INV,          I_INV,          I_INV,          I_INV,
            # 0001 CCCC AAAA AAAA JCN
            I_0001,         I_0001,         I_0001,         I_0001,
            I_0001,         I_0001,         I_0001,         I_0001,
            I_0001,         I_0001,         I_0001,         I_0001,
            I_0001,         I_0001,         I_0001,         I_0001,
            # 0010 RRR0 DDDD DDDD FIM
            # 0010 RRR1           SRC
            I_0010_RRR0,    I_0010_RRR1,    I_0010_RRR0,    I_0010_RRR1,
            I_0010_RRR0,    I_0010_RRR1,    I_0010_RRR0,    I_0010_RRR1,
            I_0010_RRR0,    I_0010_RRR1,    I_0010_RRR0,    I_0010_RRR1,
            I_0010_RRR0,    I_0010_RRR1,    I_0010_RRR0,    I_0010_RRR1,
            # 0011 RRR0           FIN
            # 0011 RRR1           JIN
            I_0011_RRR0,    I_0011_RRR1,    I_0011_RRR0,    I_0011_RRR1,
            I_0011_RRR0,    I_0011_RRR1,    I_0011_RRR0,    I_0011_RRR1,
            I_0011_RRR0,    I_0011_RRR1,    I_0011_RRR0,    I_0011_RRR1,
            I_0011_RRR0,    I_0011_RRR1,    I_0011_RRR0,    I_0011_RRR1,
            # 0100 AAAA AAAA AAAA JUN
            I_0100,         I_0100,         I_0100,         I_0100,
            I_0100,         I_0100,         I_0100,         I_0100,
            I_0100,         I_0100,         I_0100,         I_0100,
            I_0100,         I_0100,         I_0100,         I_0100,
            # 0101 AAAA AAAA AAAA JMS
            I_0101,         I_0101,         I_0101,         I_0101,
            I_0101,         I_0101,         I_0101,         I_0101,
            I_0101,         I_0101,         I_0101,         I_0101,
            I_0101,         I_0101,         I_0101,         I_0101,
            # 0110 RRRR           INC
            I_0110,         I_0110,         I_0110,         I_0110,
            I_0110,         I_0110,         I_0110,         I_0110,
            I_0110,         I_0110,         I_0110,         I_0110,
            I_0110,         I_0110,         I_0110,         I_0110,
            # 0111 RRRR AAAA AAAA ISZ
            I_0111,         I_0111,         I_0111,         I_0111,
            I_0111,         I_0111,         I_0111,         I_0111,
            I_0111,         I_0111,         I_0111,         I_0111,
            I_0111,         I_0111,         I_0111,         I_0111,
            # 1000 RRRR           ADD
            I_1000,         I_1000,         I_1000,         I_1000,
            I_1000,         I_1000,         I_1000,         I_1000,
            I_1000,         I_1000,         I_1000,         I_1000,
            I_1000,         I_1000,         I_1000,         I_1000,
            # 1001 RRRR           SUB
            I_1001,         I_1001,         I_1001,         I_1001,
            I_1001,         I_1001,         I_1001,         I_1001,
            I_1001,         I_1001,         I_1001,         I_1001,
            I_1001,         I_1001,         I_1001,         I_1001,
            # 1010 RRRR           LD
            I_1010,         I_1010,         I_1010,         I_1010,
            I_1010,         I_1010,         I_1010,         I_1010,
            I_1010,         I_1010,         I_1010,         I_1010,
            I_1010,         I_1010,         I_1010,         I_1010,
            # 1011 RRRR           XCH
            I_1011,         I_1011,         I_1011,         I_1011,
            I_1011,         I_1011,         I_1011,         I_1011,
            I_1011,         I_1011,         I_1011,         I_1011,
            I_1011,         I_1011,         I_1011,         I_1011,
            # 1100 DDDD           BBL
            I_1100,         I_1100,         I_1100,         I_1100,
            I_1100,         I_1100,         I_1100,         I_1100,
            I_1100,         I_1100,         I_1100,         I_1100,
            I_1100,         I_1100,         I_1100,         I_1100,
            # 1101 DDDD           LDM
            I_1101,         I_1101,         I_1101,         I_1101,
            I_1101,         I_1101,         I_1101,         I_1101,
            I_1101,         I_1101,         I_1101,         I_1101,
            I_1101,         I_1101,         I_1101,         I_1101,

            # 1110 0000           WRM
            # 1110 0001           WMP
            # 1110 0010           WRR
            # 1110 0011           WPM
            # 1110 0100           WR0
            # 1110 0101           WR1
            # 1110 0110           WR2
            # 1110 0111           WR3
            # 1110 1000           SBM
            # 1110 1001           RDM
            # 1110 1010           RDR
            # 1110 1011           ADM
            # 1110 1100           RD0
            # 1110 1101           RD1
            # 1110 1110           RD2
            # 1110 1111           RD3
            I_1110_0000,    I_1110_0001,    I_1110_0010,    I_1110_0011,
            I_1110_0100,    I_1110_0101,    I_1110_0110,    I_1110_0111,
            I_1110_1000,    I_1110_1001,    I_1110_1010,    I_1110_1011,
            I_1110_1100,    I_1110_1101,    I_1110_1110,    I_1110_1111,

            # 1111 0000           CLB
            # 1111 0001           CLC
            # 1111 0010           IAC
            # 1111 0011           CMC
            # 1111 0100           CMA
            # 1111 0101           RAL
            # 1111 0110           RAR
            # 1111 0111           TCC
            # 1111 1000           DAC
            # 1111 1001           TCS
            # 1111 1010           STC
            # 1111 1011           DAA
            # 1111 1100           KBP
            # 1111 1101           DCL
            I_1111_0000,    I_1111_0001,    I_1111_0010,    I_1111_0011,
            I_1111_0100,    I_1111_0101,    I_1111_0110,    I_1111_0111,
            I_1111_1000,    I_1111_1001,    I_1111_1010,    I_1111_1011,
            I_1111_1100,    I_1111_1101,    I_INV,          I_INV,
        ][byte]( stream, pos, byte )
        

def disassemble ( stream, start, stop ) :
    stream.seek(start)

    state = {
        "stream" : stream,
        "pos" : start,
    }

    pos = start

    while pos < stop :
        byte = ord(stream.read(1))
        
        state["hex"] = [
            f'{state["pos"]:08X}',
            f'{state["byte"]:03o}'
        ]
        state["pos"] += 1

        parse = parsetables["x86"][state["byte"]](state)
        if parse.startswith("PENDING") or parse.startswith("MISSING") :
            print(f'{" ".join(state["hex"]):50} {parse}')
        pos = state["pos"]
    pass

