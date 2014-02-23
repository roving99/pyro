#!/usr/bin/python

# Occupancy mapper. 
# maintains a 500 x 500 (10m2) occupancy map as a grey level image.

from PIL import Image
from PIL import ImageDraw
import math
import json

class OccupancyMap():
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.map = Image.new("L",(self.x,self.y), 128)
        self.draw = ImageDraw.Draw(self.map)
        self.scale = 2
    
    def reset(self):
        self.draw.rectangle([(0,0),(self.x-1,self.y-1)],fill=128)

    def test(self): # assumes 500x500 map!!
        self.draw.rectangle([(100,100),(400,400)], 64)
        self.draw.line([(0,250),(499,250)], fill=0)
        self.draw.line([(250,0),(250,499)], fill=255)
        self.draw.pieslice((100,100,400,400), -15,15, fill=32)
        self.draw.arc((100,100,400,400), -15,15, 192)
        self.add([100,100,0], [150,40,30,100])

    def save(self,f):
        self.map.save(f,"BMP")

    def drawCone(self, x, y, th, r, delta=5):   # takes pixel sizes.
            #print x, y, th, r, delta
#            self.draw.pieslice((x-r,y-r, x+r,y+r), th-delta, th+delta, 32)
            self.draw.arc((x-r,y-r, x+r,y+r), th-delta, th+delta, 192)

    def add(self,pose,sonar):   # add new sonar information (4 tuple). does the scaling from cm to pixel.
        x = (self.x/2)+int(pose[1]/self.scale)
        y = (self.y/2)-int(pose[0]/self.scale)   # centre coordinate system
        th = int(math.degrees(pose[2])-90)   # draw angles start at E and in degrees, robot angles at N and in radians.
        self.drawCone(x, y, th,     int(sonar[0]/self.scale))     # front
        self.drawCone(x, y, th+270, int(sonar[1]/self.scale))     # left
        self.drawCone(x, y, th+90,  int(sonar[2]/self.scale))     # right
        self.drawCone(x, y, th+180, int(sonar[3]/self.scale))     # back
 
if __name__=='__main__':
    m = OccupancyMap(500,500)
    m.test()
    m.save("test.bmp")
    m.reset()
    m.save("reset.bmp")

    f = open("log.log")
    lines = f.readlines()
    f.close()
    for line in lines:
        data = json.loads(line)
        print data['pose'], data['sonar']
        m.add(data['pose'], data['sonar'])
    m.save("map.bmp")

