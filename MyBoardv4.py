# 
# This program sets up 4 MCP23017 port expanders as inputs as defined in DEVICE[] below
# This program uses the MUX TCA9548A with I2C address changed to x70 by  taking A0 to 3v, this avoided a conflict with the HT16K33 which is also x70.
# HT16K33 wired to channel 1 on MUX
# 4 MCP23017s are wired to channels 3, 4, 5, 6 for the reed switch matrix, on the MUX
# 
# 
# 
#

# Date   : 21 April 2017
#
# http://www.chess.fortherapy.co.uk/
#
#
# Copyright 2021 Alan Bishop
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


import smbus
import time
import math
import board
import busio
import datetime
import os.path

from RPLCD import i2c
from I2C_SW_CLS import *
from adafruit_ht16k33 import matrix
from ChessBoard import ChessBoard
from subprocess import call
import subprocess

ALchess = ChessBoard()

engine = subprocess.Popen(
    '/home/pi/Python Code Chess/stockfish13',
    universal_newlines=True,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,bufsize=1)

# Channel 7 0x25 mcp23017 Buttons
# Channel 1 0x26 i2c LCD Screen
# Channel 2 0x77 HT16k33 LED
# Channel 3 0x21 mcp23017 Reed Switches 1-2
# Channel 4 0x22 mcp23017 Reed Switches 3-4
# Channel 5 0x23 mcp23017 Reed Switches 5-6
# Channel 6 0x24 mcp23017 Reed Switches 7-8

# MUX Address =0x70

# MUX stuff
I2C_address = 0x70
I2C_bus_number = 1
bus = smbus.SMBus(I2C_bus_number)

osound = 2 #0 no sound 1 = beeps 2=speech
lhint = ''
#quitgame = False
soundstring = ['Nsnd','Beep','Speak']

cmd_beg= 'espeak '
cmd_end= ' 2>/dev/null' # To dump the std errors to /dev/null
fmove = 'Moves'


boardReed = [[5]*8,[5]*8,[5]*8,[5]*8,[5]*8,[5]*8,[5]*8,[5]*8]

mbrd = [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]# mbrd is the 8 columns of the chess board this sets them to 11111111 : open w

timemove = [1000,3000,6000,10000,15000,20000,25000,30000,60000,120000,180000,300000]
timemoves = ['1s  ','3s  ','6s  ','10s ','15s ','20s ','25s ','30s ','1min','2min','3min','5min']
movet = 1
white = True
skill = 1
slptime = 0.4

chcol =["a","b","c","d","e","f","g","h",'x','y']
DEVICE = [0x21,0x22,0x23, 0x24, 0x25]  # the 4 I2c Device address of the MCP23017s (A0-A2)
GPIOn = [0x12, 0x13]
IODIRA = 0x00 # A Pin direction register for first 8 ie 1 = input or 2= output
IODIRB = 0x01 # B Pin direction register
GPIOA  = 0x12 # Register for inputs
GPIOB  = 0x13 # B Register for inputs
GPPUA = 0x0C  # Register for Pull ups A
GPPUB = 0x0D  # Register for Pull ups B
# first we do a one time setup of the MCPs
for i in range(0,5):  # for each of the 4 MCPs
# MCPs on channels 3, 4, 5, 6, 7 
    i2c_channel=i+3 # calculates binary that gives channel pos, ie channel 0 is 0b00000001 and channel 4 is b0b00010000
    
    SW.chn(i2c_channel)
       
    #for each of the 4 devices
  # Set all A 8 GPA pins as  input. ie set them to 1 oXFF = 11111111
    bus.write_byte_data(DEVICE[i],IODIRA,0xFF)
  # Set pull up on GPA pins .ie from default of 0 to 11111111
    bus.write_byte_data(DEVICE[i],GPPUA,0xFF)
  # Set all B 8 GPB pins as  input. ie set them to 1 oXFF = 11111111
    bus.write_byte_data(DEVICE[i],IODIRB,0xFF)
  # Set pull up on GPB pins .ie from default of 0 to 11111111
    bus.write_byte_data(DEVICE[i],GPPUB,0xFF)

# tested 22/1/2021 
# Create display instance on default I2C address (0x70) and bus number.
SW.chn(1) #change mux bus channel to 1

lcdmode = 'i2c'
cols = 20
rows = 4
charmap = 'A00'
i2c_expander = 'PCF8574'
address = 0x26
port = 1

# Initialise the LCD
lcd = i2c.CharLCD(i2c_expander, address, port=port, charmap=charmap,
                  cols=cols, rows=rows)


# Switch off backlight
#lcd.backlight_enabled = False 
# Clear the LCD screen
lcd.close(clear=True)

SW.chn(2) # switch to channel 2 HT16k33 LED Board
# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)
matrix = matrix.Matrix16x8(i2c)
# try blink rates 0-3
matrix.blink_rate = 2

def LCD(x,y,t):
    SW.chn(1)
    if x<0:x=0
    if x>3:x=3
    if y<0:y=0
    if y>19:y=19
    lcd.cursor_pos = (x, y)
    lcd.write_string(t)

def LCDclear():
    SW.chn(1)
    lcd.close(clear=True)

def ledmx(x,y,z):
    SW.chn(2) # switch to HT16k33 BUS (2)
    matrix[y, x]=z
    
def ReadButtons():
    SW.chn(7)
    return bus.read_byte_data(0x25,0x12)
    
