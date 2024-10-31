import os

class FileMgr:
    def __init__(self):
        self.reset_current_dir()

    def reset_current_dir(self):
        self.file_index = None
        self.directory = None
        self.directory_files = []
        self.directory_subdirs = []


    def load_file(self, fname):
        if not fname:
            self.reset_current_dir()    
            return
        
        base_dir = os.path.dirname(os.path.realpath(fname))
        self.load_directory(base_dir)

        base_name = os.path.basename(os.path.realpath(fname))
        if not base_name in self.directory_files:
            raise RuntimeError(f"File {fname} not found")
        self.file_index = self.directory_files.index(base_name)
        print(f"Setting current index to {self.file_index}")


    def load_directory(self, directory):
        if not directory:
            self.reset_current_dir()
            return

        for entry in os.listdir(directory):
            full_path = os.path.join(directory, entry)
            if os.path.isdir(full_path):
                self.directory_subdirs.append(entry)
                print(f"Directory: {entry}")
            else:
                self.directory_files.append(entry)
                print(f"File: {entry}")
        
        self.directory = directory
        self.directory_files.sort()
        self.directory_subdirs.sort()
        self.file_index = 0
        print(f"Setting current directory to {self.directory}")
        print(f"Files: {self.directory_files}")
        print(f"Directories: {self.directory_subdirs}")

            
    def current_file(self):
        if self.file_index != None:
            fname = self.directory_files[self.file_index]
            return os.path.join(self.directory, fname)
        return None


    def prev(self, allow_prev_dir = False):
        if self.file_index == None:
            return
        
        if self.file_index > 0:
            self.file_index -= 1
            return True

        return False


    def next(self, allow_next_dir = False):
        if self.file_index == None:
            return

        if self.file_index < len(self.directory_files) - 1:
            self.file_index += 1
            return True

        return False
    

    def first(self):
        if self.file_index == None:
            return

        self.file_index = 0
    

    def last(self):
        if self.file_index == None:
            return

        self.file_index = len(self.directory_files) - 1

