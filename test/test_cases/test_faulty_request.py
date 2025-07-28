from unittest import TestCase
from Connection.Connection import Connection
from Connection.DBSocket.TCPSocket import TCPSocket
from LocalDB.Local import Local
from test.test_env import TEST_IP, TEST_PORT


class TestFaultyRequest(TestCase):
    db: Local

    @classmethod
    def setUpClass(cls) -> None:
        cls.db = Local.test_instance()

    def setUp(self) -> None:
        self.conn = Connection(socket=TCPSocket(TEST_IP, TEST_PORT))
        self.collection = self.conn.get_collection()

    def tearDown(self) -> None:
        self.conn.purge()
        self.conn.close()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db.kill()

    # Errors
    # Get
    def test_get_no_arg(self):
        with self.assertRaises(Exception):
            self.conn.get([])

    # Put
    def test_put_empty(self):
        with self.assertRaises(Exception):
            self.conn.put([], [])

        with self.assertRaises(Exception):
            self.conn.put([], [[]])

        with self.assertRaises(Exception):
            self.conn.put(self.collection.a, [])

        with self.assertRaises(Exception):
            self.conn.put([], self.collection.a)

    def test_put_quote_contamination(self):
        with self.assertRaises(Exception) as e:
            self.conn.put(self.collection.a, '"')

        self.assertEqual(
            "Err: 8: Invalid Token VALUE([')', ')']) after Value",
            str(e.exception)
        )

    def test_put_length_mismatch(self):
        values = [["1"], ["2"]]
        pointer_a = self.collection.a

        with self.assertRaises(Exception):
            self.conn.put(pointer_a, values)

    # Replace
    def test_replace_with_empty(self):
        pointer_a = self.collection.a
        new = []

        with self.assertRaises(Exception) as e:
            self.assertEqual(True, self.conn.replace(pointer_a, new))

        self.assertEqual(
            "Err: 4: Invalid Token RPAREN after Values",
            str(e.exception)
        )