def ReadBoard():
  # read the 8 registers
    xp = 0
    yp = 0
    zp = 0
    for k in range(0,4):  
         # calculates binary that gives channel pos, ie channel 0 is 0b00000001 and channel 4 is b0b00010000
        SW.chn(k+3)
        for l in range(2):  # for each MCP register A and B
            #print(str(k)+' '+str(l)+' '+str((k*2)+l))
            a = bus.read_byte_data(DEVICE[k],GPIOn[l])
            x=(k*2)+l
            #mbrd[x]=a
            #print (str(x)+'  '+str(a))
            if a != mbrd[x]: # there has been a change
                c = a ^ mbrd[x]  # bitwise operation copies the bit if it is set in one operand but not both.
                #dirx = "Put Down"
                zp = 88
                if a > mbrd[x]:
                    #dirx = "Picked UP"
                    zp = 99
                y = math.frexp(c)[1]  # calculates integer part of log base 2, which is binary bit position
                    
                xp = abs(x+1)
                yp = abs(y-8)
                #print (chcol[yp], xp, dirx)
                    
                mbrd[x]=a  # update the current state of the board
            
        
    for k in range(0,8):
        bp=1
        a=mbrd[k]
        for l in range(0,8):
            #a=mbrd[abs(r-7)]
            a=mbrd[k]
                   
            sq=a&bp
            #print (str(k)+' '+str(a)+' '+str(sq))
            
            boardReed[k][l]=0
            if sq>0:
                boardReed[k][l]=1
                
            bp = bp << 1
            
            #print (bp)
    return xp,yp,zp

    
def RBoardSquare(r,c):
    ReadBoard()
    r = abs(r-7)
  
    return boardReed[c][r]

           
def whoosepiece(p):
    # returns 3 if empty space
    # returns 1 if your own piece
    # returns 2 if opponents piece
    # returns 0 Error
    
    pn = ord(p)
    
    if pn == 46: return 3 # empty square
    
    if white == True:
        if pn > 64 and pn < 91:
            return 1 
        else:
            return 2
    
    if white == False:
        if pn >96 and pn < 123:
            return 1
        else:
            return 2
    return 0

def printb():
    print ("  +-----------------+")
    
    for l in range(0,8):
        print (str(boardReed[l][0])+' '+str(boardReed[l][1])+' '+str(boardReed[l][2])+' '+str(boardReed[l][3])+' '+str(boardReed[l][4])+' '+str(boardReed[l][5])+' '+str(boardReed[l][6])+' '+str(boardReed[l][7]))
            
        

        
    print ("  +-----------------+")
    print ("    reedBOARD")  



    print ("  +-----------------+")
    for l in range(1,9):
            
        print (ALchess.WhatsOnSquare(1,l)+' '+ALchess.WhatsOnSquare(2,l)+' '+ALchess.WhatsOnSquare(3,l)+' '+ALchess.WhatsOnSquare(4,l)+' '+ALchess.WhatsOnSquare(5,l)+' '+ALchess.WhatsOnSquare(6,l)+' '+ALchess.WhatsOnSquare(7,l)+' '+ALchess.WhatsOnSquare(8,l))               
    print ("  +-----------------+")
    print ("    chessboard")

    print('mbrd '+str(mbrd[0])+' '+str(mbrd[1])+' '+str(mbrd[2])+' '+str(mbrd[3])+' '+str(mbrd[4])+' '+str(mbrd[5])+' '+str(mbrd[6])+' '+str(mbrd[7]))

def piecestring(asc):
    if asc == 80:
        return 'White Pawn'
    if asc == 82:
        return 'White Rook' 
    if asc == 78:
        return 'White Knight'
    if asc == 66:
        return 'White Bishop'
    if asc == 75:
        return 'White King'
    if asc == 81:
        return 'White Queen'

    if asc == 112:
        return 'Black Pawn'
    if asc == 114:
        return 'Black Rook' 
    if asc == 110:
        return 'Black Knight'
    if asc == 98:
        return 'Black Bishop'
    if asc == 107:
        return 'Black King'
    if asc == 113:
        return 'Black Queen'

    return 'Space'

def VerifyBoard():
    db = [0,0,0]
    
    pieceout = False
        
    db = ReadBoard()
    Gamemenu(2,'Next','',' ','Exit')
    PlaySound('Verify Board',True)
    Leave = False
    gbutp = 255
    for x in range(0,8):
        for y in range(0,8):
            yp=abs(y-7)
            reed=boardReed[x][y]
            piece = ord(ALchess.WhatsOnSquare(yp+1,x+1))
            
            pstring = piecestring(piece)
           
            
            if Leave != True:                            
                if piece == 46 and reed == 0: #Empty square its got a piece on it
                    ledmx(yp,x,1)
                    Gamemessage(1,'Remove Piece '+chcol[yp]+str(x+1))
                    PlaySound(pstring +' '+chcol[yp]+str(x+1),True)
                    pieceout =True
                 
            
                if piece >64 and piece <91 and reed == 0: #its a white piece
                    ledmx(yp,x,1)
                    Gamemessage(1,pstring +' '+chcol[yp]+str(x+1))
                    PlaySound(pstring +' '+chcol[yp]+str(x+1),True)
                    pieceout = True
                
          
                if piece >96 and piece <123 and reed == 0: #its a black piece
                    ledmx(yp,x,1)
                    Gamemessage(1,pstring +' '+chcol[yp]+str(x+1))
                    PlaySound(pstring +' '+chcol[yp]+str(x+1),True)
                    pieceout = True
                    
            
                gbutp = 255
                
                if pieceout == True:
                    gbutp = 255
                
                    while gbutp == 255:
                        gbutp = ReadButtons()
                        
            if gbutp == 247:
                Leave = True        
            
            ledmx(yp,x,0)
                
    PlaySound('Leaving Verify Board',False)       
    Gamemenu(2,' ',' ',' ',' ')          
    time.sleep(slptime)    

