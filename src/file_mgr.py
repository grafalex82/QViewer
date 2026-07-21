import os
from dataclasses import dataclass, field
from datetime import datetime

UNDECIDED = "undecided"
KEEP = "keep"
REJECT = "reject"
DISCARD_DIRECTORY_NAME = ".qviewer-discarded"


@dataclass
class DiscardResult:
    """Result of moving files into a quarantine session directory.

    ``moved`` contains the original source paths that were moved. Their new
    locations are ``destination`` joined with each source basename.
    """

    destination: str | None = None
    moved: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)


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
            if os.path.isdir(full_path) and entry != DISCARD_DIRECTORY_NAME:
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


    def create_discard_directory(self, target_files=None):
        """Create and return a unique quarantine directory for *target_files*.

        When *target_files* is omitted, the currently loaded image list is used
        to decide whether there is any work to do. No directory is created for
        an empty target list.
        """
        if target_files is None:
            target_files = self.directory_files
        if not target_files or self.directory is None:
            return None

        discard_root = os.path.join(self.directory, DISCARD_DIRECTORY_NAME)
        os.makedirs(discard_root, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        suffix = 0
        while True:
            session_name = timestamp if suffix == 0 else f"{timestamp}-{suffix}"
            session_directory = os.path.join(discard_root, session_name)
            try:
                os.mkdir(session_directory)
                return session_directory
            except FileExistsError:
                suffix += 1


    def move_to_discard_directory(self, file_paths):
        """Move managed current-directory images into a new quarantine session.

        Invalid paths and individual rename failures are reported in the
        returned result. Processing continues after each failure, and the
        manager's directory listing is refreshed only after every move has
        been attempted.
        """
        # Return an empty result when there is no loaded directory or no work.
        result = DiscardResult()
        if not file_paths or self.directory is None:
            return result

        # Resolve the current and quarantine directories, and snapshot the
        # filenames that this manager is allowed to move.
        directory = os.path.realpath(self.directory)
        discard_root = os.path.realpath(
            os.path.join(directory, DISCARD_DIRECTORY_NAME)
        )
        managed_files = set(self.directory_files)
        candidates = []

        # Validate each supplied path independently so invalid inputs are
        # reported without preventing valid files from being processed.
        for supplied_path in file_paths:
            try:
                source = os.fspath(supplied_path)
            except TypeError as error:
                result.failed.append((str(supplied_path), str(error)))
                continue

            source = os.path.realpath(source)
            try:
                is_in_discard = (
                    os.path.commonpath((source, discard_root)) == discard_root
                )
            except ValueError:
                is_in_discard = False

            if is_in_discard:
                result.failed.append(
                    (source, "Path is already inside the quarantine directory")
                )
            elif os.path.isdir(source):
                result.failed.append((source, "Path is a directory, not an image file"))
            elif os.path.normcase(os.path.dirname(source)) != os.path.normcase(directory):
                result.failed.append((source, "Path is outside the current directory"))
            elif (
                os.path.basename(source) not in managed_files
                or not self.is_supported_image(source)
                or not os.path.isfile(source)
            ):
                result.failed.append((source, "Path is not a managed current-directory image"))
            else:
                candidates.append(source)

        # Avoid creating an empty quarantine session when every input failed
        # validation.
        if not candidates:
            return result

        # Create one quarantine session for all validated source files, or
        # report directory-creation failure against every candidate.
        try:
            result.destination = self.create_discard_directory(candidates)
        except OSError as error:
            result.failed.extend((source, str(error)) for source in candidates)
            return result

        # Build a collision-free move plan before changing the filesystem.
        destinations = set()
        moves = []
        for source in candidates:
            destination = os.path.join(result.destination, os.path.basename(source))
            normalized_destination = os.path.normcase(os.path.realpath(destination))
            if os.path.exists(destination) or normalized_destination in destinations:
                result.failed.append((source, "Destination file already exists"))
            else:
                destinations.add(normalized_destination)
                moves.append((source, destination))

        # Capture the selection before moving files so it can be restored or
        # replaced by the nearest survivor after the directory refresh.
        old_index = self.file_index
        current_path = self.current_file()
        if current_path is not None:
            current_path = os.path.realpath(current_path)

        # Attempt every planned move and retain per-file failures in the
        # result instead of aborting the remaining moves.
        for source, destination in moves:
            try:
                os.rename(source, destination)
                result.moved.append(source)
            except OSError as error:
                result.failed.append((source, str(error)))

        # Forget review states only for sources that actually moved.
        for source in result.moved:
            self.review_states.pop(source, None)

        # Refresh the directory and preserve the current image when possible;
        # otherwise select the old index clamped to the remaining files.
        self.directory_files, self.directory_subdirs = self.list_dir(self.directory)
        if not self.directory_files:
            self.file_index = None
        elif current_path is not None and current_path not in result.moved:
            current_basename = os.path.basename(current_path)
            self.file_index = self.directory_files.index(current_basename)
        elif old_index is None:
            self.file_index = 0
        else:
            self.file_index = min(old_index, len(self.directory_files) - 1)

        return result


    def delete_current_file(self):
        """Permanently delete the selected image and select its successor.

        The file list is changed only after the filesystem deletion succeeds.
        ``OSError`` is deliberately allowed to propagate so the UI can report
        the operating-system error without losing the current selection.
        """
        current_path = self.current_file()
        if current_path is None:
            return None

        current_path = os.path.realpath(current_path)
        old_index = self.file_index
        os.remove(current_path)
        self.review_states.pop(current_path, None)

        self.directory_files, self.directory_subdirs = self.list_dir(self.directory)
        if not self.directory_files:
            self.file_index = None
        else:
            self.file_index = min(old_index, len(self.directory_files) - 1)

        return current_path


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
