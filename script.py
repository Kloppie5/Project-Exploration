
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
    #   UINT16 e_cparhdr -Size of header in paragraphs
    print(f"  e_cparhdr  : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 e_minalloc - Minimum extra paragraphs needed
    print(f"  e_minalloc : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 e_maxalloc - Maximum extra paragraphs needed
    print(f"  e_maxalloc : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 e_ss - Initial (relative) SSVirtualAddresslue
    print(f"  e_ss       : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 e_sp - Initial SPVirtualAddresslue
    print(f"  e_sp       : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 e_csum - Checksum
    print(f"  e_csum     : <ignored>"); f.seek(2,1)
    #   UINT16 e_ip - Initial IPVirtualAddresslue
    print(f"  e_ip       : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 e_cs - Initial (relative) CSVirtualAddresslue
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
    #   [4] Signature
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
    #   UINT16SizeOfOptionalHeader
    print(f"SizeOfOptionalHeader : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 Characteristics
    print(f"Characteristics      : {int.from_bytes(f.read(2), byteorder='little')}")
    print("-------------------")

def print_nonoptional_optional_header ( f ) :
    f.seek(60)
    e_lfanew = int.from_bytes(f.read(4), byteorder='little')
    f.seek(e_lfanew+24)
    print("---- OPTIONAL HEADER ----")
    # OPTIONAL_HEADER {
    #   UINT16 Magic
    print(f"Magic                                       : {int.from_bytes(f.read(2), byteorder='little')}")
        # 523 -> PE32+
    #   UINT8 MajorLinkerVersion
    print(f"MajorLinkerVersion                          : {int.from_bytes(f.read(1), byteorder='little')}")
    #   UINT8 MinorLinkerVersion
    print(f"MinorLinkerVersion                          : {int.from_bytes(f.read(1), byteorder='little')}")
    #   UINT32 SizeOfCode
    print(f"SizeOfCode                                  : {int.from_bytes(f.read(4), byteorder='little')}")
    #   UINT32 SizeOfInitializedData
    print(f"SizeOfInitializedData                       : {int.from_bytes(f.read(4), byteorder='little')}")
    #   UINT32 SizeOfUninitializedData
    print(f"SizeOfUninitializedData                     : {int.from_bytes(f.read(4), byteorder='little')}")
    #   UINT32 AddressOfEntryPoint
    print(f"AddressOfEntryPoint                         : {int.from_bytes(f.read(4), byteorder='little')}")
    #   UINT32 BaseOfCode
    print(f"BaseOfCode                                  : {int.from_bytes(f.read(4), byteorder='little')}")
    #   UINT64 ImageBase
    print(f"ImageBase                                   : {int.from_bytes(f.read(8), byteorder='little')}")
    #   UINT32 SectionAlignment
    print(f"SectionAlignment                            : {int.from_bytes(f.read(4), byteorder='little')}")
    #   UINT32 FileAlignment
    print(f"FileAlignment                               : {int.from_bytes(f.read(4), byteorder='little')}")
    #   UINT16 MajorOperatingSystemVersion
    print(f"MajorOperatingSystemVersion                 : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 MinorOperatingSystemVersion
    print(f"MinorOperatingSystemVersion                 : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 MajorImageVersion
    print(f"MajorImageVersion                           : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 MinorImageVersion
    print(f"MinorImageVersion                           : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 MajorSubsystemVersion
    print(f"MajorSubsystemVersion                       : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 MinorSubsystemVersion
    print(f"MinorSubsystemVersion                       : {int.from_bytes(f.read(2), byteorder='little')}")
    #   [4] Reserved1
    print(f"Reserved1                                   : <ignored>"); f.seek(4,1)
    #   UINT32 SizeOfImage
    print(f"SizeOfImage                                 : {int.from_bytes(f.read(4), byteorder='little')}")
    #   UINT32 SizeOfHeaders
    print(f"SizeOfHeaders                               : {int.from_bytes(f.read(4), byteorder='little')}")
    #   UINT32 CheckSum
    print(f"CheckSum                                    : {int.from_bytes(f.read(4), byteorder='little')}")
    #   UINT16 Subsystem
    print(f"Subsystem                                   : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT16 DllCharacteristics
    print(f"DllCharacteristics                          : {int.from_bytes(f.read(2), byteorder='little')}")
    #   UINT64 SizeOfStackReserve
    print(f"SizeOfStackReserve                          : {int.from_bytes(f.read(8), byteorder='little')}")
    #   UINT64 SizeOfStackCommit
    print(f"SizeOfStackCommit                           : {int.from_bytes(f.read(8), byteorder='little')}")
    #   UINT64 SizeOfHeapReserve
    print(f"SizeOfHeapReserve                           : {int.from_bytes(f.read(8), byteorder='little')}")
    #   UINT64 SizeOfHeapCommit
    print(f"SizeOfHeapCommit                            : {int.from_bytes(f.read(8), byteorder='little')}")
    #   UINT32 LoaderFlags
    print(f"LoaderFlags                                 : <ignored>"); f.seek(4,1)
    #   UINT32 NumberOfRvaAndSizes
    print(f"NumberOfRvaAndSizes                         : {int.from_bytes(f.read(4), byteorder='little')}")
    #   UINT32 ExportDirectoryVirtualAddress
    print(f"ExportDirectoryVirtualAddress               : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 ExportDirectorySize
    print(f"ExportDirectorySize                         : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 ImportDirectoryVirtualAddress
    print(f"ImportDirectoryVirtualAddress               : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 ImportDirectorySize
    print(f"ImportDirectorySize                         : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 ResourceDirectoryVirtualAddress
    print(f"ResourceDirectoryVirtualAddress             : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 ResourceDirectorySize
    print(f"ResourceDirectorySize                       : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 ExceptionDirectoryVirtualAddress
    print(f"ExceptionDirectoryVirtualAddress            : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 ExceptionDirectorySize
    print(f"ExceptionDirectorySize                      : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 SecurityDirectoryVirtualAddress
    print(f"SecurityDirectoryVirtualAddress             : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 SecurityDirectorySize
    print(f"SecurityDirectorySize                       : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 BaseRelocationTableVirtualAddress
    print(f"BaseRelocationTableVirtualAddress           : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 BaseRelocationTableSize
    print(f"BaseRelocationTableSize                     : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 DebugDirectoryVirtualAddress
    print(f"DebugDirectoryVirtualAddress                : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 DebugDirectorySize
    print(f"DebugDirectorySize                          : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 ArchitectureSpecificDataVirtualAddress
    print(f"ArchitectureSpecificDataVirtualAddress      : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 ArchitectureSpecificDataSize
    print(f"ArchitectureSpecificDataSize                : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 RVAofGPVirtualAddress
    print(f"RVAofGPVirtualAddress                       : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 RVAofGPSize
    print(f"RVAofGPSize                                 : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 TLSDirectoryVirtualAddress
    print(f"TLSDirectoryVirtualAddress                  : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 TLSDirectorySize
    print(f"TLSDirectorySize                            : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 LoadConfigurationDirectoryVirtualAddress
    print(f"LoadConfigurationDirectoryVirtualAddress    : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 LoadConfigurationDirectorySize
    print(f"LoadConfigurationDirectorySize              : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 BoundImportDirectoryinheadersVirtualAddress
    print(f"BoundImportDirectoryinheadersVirtualAddress : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 BoundImportDirectoryinheadersSize
    print(f"BoundImportDirectoryinheadersSize           : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 ImportAddressTableVirtualAddress
    print(f"ImportAddressTableVirtualAddress            : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 ImportAddressTableSize
    print(f"ImportAddressTableSize                      : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 DelayLoadImportDescriptorsVirtualAddress
    print(f"DelayLoadImportDescriptorsVirtualAddress    : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 DelayLoadImportDescriptorsSize
    print(f"DelayLoadImportDescriptorsSize              : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 COMRuntimedescriptorVirtualAddress
    print(f"COMRuntimedescriptorVirtualAddress          : {int.from_bytes(f.read(4), byteorder='little')}")
	#   UINT32 COMRuntimedescriptorSize
    print(f"COMRuntimedescriptorSize                    : {int.from_bytes(f.read(4), byteorder='little')}")
	#   [8] 0
    print(f"Padding                                     : <ignored>"); f.seek(8,1)
    print("-------------------------")   

def print_headers ( f ) :
    f.seek(60)
    e_lfanew = int.from_bytes(f.read(4), byteorder='little')
    f.seek(e_lfanew+6)
    NumberOfSections = int.from_bytes(f.read(2), byteorder='little')
    f.seek(e_lfanew+20)
    SizeOfOptionalHeader = int.from_bytes(f.read(2), byteorder='little')
    f.seek(e_lfanew+24+SizeOfOptionalHeader)
    
    for _ in range(NumberOfSections) :
        # SECTION_HEADER {
        #   [8] Name
        print(f"---- {f.read(8)} ----")
        #   UINT32 VirtualSize
        print(f"VirtualSize          : {int.from_bytes(f.read(4), byteorder='little')}")
        #   UINT32 VirtualAddress
        print(f"VirtualAddress       : {int.from_bytes(f.read(4), byteorder='little')}")
        #   UINT32 SizeOfRawData
        print(f"SizeOfRawData        : {int.from_bytes(f.read(4), byteorder='little')}")
        #   UINT32 PointerToRawData
        print(f"PointerToRawData     : {int.from_bytes(f.read(4), byteorder='little')}")
        #   UINT32 PointerToRelocations
        print(f"PointerToRelocations : {int.from_bytes(f.read(4), byteorder='little')}")
        #   UINT32 PointerToLinenumbers
        print(f"PointerToLinenumbers : {int.from_bytes(f.read(4), byteorder='little')}")
        #   UINT16 NumberOfRelocations
        print(f"NumberOfRelocations  : {int.from_bytes(f.read(2), byteorder='little')}")
        #   UINT16 NumberOfLinenumbers
        print(f"NumberOfLinenumbers  : {int.from_bytes(f.read(2), byteorder='little')}")
        #   UINT32 Characteristics
        print(f"Characteristics      : {int.from_bytes(f.read(4), byteorder='little')}")
        print(f"------------------")

with open("E:/SteamLibrary/steamapps/common/Monster Hunter World/MonsterHunterWorld.exe", "rb") as f:
    # hexview_line_gen(f, 1000)
    # print_dos_header(f)
    print_pe_header(f)
    print_nonoptional_optional_header(f)
    print_headers(f)
