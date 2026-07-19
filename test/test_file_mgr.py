import os

import pytest
from file_mgr import KEEP, REJECT, UNDECIDED, FileMgr

@pytest.fixture
def mgr():
    yield FileMgr()

@pytest.fixture
def testdir(tmpdir):
    tmpdir.join("test1.jpg").write("")
    tmpdir.join("test2.jpg").write("")
    tmpdir.join("test3.jpg").write("")
    d1 = tmpdir.mkdir("Sub1")
    d1.join("test4.jpg").write("")
    d1.join("test5.jpg").write("")
    d1.join("test6.jpg").write("")
    d2 = tmpdir.mkdir("Sub2Empty")
    d3 = tmpdir.mkdir("Sub3")
    d3.join("test7.jpg").write("")
    d3.join("test8.jpg").write("")
    d3.join("test9.jpg").write("")
    yield tmpdir


def test_empty_mgr(mgr):
    assert mgr.current_file() == None
    assert mgr.current_file_position() == None


def test_load_file(mgr, testdir):
    fname = str(testdir.join("test1.jpg"))
    mgr.load_file(fname)
    assert fname == mgr.current_file()
    assert mgr.current_directory() == testdir


def test_load_path_with_file(mgr, testdir):
    fname = str(testdir.join("test2.jpg"))

    mgr.load_path(fname)

    assert mgr.current_file() == fname


def test_load_path_with_directory_loads_first_file(mgr, testdir):
    mgr.load_path(str(testdir))

    assert mgr.current_file() == testdir.join("test1.jpg")


def test_load_path_with_empty_directory(mgr, testdir):
    empty_dir = testdir.join("Sub2Empty")

    mgr.load_path(str(empty_dir))

    assert mgr.current_directory() == empty_dir
    assert mgr.current_file() == None


def test_load_directory(mgr, testdir):
    mgr.load_directory(testdir)
    assert mgr.current_file() == testdir.join("test1.jpg")
    assert mgr.current_directory() == testdir


def test_empty_directory(mgr, testdir):
    mgr.load_directory(testdir.join("Sub2Empty"))
    assert mgr.current_file() == None
    assert mgr.current_file_position() == None


def test_directory_manages_only_supported_direct_child_images(mgr, tmpdir):
    for name in ("photo.jpg", "photo.JPEG", "photo.png"):
        tmpdir.join(name).write("")
    for name in ("notes.txt", "metadata.json"):
        tmpdir.join(name).write("")
    subdir = tmpdir.mkdir("nested")
    subdir.join("nested.jpg").write("")
    quarantine = tmpdir.mkdir("quarantine")
    quarantine.join("discarded.jpg").write("")

    mgr.load_directory(tmpdir)

    assert mgr.directory_files == ["photo.JPEG", "photo.jpg", "photo.png"]
    assert mgr.current_file_position() == (1, 3)


@pytest.mark.parametrize(
    "name",
    ("photo.jpg", "photo.JPG", "photo.jpeg", "photo.JPEG", "photo.png", "photo.PNG"),
)
def test_supported_image_check_is_case_insensitive(name):
    assert FileMgr.is_supported_image(name)


@pytest.mark.parametrize("name", ("notes.txt", "metadata.json", "photo.jpg.tmp"))
def test_supported_image_check_rejects_unsupported_extensions(name):
    assert not FileMgr.is_supported_image(name)


def test_load_file_arbitrary(mgr, testdir):
    fname = str(testdir.join("test2.jpg"))  # Not the first and not the last in the directory
    mgr.load_file(fname)
    assert fname == mgr.current_file()
    assert mgr.current_file_position() == (2, 3)


def test_file_position_updates_during_navigation(mgr, testdir):
    mgr.load_file(testdir.join("test1.jpg"))
    assert mgr.current_file_position() == (1, 3)

    assert mgr.next()
    assert mgr.current_file_position() == (2, 3)

    assert mgr.last()
    assert mgr.current_file_position() == (3, 3)

    assert mgr.first()
    assert mgr.current_file_position() == (1, 3)


def test_next(mgr, testdir):
    mgr.load_file(testdir.join("test1.jpg"))
    assert mgr.next()
    assert mgr.current_file() == testdir.join("test2.jpg")


def test_next_fails_on_last_file(mgr, testdir):
    mgr.load_file(testdir.join("test3.jpg"))
    assert mgr.next() == False
    assert mgr.current_file() == testdir.join("test3.jpg")


