import os

UNDECIDED = "undecided"
KEEP = "keep"
REJECT = "reject"


class FileMgr:
    """Track the current directory and navigate its files and sibling folders.

    This class provides the viewer's filesystem-navigation model. It loads a
    file or directory, maintains the current file position, and exposes ordered
    movement between files and adjacent directories without depending on Qt.
    """

    SUPPORTED_IMAGE_EXTENSIONS = frozenset((".png", ".jpg", ".jpeg"))

    def __init__(self):
        self.review_states = {}
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


    @classmethod
    def is_supported_image(cls, path):
        """Return whether *path* has an image extension managed by QViewer."""
        return os.path.splitext(os.fspath(path))[1].lower() in cls.SUPPORTED_IMAGE_EXTENSIONS


    def list_dir(self, directory):
        files = []
        subdirs = []
        for entry in os.listdir(directory):
            full_path = os.path.join(directory, entry)
            if os.path.isdir(full_path):
                subdirs.append(entry)
            elif os.path.isfile(full_path) and self.is_supported_image(entry):
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


    def get_review_state(self, fname):
        """Return the review state for *fname*."""
        if not fname:
            return UNDECIDED

        return self.review_states.get(os.path.realpath(fname), UNDECIDED)


    def get_current_review_state(self):
        """Return the selected file's review state."""
        return self.get_review_state(self.current_file())


    def current_files_with_states(self, states):
        """Return current-directory files whose review state is in *states*."""
        if self.directory is None:
            return []

        matching_files = []
        for fname in self.directory_files:
            path = os.path.realpath(os.path.join(self.directory, fname))
            if self.get_review_state(path) in states:
                matching_files.append(path)
        return matching_files


    def current_rejected_files(self):
        """Return rejected files in the current directory."""
        return self.current_files_with_states({REJECT})


    def current_not_kept_files(self):
        """Return rejected and undecided files in the current directory."""
        return self.current_files_with_states({REJECT, UNDECIDED})


    def current_review_counts(self):
        """Return review-state counts for files in the current directory."""
        counts = {UNDECIDED: 0, KEEP: 0, REJECT: 0}
        if self.directory is None:
            return counts

        for fname in self.directory_files:
            path = os.path.realpath(os.path.join(self.directory, fname))
            counts[self.get_review_state(path)] += 1
        return counts


    def set_current_review_state(self, state):
        """Set the selected file's review state, if a file is selected."""
        fname = self.current_file()
        if fname is None:
            return
        if state not in (UNDECIDED, KEEP, REJECT):
            raise ValueError(f"Unknown review state: {state}")

        fname = os.path.realpath(fname)
        if state == UNDECIDED:
            self.review_states.pop(fname, None)
        else:
            self.review_states[fname] = state


    def toggle_keep(self):
        """Toggle Keep for the selected file."""
        if self.current_file() is None:
            return

        state = self.get_current_review_state()
        self.set_current_review_state(UNDECIDED if state == KEEP else KEEP)


    def toggle_reject(self):
        """Toggle Reject for the selected file."""
        if self.current_file() is None:
            return

        state = self.get_current_review_state()
        self.set_current_review_state(UNDECIDED if state == REJECT else REJECT)


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