def SyncBoard():
    db = [0,0,0]
    
    pieceout = False
    
    while pieceout == False:
        
        db = ReadBoard()
        pieceout = True
        
        for x in range(0,8):
            for y in range(0,8):
                yp=abs(y-7)
                reed=boardReed[x][y]
                piece = ord(ALchess.WhatsOnSquare(yp+1,x+1))
            
                pstring = piecestring(piece)            
                        
                if piece == 46 and reed == 0: #its an empty square and its got a piece on it
                    
                    pieceout = False
                    Gamemessage(1,'Remove Piece '+chcol[yp]+str(x+1))
                   
                    ledmx(yp,x,1)
                    PlaySound('Remove Piece '+chcol[yp]+str(x+1),True)
                
                    while boardReed[x][y] == 0:
                        db = ReadBoard()    
                      
                    ledmx(yp,x,0)
                
                if piece >64 and piece <91 and reed == 1: #its a white piece but nothing on the board
                
                    pieceout = False 
                    
                    Gamemessage(1,'Put '+ pstring +' '+chcol[yp]+str(x+1))
                    
                    ledmx(yp,x,1)
                    PlaySound('Put '+ pstring +' '+chcol[yp]+str(x+1),True)
                    while boardReed[x][y] == 1:
                        db = ReadBoard()
                            
                    ledmx(yp,x,0)
                    
                if piece >96 and piece <123 and reed == 1: #its a black piece but nothing on the board 
                
                    pieceout = False 
                    
                    Gamemessage(1,'Put '+ pstring +' '+chcol[yp]+str(x+1))
                    
                    ledmx(yp,x,1)
                    PlaySound('Put '+ pstring +' '+chcol[yp]+str(x+1),True)
                    while boardReed[x][y] == 1:
                        db=ReadBoard()
                    
                    ledmx(yp,x,0)


def getbrdmove():
    
    # moveone (x,y,z)
    # x = x cood of board change
    # y = y cood of board change
    # z = piece picked up = 99 or piece put down = 88
    #    
    
    moveone = [0,0,0]
    movetwo = [0,0,0]
    movethree = [0,0,0]
    
    lx1 = 0
    lx2 = 0
    
    # sqone = own piece = 1 opponents piece =2 empty square =3
    
    sqone = 0
    sqtwo = 0
    sqthree = 0
    
    movestr1 =""
    movestr2 =""
    movestr2 =""
    
    lmove=ALchess.getLastTextMove(0)
    
    if lmove == None:
        #no moves to take back
        lmove1 = ''
        lmove2 = ''

    else:
        print ('lastmove '+lmove)
        lmove1 = lmove[0:2]
        lmove2 = lmove[2:4]
        
    print('move one '+lmove1)
    print('move two '+lmove2)
    
    capturetype = 0
    
    # capturetype = 0 NO capture
    #             = 1 capture move opponents piece first then own piece then put own piece
    #             = 2 capture pick up own piece first then opponents then put own piece down
    
    takeback = False
    
    invalidmove = False
    mymove = ''
    butp = 0
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    
    moveone = [0,0,0]
        
    while moveone[2] != 99 and butp != 247:
        butp = CheckButtons()
        moveone = ReadBoard()
    
    if butp == 247:
        mymove = 'quit'
        
    if mymove != 'quit':
    
        movestr1 = chcol[moveone[1]]+str(moveone[0])
    
        sqone=whoosepiece(ALchess.WhatsOnSquare(moveone[1]+1,moveone[0]))
                
        if sqone == 1:
            print ('Thats My Piece')
            ledmx(moveone[1],moveone[0]-1,1)
        elif sqone == 2:
            print ('Thats NOT my piece')
            capturetype = 1
            print('capturetype 1 opponents piece your piece your piece')
            
            if lmove2 == movestr1:
                takeback = True
                #light up led square for taking back move
                
                print('Takeback from last square TAKEBACK = TRUE Capturetype False')
                lx1 = 0
                
                for i, j in enumerate(chcol):
                    if j == lmove1[0]:
                        lx1 = i
                
                
                lx2 = int(lmove1[1])
                
                ledmx(lx1,lx2-1,1)
                
                
                
            ledmx(moveone[1],moveone[0]-1,1)
            
        elif sqone == 3:
            print ('empty square')
            print('Move One Set Invalid Move')
            invalidmove == True
        #time.sleep(slptime)    
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if mymove != 'quit':
        
            if invalidmove != True:
                time.sleep(slptime)
                movetwo = [0,0,0]
        
                while movetwo[2] < 88:
                    butp = CheckButtons()
                    movetwo = ReadBoard()
        
                if butp == 247: mymove = 'quit'
        
                ledmx(movetwo[1],movetwo[0]-1,1)
                movestr2 = chcol[movetwo[1]]+str(movetwo[0])
   
                sqtwo=whoosepiece(ALchess.WhatsOnSquare(movetwo[1]+1,movetwo[0]))
   
                if movetwo[2] == 88: #a piece has been put down
                    if sqtwo == 3: #move onto empty square
                        print('Move Two')
                        print('lmove1 '+lmove1)
                        print('movestr2 '+movestr2)
                        
                        mymove = "m"+movestr1+movestr2
                    
                        if lmove1 == movestr2:
                            if takeback == True:
                                mymove = 't'+movestr2+movestr1
                                capturetype = 0
                                print('TAKEBACK CONFIRMED!!')
                            
                    if moveone[0] == movetwo[0] and moveone[1] == movetwo[1]: #replaced piece
            #ledmx(moveone[0],moveone[1],0)
                        print('Move Two Set Invalid Move')
            
                        invalidmove=True
            
                if movetwo[2] == 99: # apiece has been picked up
                    if sqtwo == 2 and sqone == 1: # opponents piece lifted
                        capturetype = 2
                #ledmx(movetwo[0],movetwo[1],1)
                        print('capturetype 2 your piece opponents piece your piece')
            
                    if capturetype == 1:
                        if sqtwo != 1: #not your own piece
                            invalidmove == True#
                            capturetype = 0
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                time.sleep(slptime)
                if mymove != 'quit':
                    if invalidmove != True:
                        if capturetype > 0:
                            while movethree[2] != 88: #put down piece taking
                                butp = CheckButtons()
                                movethree = ReadBoard()
                    
                            if butp == 247: mymove = 'quit'
                        
                        
                    
                            print('put down taking piece')
                            movestr3 = chcol[movethree[1]]+str(movethree[0])
        
                            sqthree=whoosepiece(ALchess.WhatsOnSquare(movetwo[1]+1,movetwo[0]))
   
                            if capturetype == 1:
                                if moveone[0] != movethree[0] or moveone[1] != movethree[1]:
                                    invalidmove = True
                    
                                mymove = 'm'+movestr2+movestr1
    
                            if capturetype == 2:
                                if movetwo[0] != movethree[0] or movetwo[1] != movethree[1]:
                                    invalidmove = True
                
                                mymove = 'm'+movestr1+movestr2
    
    if invalidmove == True and mymove != 'quit':
        mymove=""
    
    
    time.sleep(slptime)
    ledmx(moveone[1],moveone[0]-1,0)
    ledmx(movetwo[1],movetwo[0]-1,0)
    ledmx(movethree[1],movethree[0]-1,0)
    ledmx(lx1,lx2-1,0)   
    
    
    print('End of GETBOARD MOVE Result ='+mymove)
    return mymove


