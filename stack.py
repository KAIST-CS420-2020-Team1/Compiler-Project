# Calls from the caller
# def function_call(caller_name, caller_line):
#     call_stack.link(CallContext(caller_name, caller_line))

# Returns to the caller
# def function_return(callee_val_table):
#    callee_val_table.free_local()
#    return call_stack.ret()

class ValueTable:
    def __init__(self):
        self.table = dict()
    # Allocates a local variable
    def allocate_local(self, name, value, line):
        self.table[name] = value_stack.allocate(value, line)
    # Frees all local variable
    def free_local(self):
        value_stack.free(len(self.table))
        self.table.clear()

    def has_value(self, name):
        return name in self.table
    # Gets address for given name
    def get_address(self, name):
        return self.table[name]
    # Gets value from address
    def get_value_from_address(self, addr):
        if addr >= 0 and addr < len(value_stack.values):
            return value_stack.get_value(addr)
        else:
            return None
    # Sets value from address
    def set_value_from_address(self, addr, value, line):
        value_stack.set_value(addr, value, line)
    def get_value(self, name):
        return value_stack.get_value(self.table[name])
    def get_history(self, name):
        return value_stack.get_history(self.table[name])
    def set_value(self, name, value, line):
        value_stack.set_value(self.table[name], value, line)

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
        if num != 0:
            self.values = self.values[:-num]

    def __get__(self, address):
        if(address == -1):
            return {"value": None, "history": []} # Not yet initialized
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
        entry = self.__get__(address)
        entry["value"] = value
        entry["history"] = entry["history"] + [(value, line)]

class CallStack:
    def __init__(self):
        self.called = []
    # Stores current context into the stack
    def link(self, ctxt):
        self.called = [ctxt] + self.called
    # Returns to the parent, returning the context
    def ret(self):
        ret_ctxt = self.called[0]
        self.called = self.called[1:]
        return ret_ctxt
    # Returns the top of the stack without popping
    def top(self):
        return self.called[0]


# Calling context. Stores parent function name and line
class CallContext:
    def __init__(self, fn_name, cur_line):
        self.name = fn_name
        self.line = cur_line

# These stacks are global
value_stack = ValueStack()
call_stack = CallStack()

def example_avg_call(value_table):
#    function_call("main", 16) # Calls this avg function from the main function
    if(isinstance(value_table, ValueTable)):
        value_table.allocate_local("hello", 3, 10) # 10> int hello = 3;
        value_table.allocate_local("done", 2.0, 12) # 12> int done = 2.0;
        value_table.set_value("hello", 5, 15) # 15> hello = 5;
        print(value_table.get_value("hello")) # print(hello)
#        return function_return(value_table)
    value_table.free_local() # Frees existing
