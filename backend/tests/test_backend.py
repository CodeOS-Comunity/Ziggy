"""Ziggy backend tests — stdlib unittest, no pip dependencies.

Run:  python3 -m unittest discover -s backend/tests
"""

import threading
import unittest

import engine
from server import ZiggyHandler, DEFAULT_PORT


class EngineTests(unittest.TestCase):
    """Behaviour parity with the old in-kernel C engine, plus the Ziggy
    persona updates and the new Python-backend facts."""

    def test_exact_quit_and_exit_have_no_answer(self):
        self.assertIsNone(engine.response("quit"))
        self.assertIsNone(engine.response("exit"))

    def test_help(self):
        reply = engine.response("help")
        self.assertIn("Ask me about the kernel", reply)
        self.assertEqual(engine.response("?"), reply)

    def test_about_persona_is_ziggy(self):
        self.assertIn("Ziggy", engine.response("about"))
        self.assertIn("FreeCode", engine.response("about"))  # backstory kept

    def test_codeos_describes_the_os(self):
        self.assertIn("From scratch x86_64", engine.response("codeos"))

    def test_joke(self):
        self.assertIn("hide and seek", engine.response("joke"))

    def test_clear_is_control_reply(self):
        self.assertEqual(engine.response("clear"), "__CLEAR__")

    def test_greeting(self):
        self.assertIn("Didn't see you there", engine.response("hey there"))

    def test_kernel_memory_rule(self):
        self.assertIn("bitmap allocator", engine.response("kernel memory"))

    def test_kernel_scheduler_rule(self):
        self.assertIn("runqueues", engine.response("kernel scheduler"))

    def test_system_word_hits_hybrid_rule_before_monitor_rule(self):
        # C-order fidelity: OR(kernel/os/system) shadows the system+monitor
        # AND rule, so "system monitor" answers about the hybrid kernel.
        self.assertIn("Hybrid x86_64 kernel", engine.response("system monitor"))

    def test_file_word_hits_fs_rule_before_manager_rule(self):
        # C-order fidelity: OR(file/filesystem/ext2) shadows file+manager.
        self.assertIn("Ext2 primary", engine.response("file manager"))

    def test_ziggy_intro(self):
        reply = engine.response("what are you ziggy")
        self.assertIn("Python backend", reply)

    def test_freecode_renamed(self):
        self.assertIn("renamed", engine.response("freecode"))

    def test_help_without_kernel_lists_topics(self):
        # "help" mid-sentence (not a prefix command) + no "kernel" → topics.
        self.assertIn("I know about", engine.response("give me some help"))

    def test_help_with_kernel_does_not_list_topics(self):
        # "help" at the start is the exact help command (C match_exact) —
        # "help with kernel" still gets the help text, not the topic list.
        reply = engine.response("help with kernel")
        self.assertIn("Ugh, fine", reply)  # exact help command wins
        # A non-prefix "help" + "kernel" hits the kernel content rule first
        # (C order), so it never reaches the notand(help, !kernel) default.
        self.assertIn("Hybrid x86_64 kernel",
                      engine.response("want some help with kernel"))

    def test_package_topic_mentions_fetch_and_org(self):
        # "fetch" matches the CCP rule; no stemming ("packages" would not
        # match "package" — same as the C engine).
        self.assertIn("CodeOS-Comunity",
                      engine.response("how does fetch work"))

    def test_unknown_falls_back(self):
        self.assertIn("I dunno man", engine.response("what is the weather like"))

    def test_empty_prompt_is_no_answer(self):
        self.assertIsNone(engine.response("   "))


class ServerTests(unittest.TestCase):
    """In-process round trip through the real HTTP handler."""

    @classmethod
    def setUpClass(cls):
        import http.server
        from http.server import ThreadingHTTPServer
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), ZiggyHandler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def _post(self, body):
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("POST", "/query", body=body,
                     headers={"Content-Type": "text/plain"})
        resp = conn.getresponse()
        data = resp.read()
        conn.close()
        return resp.status, data

    def test_greeting_round_trip(self):
        status, data = self._post("hello ziggy".encode("utf-8"))
        self.assertEqual(status, 200)
        self.assertIn(b"Didn't see you there", data)

    def test_clear_round_trip(self):
        status, data = self._post(b"clear")
        self.assertEqual(status, 200)
        self.assertEqual(data, b"__CLEAR__")

    def test_no_answer_returns_204(self):
        status, data = self._post(b"quit")
        self.assertEqual(status, 204)
        self.assertEqual(data, b"")

    def test_unknown_path_404(self):
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", "/other")
        resp = conn.getresponse()
        resp.read()
        conn.close()
        self.assertEqual(resp.status, 404)


if __name__ == "__main__":
    unittest.main()