def makecomputermove(smove):
    #SyncBoard()
    x1 = 9
    x2 = 9
    y1 = 9
    y2 = 9
    
    x1=chcol.index(smove[0])
    x2=chcol.index(smove[2])

    y1 = int(smove[1])-1
    y2 = int(smove[3])-1
    
    db = 0
    print(x1,y1,x2,y2)
    ledmx(x1,y1,1)
    #ledmx(x2,y2,1) 
    printb()
    
    
    db = RBoardSquare(x1,y1)
    ledmx(x1,y1,1)
    while db == 0:  #pick up piece
        
        db = RBoardSquare(x1,y1)
        
    ledmx(x1,y1,0)
        
    print ('Picked Up')
    
    
    
    
    db = RBoardSquare(x2,y2)
    if db == 0:
        print ('i think there is a piece on square '+str(x2)+str(y2))
    #time.sleep(slptime)
    if db == 0: #there is a piece on the destination square wait for it to be picked up
        print ('Pick Up Captured Piece')  
        db = RBoardSquare(x2,y2)
        ledmx(x2,y2,1)
        while db == 0:
            
            db = RBoardSquare(x2,y2)
        
        ledmx(x2,y2,0)
        
        print ('Captured Piece picked up')  
    #time.sleep(slptime)
    db = RBoardSquare(x2,y2)
    ledmx(x2,y2,1)
    while db == 1:  #put the piece down
        
        db = RBoardSquare(x2,y2)
    
    time.sleep(slptime)       
    ledmx(x2,y2,0)
        
    print ('Put Down')
        
def TakeBackMove(smove,takeback):
    if takeback == True:
        print ('Takeback '+smove)
    
    x1 = 9
    x2 = 9
    y1 = 9
    y2 = 9
    
    x1=chcol.index(smove[0])
    x2=chcol.index(smove[2])

    y1 = int(smove[1])-1
    y2 = int(smove[3])-1
    
    db = 0
    print(x1,y1,x2,y2)
    ledmx(x1,y1,1)
    #ledmx(x2,y2,1) 
    printb()
    
    
    db = RBoardSquare(x1,y1)
    ledmx(x1,y1,1)
    gbutp = 255
    print('ENTER FIRST LOOP')
    while db == 0 and gbutp != 254:  #pick up piece
        if takeback == True:
            gbutp = ReadButtons()
        
        db = RBoardSquare(x1,y1)
        
    
    print('TAKEBACK OUT OF FIRST LOOP')
    ledmx(x1,y1,0)
    if gbutp == 254 and takeback == True:
        print('Sent back from TakeBackMove')
        return False   
    print ('Picked Up')
    
    
    
    
    db = RBoardSquare(x2,y2)
    ledmx(x2,y2,1)
    while db == 1 and gbutp != 254:  #put the piece down
        if takeback == True:
            gbutp = ReadButtons()
        db = RBoardSquare(x2,y2)
    
    time.sleep(slptime)       
    ledmx(x2,y2,0)
    
    if gbutp == 254 and takeback == True:
        print('Sent back from TakeBackMove')
        return False
    
    print ('Put Down')
    print('TakeBackMove Made Sent Back')
    return True

def LCDmenu(c,title,mOne,mTwo,mThree,mFour):      
    if c == 1:
        LCDclear()
        
    if title != 'X':
     xpos = (19 - len(title))/2    
     #print (int(xpos))
     LCD(1,int(xpos),title)
    if mTwo != 'X': 
        LCD(2,3,mTwo)
    
    if mThree != 'X':
        LCD(2,11,mThree)
    
    if mOne != 'X':
        LCD(3,0,mOne)
    
    if mFour != 'X':
        xpos = (19 - len(mFour))
        LCD(3,int(xpos),mFour)
        
