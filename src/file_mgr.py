import os

class FileMgr:
    def __init__(self):
        self.reset_current_dir()

    def reset_current_dir(self):
        self.file_index = None
        self.directory = None
        self.directory_files = []
        self.directory_subdirs = []


    def load_path(self, path):
        if path and os.path.isdir(path):
            self.load_directory(path)
        else:
            self.load_file(path)


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


    def load_directory(self, directory):
        if not directory:
            self.reset_current_dir()
            return

        self.directory_files, self.directory_subdirs = self.list_dir(directory)
        self.directory = directory
        self.file_index = 0 if len(self.directory_files) else None


    def list_dir(self, directory):
        files = []
        subdirs = []
        for entry in os.listdir(directory):
            full_path = os.path.join(directory, entry)
            if os.path.isdir(full_path):
                subdirs.append(entry)
            else:
                files.append(entry)

        files.sort()
        subdirs.sort()
        return files, subdirs

            
    def current_file(self):
        if self.file_index is not None:
            fname = self.directory_files[self.file_index]
            return os.path.join(self.directory, fname)
        return None


    def current_file_position(self):
        if self.file_index is None:
            return None

        return self.file_index + 1, len(self.directory_files)


    def current_directory(self):
        return self.directory


    def prev(self, allow_prev_dir = False):
        if self.file_index is None:
            return False
        
        if self.file_index > 0:
            self.file_index -= 1
            return True

        return False


    def next(self, allow_next_dir = False):
        if self.file_index is None:
            return False

        if self.file_index < len(self.directory_files) - 1:
            self.file_index += 1
            return True

        return False
    

    def first(self):
        if self.file_index is None:
            return False

        self.file_index = 0
        return True
    

    def last(self):
        if self.file_index is None:
            return False

        self.file_index = len(self.directory_files) - 1
        return True

    def next_dir(self):
        parent, dirname = os.path.split(self.directory)
        files, subdirs = self.list_dir(parent)
        index = subdirs.index(dirname)

        if index < len(subdirs) - 1:
            index += 1
            self.load_directory(os.path.join(parent, subdirs[index]))
            return True

        return False


    def prev_dir(self):
        parent, dirname = os.path.split(self.directory)
        files, subdirs = self.list_dir(parent)
        index = subdirs.index(dirname)

        if index > 0:
            index -= 1
            self.load_directory(os.path.join(parent, subdirs[index]))
            return True

        return False
