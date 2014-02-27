# based on epuck.py

import time
import math

try:
    import smbus
except:
    print "NO smbus module!"

import wii
import sonar
import bumpers

MD25_SPEED    = 0
MD25_ROTATE   = 1
MD25_ENCODER1 = 2
MD25_ENCODER2 = 6
MD25_VOLTS    = 10
MD25_CURRENT1 = 11
MD25_CURRENT2 = 12
MD25_VERSION  = 13
MD25_ACCELERATE= 14
MD25_MODE     = 15
MD25_COMMAND  = 16

MD25_ADDRESS = 0x5A

class Md25():

    def __init__(self, fake=False):
        """
        call Robot __init__ and set up own instance vars 
        """
        self.wheel_spacing=21.2		# cm  taken down .2
        self.wheel_circumference=32.55	# cm	
        self.wheel_counts_per_rev = 360.0	# 
        self.cm_per_tick = (self.wheel_circumference/self.wheel_counts_per_rev)
        self.full_circle =  self.wheel_counts_per_rev*((self.wheel_spacing*math.pi)/self.wheel_circumference)

        self.robotinfo = {'robot': ['md25'],
                          'robot-version': ['0.2'],
                          }
        self.sensor = {"ir": [1,2],
                       "sonar": [10,20,30,40],
                       "bump": [False,False],
                       "cliff": [False,False] ,
                       "battery": [13.0],
                       "pose": [0.0, 0.0, 0.0],
                       'compass':[0.25],
                       "count":[0,0],
                       "motion":[0.0,0.0],
                       "time":[0.0],
                       "camera":[None, None, None, None],
                       }
        self.config = { "ir": 2, 
                        "sonar":4, 
                        "bump":2, 
                        "cliff":2, 
                        "battery":1, 
                        "compass":1, 
                        "pose":3, 
                        "count":2, 
                        "time":1, 
                        "camera":4, 
                        "motion":2, 
                        }
        
        self.fake = fake

        if (self.fake):
            self.i2c = None
            self.wii = None
            self.sonar = None
            self.bumpers = None
        else:
            self.i2c = smbus.SMBus(1)
            self.wii = wii.Wii(self.i2c)
            self.sonar = sonar.Sonar(self.i2c)
            self.bumpers = bumpers.Bumpers()

        self.name = "md25"              # robot name
        self.version = "0.5"            # version number    
        self.startTime = time.time()    # mission time

        self.lastUpdate = time.time()   # time (s since epoch) of last update - used to move simulated robot.
        self.tranSpeed = 200            # Translational speed of simulated robot at 1.0 forward. clicks/s.
        self.rotSpeed = 200             # Rotational simulated robot at 1.0 rot. clicks/s.

        self._lastTranslate = 0.0
        self._lastRotate = 0.0
        self.last_encoder1 = 0
        self.last_encoder2 = 0
        self.encoder1 = 0
        self.encoder2 = 0
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.SonarMap = None

        self.safe = True                # prevent forward motion if bump or cliff sensors active

        self.reset()

    def reset(self):
        """
        reset robot. zero location.
        """
        if self.fake:
            pass
        else:
            self._send(MD25_COMMAND, 0x20)		# reset counters
            self._send(MD25_COMMAND, 0x31)		# set automatic speed regulation
            self._send(MD25_MODE, 0x02)		# set mode to speed, turn. Centre = 128
        self._lastTranslate = 0
        self._lastRotate = 0
        self.last_encoder1 = 0
        self.last_encoder2 = 0
        self.encoder1 = 0
        self.encoder2 = 0
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        print 'Robot ready'


    def position_update(self):       # calculate new X, Y, Theta 
        left_ticks   = self.encoder1 - self.last_encoder1
        right_ticks  = self.encoder2 - self.last_encoder2
        self.last_encoder1 = self.encoder1
        self.last_encoder2 = self.encoder2
        
        dist_left   = float(left_ticks) * self.cm_per_tick;
        dist_right  = float(right_ticks) * self.cm_per_tick;
        cos_current = math.cos(self.theta);
        sin_current = math.sin(self.theta);
        right_minus_left = float(dist_right-dist_left);
             
        if (left_ticks == right_ticks):            # Moving in a straight line 
            self.x += dist_left*cos_current
            self.y += dist_left*sin_current
        else:                                      # Moving in an arc 
            expr1 = self.wheel_spacing * float(dist_right + dist_left) / 2.0 / float(dist_right - dist_left);
            right_minus_left = dist_right - dist_left
            self.x     += expr1 * (math.sin(right_minus_left/self.wheel_spacing + self.theta) - sin_current)
            self.y     -= expr1 * (math.cos(right_minus_left/self.wheel_spacing + self.theta) - cos_current)
            self.theta += right_minus_left / self.wheel_spacing
            
        if (self.theta<0.0):     
            self.theta = (2*math.pi)+self.theta
        if (self.theta>=(2*math.pi)):
            self.theta = self.theta-(2*math.pi)

        
    def _send(self, register, data):                            #### ALL i2c DATA TO GO THROUGH THIS CALL !! 
        """
        All messages to i2c go via this method.
        """
        if register<0:
            output = self.i2c.read_i2c_block_data(MD25_ADDRESS, 0, 16)
            return output
        else:
            output = self.i2c.write_byte_data(MD25_ADDRESS, register, data)
            return output