def Gamemenu(c,gOne,gTwo,gThree,gFour):
    if c == 1:
        LCD(3,0,'                   ')
    if c == 2:
        LCDclear()
    
    if gOne != 'X':
        LCD(3,0,gOne)
    
    if gTwo != 'X': 
        LCD(3,5,gTwo)
    
    if gThree != 'X':
        LCD(3,10,gThree)
    
    if gFour != 'X':
        LCD(3,16,gFour)
        
def Gamemessage(l,mess):
    #clears a line on lcd screen and puts centered message (mess) on it
    LCD(l,0,"                   ")
    xpos = (19 - len(mess))/2
    LCD(l,int(xpos),mess)

def CheckButtons():
    gbutp = ReadButtons()
    global osound
    global quitgame
    global lhint
    
    if gbutp == 254: #green button verify
        time.sleep(slptime)
        VerifyBoard()
        Gamemenu(2,'VBrd','Hint',soundstring[osound],'Quit')
        PlaySound('Your Move',True)
        
    if gbutp == 253: #chrome hint
        time.sleep(slptime)
        if lhint != '':
            Gamemessage(2,lhint)
            PlaySound('I suggest '+lhint,False)
        else:
            PlaySound('I Have No Suggestions at The Moment',False)
    if gbutp == 251: #red sound
        time.sleep(slptime)
        osound = osound +1
        
        if osound >2:
            osound = 0
        
        if osound == 0:
            PlaySound('No sounds',True)
        if osound == 1:
            PlaySound('Beeps',True)
        if osound == 2:
            PlaySound('Speech',False)
            
        Gamemenu(1,'VBrd','Hint',soundstring[osound],'Quit')
        
    if gbutp == 247: #black quit
       
        Gamemessage(1,'Press Black To QUIT')
        PlaySound('Quit Game',True)
        time.sleep(slptime*2)
        PlaySound('Press Black Button again To Quit Game',True)
        gbutp = 255
        while gbutp > 254:
            gbutp = ReadButtons()
            
        if gbutp == 247: #really quit
            quitgame = True
            
    return gbutp
 
def PlaySound(saythis,beep):
    global osound
    
    #if osound == 0:
        #no sound
        #no Sound
        
    if osound == 1 and beep == True:# beep
        os.system('aplay /home/pi/Python\ Code\ Chess/Sound/beep-02.wav')
    
    if osound == 2:#speech
        spch = 'echo '+saythis+' | festival --tts'
        os.system(spch)

def GetTxtReason(en):
    rtxt = 'INVALID MOVE'
    
    if en == 1:
        rtxt = 'INVALID MOVE'
    if en == 2:
        rtxt = 'INVALID Colour'
    if en == 3:
        rtxt = 'INVALID From Location'
    if en == 4:
        rtxt = 'INVALID to Location'
    if en == 5:
        rtxt = 'Must Set Promotion'
    if en == 6:
        rtxt = 'Game IS Over'
    if en == 7:
        rtxt = 'Ambiguous Move'

    return rtxt
    #INVALID_MOVE = 1
    #INVALID_COLOR = 2
    #INVALID_FROM_LOCATION = 3
    #INVALID_TO_LOCATION = 4
    #MUST_SET_PROMOTION = 5
    #GAME_IS_OVER = 6
    #AMBIGUOUS_MOVE = 7

def set_promotion():
    Gamemessage(1,'Set Promotion')
    Gamemessage(2,'Q   R   K   B')
    PlaySound('Set Promotion Piece',True)
    time.sleep(slptime)
    gbutp = 255
    while gbutp == 255:
        gbutp = ReadButtons()
    
    Gamemessage(1,'             ')
    Gamemessage(2,'             ')    
   
    if gbutp == 254: #promote to queen
        ALchess.setPromotion(1)
        PlaySound('Pawn Promoted to Queen',False)
        return 'q'
    elif gbutp == 253: #promote to rook
        ALchess.setPromotion(2)
        PlaySound('Pawn Promoted to Rook',False)
        return 'r'
    elif gbutp == 251: #promote to knight
        ALchess.setPromotion(3)
        PlaySound('Pawn Promoted to Knight',False)
        return 'n'
    elif gbutp == 247: #promote to bishop
        ALchess.setPromotion(4)
        PlaySound('Pawn Promoted to Bishop',False)
        return 'b'
    else:
        ALchess.setPromotion(1)# default to promote to queen
        PlaySound('Pawn Promoted By Default to Queen',False)
        return 'q'   
    
def getMoveType(mt):
    #0=NORMAL_MOVE
    #1=EP_MOVE (Pawn is moved two steps and is valid for en passant strike)
    #2=EP_CAPTURE_MOVE (A pawn has captured another pawn by using the en passant rule)
    #3=PROMOTION_MOVE (A pawn has been promoted. Use getPromotion() to see the promotion piece.)
    #4=KING_CASTLE_MOVE (Castling on the king side.)
    #5=QUEEN_CASTLE_MOVE (Castling on the queen side.)
    
    if mt == 0:
        #normal move
        return 'X'
    elif mt == 1:
        #en Passant move
        return 'X'
    elif mt == 2:
        #en passant capture
        return 'Capture En Passant'
    elif mt == 3:
        # Pawn Promotion
        return 'X'
    elif mt == 4:
        # Castle King Side
        return 'Castle King Side'
    elif mt == 5:
        # Castle Queen Side
        return 'Castle Queen Side' 
    else:
        return 'X' #return nothing
    
