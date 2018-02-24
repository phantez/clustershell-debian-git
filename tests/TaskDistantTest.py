#!/usr/bin/env python
# ClusterShell (distant) test suite
# Written by S. Thiell 2009-02-13
# $Id: TaskDistantTest.py 289 2010-07-12 21:30:00Z st-cea $


"""Unit test for ClusterShell Task (distant)"""

import copy
import shutil
import sys
import unittest

sys.path.insert(0, '../lib')

from ClusterShell.Event import EventHandler
from ClusterShell.NodeSet import NodeSet
from ClusterShell.Task import *
from ClusterShell.Worker.Ssh import WorkerSsh
from ClusterShell.Worker.EngineClient import *

import socket

# TEventHandlerChecker 'received event' flags
EV_START=0x01
EV_READ=0x02
EV_WRITTEN=0x04
EV_HUP=0x08
EV_TIMEOUT=0x10
EV_CLOSE=0x20

class TaskDistantTest(unittest.TestCase):

    def setUp(self):
        self._task = task_self()
        self.assert_(self._task != None)

    def testLocalhostCommand(self):
        """test simple localhost command"""
        # init worker
        worker = self._task.shell("/bin/hostname", nodes='localhost')
        self.assert_(worker != None)
        # run task
        self._task.resume()
    
    def testLocalhostCommand2(self):
        """test two simple localhost commands"""
        # init worker
        worker = self._task.shell("/bin/hostname", nodes='localhost')
        self.assert_(worker != None)

        worker = self._task.shell("/bin/uname -r", nodes='localhost')
        self.assert_(worker != None)
        # run task
        self._task.resume()
    
    def testTaskShellWorkerGetCommand(self):
        """test worker.command with task.shell()"""
        worker1 = self._task.shell("/bin/hostname", nodes='localhost')
        self.assert_(worker1 != None)
        worker2 = self._task.shell("/bin/uname -r", nodes='localhost')
        self.assert_(worker2 != None)
        self._task.resume()
        self.assert_(hasattr(worker1, 'command'))
        self.assert_(hasattr(worker2, 'command'))
        self.assertEqual(worker1.command, "/bin/hostname")
        self.assertEqual(worker2.command, "/bin/uname -r")
    
    def testLocalhostCopy(self):
        """test simple localhost copy"""
        # init worker
        worker = self._task.copy("/etc/hosts",
                "/tmp/cs-test_testLocalhostCopy", nodes='localhost')
        self.assert_(worker != None)
        # run task
        self._task.resume()

    def testCopyNodeFailure(self):
        """test node failure error handling on simple copy"""
        # == stderr merged ==
        self._task.set_default("stderr", False)
        worker = self._task.copy("/etc/hosts",
                "/tmp/cs-test_testLocalhostCopyF", nodes='unlikely-node,localhost')
        self.assert_(worker != None)
        self._task.resume()
        self.assert_(worker.node_error_buffer("unlikely-node") is None)
        self.assert_(len(worker.node_buffer("unlikely-node")) > 2)

        # == stderr separated ==
        self._task.set_default("stderr", True)
        try:
            worker = self._task.copy("/etc/hosts",
                    "/tmp/cs-test_testLocalhostCopyF2", nodes='unlikely-node,localhost')
            self.assert_(worker != None)
            # run task
            self._task.resume()
            self.assert_(worker.node_buffer("unlikely-node") is None)
            self.assert_(len(worker.node_error_buffer("unlikely-node")) > 2)
        finally:
            self._task.set_default("stderr", False)

    def testLocalhostCopyDir(self):
        """test simple localhost directory copy"""
        # assume there is a /etc/rc.d directory
        dest = "/tmp/cs-test_testLocalhostCopyDirectory"
        shutil.rmtree(dest, ignore_errors=True)
        worker = self._task.copy("/etc/rc.d", dest, nodes='localhost')
        self.assert_(worker != None)
        # run task
        self._task.resume()

    def testLocalhostExplicitSshCopy(self):
        """test simple localhost copy with explicit ssh worker"""
        # init worker
        worker = WorkerSsh("localhost", source="/etc/hosts",
                dest="/tmp/cs-test_testLocalhostExplicitSshCopy",
                handler=None, timeout=10)
        self._task.schedule(worker) 
        self._task.resume()

    def testLocalhostExplicitSshCopyDir(self):
        """test simple localhost copy dir with explicit ssh worker"""
        # init worker
        dest = "/tmp/cs-test_testLocalhostExplicitSshCopyDirectory"
        shutil.rmtree(dest, ignore_errors=True)
        worker = WorkerSsh("localhost", source="/etc/rc.d",
                dest=dest, handler=None, timeout=10)
        self._task.schedule(worker) 
        self._task.resume()
        self.assertEqual(worker.source, "/etc/rc.d")
        self.assertEqual(worker.dest, dest)

    def testLocalhostExplicitSshCopyDirPreserve(self):
        """test simple localhost preserve copy dir with explicit ssh worker"""
        # init worker
        dest = "/tmp/cs-test_testLocalhostExplicitSshPreserveCopyDirectory"
        shutil.rmtree(dest, ignore_errors=True)
        worker = WorkerSsh("localhost", source="/etc/rc.d",
                dest=dest, handler=None, timeout=10, preserve=True)
        self._task.schedule(worker) 
        self._task.resume()

    def testExplicitSshWorker(self):
        """test simple localhost command with explicit ssh worker"""
        # init worker
        worker = WorkerSsh("localhost", command="/bin/echo alright", handler=None, timeout=5)
        self.assert_(worker != None)
        self._task.schedule(worker)
        # run task
        self._task.resume()
        # test output
        self.assertEqual(worker.node_buffer("localhost"), "alright")

    def testExplicitSshWorkerStdErr(self):
        """test simple localhost command with explicit ssh worker (stderr)"""
        # init worker
        worker = WorkerSsh("localhost", command="/bin/echo alright 1>&2",
                    handler=None, stderr=True, timeout=5)
        self.assert_(worker != None)
        self._task.schedule(worker)
        # run task
        self._task.resume()
        # test output
        self.assertEqual(worker.node_error_buffer("localhost"), "alright")

        # Re-test with stderr=False
        worker = WorkerSsh("localhost", command="/bin/echo alright 1>&2",
                    handler=None, stderr=False, timeout=5)
        self.assert_(worker != None)
        self._task.schedule(worker)
        # run task
        self._task.resume()
        # test output
        self.assertEqual(worker.node_error_buffer("localhost"), None)

    class TEventHandlerChecker(EventHandler):

        """simple event trigger validator"""
        def __init__(self, test):
            self.test = test
            self.flags = 0
            self.read_count = 0
            self.written_count = 0
        def ev_start(self, worker):
            self.test.assertEqual(self.flags, 0)
            self.flags |= EV_START
        def ev_read(self, worker):
            self.test.assertEqual(self.flags, EV_START)
            self.flags |= EV_READ
            self.last_node, self.last_read = worker.last_read()
        def ev_written(self, worker):
            self.test.assert_(self.flags & EV_START)
            self.flags |= EV_WRITTEN
        def ev_hup(self, worker):
            self.test.assert_(self.flags & EV_START)
            self.flags |= EV_HUP
            self.last_rc = worker.last_retcode()
        def ev_timeout(self, worker):
            self.test.assert_(self.flags & EV_START)
            self.flags |= EV_TIMEOUT
            self.last_node = worker.last_node()
        def ev_close(self, worker):
            self.test.assert_(self.flags & EV_START)
            self.test.assert_(self.flags & EV_CLOSE == 0)
            self.flags |= EV_CLOSE

    def testShellEvents(self):
        """test triggered events"""
        # init worker
        test_eh = self.__class__.TEventHandlerChecker(self)
        worker = self._task.shell("/bin/hostname", nodes='localhost', handler=test_eh)
        self.assert_(worker != None)
        # run task
        self._task.resume()
        # test events received: start, read, hup, close
        self.assertEqual(test_eh.flags, EV_START | EV_READ | EV_HUP | EV_CLOSE)
    
    def testShellEventsWithTimeout(self):
        """test triggered events (with timeout)"""
        # init worker
        test_eh = self.__class__.TEventHandlerChecker(self)
        worker = self._task.shell("/bin/echo alright && /bin/sleep 10", nodes='localhost', handler=test_eh,
                timeout=2)
        self.assert_(worker != None)
        # run task
        self._task.resume()
        # test events received: start, read, timeout, close
        self.assertEqual(test_eh.flags, EV_START | EV_READ | EV_TIMEOUT | EV_CLOSE)
        self.assertEqual(worker.node_buffer("localhost"), "alright")
        self.assertEqual(worker.num_timeout(), 1)
        self.assertEqual(self._task.num_timeout(), 1)
        count = 0
        for node in self._task.iter_keys_timeout():
            count += 1
            self.assertEqual(node, "localhost")
        self.assertEqual(count, 1)
        count = 0
        for node in worker.iter_keys_timeout():
            count += 1
            self.assertEqual(node, "localhost")
        self.assertEqual(count, 1)

    def testShellEventsWithTimeout2(self):
        """test triggered events (with timeout) (more)"""
        # init worker
        test_eh1 = self.__class__.TEventHandlerChecker(self)
        worker1 = self._task.shell("/bin/echo alright && /bin/sleep 10", nodes='localhost', handler=test_eh1,
                timeout=2)
        self.assert_(worker1 != None)
        test_eh2 = self.__class__.TEventHandlerChecker(self)
        worker2 = self._task.shell("/bin/echo okay && /bin/sleep 10", nodes='localhost', handler=test_eh2,
                timeout=3)
        self.assert_(worker2 != None)
        # run task
        self._task.resume()
        # test events received: start, read, timeout, close
        self.assertEqual(test_eh1.flags, EV_START | EV_READ | EV_TIMEOUT | EV_CLOSE)
        self.assertEqual(test_eh2.flags, EV_START | EV_READ | EV_TIMEOUT | EV_CLOSE)
        self.assertEqual(worker1.node_buffer("localhost"), "alright")
        self.assertEqual(worker2.node_buffer("localhost"), "okay")
        self.assertEqual(worker1.num_timeout(), 1)
        self.assertEqual(worker2.num_timeout(), 1)
        self.assertEqual(self._task.num_timeout(), 2)

    def testShellEventsReadNoEOL(self):
        """test triggered events (read without EOL)"""
        # init worker
        test_eh = self.__class__.TEventHandlerChecker(self)
        worker = self._task.shell("/bin/echo -n okay", nodes='localhost', handler=test_eh)
        self.assert_(worker != None)
        # run task
        self._task.resume()
        # test events received: start, close
        self.assertEqual(test_eh.flags, EV_START | EV_READ | EV_HUP | EV_CLOSE)
        self.assertEqual(worker.node_buffer("localhost"), "okay")

    def testShellEventsNoReadNoTimeout(self):
        """test triggered events (no read, no timeout)"""
        # init worker
        test_eh = self.__class__.TEventHandlerChecker(self)
        worker = self._task.shell("/bin/sleep 2", nodes='localhost', handler=test_eh)
        self.assert_(worker != None)
        # run task
        self._task.resume()
        # test events received: start, close
        self.assertEqual(test_eh.flags, EV_START | EV_HUP | EV_CLOSE)
        self.assertEqual(worker.node_buffer("localhost"), None)

    def testLocalhostCommandFanout(self):
        """test fanout with localhost commands"""
        fanout = self._task.info("fanout")
        self._task.set_info("fanout", 2)
        # init worker
        for i in range(0, 10):
            worker = self._task.shell("/bin/echo %d" % i, nodes='localhost')
            self.assert_(worker != None)
        # run task
        self._task.resume()
        # restore fanout value
        self._task.set_info("fanout", fanout)

    def testWorkerBuffers(self):
        """test buffers at worker level"""
        task = task_self()
        self.assert_(task != None)

        worker = task.shell("/usr/bin/printf 'foo\nbar\nxxx\n'", nodes='localhost')
        task.resume()

        cnt = 2
        for buf, nodes in worker.iter_buffers():
            cnt -= 1
            if buf == "foo\nbar\nxxx\n":
                self.assertEqual(len(nodes), 1)
                self.assertEqual(str(nodes), "localhost")
        self.assertEqual(cnt, 1)
        for buf, nodes in worker.iter_buffers("localhost"):
            cnt -= 1
            if buf == "foo\nbar\nxxx\n":
                self.assertEqual(len(nodes), 1)
                self.assertEqual(str(nodes), "localhost")
        self.assertEqual(cnt, 0)

    def testWorkerNodeBuffers(self):
        """test iter_node_buffers on distant workers"""
        task = task_self()
        self.assert_(task != None)

        worker = task.shell("/usr/bin/printf 'foo\nbar\nxxx\n'",
                            nodes='localhost')

        task.resume()

        cnt = 1
        for node, buf in worker.iter_node_buffers():
            cnt -= 1
            if buf == "foo\nbar\nxxx\n":
                self.assertEqual(node, "localhost")
        self.assertEqual(cnt, 0)

    def testWorkerNodeErrors(self):
        """test iter_node_errors on distant workers"""
        task = task_self()
        self.assert_(task != None)

        worker = task.shell("/usr/bin/printf 'foo\nbar\nxxx\n' 1>&2",
                            nodes='localhost', stderr=True)

        task.resume()

        cnt = 1
        for node, buf in worker.iter_node_errors():
            cnt -= 1
            if buf == "foo\nbar\nxxx\n":
                self.assertEqual(node, "localhost")
        self.assertEqual(cnt, 0)

    def testWorkerRetcodes(self):
        """test retcodes on distant workers"""
        task = task_self()
        self.assert_(task != None)

        worker = task.shell("/bin/sh -c 'exit 3'", nodes="localhost")

        task.resume()

        cnt = 2
        for rc, keys in worker.iter_retcodes():
            cnt -= 1
            self.assertEqual(rc, 3)
            self.assertEqual(len(keys), 1)
            self.assert_(keys[0] == "localhost")

        self.assertEqual(cnt, 1)

        for rc, keys in worker.iter_retcodes("localhost"):
            cnt -= 1
            self.assertEqual(rc, 3)
            self.assertEqual(len(keys), 1)
            self.assert_(keys[0] == "localhost")

        self.assertEqual(cnt, 0)

        # test node_retcode
        self.assertEqual(worker.node_retcode("localhost"), 3)   # 1.2.91+
        self.assertEqual(worker.node_rc("localhost"), 3)

        # test node_retcode failure
        self.assertRaises(KeyError, worker.node_retcode, "dummy")

        # test max retcode API
        self.assertEqual(task.max_retcode(), 3)

    def testWorkerNodeRetcodes(self):
        """test iter_node_retcodes on distant workers"""
        task = task_self()
        self.assert_(task != None)

        worker = task.shell("/bin/sh -c 'exit 3'", nodes="localhost")

        task.resume()

        cnt = 1
        for node, rc in worker.iter_node_retcodes():
            cnt -= 1
            self.assertEqual(rc, 3)
            self.assertEqual(node, "localhost")

        self.assertEqual(cnt, 0)

    
    def testEscape(self):
        """test distant worker (ssh) cmd with escaped variable"""
        worker = self._task.shell("export CSTEST=foobar; /bin/echo \$CSTEST | sed 's/\ foo/bar/'", nodes="localhost")
        # execute
        self._task.resume()
        # read result
        self.assertEqual(worker.node_buffer("localhost"), "$CSTEST")

    def testEscape2(self):
        """test distant worker (ssh) cmd with non-escaped variable"""
        worker = self._task.shell("export CSTEST=foobar; /bin/echo $CSTEST | sed 's/\ foo/bar/'", nodes="localhost")
        # execute
        self._task.resume()
        # read result
        self.assertEqual(worker.node_buffer("localhost"), "foobar")

    def testSshUserOption(self):
        """test task.shell() with ssh_user set"""
        ssh_user_orig = self._task.info("ssh_user")
        self._task.set_info("ssh_user", os.getlogin())
        worker = self._task.shell("/bin/echo foobar", nodes="localhost")
        self.assert_(worker != None)
        self._task.resume()
        # restore original ssh_user (None)
        self.assertEqual(ssh_user_orig, None)
        self._task.set_info("ssh_user", ssh_user_orig)

    def testSshUserOptionForScp(self):
        """test task.copy() with ssh_user set"""
        ssh_user_orig = self._task.info("ssh_user")
        self._task.set_info("ssh_user", os.getlogin())
        worker = self._task.copy("/etc/hosts",
                "/tmp/cs-test_testLocalhostCopyU", nodes='localhost')
        self.assert_(worker != None)
        self._task.resume()
        # restore original ssh_user (None)
        self.assertEqual(ssh_user_orig, None)
        self._task.set_info("ssh_user", ssh_user_orig)

    def testSshOptionsOption(self):
        """test task.shell() with ssh_options set"""
        ssh_options_orig = self._task.info("ssh_options")
        self._task.set_info("ssh_options", "-oLogLevel=DEBUG")
        worker = self._task.shell("/bin/echo foobar", nodes="localhost")
        self.assert_(worker != None)
        self._task.resume()
        # restore original ssh_user (None)
        self.assertEqual(ssh_options_orig, None)
        self._task.set_info("ssh_options", ssh_options_orig)

    def testSshOptionsOptionForScp(self):
        """test task.copy() with ssh_options set"""
        ssh_options_orig = self._task.info("ssh_options")
        self._task.set_info("ssh_options", "-oLogLevel=DEBUG")
        worker = self._task.copy("/etc/hosts",
                "/tmp/cs-test_testLocalhostCopyO", nodes='localhost')
        self.assert_(worker != None)
        self._task.resume()
        # restore original ssh_user (None)
        self.assertEqual(ssh_options_orig, None)
        self._task.set_info("ssh_options", ssh_options_orig)

    def testShellStderrWithHandler(self):
        """test reading stderr of distant task.shell() on event handler"""
        class StdErrHandler(EventHandler):
            def ev_error(self, worker):
                assert worker.last_error() == "something wrong"

        worker = self._task.shell("echo something wrong 1>&2", nodes='localhost',
                                  handler=StdErrHandler())
        self._task.resume()
        for buf, nodes in worker.iter_errors():
            self.assertEqual(buf, "something wrong")
        for buf, nodes in worker.iter_errors('localhost'):
            self.assertEqual(buf, "something wrong")

    def testShellWriteSimple(self):
        """test simple write on distant task.shell()"""
        worker = self._task.shell("cat", nodes='localhost')
        worker.write("this is a test\n")
        worker.set_write_eof()
        self._task.resume()
        self.assertEqual(worker.node_buffer("localhost"), "this is a test")

    def testShellWriteHandler(self):
        """test write in event handler on distant task.shell()"""
        class WriteOnReadHandler(EventHandler):
            def __init__(self, target_worker):
                self.target_worker = target_worker
            def ev_read(self, worker):
                self.target_worker.write("%s:%s\n" % worker.last_read())
                self.target_worker.set_write_eof()

        reader = self._task.shell("cat", nodes='localhost')
        worker = self._task.shell("sleep 1; echo foobar", nodes='localhost',
                                  handler=WriteOnReadHandler(reader))
        self._task.resume()
        self.assertEqual(reader.node_buffer("localhost"), "localhost:foobar")


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TaskDistantTest)
    unittest.TextTestRunner(verbosity=2).run(suite)

