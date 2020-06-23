"""
    nonoptional OPTIONAL_HEADER {
        UINT16  Magic;
        UCHAR   MajorLinkerVersion;
        UCHAR   MinorLinkerVersion;
        UINT32   SizeOfCode;
        UINT32   SizeOfInitializedData;
        UINT32   SizeOfUninitializedData;
        UINT32   AddressOfEntryPoint;
        UINT32   BaseOfCode;
        UINT32   BaseOfData;
 
        UINT32   ImageBase;
        UINT32   SectionAlignment;
        UINT32   FileAlignment;
        UINT16  MajorOperatingSystemVersion;
        UINT16  MinorOperatingSystemVersion;
        UINT16  MajorImageVersion;
        UINT16  MinorImageVersion;
        UINT16  MajorSubsystemVersion;
        UINT16  MinorSubsystemVersion;
        UINT32   Reserved1;
        UINT32   SizeOfImage;
        UINT32   SizeOfHeaders;
        UINT32   CheckSum;
        UINT16  Subsystem;
        UINT16  DllCharacteristics;
        UINT32   SizeOfStackReserve;
        UINT32   SizeOfStackCommit;
        UINT32   SizeOfHeapReserve;
        UINT32   SizeOfHeapCommit;
        UINT32   LoaderFlags;
        UINT32   NumberOfRvaAndSizes;
        DATA_DIRECTORY DataDirectory[NUMBEROF_DIRECTORY_ENTRIES];
    }

    DATA_DIRECTORY {
        UINT32   VirtualAddress;
        UINT32   Size;
    }

    SECTION_HEADER {
        UCHAR   Name[IMAGE_SIZEOF_SHORT_NAME];
        union {
                UINT32   PhysicalAddress;
                UINT32   VirtualSize;
        } Misc;
        UINT32   VirtualAddress;
        UINT32   SizeOfRawData;
        UINT32   PointerToRawData;
        UINT32   PointerToRelocations;
        UINT32   PointerToLinenumbers;
        UINT16  NumberOfRelocations;
        UINT16  NumberOfLinenumbers;
        UINT32   Characteristics;
    }
"""

def hexview_line_gen ( f, limit = -1 ) :
    i = 0
    while 1:
        _hex = ""
        _asc = ""

        for _ in range(16):
            byte = f.read(1)
            if not byte:
                break 
            _hex += byte.hex()+" "
            _asc += byte.decode('utf-8', 'replace').replace(u'\ufffd', '.')
        
        print(f"{i:08d}: {_hex:48} {_asc:16}")
        
        if not byte or (limit != -1 and i > limit):
            break
        
        i += 1

def print_dos_header ( f ) :
    f.seek(0)
    # DOS_HEADER { 64 bytes
    print("---- DOS HEADER ----")
    #   UINT16 e_magic - Magic number
    print(f"  e_magic    : {f.read(2)}")
    #   UINT16 e_cblp - Bytes on the last page of the file
    print(f"  e_cblp     : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 e_cp - Pages in the file
    print(f"  e_cp       : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 e_crlc - Relocations
    print(f"  e_crlc     : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 e_cparhdr - Size of header in paragraphs
    print(f"  e_cparhdr  : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 e_minalloc - Minimum extra paragraphs needed
    print(f"  e_minalloc : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 e_maxalloc - Maximum extra paragraphs needed
    print(f"  e_maxalloc : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 e_ss - Initial (relative) SS value
    print(f"  e_ss       : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 e_sp - Initial SP value
    print(f"  e_sp       : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 e_csum - Checksum
    print(f"  e_csum     : <ignored>"); f.seek(2,1)
    #   UINT16 e_ip - Initial IP value
    print(f"  e_ip       : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 e_cs - Initial (relative) CS value
    print(f"  e_cs       : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 e_lfarlc - File address of relocation table
    print(f"  e_lfarlc   : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 e_ovno - Overlay number
    print(f"  e_ovno     : <ignored>"); f.seek(2,1)
    #   [8] e_res - Reserved words
    print(f"  e_res      : <ignored>"); f.seek(8,1)
    #   UINT16 e_oemid - OEM identifier
    print(f"  e_oemid    : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 e_oeminfo - OEM information
    print(f"  e_oeminfo  : {int.from_bytes(f.read(2), byteorder='little')}")
    #   [20] e_res2 - Reserved words
    print(f"  e_res2     : <ignored>"); f.seek(20,1)
    #   LONG e_lfanew - File address of new exe header
    print(f"  e_lfanew   : {int.from_bytes(f.read(4), byteorder='little')}")
    print("--------------------")

def print_pe_header ( f ) :
    f.seek(60)
    e_lfanew = int.from_bytes(f.read(4), byteorder='little')
    f.seek(e_lfanew)
    print("---- PE HEADER ----")
    # PE HEADER {
    #   [4] Signature;
    print(f"Signature            : {f.read(4)}")
    #   UINT16 Machine
    print(f"Machine              : {int.from_bytes(f.read(2), byteorder='little')}")
        # 34404 -> AMD64
    #   UINT16 NumberOfSections
    print(f"NumberOfSections     : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT32 TimeDateStamp
    print(f"TimeDateStamp        : {int.from_bytes(f.read(4), byteorder='little')}")
    #   UINT32 PointerToSymbolTable
    print(f"PointerToSymbolTable : {int.from_bytes(f.read(4), byteorder='little')}")
    #   UINT32 NumberOfSymbols
    print(f"NumberOfSymbols      : {int.from_bytes(f.read(4), byteorder='little')}")
    #   UINT16 SizeOfOptionalHeader
    print(f"SizeOfOptionalHeader : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 Characteristics
    print(f"Characteristics      : {int.from_bytes(f.read(2), byteorder='little')}")
    print("-------------------")
    

with open("E:/SteamLibrary/steamapps/common/Monster Hunter World/MonsterHunterWorld.exe", "rb") as f:
    hexview_line_gen(f, 1000)
    print_dos_header(f)
    print_pe_header(f)