def PlayerMove():
    global fmove
    global cmove
    global bmessage
    sp='q'
    Gamemessage(1,'Your Move')
    PlaySound('Your Move',True)
    bmessage = getboard()
    #check for takeback
    brdmove = bmessage[1:5].lower()
    
    if bmessage[0] == 'm':
        if ALchess.addTextMove(brdmove) == False and ALchess.getReason() != 5:
            badmove = ALchess.getReason()
            gm = GetTxtReason(badmove)
            Gamemessage(1,'Error '+ gm +' '+brdmove)
            PlaySound('Error '+gm+' '+brdmove,True)
            ALchess.printBoard()
            bmessage = 'error'
        else:
            if ALchess.getReason() == 5:# need to set pawn promotion
            
                sp = set_promotion()
            
                if ALchess.addTextMove(brdmove) == False:
                    badmove=ALchess.getReason()
                    Gamemessage(1,'Error Promotion Code')
                    PlaySound('Error Promotion Add Move',True)
                    bmessage = 'error'
                    return bmessage
                else:
                    brdmove=brdmove + sp
                    ALchess.setPromotion(0)
            fmove = fmove + ' '+brdmove

            instr=' to '
            chktype = ''
            chksym = ''
            lastm = ALchess.getLastTextMove(1)
            if lastm.find('x') != -1: 
                instr = ' Takes On ' 
            
            if lastm.find('+') != -1: 
                chktype = 'Check'
                chksym = '+'
            if lastm.find('#') != -1: 
                chktype = 'Checkmate' 
                chksym = '#'
            
            if bmessage.find('a') != -1:
                bmessage = bmessage.upper()
            PlaySound(bmessage[1]+' '+bmessage[2]+instr+bmessage[3]+' '+bmessage[4],True)
            
            bmessage = bmessage.lower()
            
            Gamemessage(2,bmessage[1:5]+chksym)
            
            mt = ALchess.getLastMoveType()
            tm = getMoveType(mt)
            if tm != 'X':
                PlaySound(tm,False)
            
            if chktype != '': 
                PlaySound(chktype,True) 
             
            
            #CheckforCheck()
        #check for special move
          
            SyncBoard()
            
def ComputerMove():
    global fmove
    global cmove
    global lhint
    
    cmove = "position startpos moves"+fmove
    print (cmove)
       
    put(cmove)
    # send move to engine & get engines move
    Gamemessage(1,'Thinking...')   
    put("go movetime "+movetime)        
    text = sget()
    print (text)
    compmove=str.split(text)
                                
    smove = ''
    if len(compmove) > 1:
        smove = compmove[1]
    hint = ''
    if len(compmove) > 3:
        hint = compmove[3]
        lhint = hint
    print('computer move '+smove)
    print('hint '+lhint)
    print('promotion piece '+smove[-1])
    print('smove[0:4] '+smove[0:4])
    
    if ALchess.addTextMove(smove[0:4]) != True and ALchess.getReason() != 5:
        Gamemessage(1,"Error "+ str(ALchess.getReason())+' '+smove)
        ALchess.printBoard()
        sendboard(smove)

    else:
        if ALchess.getReason() == 5: #set pawn promotion Computer
            #1=QUEEN,2=ROOK,3=KNIGHT,4=BISHOP
                
            pp = smove[-1]
            if pp == 'q':#promote to queen
                ALchess.setPromotion(1)
                PlaySound('Pawn Promoted to Queen',False)
            elif pp == 'r':#promote to rook
                ALchess.setPromotion(2)
                PlaySound('Pawn Promoted to Rook',False)
            elif pp == 'n':#promote to Knight
                ALchess.setPromotion(3)
                PlaySound('Pawn Promoted to Knight',False)
            elif pp == 'b':#promote to bishop
                ALchess.setPromotion(4)
                PlaySound('Pawn Promoted to Bishop',False)
            else:
                ALchess.setPromotion(1)#default to queen
                PlaySound('Pawn Promoted by Default to Queen',False)
            
            if ALchess.addTextMove(smove[0:4]) != True:
                Gamemessage(1,'Error Promotion '+brdmove)
                PlaySound('Error In Promotion '+brdmove,True)
                return 'error'
            else:
                ALchess.setPromotion(0)
                
    stx = smove+hint      
    sendboard(stx)
            
    ALchess.printBoard()
        
    sm = getMoveType(ALchess.getLastMoveType())           
        
    instr=' to '
    chktype = ''
    chktxt = ''
    lastm = ALchess.getLastTextMove(1)
    
    if (lastm.find('x') != -1): 
        instr = ' Takes On ' 
    
    if (lastm.find('+') != -1): 
        chktype = 'Check'
        chktxt = '+'
        
    if (lastm.find('#') != -1): 
        chktype = 'Checkmate'
        chktxt = '#'
    
    Gamemessage(1,"My Move: " +smove.lower()+chktxt)
    if smove.find('a') != -1:
        smove = smove.upper()
        
    PlaySound('My Move '+smove[0]+' '+smove[1]+instr+smove[2]+' '+smove[3],True)
    smove = smove.lower()
 
        
    if sm != 'X':
        PlaySound(sm,False)
    
    if chktype != '':
        PlaySound(chktype,False) 
    
    Gamemessage(2,'')
    makecomputermove(smove)
    #CheckforCheck()
    fmove = fmove + ' ' +smove        

    
