class Function_Table:
    def __init__(self):
        self.table = {}

    def insert(self, f_name, r_type, p_type, line, ref):
        if (f_name in self.table.keys()):
            print("Error")
            return False
        else:
            f_new = Function_Entry(r_type, p_type, line, ref)
            self.table[f_name] = f_new
            return True

    def delete(self, f_name):
        if (f_name in self.table.keys()):
            del(self.table[f_name])
            return True
        else:
            return False

class Function_Entry:
    def __init__(self, r_type, p_type, line, ref):
        self.r_type = r_type
        self.p_type = p_type
        self.line = line
        self.ref = ref

class Symbol_Table:
    def __init__(self, ref):
        self.table = {}
        self.ref = ref

    def insert(self, name, s_type, s_length):
        if (name in self.table.keys()):
            s_next = self.table[name]
            s_new = Symbol_Entry(s_type, s_length, s_next)
            self.table[name] = s_new
        else:
            s_new = Symbol_Entry(s_type, s_length, None)
            self.table[name] = s_new

    def delete(self, name):
        if (name in self.table.keys()):
            del(self.table[name])
            return True
        else:
            return False

class Symbol_Entry:
    def __init__(self, s_type, s_length, s_next):
        self.type = s_type
        self.length = s_length
        self.next = s_next


def main():
    f_table = Function_Table()
    s_table = Symbol_Table(f_table)
    f_table.insert("f", "a", "b", 1, s_table)
    print(f_table.delete("f"))
    print(f_table.delete("f"))

if __name__ == "__main__":
    main()