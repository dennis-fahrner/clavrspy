from unittest import TestCase
from Connection.Connection import Connection
from Connection.DBSocket.TCPSocket import TCPSocket
from LocalDB.Local import Local
from test.test_env import TEST_IP, TEST_PORT


class TestRequest(TestCase):
    db: Local

    @classmethod
    def setUpClass(cls) -> None:
        cls.db = Local.test_instance(permission_file="permission.yaml")

    def setUp(self) -> None:
        self.conn = Connection(socket=TCPSocket(TEST_IP, TEST_PORT))
        self.conn.authenticate("root", "root")
        self.collection = self.conn.get_collection()

    def tearDown(self) -> None:
        self.conn.purge()
        self.conn.close()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db.kill()

    # READ-METHODS
    # GET-METHOD
    def test_get(self):
        a = self.collection.a
        value = "value"
        self.conn.put(a, value)

        self.assertEqual(
            [[value]],
            self.conn.get(a)
        )

    def test_get_empty(self):
        self.assertEqual(
            [[]],
            self.conn.get(self.collection.get_new_pointer()),
        )

    def test_get_empty_2(self):
        self.assertEqual(
            [[]],
            self.conn.get(self.collection.a)
        )

    def test_get_empty_3(self):
        self.assertNotEqual(
            [None],
            self.conn.get(self.collection.a)
        )

    def test_get_empty_many(self):
        self.assertEqual(
            [[], []],
            self.conn.get([self.collection.get_new_pointer(), self.collection.get_new_pointer()])
        )

    def test_get_empty_many_2(self):
        self.assertEqual(
            [[], [], []],
            self.conn.get([self.collection.a, self.collection.b, self.collection.c])
        )

    def test_get_multiple_entries(self):
        a = self.collection.a
        value = ["value1", "value2", "value3"]
        self.conn.put(a, value)

        self.assertEqual(
            [value],
            self.conn.get(a)
        )

    def test_get_some_in_string(self):
        a = self.collection.a
        b = self.collection.b
        value_a = "Some(['value'])"
        value_b = "Some(Some(['value'])"
        self.conn.put(a, value_a)
        self.conn.put(b, value_b)

        self.assertEqual(
            [[value_a]],
            self.conn.get(a)
        )

        self.assertEqual(
            [[value_b]],
            self.conn.get(b)
        )

    # EXISTS
    def test_exists(self):
        a, b = self.collection.get_new_pointer(), self.collection.get_new_pointer()
        self.conn.put(a, "_")

        self.assertEqual([True], self.conn.exists(a))
        self.assertEqual([False], self.conn.exists(b))

    # HAS
    def test_has(self):
        a = self.collection.a
        value = "value1"
        self.conn.put(a, value)
        self.assertEqual([True], self.conn.has(a, value))
        self.assertEqual([False], self.conn.has(a, "valueX"))

    def test_has_many(self):
        a = self.collection.a
        b = self.collection.b
        value = "value1"
        self.conn.put(a, value)
        self.assertEqual([True, False], self.conn.has([a, b], value))

    def test_has_empty(self):
        a = self.collection.a
        self.assertEqual(self.conn.has(a, "valueX"), [False])
        self.conn.put(a, "value1")
        self.assertEqual(self.conn.has(a, ""), [False])

    # WRITE
    # PUT-METHOD
    def test_put(self):
        a = "value1"
        pointer_a = self.collection.a
        self.conn.put(pointer_a, a)
        self.assertEqual([[a]], self.conn.get(pointer_a))

    def test_put_identical(self):
        value = "value1"
        pointer_a = self.collection.a
        self.conn.put(pointer_a, [value, value])
        self.assertEqual([[value, value]], self.conn.get(pointer_a))

    def test_put_many(self):
        a = ["value1", "value2"]
        pointer_a = self.collection.a
        self.conn.put(pointer_a, a)
        self.assertEqual([a], self.conn.get(pointer_a))

    def test_put_many_2(self):
        values = [["value11", "value12"], ["value21", "value22"]]
        pointer_a = self.collection.a
        pointer_b = self.collection.b
        self.conn.put([pointer_a, pointer_b], values)

        self.assertEqual([values[0]], self.conn.get(pointer_a))
        self.assertEqual([values[1]], self.conn.get(pointer_b))

    def test_put_many_sequential(self):
        values = ["value1", "value2", "value3", "value4"]
        pointer_a = self.collection.a

        for value in values:
            self.conn.put(pointer_a, value)

        self.assertEqual([values], self.conn.get(pointer_a))

    # DELETE
    def test_delete(self):
        pointer_a = self.collection.a
        self.conn.put(pointer_a, "value1")
        self.assertEqual([True], self.conn.exists(pointer_a))
        self.assertEqual(True, self.conn.delete(pointer_a))
        self.assertEqual([False], self.conn.exists(pointer_a))

    def test_delete_empty(self):
        pointer_a = self.collection.a
        self.assertEqual(True, self.conn.delete(pointer_a))
        self.assertEqual([False], self.conn.exists(pointer_a))

    def test_delete_many(self):
        pointer_a = self.collection.a
        pointer_b = self.collection.b
        self.conn.put(pointer_a, "value1")
        self.conn.put(pointer_b, "value2")

        self.assertEqual([True, True], self.conn.exists([pointer_a, pointer_b]))
        self.assertEqual(True, self.conn.delete([pointer_a, pointer_b]))
        self.assertEqual([False, False], self.conn.exists([pointer_a, pointer_b]))

    def test_delete_partial_empty(self):
        pointer_a = self.collection.a
        pointer_b = self.collection.b
        self.conn.put(pointer_a, "value1")

        self.assertEqual([True, False], self.conn.exists([pointer_a, pointer_b]))
        self.assertEqual(True, self.conn.delete([pointer_a, pointer_b]))
        self.assertEqual([False, False], self.conn.exists([pointer_a, pointer_b]))

    # CLEAR
    def test_clear(self):
        pointer_a = self.collection.a
        self.conn.put(pointer_a, "value1")
        self.assertEqual([True], self.conn.exists(pointer_a))
        self.assertEqual(True, self.conn.clear(pointer_a))
        self.assertEqual([[]], self.conn.get(pointer_a))

    def test_clear_empty(self):
        pointer_a = self.collection.a
        self.assertEqual(True, self.conn.clear(pointer_a))
        self.assertEqual([False], self.conn.exists(pointer_a))

    def test_clear_partial_empty(self):
        pointer_a = self.collection.a
        pointer_b = self.collection.b
        self.conn.put(pointer_a, "value")
        self.assertEqual([True], self.conn.exists(pointer_a))
        self.assertEqual(True, self.conn.clear([pointer_a, pointer_b]))
        self.assertEqual([True, False], self.conn.exists([pointer_a, pointer_b]))

    def test_clear_one(self):
        pointer_a = self.collection.a
        value = ["value1", "value2"]
        self.conn.put(pointer_a, value)
        self.assertEqual([value], self.conn.get(pointer_a))
        self.assertEqual(True, self.conn.clear(pointer_a))
        self.assertEqual([[]], self.conn.get(pointer_a))

    # RETRACT
    def test_retract(self):
        pointer_a = self.collection.a
        keep = ["keep1", "keep2", "keep3"]
        remove = ["remove1", "remove2", "remove3"]
        self.conn.put(pointer_a, value=keep + remove)
        self.assertEqual([keep + remove], self.conn.get(pointer_a))
        self.assertEqual(True, self.conn.retract(pointer_a, remove))
        self.assertEqual([keep], self.conn.get(pointer_a))

    def test_retract_empty(self):
        pointer_a = self.collection.a
        self.assertEqual(True, self.conn.retract(pointer_a, ["test"]))
        self.assertEqual([False], self.conn.exists(pointer_a))

    def test_retract_empty_pointer(self):
        pointer_a = self.collection.a
        value = "value"
        self.conn.put(pointer_a, value)
        self.assertEqual([[value]], self.conn.get(pointer_a))
        self.assertEqual(True, self.conn.retract(pointer_a, ["test"]))
        self.assertEqual([[value]], self.conn.get(pointer_a))

    def test_retract_multiple(self):
        pointer_a = self.collection.a
        keep = ["keep1", "keep2"]
        remove = ["remove1", "remove2"]
        self.conn.put(pointer_a, keep + remove)
        self.assertEqual(True, self.conn.retract(pointer_a, remove[1]))
        self.assertEqual([keep + [remove[0]]], self.conn.get(pointer_a))
        self.assertEqual(True, self.conn.retract(pointer_a, remove[0]))
        self.assertEqual([keep], self.conn.get(pointer_a))

    def test_retract_keep_sequence(self):
        pointer_a = self.collection.a
        remove = "remove"
        keep = ["1", "2", "3"]
        values = []
        for k in keep:
            values.append(k)
            values.append(remove)
        self.conn.put(pointer_a, values)
        self.assertEqual(True, self.conn.retract(pointer_a, remove))
        self.assertEqual([keep], self.conn.get(pointer_a))

    def test_retract_multiple_identical(self):
        # Removes just one instance of that value
        pointer_a = self.collection.a
        keep = "keep"
        remove = "remove"
        self.conn.put(pointer_a, [keep, remove, keep, remove])
        self.assertEqual(True, self.conn.retract(pointer_a, remove))
        self.assertEqual([[keep, keep]], self.conn.get(pointer_a))

    # REPLACE METHOD
    def test_replace(self):
        pointer_a = self.collection.a
        old = ["old1", "old2", "old3"]
        new = ["new1", "new2", "new3"]
        self.conn.put(pointer_a, old)
        self.assertEqual([old], self.conn.get(pointer_a))
        self.assertEqual(True, self.conn.replace(pointer_a, new))
        self.assertEqual([new], self.conn.get(pointer_a))

    def test_replace_empty(self):
        pointer_a = self.collection.a
        new = ["new1", "new2"]
        self.assertEqual(True, self.conn.replace(pointer_a, new))
        self.assertEqual([new], self.conn.get(pointer_a))

    def test_replace_with_other_pointer(self):
        pointer_a = self.collection.a
        pointer_b = self.collection.b
        values = ["value1", "value2"]
        self.conn.put(pointer_b, values)
        self.conn.replace(pointer_a, self.conn.get(pointer_b)[0])
        self.assertEqual(self.conn.get(pointer_b), self.conn.get(pointer_a))
        self.assertEqual([values], self.conn.get(pointer_a))

    # READ-WRITE
    # POP-METHOD
    def test_pop(self):
        pointer_a = self.collection.a
        values = ["value1", "value2"]
        self.conn.put(pointer_a, values)
        self.assertEqual(values, self.conn.pop(pointer_a))
        self.assertEqual([[]], self.conn.get(pointer_a))

    def test_pop_empty(self):
        pointer_a = self.collection.a
        self.assertEqual([], self.conn.pop(pointer_a))

    def test_pop_cleared_bag(self):
        pointer_a = self.collection.a
        self.conn.put(pointer_a, [["a"]])
        self.conn.clear(pointer_a)
        self.assertEqual([], self.conn.pop(pointer_a))
