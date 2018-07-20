#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-

class UndoRedo():

    # init status arrays for undo and redo
    def __init__(self):
        self.current = []
        self.undoRedo = [[[],[]]]
        self.undoRedoTodo = []
        self.undoRedoDone = []
        self.undoRedoIndex = -1
        self.status = ""
        self.undoRedoLength = 5
        self.editIndex = 0


def main():
    app = UndoRedo()


if __name__ == '__main__':
    main()