def test_next_fails_on_empty_dir(mgr, testdir):
    mgr.load_directory(testdir.join("Sub2Empty"))
    assert mgr.next() == False
    assert mgr.current_file() == None


def test_prev(mgr, testdir):
    mgr.load_file(testdir.join("test2.jpg"))
    assert mgr.prev()
    assert mgr.current_file() == testdir.join("test1.jpg")


def test_prev_fails_on_first_file(mgr, testdir):
    mgr.load_file(testdir.join("test1.jpg"))
    assert mgr.prev() == False
    assert mgr.current_file() == testdir.join("test1.jpg")


def test_prev_fails_on_empty_dir(mgr, testdir):
    mgr.load_directory(testdir.join("Sub2Empty"))
    assert mgr.prev() == False
    assert mgr.current_file() == None


def test_first(mgr, testdir):
    mgr.load_file(testdir.join("test2.jpg"))
    assert mgr.first()
    assert mgr.current_file() == testdir.join("test1.jpg")


def test_first_fails_on_empty_dir(mgr, testdir):
    mgr.load_directory(testdir.join("Sub2Empty"))
    assert mgr.first() == False
    assert mgr.current_file() == None


def test_last(mgr, testdir):
    mgr.load_file(testdir.join("test2.jpg"))
    assert mgr.last()
    assert mgr.current_file() == testdir.join("test3.jpg")


def test_last_fails_on_empty_dir(mgr, testdir):
    mgr.load_directory(testdir.join("Sub2Empty"))
    assert mgr.last() == False
    assert mgr.current_file() == None


def test_next_dir(mgr, testdir):
    mgr.load_directory(testdir.join("Sub1"))
    assert mgr.next_dir() == True
    assert mgr.current_directory() == testdir.join("Sub2Empty")
    assert mgr.current_file() == None


def test_next_dir2(mgr, testdir):
    print(testdir.join("Sub2Empty"))
    mgr.load_directory(testdir.join("Sub2Empty"))
    assert mgr.next_dir() == True
    assert mgr.current_directory() == testdir.join("Sub3")
    assert mgr.current_file() == testdir.join("Sub3").join("test7.jpg")


def test_prev_dir(mgr, testdir):
    mgr.load_directory(testdir.join("Sub3"))
    assert mgr.prev_dir() == True
    assert mgr.current_directory() == testdir.join("Sub2Empty")
    assert mgr.current_file() == None


def test_prev_dir2(mgr, testdir):
    print(testdir.join("Sub2Empty"))
    mgr.load_directory(testdir.join("Sub2Empty"))
    assert mgr.prev_dir() == True
    assert mgr.current_directory() == testdir.join("Sub1")
    assert mgr.current_file() == testdir.join("Sub1").join("test4.jpg")


def test_newly_loaded_file_is_undecided(mgr, testdir):
    fname = testdir.join("test1.jpg")
    mgr.load_file(fname)

    assert mgr.get_review_state(fname) == UNDECIDED
    assert mgr.get_current_review_state() == UNDECIDED


@pytest.mark.parametrize(
    ("initial_state", "expected_state"),
    [
        (UNDECIDED, KEEP),
        (KEEP, UNDECIDED),
        (REJECT, KEEP),
    ],
)
def test_toggle_keep_transitions(mgr, testdir, initial_state, expected_state):
    mgr.load_file(testdir.join("test1.jpg"))
    mgr.set_current_review_state(initial_state)

    mgr.toggle_keep()

    assert mgr.get_current_review_state() == expected_state


@pytest.mark.parametrize(
    ("initial_state", "expected_state"),
    [
        (UNDECIDED, REJECT),
        (REJECT, UNDECIDED),
        (KEEP, REJECT),
    ],
)
def test_toggle_reject_transitions(mgr, testdir, initial_state, expected_state):
    mgr.load_file(testdir.join("test1.jpg"))
    mgr.set_current_review_state(initial_state)

    mgr.toggle_reject()

    assert mgr.get_current_review_state() == expected_state


def test_review_state_is_keyed_by_full_path(mgr, tmpdir):
    first = tmpdir.mkdir("first").join("same.jpg")
    second = tmpdir.mkdir("second").join("same.jpg")
    first.write("")
    second.write("")

    mgr.load_file(first)
    mgr.set_current_review_state(KEEP)
    mgr.load_file(second)
    mgr.set_current_review_state(REJECT)

    assert mgr.get_review_state(first) == KEEP
    assert mgr.get_review_state(second) == REJECT


