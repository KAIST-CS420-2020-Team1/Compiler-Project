class ValueTable:
    def __init__(self, local_list):
        for local in local_list:
            self.table[local] = -1 # Invalid address
    # Allocates a local variable
    def allocate_local(self, name, value, line):
        self.table[name] = value_stack.allocate(value, line)
    # Frees all local variable
    def free_local(self):
        value_stack.free(len(self.table))

    def get_value(self):

        pass

class ValueStack:
    def __init__(self):
        # Local variables are stored in symbol table, free as many as that
        self.values = []
    # Allocates a value, returning current address of the value
    def allocate(self, value, line):
        index = len(self.values)
        self.values = self.values + [{"value": value, "history": [(value, line)]}]
        return index
    # Frees num amount of values - Can automate this process
    def free(self, num):
        self.values = self.values[:-num]

    def __get__(self, address):
        if(address > len(self.values) or address < 0):
            print("Error: Stack inconsistency")
        return self.values[address]
    # Attains certain value via address
    def get_value(self, address):
        return self.__get__(address)["value"]
    def get_history(self, address):
        return self.__get__(address)["history"]

    # Sets the value
    def set_value(self, address, value, line):
        entry = self.__get__(self, address)
        entry["value"] = value
        entry["history"] = entry["history"] + [(value, line)]

class CallStack:
    def __init__(self):
        self.called = []
    # Stores current context into the stack
    def call(self, ctxt):
        self.called = [ctxt] + self.called
    # Returns to the parent, returning the context
    def ret(self):
        self.called = self.called[1:]
        return self.called[0]

# Calling context
class CallContext:
    def __init__(self, fn_name, cur_line):
        self.name = fn_name
        self.line = cur_line

# These stacks are global
value_stack = ValueStack()
call_stack = CallStack()
