# _*_ coding: UTF-8 _*_
##############################################################
## this module wraps around the panda keybpard event handling
## and holds the information about all (un-) pressed keys
##############################################################

from panda3d.core import *
from direct.showbase.ShowBase import ShowBase

# ---------------------------------------------------------
# ---------------------------------------------------------
# ---------------------------------------------------------

class KeyboardDevice():
    '''
    This class holds data about the keyboard
    '''
    def __init__(self):
        '''
        '''

        base.buttonThrowers[0].node().setButtonUpEvent("button-up")
        base.buttonThrowers[0].node().setButtonDownEvent("button")
        base.accept("button-up", self.setKey, [False])
        base.accept("button", self.setKey, [True])

        self.keys = {}

    # ---------------------------------------------------------

    def setKey(self, value, key):
        '''
        '''
        self.keys[key] = value
        #print [key, self.keys[key]]

    # ---------------------------------------------------------


if __name__ == "__main__":

    #from panda3d.core import *
    #from direct.showbase.ShowBase import ShowBase
    sb = ShowBase()

    k = KeyboardDevice()

    run()