def test_navigation_does_not_transfer_review_state(mgr, testdir):
    mgr.load_file(testdir.join("test1.jpg"))
    mgr.set_current_review_state(KEEP)

    mgr.next()

    assert mgr.get_current_review_state() == UNDECIDED
    assert mgr.get_review_state(testdir.join("test1.jpg")) == KEEP


def test_review_methods_are_no_ops_without_selected_file(mgr, testdir):
    mgr.load_directory(testdir.join("Sub2Empty"))

    mgr.set_current_review_state(KEEP)
    mgr.toggle_keep()
    mgr.toggle_reject()

    assert mgr.get_current_review_state() == UNDECIDED
    assert mgr.review_states == {}


def test_current_review_queries_return_matching_absolute_paths_in_navigation_order(mgr, tmpdir):
    for name in ("c.jpg", "a.jpg", "b.jpg"):
        tmpdir.join(name).write("")
    mgr.load_directory(tmpdir)

    mgr.load_file(tmpdir.join("a.jpg"))
    mgr.set_current_review_state(REJECT)
    mgr.load_file(tmpdir.join("b.jpg"))
    mgr.set_current_review_state(KEEP)
    mgr.load_file(tmpdir.join("c.jpg"))
    mgr.set_current_review_state(REJECT)
    selected_file = mgr.current_file()
    review_states = mgr.review_states.copy()

    assert mgr.current_rejected_files() == [
        os.path.realpath(tmpdir.join("a.jpg")),
        os.path.realpath(tmpdir.join("c.jpg")),
    ]
    assert mgr.current_files_with_states({KEEP}) == [
        os.path.realpath(tmpdir.join("b.jpg"))
    ]
    assert mgr.current_review_counts() == {UNDECIDED: 0, KEEP: 1, REJECT: 2}
    assert mgr.current_file() == selected_file
    assert mgr.review_states == review_states


def test_current_not_kept_includes_rejected_and_undecided_but_never_keep(mgr, tmpdir):
    for name in ("keep.jpg", "reject.jpg", "undecided.jpg"):
        tmpdir.join(name).write("")
    mgr.load_directory(tmpdir)

    mgr.load_file(tmpdir.join("keep.jpg"))
    mgr.set_current_review_state(KEEP)
    mgr.load_file(tmpdir.join("reject.jpg"))
    mgr.set_current_review_state(REJECT)

    assert mgr.current_not_kept_files() == [
        os.path.realpath(tmpdir.join("reject.jpg")),
        os.path.realpath(tmpdir.join("undecided.jpg")),
    ]


def test_current_review_queries_ignore_remembered_states_from_other_directory(mgr, tmpdir):
    previous = tmpdir.mkdir("previous")
    previous_file = previous.join("old.jpg")
    previous_file.write("")
    current = tmpdir.mkdir("current")
    current_file = current.join("new.jpg")
    current_file.write("")

    mgr.load_file(previous_file)
    mgr.set_current_review_state(REJECT)
    mgr.load_directory(current)

    assert mgr.current_rejected_files() == []
    assert mgr.current_not_kept_files() == [os.path.realpath(current_file)]
    assert mgr.current_review_counts() == {UNDECIDED: 1, KEEP: 0, REJECT: 0}


def test_current_review_queries_are_empty_for_empty_directory(mgr, tmpdir):
    mgr.load_directory(tmpdir)

    assert mgr.current_files_with_states({UNDECIDED, KEEP, REJECT}) == []
    assert mgr.current_rejected_files() == []
    assert mgr.current_not_kept_files() == []
    assert mgr.current_review_counts() == {UNDECIDED: 0, KEEP: 0, REJECT: 0}


def test_current_review_queries_exclude_unsupported_files(mgr, tmpdir):
    supported = tmpdir.join("photo.jpg")
    unsupported = tmpdir.join("notes.txt")
    supported.write("")
    unsupported.write("")
    mgr.load_directory(tmpdir)
    mgr.review_states[os.path.realpath(unsupported)] = REJECT

    assert mgr.current_rejected_files() == []
    assert mgr.current_not_kept_files() == [os.path.realpath(supported)]
    assert mgr.current_review_counts() == {UNDECIDED: 1, KEEP: 0, REJECT: 0}
