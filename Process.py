import ctypes
import ctypes.wintypes

class Process ( object ):
    def __init__ ( self, name: str = None ):
        self.name = name
        self.pid = None
        self.handle = None

    def __repr__ ( self ) -> str:
        return f'{self.__class__.__name__}: "{self.name}"'

    def open_by_pid ( self, pid ) :
        handle = ctypes.windll.kernel32.OpenProcess(0x438, False, pid)
        if not handle:
            print(f'Unable to open process with pid {self.name}')
            return
        self.name = None
        self.pid = pid
        self.handle = handle   

    def get_pointer(self, lp_base_address: hex, offsets: List[hex] = ()) -> int:
        """
        Get the pointer of a given address.
        :param lp_base_address: The address from where you want to get the pointer.
        :param offsets: a list of offets.
        :return: The pointer of a give address.
        """
        temp_address = self.read(lp_base_address)
        pointer = 0x0
        if not offsets:
            return lp_base_address
        else:
            for offset in offsets:
                pointer = int(str(temp_address), 0) + int(str(offset), 0)
                temp_address = self.read(pointer)
            return pointer

    def read ( self, lp_base_address : int ) -> Any:
        read_buffer = ctypes.c_uint()
        lp_buffer = ctypes.byref(read_buffer)
        n_size = ctypes.sizeof(read_buffer)
        lp_number_of_bytes_read = ctypes.c_ulong(0)
        ctypes.windll.kernel32.ReadProcessMemory(self.handle, lp_base_address, lp_buffer, n_size, lp_number_of_bytes_read)
        return read_buffer.value


    def write(self, lp_base_address: int, value: int):
            write_buffer = ctypes.c_uint(value)
            lp_buffer = ctypes.byref(write_buffer)
            n_size = ctypes.sizeof(write_buffer)
            lp_number_of_bytes_written = ctypes.c_ulong(0)
            ctypes.windll.kernel32.WriteProcessMemory(self.handle, lp_base_address, lp_buffer, n_size, lp_number_of_bytes_written)



class ReadWriteMemory:
    def __init__(self):
        self.process = Process()

    def get_process_by_name(self, process_name: [str, bytes]) -> "Process":
        """
        :description: Get the process by the process executabe\'s name and return a Process object.
        :param process_name: The name of the executable file for the specified process for example, my_program.exe.
        :return: A Process object containing the information from the requested Process.
        """
        if not process_name.endswith('.exe'):
            self.process.name = process_name + '.exe'

        process_ids = self.enumerate_processes()

        for process_id in process_ids:
            self.process.handle = ctypes.windll.kernel32.OpenProcess(0x0400, False, process_id)
            if self.process.handle:
                image_file_name = (ctypes.c_char * MAX_PATH)()
                if ctypes.windll.psapi.GetProcessImageFileNameA(self.process.handle, image_file_name, MAX_PATH) > 0:
                    filename = os.path.basename(image_file_name.value)
                    if filename.decode('utf-8') == process_name:
                        self.process.pid = process_id
                        self.process.name = process_name
                        return self.process
                self.process.close()

        raise ReadWriteMemoryError(f'Process "{self.process.name}" not found!')

    def get_process_by_id(self, process_id: int) -> "Process":
        """
        :description: Get the process by the process ID and return a Process object.
        :param process_id: The process ID.
        :return: A Process object containing the information from the requested Process.
        """

        self.process.handle = ctypes.windll.kernel32.OpenProcess(0x0400, False, process_id)
        if self.process.handle:
            image_file_name = (ctypes.c_char * MAX_PATH)()
            if ctypes.windll.psapi.GetProcessImageFileNameA(self.process.handle, image_file_name, MAX_PATH) > 0:
                filename = os.path.basename(image_file_name.value)
                self.process.pid = process_id
                self.process.name = filename.decode('utf-8')
                self.process.close()
                return self.process
            else:
                raise ReadWriteMemoryError(f'Unable to get the executable\'s name for PID={self.process.pid}!')

        raise ReadWriteMemoryError(f'Process "{self.process.pid}" not found!')

    @staticmethod
    def enumerate_processes() -> list:
        """
        Get the list of running processes ID's from the current system.
        :return: A list of processes ID's
        """
        count = 32
        while True:
            process_ids = (ctypes.wintypes.DWORD * count)()
            cb = ctypes.sizeof(process_ids)
            bytes_returned = ctypes.wintypes.DWORD()
            if ctypes.windll.Psapi.EnumProcesses(ctypes.byref(process_ids), cb, ctypes.byref(bytes_returned)):
                if bytes_returned.value < cb:
                    return list(set(process_ids))
                else:
                    count *= 2