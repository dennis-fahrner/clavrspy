from unittest import TestCase
from Connection.Connection import Connection, Transaction
from Connection.DBSocket.TCPSocket import TCPSocket
from LocalDB.Local import Local
from test.test_env import TEST_IP, TEST_PORT


class TestTransaction(TestCase):
    db: Local

    @classmethod
    def setUpClass(cls) -> None:
        cls.db = Local.test_instance()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db.kill()

    def setUp(self) -> None:
        self.conn_transaction = Connection(socket=TCPSocket(TEST_IP, TEST_PORT))
        self.conn_validation = Connection(socket=TCPSocket(TEST_IP, TEST_PORT))
        self.collection_transaction = self.conn_transaction.get_collection()
        self.collection_validation = self.conn_validation.get_collection()

    def tearDown(self) -> None:
        self.conn_transaction.close()
        self.conn_validation.close()

    def test_transaction(self):
        pointer_a = self.collection_transaction.a
        value = "test"
        with Transaction(self.conn_transaction) as t:
            self.conn_transaction.put(pointer_a, value)
            self.assertEqual([[]], self.conn_validation.get(pointer_a))

        self.assertEqual([[value]], self.conn_validation.get(pointer_a))

    def test_transaction_abort(self):
        pointer_a = self.collection_transaction.a
        value = "test"

        try:
            with Transaction(self.conn_transaction):
                self.conn_transaction.put(pointer_a, value)
                self.assertEqual([[]], self.conn_validation.get(pointer_a))
                raise SyntaxError
        except SyntaxError:
            pass
        finally:
            self.assertEqual([[]], self.conn_validation.get(pointer_a))

    def test_transaction_abort_manual(self):
        pointer_a = self.collection_transaction.a
        value = "test"

        with Transaction(self.conn_transaction) as t:
            self.conn_transaction.put(pointer_a, value)
            self.assertEqual([[]], self.conn_validation.get(pointer_a))
            t.abort()

        self.assertEqual([[]], self.conn_validation.get(pointer_a))

    def test_transaction_concurrent_write(self):
        pointer_a = self.collection_transaction.a
        value1 = "test1"
        value2 = "test2"

        with Transaction(self.conn_transaction) as t:
            self.conn_transaction.put(pointer_a, value2)
            self.assertEqual([[]], self.conn_validation.get(pointer_a))
            self.conn_validation.put(pointer_a, value1)

        self.assertEqual([[value1, value2]], self.conn_validation.get(pointer_a))
