#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets, QtCore
import main as mainFile

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
        self.toDoList = mainFile.Window.toDoList
        self.doneList = mainFile.Window.doneList

    # sets the status of the window to one status backwards
    def undo(self):
        print("undo")
        self.undoRedoIndex -= 1
        self.undoRedoTodoList()
        self.undoRedoDoneList()
        self.status = "undo"

    # sets the status of the window to one status forward
    def redo(self):
        if self.undoRedoIndex + 1 <= -1:
            self.undoRedoIndex += 1
        self.undoRedoTodoList()
        self.undoRedoDoneList()
        self.status = ""

        # sets the to do list to a new state
    def undoRedoTodoList(self):
        print("undoRedoTodoList")
        if len(self.undoRedo) + self.undoRedoIndex >= 0:
            self.undoRedoTodo = self.undoRedo[self.undoRedoIndex][0][:]
        self.todoList.clear()
        print("todoList", self.toDoList.count())
        print("undoredotodo", self.undoRedoTodo)
        if len(self.undoRedoTodo) > 0:
            for i in range(len(self.undoRedoTodo)):
                item = QtWidgets.QListWidgetItem(self.undoRedoTodo[i])
                item.setCheckState(QtCore.Qt.Unchecked)
                self.toDoList.addItem(item)
            print(self.toDoList.item(0).text())
           # print(self.toDoList.item(1).text())
            self.toDoList.setCurrentRow(0)
            print("item", self.toDoList.item(0).text())

    # sets the done list to a new state
    def undoRedoDoneList(self):
        if len(self.undoRedo) + self.undoRedoIndex >= 0:
            self.undoRedoDone = self.undoRedo[self.undoRedoIndex][1][:]
        self.doneList.clear()
        if len(self.undoRedoDone) > 0:
            for i in range(len(self.undoRedoDone)):
                item = QtWidgets.QListWidgetItem(self.undoRedoDone[i])
                item.setCheckState(QtCore.Qt.Checked)
                self.doneList.addItem(item)
            self.doneList.setCurrentRow(0)

    # if a action like add, remove, check, uncheck was made, the tod o and undo lists are updated
    def undoRedoUpdateLists(self):
        self.current = []
        self.current.append(self.undoRedoTodo[:])
        self.current.append(self.undoRedoDone[:])
        print("current", self.current)

        if self.status == "undo":
            self.undoRedo = self.undoRedo[:(self.undoRedoIndex + 1)][:]
            self.undoRedoIndex = -1
            self.status = ""

        self.undoRedo.append(self.current[:])
        print("undoredo", self.undoRedo)

        if len(self.undoRedo) > self.undoRedoLength:
            length = len(self.undoRedo) - self.undoRedoLength
            self.undoRedo = self.undoRedo[length:][:]

    def updateListsAddNewEntry(self, newEntry):
        self.undoRedoTodo.insert(0, newEntry)
        if self.status == "undo":
            self.undoRedo = self.undoRedo[:self.undoRedoIndex + 1][:]
            self.undoRedoIndex = -1
            self.status = ""

    def updateListsEditEntry(self, tab, editIndex, editEntry):
        if tab == 0:
            del self.undoRedoTodo[editIndex]
            self.undoRedoTodo.insert(editIndex, editEntry)
        if tab == 1:
            del self.undoRedoDone[editIndex]
            self.undoRedoDone.insert(editIndex, editEntry)

    def updateListsUncheck(self, item, newItem):
        self.undoRedoTodo.append(item.text())
        del self.undoRedoDone[self.toDoList.row(item)]
        self.toDoList.insertItem(0, newItem)
        self.toDoList.setCurrentItem(newItem)

    def updateListsCheck(self, text, x):
        self.undoRedoDone.append(text)
        del self.undoRedoTodo[x]

    def updateListsDelete(self, tab, item):
        if item is not -1:
            if tab == 0:
                del self.undoRedoTodo[item]
            if tab == 1:
                del self.undoRedoDone[item]
            self.undoRedoUpdateLists()

    def updateListsOneItemUpTodo(self, itemTodo, currentItem):
        self.moveOneUp = False
        del self.undoRedoTodo[itemTodo]
        self.undoRedoTodo.insert(itemTodo - 1, currentItem.text())
        self.undoRedoUpdateLists()

    def updateListsOneItemUpDone(self, itemDone, currentItem):
        del self.undoRedoDone[itemDone]
        self.undoRedoDone.insert(itemDone - 1, currentItem.text())
        self.undoRedoUpdateLists()

    def updateListsOneItemDownTodo(self, itemTodo, currentItem):
        del self.undoRedoTodo[itemTodo]
        self.undoRedoTodo.insert(itemTodo + 1, currentItem.text())
        self.undoRedoUpdateLists()

    def updateListsOneItemDownDone(self, itemDone, currentItem):
        del self.undoRedoDone[itemDone]
        self.undoRedoDone.insert(itemDone + 1, currentItem.text())
        self.undoRedoUpdateLists()

    def updateListsItemToTopTodo(self, itemTodo, currentItem):
        del self.undoRedoTodo[itemTodo]
        self.undoRedoTodo.insert(0, currentItem.text())
        self.undoRedoUpdateLists()

    def updateListsItemToTopDone(self, itemDone, currentItem):
        del self.undoRedoDone[itemDone]
        self.undoRedoDone.insert(0, currentItem.text())
        self.undoRedoUpdateLists()

    def updateListsItemToBottomTodo(self, itemTodo, currentItem, newitempos):
        del self.undoRedoTodo[itemTodo]
        self.undoRedoTodo.insert(newitempos, currentItem.text())
        self.undoRedoUpdateLists()

    def updateListsItemToBottomDone(self, itemDone, currentItem, newitempos):
        del self.undoRedoDone[itemDone]
        self.undoRedoDone.insert(newitempos, currentItem.text())
        self.undoRedoUpdateLists()

def main():
    app = UndoRedo()


if __name__ == '__main__':
    main()
