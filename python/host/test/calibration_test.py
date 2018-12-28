import time
import threading
import thread
import sys
import collections
import random

#constants
_pulesPerRev = 200.0;
_debug = False
_debug = True

class PulseShim(threading.Thread):
    def __init__(self, name):
        #setup the windowing
        self._lock = threading.Lock()
        self._firstSampleTime = 0
        self._lastSampleTime = 0
        #delay between increments
        self._numberOfPulses = 0
        self.shimUpdateRPMs(10.0)
        self._nextSleepUntilTime = 0
        self.calMiles = None;
        self.calTime = None;
        self.calRevolutions = None;
        self.calRevToMilesScale = None;
        super(PulseShim, self).__init__()

    def run(self):
        while self._shimIncrementDelay != 0:
            curTime = time.time()
            if self._nextSleepUntilTime == 0:
                self._nextSleepUntilTime = curTime + self._shimIncrementDelay
            delayTime = self._nextSleepUntilTime - curTime
            if _debug:
                print "curTime", curTime
                print "self._shimIncrementDelay", (self._shimIncrementDelay)
                print "_nextSleepUntilTime", self._nextSleepUntilTime
                print "delayTime", delayTime
                print ""
            if (delayTime>0):
                time.sleep(delayTime)
            curTime = time.time()
            self._nextSleepUntilTime = curTime + self._shimIncrementDelay
            self._lock.acquire()
            self._lastSampleTime = curTime
            if self._firstSampleTime == 0:
                self._firstSampleTime = curTime
            else:
                self._numberOfPulses += 1
            self._lock.release()

    def shimUpdateRPMs(self, RPMs):
        if RPMs == 0:
            self._shimIncrementDelay = 0
        else:
            self._shimRPMs = float(RPMs);
            self._shimRPS = self._shimRPMs/60.0
            self._shimIncrementDelay = (1.0/_pulesPerRev)/self._shimRPS

    def getTimedRevolutions(self):
        self._lock.acquire()
        totalTime = self._lastSampleTime - self._firstSampleTime
        if totalTime == 0:
            self._lock.release()
            return (None, None)
        numberOfPulses = self._numberOfPulses
        self._firstSampleTime = 0
        self._numberOfPulses = 0
        self._lastSampleTime = 0
        self._lock.release()
        revolutions = numberOfPulses/_pulesPerRev
        if _debug:
            print "numberOfPulses", numberOfPulses
            print "revolutions", revolutions 
        return revolutions, totalTime

    def getRPMs(self):
        revolutions, totalTime = self.getTimedRevolutions()
        minutes = totalTime / 60.0
        if _debug:
            print "minutes", minutes
        return revolutions/minutes

    def getDistance(self):
        revolutions, totalTime = self.getTimedRevolutions()
        return revolutions * self.calRevToMilesScale

    def calibrate(self, MPH, timeSec):
        self._lock.acquire()
        self._firstSampleTime = 0
        self._numberOfPulses = 0
        self._lastSampleTime = 0
        self._lock.release()
        time.sleep(timeSec)
        revolutions, totalTime = self.getTimedRevolutions()
        self.calTime = timeSec
        self.calRevolutions  = revolutions
        self.calMiles = (MPH/60.0)*(timeSec/60.0)
        self.calRevToMilesScale = self.calMiles/self.calRevolutions
        if _debug:
            print "self.calTime", self.calTime
            print "self.calRevolutions", self.calRevolutions
            print "self.calMiles", self.calMiles
            print "self.calRevToMilesScale", self.calRevToMilesScale
    
if __name__ == '__main__':
    try:
        t = PulseShim(name = 'fakecounter')
    except Exception,e:
        print str(e)
        sys.exit(-1)
    try:
        t.start();

        t.shimUpdateRPMs(10.0)

        t.calibrate(MPH=6, timeSec=10)

        t.shimUpdateRPMs(20.0)

        time.sleep(5)

        print t.getDistance()

    finally:
        t.shimUpdateRPMs(0)

        print "self.calTime", t.calTime
        print "self.calRevolutions", t.calRevolutions
        print "self.calMiles", t.calMiles
        print "self.calRevToMilesScale", t.calRevToMilesScale

