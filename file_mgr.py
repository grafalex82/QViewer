import os

class FileMgr:
    def __init__(self):
        self.reset_current_dir()

    def reset_current_dir(self):
        self.__file_index = None
        self.__directory = None
        self.__directory_files = []
        self.__directory_subdirs = []

    def load_file(self, fname):
        if not fname:
            self.reset_current_dir()    
            return
        
        base_dir = os.path.dirname(os.path.realpath(fname))
        self.load_directory(base_dir)

        base_name = os.path.basename(os.path.realpath(fname))
        if not base_name in self.__directory_files:
            raise RuntimeError(f"File {fname} not found")
        self.__file_index = self.__directory_files.index(base_name)
        print(f"Setting current index to {self.__file_index}")

    def load_directory(self, directory):
        if not directory:
            self.reset_current_dir()
            return

        for entry in os.listdir(directory):
            full_path = os.path.join(directory, entry)
            if os.path.isdir(full_path):
                self.__directory_subdirs.append(entry)
                print(f"Directory: {entry}")
            else:
                self.__directory_files.append(entry)
                print(f"File: {entry}")
        
        self.__directory = directory
        self.__directory_files.sort()
        self.__directory_subdirs.sort()
        self.__file_index = 0
        print(f"Setting current directory to {self.__directory}")
        print(f"Files: {self.__directory_files}")
        print(f"Directories: {self.__directory_subdirs}")

            
    def current_file(self):
        if self.__file_index != None:
            fname = self.__directory_files[self.__file_index]
            return os.path.join(self.__directory, fname)
        return None

