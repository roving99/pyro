# maps.py - maps (point cloud, vector cloud, ocupancy grid)

import math

class SonarMap:         # array of gaussians

    def __init__(self, pose, time):
        self.map = []
        self.pose = pose
        self.time = time
        self.length = 0
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0 
        for i in range(0,64):
            self.map.append(Gaussian(0,300))
        pass
    
    def clear():
        for i in range(0,64):
            self.set(i,300,300)

    def set(self,slot,mean, conv):    # set slots gaussian values
        self.map[slot] = Gaussian(mean, conv)

    def update(self,slot,mean, conv):    # update slots gaussian values
        self.map[slot].update(mean, conv)
    
    def updateTheta(self,th,mean, conv):
        slot = thetaToSlot(th)
        self.update(slot, mean, conv)

    def updateAll(self, heading, sonar):    #    (<bearing>,[23,34,45,56])
        self.updateTheta(heading, sonar[0],10)              # forward
        self.updateTheta(heading + math.pi/2., sonar[1],10) # left  
        self.updateTheta(heading + math.pi, sonar[2],10)    # back  
        self.updateTheta(heading - math.pi/2., sonar[3],10) # right

    def setTheta(self,th,mean, conv):
        slot = thetaToSlot(th)
        self.set(slot, mean, conv)

    def setAll(self, heading, sonar):    #    (<bearing>,[23,34,45,56])
        self.setTheta(heading, sonar[0],10)              # forward
        self.setTheta(heading + math.pi/2., sonar[1],10) # left  
        self.setTheta(heading + math.pi, sonar[2],10)    # back  
        self.setTheta(heading - math.pi/2., sonar[3],10) # right

    def list(self):   # list of gaussian pairs for each slot
        l = []
        for i in range(0,64):
            l.append([self.map[i].mean,self.map[i].var])
        return l

    def listRect(self, absolute = False):
        l = []
        if absolute:
            x = self.pose[0]
            y = self.pose[1]
        else:
            x = 0.
            y = 0. 
        for i in range(0,64):
            l.append([self.map[i].mean*math.sin(slotToTheta(i))+x, self.map[i].mean*math.cos(slotToTheta(i))+y])
        return l

#==========================================================================================
class Gaussian:
    def __init__(self, mean, var):
        self.mean = mean
        self.var = var

    def set(self, mean,var):
        self.mean = mean
        self.var = var

    def update(self, mean, var):
        newMean = (1./(self.var+var)) * (self.mean*var + self.var*mean)
        newVar = 1./((1./var)+(1./self.var))
        self.mean = newMean
        self.var = newVar
        return (self.mean, self.var)

    def fn(self, x):
        return 1./math.sqrt(2.*math.pi*self.var) * math.exp(-.5*(x-self.mean)**2. / self.var)

#==========================================================================================
def rect(theta, r):
    x = r*math.cos(theta)
    y = r*math.sin(theta)
    return x, y

def polar(x,y):
    theta = math.pi-math.atan2(y,x)
    r = math.sqrt(x*x+y*y)
    return theta, r

def dtheta(a,b):        # calculate angle between two angles from a to b
    delta = b-a
    if delta>math.pi:
        delta = delta-2*math.pi
    if abs(delta)>math.pi:
        if delta>0.0:
            delta -=math.pi*2
        else:
            delta +=math.pi*2
    return delta

def drect(a,b):		# r, theta from point A to B
    dx=b[0]-a[0]
    dy=b[1]-a[1]
    r = math.sqrt(dx*dx+dy*dy)
    theta = math.atan2(dx,dy)
    return r, theta

def quantize(th, ntheta=64.):     # round angle to nearest 2*pi/ntheta
    return int(th/((2*math.pi)/ntheta)) * ((2*math.pi)/ntheta)

def slotToTheta(i):
    if i>32:
        return -(2.*math.pi - i*(2.*math.pi/64))
    else:
        return i*(2.*math.pi/64)

def thetaToSlot(th):
    th = quantize(thnorm(th))
    if th>=0.0:
        n = int(th/(2.*math.pi/64))
    else:
        n = 64 + int(th/(2.*math.pi/64))
    return n
    
def thnorm(th):     # return theta with -pi - +pi
    if th>=0.:
        th = th%(2.*math.pi)
        if th>math.pi:
            th = -((math.pi*2.)-th)
    else:
        th = -((2.*math.pi)-th%(2.*math.pi))
        if th<-math.pi:
            th = ((math.pi*2.)+th)
    return th