def TakeBack():
    # TakeBack Mode
    # get the next move to take back
    global fmove
    lmove=ALchess.getAllTextMoves(0)
    currmove = len(lmove)-2
    
    Gamemenu(2,'Cont','Undo','Redo','Save')
    Gamemessage(1,'Takeback Mode')
    
    resume = False
    
    while resume == False:
        
        lcdline = ''
    
        if currmove-1 >= 0:
            lcdline = lmove[currmove-1] + ' '
        else:
            lcdline = '     '
    
        if currmove >= 0:
            lcdline = lcdline + lmove[currmove] + ' '
        else:
            lcdline = lcdline + '     '
        
        if currmove+1 <= len(lmove)-1:
            lcdline = lcdline +lmove[currmove+1]
        else:
            lcdline = lcdline + '     '
    
        Gamemessage(2,lcdline)
        
        print(lmove)
        print('Current Move '+lmove[currmove])
        print('Current move # '+str(currmove))
        
        gbutp = 255
        while gbutp == 255:
            gbutp = ReadButtons()
    
        if gbutp == 254: #user pushed green button 'resume'
            resume = True
            #rebuild fmove
        
        if gbutp == 253: #user pushed chrome button 'undo'
            if currmove >= 0:
            
                lastmove = lmove[currmove]
                print ('lastmove '+lastmove)
                lmove1 = lastmove[0:2]
                lmove2 = lastmove[2:4] 
                cont = TakeBackMove(lmove2+lmove1,True)
                if cont == True:
                    print('Back from TackBackMove Move TAKEN BACK SUCCESSFULLY')
                    ALchess.undo()
                    SyncBoard()        
                    currmove -=1
                    if currmove < -1: currmove = -1
            else:
                print('No More Moves to Undo')
                PlaySound('No More Move To Undo',True)
        
                
                
        if gbutp == 251: #user pushed red button 'redo'
            if currmove+1 <= len(lmove)-1:
                lastmove = lmove[currmove+1]
            
                print ('lastmove '+lastmove)
                lmove1 = lastmove[0:2]
                lmove2 = lastmove[2:4] 
                cont = TakeBackMove(lmove1+lmove2,True)
                if cont == True:
                    print('Back from TackBackMove Move redone BACK SUCCESSFULLY')
                    ALchess.redo()
                    SyncBoard()        
                    currmove +=1
                    if currmove > len(lmove)-1: currmove = len(lmove)-1
            else:
                print('No More Move To Redo')
                PlaySound('No More Move To Redo',True)
        
        if gbutp == 247: #user pushed black button 'save'
            gbutp = 247
    
    
    print('Leaving Takeback/Redo I think its '+str(ALchess.getTurn()))
    #rebuild fmove
    print('fmove BEFORE rebuild '+fmove)
    fmove=' '
    
    for i in lmove[:currmove+1]:
        fmove = fmove + i + ' '
    
    fmove = fmove[:-1]
    print('fmove AFTER rebuild '+fmove)
    
    #make sure the turn is correct
    #if (len(lmove) % 2) == 0:
       # ALchess.setTurn(True)
    #else:
       # ALchess.setTurn(False)
    
    Gamemessage(2,'                    ')
        
 #save game code
def SaveGame(result):                
    global white
    
    td = datetime.datetime.now()
    if white == True:
        fn='Player v StockFish13 Pi Level '+str(skill)+' '
    else:
        fn='StockFish13 Pi Level '+str(skill)+' v Player '
                                
    fn = fn + td.strftime("%d") +' '+ td.strftime("%B") +' '+ td.strftime("%Y")
    fn = fn + ' '+td.strftime("%H")+' '+td.strftime("%M")
                
    f = open("/home/pi/ChessGames/"+fn+'.pgn', "x")
    f.write('[Event "N/A"]\n')
    f.write('[Site "Oxted, England GBR"]\n')
    f.write('[Date "'+ td.strftime("%Y.%m.%d") + '"]\n')
    f.write('[Round "N/A"]\n')
    if white == True:
        f.write('[White "Bishop, Alan K"]\n')
        f.write('[Black "StockFish13 Pi"]\n')   
        if result == 6:
            f.write('[Result "0-1"]\n')
    else:
        f.write('[White "StockFish13 Pi"]\n')
        f.write('[Black "Bishop, Alan K"]\n')
        if result == 6:
            f.write('[Result "1-0"]\n')
        
    if result == 1:
        f.write('[Result "1-0"]\n')    
    elif result == 2:
        f.write('[Result "0-1"]\n')
    elif result >2 and result < 6:
        f.write('[Result "1/2-1/2"]\n')
            
    
    moves = ALchess.getAllTextMoves(1)
    print(moves)
    f.write('\n')
    f.write('1. '+moves[0]+' '+moves[1]+' ')
                    
    mn = 1
    for move in moves:
        mn+=1
        ind = (mn*2)
                                                 
        if ind-1 <= len(moves):
            f.write(str(mn)+'. ')
            f.write(moves[ind-2])
            
        if ind <= len(moves):
            f.write(' '+moves[ind-1]+' ')
                            
        if ind  > len(moves):
            break
                        
    f.write('\n')                    
    
    if result == 6:
        if white == True:
            f.write(' 0-1\n')
        else:
            f.write(' 1-0\n')
    
    elif result == 1:
        f.write(' 1-0\n')    
    elif result == 2:
        f.write(' 0-1\n')
    elif result >2 and result < 6:
        f.write(' 1/2-1/2\n')
    
    f.write('                                     \n')
    f.close()

    LCD(2,5,'Game Saved')
                      
    #--------------------maxdemo stuff-------------------------------------------
