
def disassemble_x64 ( f, start, limit = -1 ) :
    print("DISASSEMBLING X86")
    def byte_stream () :
        f.seek(start)
        i = 0
        while 1:
            byte = f.read(1)
            if not byte: break 
            yield byte
            if limit != -1 and i > limit: break
            i += 1
    
    gen = byte_stream()
    try :
        while 1 :
            byte = next(gen)

            if byte == b'\x48' :
                print(f"48 - REX.W prefix")
                byte = next(gen)
                if byte == b'\x8D' :
                    print(f"   8D - LEA r r m")
                    
                    continue

                print(f"   {byte} - {'UNKNOWN'}")
                continue

            print(f"{byte} - {'UNKNOWN'}")
    except StopIteration : pass