from unittest import TestCase
import re
from types import FunctionType
import inspect
import yaml
from Connection.DataPointer import DataPointer
from typing import get_type_hints, get_args, get_origin


from LocalDB.get_path import get_base_path
from LocalDB.Local import Local
from test.test_env import TEST_IP, TEST_PORT
from Connection.Connection import Connection
from Connection.DBSocket.TCPSocket import TCPSocket


class BlankLineDumper(yaml.SafeDumper):
    def write_line_break(self, data=None):
        super().write_line_break(data)
        # Add extra newline between top-level entries
        if len(self.indents) == 1:
            super().write_line_break()


class TestPermissions(TestCase):
    db: Local
    __pattern: str = r"Permissions<([^>]*)>"
    functions: dict = {}

    @classmethod
    def setUpClass(cls) -> None:
        # Set up matrix check:
        # functions with annotations %ignore Permission<read.get,-write>  # - explicitly puts false
        perm_file = "permission_test.yaml"
        def get_matches(text):
            re_match = re.search(cls.__pattern, text)

            if re_match:
                return re.findall(r"-?[\w\.]+", re_match.group(1))
            return []

        # Get the permissions from the annotations of each function
        instance_methods = {
            # add the permissions, - indicates False should be set. e.g. -write means no write
            name: {"authtoken": "auth", "operations": {k.strip("-"): False if k.startswith("-") else True for k in get_matches(attr.__doc__)}}
            for name, attr in cls.__dict__.items()
            if isinstance(attr, FunctionType) and name.startswith("test_")  # plain function, unbound
        }

        # Remove all where no permission more is needed
        instance_methods["root"] = {"authtoken": "root"}
        instance_methods["default"] = {"authtoken": "default", "operations": {"write": False, "read": False, "transaction": False}}

        # Create the yaml that has a permission for each test
        with open(str(get_base_path() / perm_file), "w", encoding="utf-8") as yaml_file:
            yaml.dump(instance_methods, yaml_file, Dumper=BlankLineDumper, default_flow_style=False)
        
        cls.db = Local.test_instance(permission_file=perm_file)

    def setUp(self) -> None:
        # Set up the root connection
        self.root_conn = Connection(socket=TCPSocket(TEST_IP, TEST_PORT))
        self.root_conn.authenticate("root", "root")
        self.root_collection = self.root_conn.get_collection()

        # Set up the permissions connection
        self.perm_conn = Connection(socket=TCPSocket(TEST_IP, TEST_PORT))
        # This loads the correct permission for each 
        self.perm_conn.authenticate(self._testMethodName, "auth")
        if self.perm_conn.user != self._testMethodName:
            raise PermissionError(f"Should have authenticated as <{self._testMethodName}> is <{self.perm_conn.user}> instead")


    def tearDown(self) -> None:
        self.root_conn.purge()
        self.root_conn.close()
        self.perm_conn.close()

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.db is not None:
            cls.db.kill()

    def test_write(self) -> None:
        """%ignore
        Permissions<write>
        """
        write_funcs = {
            k: v for k, v in self.functions.items()
            if "read" in v[0].__testhint__["op_type"]
        }
        for key, value in write_funcs.items():
            with self.subTest(key=key):
                func, data = value[0], value[1]
                data = {k: param_func(self) for k, param_func in data.items()}
                try:
                    func(self.perm_conn, **data)
                except Exception as e:
                    raise

def __set_up_functions(cls) -> None:
    # For every database operation function (with __testhint__ decorator) generate two test
    # These tests are then added to the TestPermissions Class
    for func_name, func in {
        k: v
        for k, v in Connection.__dict__.items()
        if isinstance(v, FunctionType)  # is a function
        and not k.startswith("_")
        and "__testhint__" in v.__dict__
    }.items():
        # Remove the 'self' from the function
        type_hints = get_type_hints(func)

        # This gets a dummy value generating lambda for every parameter that the function requires
        parameters = {}
        for parameter_name in inspect.signature(func).parameters.keys():
            if parameter_name == "self":
                continue
            
            type_hint = type_hints[parameter_name]
            # Get the first typehint, that is not a list
            type_hint = ([typehint for typehint in get_args(type_hint) if get_origin(typehint) is not list] or [type_hint])[0]

            # Create a lambda function that generates a dummy value
            value_generator = lambda *args, **kwargs: None
            match type_hint:
                case _ if type_hint is DataPointer:
                    value_generator = lambda self, *args, **kwargs: self.root_collection.a
                case _ if type_hint is str:
                    value_generator = lambda *args, **kwargs: "test"
            parameters[parameter_name] = value_generator

        # Get the operation type: read, write
        op_type = func.__testhint__['op_type']  # type: ignore

        # Permission name for the yaml file
        permission_name = f"{op_type}.{func_name}"
        
        # Generate the positive test, if all is false except that specific operation => it should work
        test_name = f"test__auto__{op_type}_{func_name}"
        def fn(self, _parameters=parameters, _func=func):
            _fn = {key: param_func(self) for key, param_func in _parameters.items()}
            _func(self.perm_conn, **_fn)
        fn.__doc__ = f"%ignore\nPermissions<{permission_name}>"
        setattr(cls, test_name, fn)

        # Generate the negative test, if all is true except that specific operation => it should not work
        negative_test_name = f"test__auto__{op_type}_{func_name}_denied"
        def fn_(self, _parameters=parameters, _func=func):
            with self.assertRaises(Exception) as err:
                _fn = {key: param_func(self) for key, param_func in _parameters.items()}
                _func(self.perm_conn, **_fn)

            self.assertIn("Permission", str(err.exception),  
                        msg=f"Expected 'Permission' in exception message, but got:\n{str(err.exception)}")

        fn_.__doc__ = f"%ignore\nPermissions<-{permission_name},write,read>"
        setattr(cls, negative_test_name, fn_)

        # ToDo, make it a lambda call
        # FIX THIS
        # This is so that you can check for every read / writes
        cls.functions[func_name] = (func, parameters)

    # print(cls.functions.items())
    # cls.__doc__ = str(cls.functions.items())



__set_up_functions(TestPermissions)