def get():
    # using the 'isready' command (engine has to answer 'readyok')
    # to indicate current last line of stdout
    stx=""
    engine.stdin.write('isready\n')
    print('\nengine:')
    while True :
        text = engine.stdout.readline().strip()
        if text == 'readyok':
            break
        if text !='':   
            print('\t'+text)
        if text[0:8] == 'bestmove':
            return text

def sget():
    # using the 'isready' command (engine has to answer 'readyok')
    # to indicate current last line of stdout
    stx=""
    engine.stdin.write('isready\n')
    print('\nengine:')
    while True :
        text = engine.stdout.readline().strip()
        if text !='':   
            print('\t'+text)
        if text[0:8] == 'bestmove':
            mtext=text
            return mtext   

def getboard():
    """ gets a text string from the board """
    
    btxt=getbrdmove()
    while btxt == "":
        btxt=getbrdmove()
    
    
    
    return btxt
    
def sendboard(stxt):
    """ sends a text string to the board """
    print("\n send to board: " +stxt)

def newgame():
    get ()
    put('uci')
    get ()
    put('setoption name Skill Level value ' +str(skill))
    get ()
    put('setoption name Hash value 128')
    get()
    put('uci')
    get ()
    put('ucinewgame')
    white = True
    ALchess.resetBoard()
    fmove=""
    return fmove


def put(command):
    print('\nyou:\n\t'+command)
    engine.stdin.write(command+'\n')
    
    
#main menu
while True:
    #load save setup position menu
    
    
    
    
    
    
    if white==True:
        cside ='White'
    else:
        cside = 'Black'
    LCDclear()
    LCDmenu(1,'Main Menu','Start',cside,'Lvl '+str(skill),timemoves[movet])

    bpress = ReadButtons()

    while bpress != 254:
        bpress = ReadButtons()
        if bpress == 253:  #Black or White
            
            if white == True:
                white = False
                LCDmenu(0,'X','X','Black','X','X')
            else:
                white = True
                LCDmenu(0,'X','X','White','X','X')
            time.sleep(slptime)    
        elif bpress == 251:  #Skill Level 0-20
             
            skill = skill +1
            if skill > 20:
                skill = 0
            LCDmenu(0,'X','X','X','Lvl '+str(skill)+' ','X')
            time.sleep(slptime)
        elif bpress == 247:
            
            movet = movet +1
            if movet > 11:
                movet = 0
            LCDmenu(0,'X','X','X','X',timemoves[movet])
            time.sleep(slptime)  
    
    #Gamemenu
    
    
    
    movetime=str(timemove[movet])
    
    fmove = newgame()
    #fmove = ' e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 b7b5 a4b3 g8f6 b1c3 f8b4 a2a3 b4c5 d2d4 e5d4 f3d4 c6d4 e1g1 f6e4 c3e4 c5b6 c2c3 d4f5 e4g5 h7h6 g5f7 d8e7 f7h8 d7d5 b3d5 f5e3 f2e3 b6e3 c1e3 e7e3 g1h1 c8f5 d5a8 f5d7 f1e1 e3e1 d1e1 e8d8 e1g3 h6h5 g3g7 c7c6 g7g5 d8c8 g5h5 a6a5 g2g4 a5a4 g4g5 c8c7 g5g6 c7c8'
    
    result = 0
    #FirstMove = True
    

    #ALchess.setFEN('B1k4N/3b4/2p3P1/1p5Q/p7/P1P5/1P5P/R6K w - - 1 31')
    
    Gamemenu(2,'VBrd','Hint',soundstring[osound],'Quit')
    SyncBoard()
    
    gbutp = 0
    
    while result == 0:
        
        Gamemenu(1,'VBrd','Hint',soundstring[osound],'Quit')
        
        if result == 0:
            bmessage = ''
            whooseTurn = ALchess.getTurn()
            print('whooseturn '+str(ALchess.getTurn()))
     
            if whooseTurn == 0:
                if white == True:#its whites turn and player is white
                    print('gone to player white move')
                    PlayerMove()
                else:
                    bmessage ='comp'
                    ComputerMove()
            else:
                if white == True:
                    bmessage = 'comp'
                    ComputerMove()
                else:
                    PlayerMove()

            #------------------moves have been made---------------------------------
            result = ALchess.getGameResult()
            print(bmessage)
            code = bmessage[0]
            #if code == 'm'
            if code == 't':
                print('Main Menu Takeback Code Reached WELL DONE!!')
                          
                # a move has already been taken back so
                ALchess.undo() #take back move
                print('fmove BEFORE takeoff '+fmove)
                #ind = fmove.rfind(' ')
                #fmove = fmove[:ind]
                ind = fmove.rfind(' ')
                fmove = fmove[:ind]
                print('fmove AFTER takeoff '+fmove)
                
                SyncBoard() #check board is correct
                #inform user they are in takeback mode
               
                ok = TakeBack() #deal with takeback of moves
                
               
                
                print('NEW fmove '+fmove)
                                     
            if code == 'q': result = 6
           
            SyncBoard()
    
            
        if result != 0:
            if result == 1:
                LcdText="White Win"
            if result == 2:
                LcdText="Black Win"
            if result == 3:
                LcdText="Stalemate"
            if result == 4:
                LcdText="Fifty Moves Rule"   
            if result == 5:
                LcdText="Three Fold Repetition"
            if result == 6:
                LcdText='Quit Game'
            LCDclear()
            LCD(2,5,LcdText)
            PlaySound(LcdText,False)
            LCD(3,0,'Main Menu')
            LCD(3,11,'Save Game')
            butp = 0
            while butp != 254:
                butp = ReadButtons()
                
                if butp == 251:
                    SaveGame(result)
                    
                    time.sleep(slptime*2)   
                    butp = 254
      

  