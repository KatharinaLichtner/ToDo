#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-

# memento pattern was used here, source: Skript "Undo", Session 17, ITT


class UndoRedo():

    # inits all important variables for undo and redo
    def __init__(self):
        super(UndoRedo, self).__init__()
        self.current = []
        self.undoRedo = [[[], []]]
        self.undoRedoTodo = []
        self.undoRedoDone = []
        self.undoRedoIndex = -1
        self.status = ""
        self.undoRedoLength = 5
        self.editIndex = 0

    # sets the status of the window to one status backwards
    def undo(self):
        self.undoRedoIndex -= 1
        self.undoRedoTodoList()
        self.undoRedoDoneList()
        self.status = "undo"
        return self.undoRedoTodo, self.undoRedoDone

    # sets the status of the window to one status forward
    def redo(self):
        if self.undoRedoIndex + 1 <= -1:
            self.undoRedoIndex += 1
        self.undoRedoTodoList()
        self.undoRedoDoneList()
        self.status = ""
        return self.undoRedoTodo, self.undoRedoDone

    # gets the updated to do list for undo or redo if there is any status left
    def undoRedoTodoList(self):
        if len(self.undoRedo) + self.undoRedoIndex >= 0:
            self.undoRedoTodo = self.undoRedo[self.undoRedoIndex][0][:]

    # gets the updated done list for undo or redo if there is any status left
    def undoRedoDoneList(self):
        if len(self.undoRedo) + self.undoRedoIndex >= 0:
            self.undoRedoDone = self.undoRedo[self.undoRedoIndex][1][:]

    # if a action like add, remove, check, uncheck was made, the to do and undo lists are updated
    def undoRedoUpdateLists(self):
        self.current = []
        self.current.append(self.undoRedoTodo[:])
        self.current.append(self.undoRedoDone[:])
        if self.status == "undo":
            self.undoRedo = self.undoRedo[:(self.undoRedoIndex + 1)][:]
            self.undoRedoIndex = -1
            self.status = ""

        self.undoRedo.append(self.current[:])
        if len(self.undoRedo) > self.undoRedoLength:
            length = len(self.undoRedo) - self.undoRedoLength
            self.undoRedo = self.undoRedo[length:][:]

    # a new entry is inserted and if there was a redo before, all the status afterwards are deleted
    def updateListsAddNewEntry(self, newEntry):
        self.undoRedoTodo.insert(0, newEntry)
        if self.status == "undo":
            self.undoRedo = self.undoRedo[:self.undoRedoIndex + 1][:]
            self.undoRedoIndex = -1
            self.status = ""

    # looks if it is the to do or the done tab, deletes the old item and adds the new edited one
    def updateListsEditEntry(self, tab, editIndex, editEntry):
        if tab == 0:
            del self.undoRedoTodo[editIndex]
            self.undoRedoTodo.insert(editIndex, editEntry)
        if tab == 1:
            del self.undoRedoDone[editIndex]
            self.undoRedoDone.insert(editIndex, editEntry)

    # the unchecked item is appended to the to do list and deleted of the done list
    def updateListsUncheck(self, row, text):
        self.undoRedoTodo.append(text)
        del self.undoRedoDone[row]

    # the checked item is appended to the done list and deleted of the to do list
    def updateListsCheck(self, text, x):
        self.undoRedoDone.append(text)
        del self.undoRedoTodo[x]

    # the item is deleted of the list that is given
    def updateListsDelete(self, tab, item):
        if item is not -1:
            if tab == 0:
                del self.undoRedoTodo[item]
            if tab == 1:
                del self.undoRedoDone[item]
            self.undoRedoUpdateLists()

    # sets the item one position up in the to do list
    def updateListsOneItemUpTodo(self, itemTodo, currentItem):
        del self.undoRedoTodo[itemTodo]
        self.undoRedoTodo.insert(itemTodo - 1, currentItem.text())
        self.undoRedoUpdateLists()

    # sets the item one position up in the done list
    def updateListsOneItemUpDone(self, itemDone, currentItem):
        del self.undoRedoDone[itemDone]
        self.undoRedoDone.insert(itemDone - 1, currentItem.text())
        self.undoRedoUpdateLists()

    # sets the item one position down in the to do list
    def updateListsOneItemDownTodo(self, itemTodo, currentItem):
        del self.undoRedoTodo[itemTodo]
        self.undoRedoTodo.insert(itemTodo + 1, currentItem.text())
        self.undoRedoUpdateLists()

    # sets the item one position down in the done list
    def updateListsOneItemDownDone(self, itemDone, currentItem):
        del self.undoRedoDone[itemDone]
        self.undoRedoDone.insert(itemDone + 1, currentItem.text())
        self.undoRedoUpdateLists()

    # sets the item to the top of the to do list
    def updateListsItemToTopTodo(self, itemTodo, currentItem):
        del self.undoRedoTodo[itemTodo]
        self.undoRedoTodo.insert(0, currentItem.text())
        self.undoRedoUpdateLists()

    # sets the item on the top of the done list
    def updateListsItemToTopDone(self, itemDone, currentItem):
        del self.undoRedoDone[itemDone]
        self.undoRedoDone.insert(0, currentItem.text())
        self.undoRedoUpdateLists()

    # sets the item on the buttom of the to do list
    def updateListsItemToBottomTodo(self, itemTodo, currentItem, newitempos):
        del self.undoRedoTodo[itemTodo]
        self.undoRedoTodo.insert(newitempos, currentItem.text())
        self.undoRedoUpdateLists()

    # sets the item on the bottom of the done list
    def updateListsItemToBottomDone(self, itemDone, currentItem, newitempos):
        del self.undoRedoDone[itemDone]
        self.undoRedoDone.insert(newitempos, currentItem.text())
        self.undoRedoUpdateLists()
