from Connection.Connection import Connection
from Connection.DBSocket.TCPSocket import TCPSocket
from test.test_env import TEST_IP, TEST_PORT

if __name__ == '__main__':
    # TODO Transactions
    # Instead of having execute, execute_single with parts, return the operation before hand.
    # Then decide in the handle_request function how to implement it.
    # Presumably with a flag that shows one is currently in a transaction
    # How to make sure execute_sequence runs uninterrupted?
    # Maybe acquire_lock-beforehand?
    # TODO: Transaction testing
    #
    # TODO Create Permissions
    # Permissions are given once authentication has occurred
    # Permission takes both user-permissions and db-mode into account
    #
    # Credential Storage
    #   cred-name: Server-Side unique name given for credentials
    #   auth-name: Necessary Name to receive this credential
    #   auth-token: Optional Auth Token
    #   ip-mask-list: Optional Ip mask list
    #   permission-dict: Necessary-Permission List
    #       commands:
    #           "-" minus stands for disallow something
    #           "+" plus stands for allowing something
    #           "get" get (which could be replaced by any other command)
    #               (transaction has to be one, else you can start but not stop one)
    #           "R*", "W*" "RW*", "C*" are groups which turn into all values
    #               (R* = Read, W* = Write, RW* = Readwrite, C* Control)
    #           example: +R* -has # means all reads except get
    #
    #   User(ip) -> send auth-name and if required auth-token
    #     If auth successful    -> upgrade Connection
    #     If auth unsuccessful  -> refuse Upgrade
    #
    # TODO Collection / Contract
    # Collection / Contract works like this
    # You have to select one, or you will use the standard contract
    # The last one selected will be used until a new one is selected
    # So Connection would store the last contract used.
    # And Collection would check, me == last_contract_used.
    # And if not, swap the collection
    #
    # TODO Create Empty
    # there is no method to definitively create an empty bag, should there be one?
    #
    # https://redis.io/docs/interact/transactions/#:~:text=Redis%20Transactions%20allow%20the%20execution,are%20serialized%20and%20executed%20sequentially.
    # TODO implement WATCH keyword from redis
    # ???
    #
    # TODO Persist and Load
    # Use read_handle.map_into()
    #
    from LocalDB.Local import Local

    local = Local.test_instance()
    socket = TCPSocket(TEST_IP, TEST_PORT)

    with Connection("user!auth/?name:name", socket=socket) as db:
        col = db.get_collection()
        print(db.put(col.a, "value1"))
        print(db.get(col.a))
        print(db.raw("PURGE", give_error=True))
        print(db.get(col.a))
        print("EXISTS:", db.exists(col.a), db.exists(col.b))
        print("GET:", db.get(col.a))
        print("HAS:", db.has(col.a, "a"), db.has(col.a, "b"), db.has(col.b, "b"))
        print("DELETE:", db.delete(col.b), db.exists(col.b))
        print("CLEAR:", db.clear(col.a), db.get(col.a))
        print("RETRACT:", db.put(col.a, "a2"), db.put(col.a, "a3"), db.retract(col.a, "a2"))
        print("REPLACE:", db.get(col.a), db.replace(col.a, "aReplace"))
        print("POP:", db.pop(col.a), db.get(col.a))
        db.put(col.a, ["a", "b"])
        # print("RAW:", db.raw("UnpollutedPartOfMessageMessagePollutedErrorPython"))
        # print("RAW2:", db.raw("Test"))
    exit(0)
