from unittest import TestCase
from Connection.Connection import Connection
from Connection.ConnectionString import ConnectionString
from Connection.DBSocket.TCPSocket import TCPSocket
from LocalDB.Local import Local
from test.test_env import TEST_IP, TEST_PORT


class TestConnection(TestCase):
    db: Local

    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.db = Local.test_instance()
        except Exception as e:
            cls.db = None

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db.kill()

    def test_conn_string(self):
        user, auth, name, test = ("user", "auth", "name", "1")
        connection_string = ConnectionString(f"{user}@{auth}/?name:{name}&test:{test}")
        self.assertEqual(user, connection_string.user)
        self.assertEqual(auth, connection_string.auth)
        self.assertEqual(name, connection_string.name)
        self.assertEqual(int(test), connection_string.test)

    def test_conn_string_raises_empty(self):
        with self.assertRaises(ValueError):
            ConnectionString("")

    def test_conn_string_raises_duplicate(self):
        with self.assertRaises(ValueError):
            ConnectionString("user@auth/?name:name&name:name")

    def test_conn_string_raises_invalid_param(self):
        with self.assertRaises(ValueError):
            ConnectionString("user@auth/?uwu:test")

    def test_conn_string_raises_invalid_type(self):
        # Does not work figure it out
        with self.assertRaises(TypeError):
            ConnectionString("user@auth/?test:str")

    def test_conn_bare(self):
        connection = Connection(socket=TCPSocket(TEST_IP, TEST_PORT))
        self.assertEqual(True, connection.__alive__)
