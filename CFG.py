import os


class Node:
    def __init__(self, block, line_list):
        self.index = -1
        self.prev = []
        self.next = []

        self.block = block
        self.line_list = line_list

        self.branch = False

    def insert_next(self, node):
        self.next.append(node)
        node.prev.append(self)
        if len(self.next) > 1:
            self.branch = True

    def insert_prev(self, node):
        self.prev.append(node)
        node.next.append(self)

    def get_next(self):
        return self.next

    def get_prev(self):
        return self.prev

    def get_line_list(self):
        return self.line_list

    def get_line(self, num):
        return self.block[self.line_list.index(num)]

    def find_prev_branch(self):
        pass

    def next_line(self, cur):
        if cur != max(self.get_line_list()):
            return self.get_line(cur+1)
        else:
            if cur+1 in self.get_next()[0].get_line_list():
                return self.get_next()[0].get_line(cur+1)
            else:
                raise Exception()


class Block:
    def __init__(self):
        pass
