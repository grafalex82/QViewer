import pytest
from file_mgr import FileMgr

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


def test_load_file(mgr, testdir):
    fname = str(testdir.join("test1.jpg"))
    mgr.load_file(fname)
    assert fname == mgr.current_file()


def test_load_directory(mgr, testdir):
    mgr.load_directory(testdir)
    assert mgr.current_file() == testdir.join("test1.jpg")


def test_empty_directory(mgr, testdir):
    mgr.load_directory(testdir.join("Sub2Empty"))
    assert mgr.current_file() == None


def test_load_file_arbitrary(mgr, testdir):
    fname = str(testdir.join("test2.jpg"))  # Not the first and not the last in the directory
    mgr.load_file(fname)
    assert fname == mgr.current_file()


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