# MOVEMENT functions =============================================================================

    ''' MOVEMENT
        all use self._adjustSpeed(translate,rotate), substituting last translate/rotate if not supplied.
        will also pause for a number of seconds and call an all-stop, if 'seconds' arg defined.
        translation and rotation are >=-1.0, <=1.0
        '''

    def move(self, translate, rotate, seconds=None):
        assert -1 <= translate <= 1, 'move called with bad translate value: %g' % translate
        assert -1 <= rotate <= 1, 'move called with bad rotate value: %g' % rotate
        self._adjustSpeed(translate, rotate)
        if seconds is not None:
            time.sleep(seconds)
            self.stop()

    def stop(self):
        self._adjustSpeed(0, 0)

    def _adjustSpeed(self, translate, rotate):
        if self.safe:                                                       # crash avoidance!
            if True in self.sensor['cliff'] or True in self.sensor['bump']:
                if not(rotate==0.0 and translate<0.0):
                    rotate=0.0
                    translate=0.0

        self._lastTranslate = translate
        self._lastRotate = rotate
        if not self.fake:
            hexRotate = 0x80+int(rotate*16.0)
            hexTranslate = 0x80+int(translate*16.0)
            self._send(MD25_SPEED, hexTranslate)
            self._send(MD25_ROTATE, hexRotate)
    
# GET SENSOR DATA =============================================================================

    def getTranslate(self):
        return self._lastTranslate

    def getRotate(self):
        return self._lastRotate

    def get(self, sensor, update):
        '''
        get('all') - return all sensors, all positions
        get('config') - return list of sensors, and their number
        get('name') - return name of robot
        '''
        if update:
            if self.fake:
                self.updateFake()
            else:
                self.update()                  # Update sensor values

        sensor = sensor.lower()                 
        if sensor == "config":                  # return number and types of sensors
            return self.config
        elif sensor == "name":                  # robot name
            return self.name
        elif sensor == "all":           # 'all' returns all sensors, all positions
            return self.sensor

    def update(self):
        b = self._send(-1,0)   # returns byte array of registers 0-15
        sp1    = b[MD25_SPEED]
        sp2    = b[MD25_ROTATE]
        self.encoder1 = (b[MD25_ENCODER1]<<24) + (b[MD25_ENCODER1+1]<<16) + (b[MD25_ENCODER1+2]<<8) + b[MD25_ENCODER1+3] 
        self.encoder2 = (b[MD25_ENCODER2]<<24) + (b[MD25_ENCODER2+1]<<16) + (b[MD25_ENCODER2+2]<<8) + b[MD25_ENCODER2+3] 
        if self.encoder1>((1<<31)-1): self.encoder1-=(1<<32)
        if self.encoder2>((1<<31)-1): self.encoder2-=(1<<32)
        volts  = float(b[MD25_VOLTS])/10.0
        compass= 0.0

        self.sonar.update()
        self.wii.update()
        self.bumpers.update()
        self.position_update()

        self.sensor['bump']   = [self.bumpers.data[0],self.bumpers.data[1]]
        self.sensor['cliff']  = [self.bumpers.data[2],self.bumpers.data[3]]
        self.sensor['ir']     = [0, 0]
        self.sensor['sonar']  = self.sonar.data
        self.sensor['camera'] = self.wii.data
        self.sensor['count']  = [self.encoder1, self.encoder2]
        self.sensor['battery']= [volts]
        self.sensor['compass']= [compass]
        angle = self.theta
        if angle>math.pi:
            angle = 0.0-((2*math.pi)-angle)
        self.sensor['pose']   = [self.x, self.y, angle]

        self.sensor['motion'] = [self.getTranslate(), self.getRotate()]
        self.sensor['time']   = [int(1000*(time.time()-self.startTime))/1000.0]

        if self.safe:
            if (True in self.sensor['bump'] or True in self.sensor['cliff']) and (self.sensor['motion'][0]>0.0 or self.sensor['motion'][1]!=0.0):
                self.stop()
                
    def updateFake(self):
        secondsPassed = time.time()-self.lastUpdate         # time in secs since last update
        self.lastUpdate = time.time()
        self.encoder1 += self.tranSpeed*secondsPassed*self.getTranslate()
        self.encoder2 += self.tranSpeed*secondsPassed*self.getTranslate()
        self.encoder1 += self.rotSpeed*secondsPassed*self.getRotate()
        self.encoder2 -= self.rotSpeed*secondsPassed*self.getRotate()

        if self.encoder1>((1<<31)-1): self.encoder1-=(1<<32)
        if self.encoder2>((1<<31)-1): self.encoder2-=(1<<32)
        volts  = self.sensor['battery'][0]-0.0000001
        compass= 0.0

        #self.sonar.update()
        #self.wii.update()
        #self.bumpers.update()
        self.position_update()

        self.sensor['bump']   = [False, False]
        self.sensor['cliff']  = [False, False]
        self.sensor['ir']     = [0, 0]
        #self.sensor['sonar']  = self.sonar.data
        #self.sensor['camera'] = self.wii.data
        self.sensor['count']  = [self.encoder1, self.encoder2]
        self.sensor['battery']= [volts]
        self.sensor['compass']= [compass]
        angle = self.theta
        if angle>math.pi:
            angle = 0.0-((2*math.pi)-angle)
        self.sensor['pose']   = [self.x, self.y, angle]

        self.sensor['motion'] = [self.getTranslate(), self.getRotate()]
        self.sensor['time']   = [int(1000*(time.time()-self.startTime))/1000.0]

        if self.safe:
            if (True in self.sensor['bump'] or True in self.sensor['cliff']) and (self.sensor['motion'][0]>0.0 or self.sensor['motion'][1]!=0.0):
                self.stop()
