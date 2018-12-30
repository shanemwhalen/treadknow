import time
import datetime
import threading
import thread
import sys
import collections
import random
import os

sys.path.append('protobufs/build/python')

import calibration_pb2

#constants
_pulesPerRev = 200.0;
_debug = False
#_debug = True

class PulseShim(threading.Thread):
    PulsesPerRev = 200.0;
    CalFile = "/tmp/treadknow.cal"
    def __init__(self, name):
        self.Calibration = calibration_pb2.Calibration()
        #setup the windowing
        self.lock = threading.Lock()
        self.prevSampleTime = 0
        self.prevNumPulses = 0
        #delay between increments
        self.numPulses = 0
        self.shimUpdateRPMs(10.0)
        self.nextSleepUntilTime = 0
        self.calMiles = None;
        self.calDurationSec = None;
        self.calRevolutions = None;
        self.calRevToMilesScale = 0.0;
        super(PulseShim, self).__init__()

    def run(self):
        self.nextSleepUntilTime = time.time() + self.shimIncrementDelay
        while self.shimIncrementDelay != 0:
            curTime = time.time()
            delayTime = self.nextSleepUntilTime - curTime
            if _debug:
                print "curTime", curTime
                print "self.shimIncrementDelay", (self.shimIncrementDelay)
                print "_nextSleepUntilTime", self.nextSleepUntilTime
                print "delayTime", delayTime
                print ""
            if (delayTime>0):
                time.sleep(delayTime)
            curTime = time.time()
            self.nextSleepUntilTime = curTime + self.shimIncrementDelay
            self.lock.acquire()
            self.numPulses += 1
            self.lock.release()

    def shimUpdateRPMs(self, RPMs):
        if RPMs == 0:
            self.shimIncrementDelay = 0
        else:
            self.shimRPMs = float(RPMs);
            self.shimRPS = self.shimRPMs/60.0
            self.shimIncrementDelay = (1.0/PulseShim.PulsesPerRev)/self.shimRPS

    def getTimedRevolutions(self):
        self.lock.acquire()
        curTime = time.time()
        totalTime = curTime - self.prevSampleTime
        self.prevSampleTime = curTime
        curPulses = self.numPulses - self.prevNumPulses
        self.prevNumPulses = curPulses
        self.lock.release()
        revolutions = curPulses/PulseShim.PulsesPerRev
        if _debug:
            print "curPulses", curPulses
            print "revolutions", revolutions 
            print "totalTime", totalTime 
            print ""
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

    def getCalibrationData(self):
        calString = None
        if os.path.exists(PulseShim.CalFile):
            with open(PulseShim.CalFile, 'rb') as f:
                try:
                    calString = f.read()
                    self.Calibration.ParseFromString(calString)
                    if self.Calibration.HasField('calDistance'):
                        print "Found calibration"
                    else:
                        calString = None
                except IOError:
                    print "Could not read cal file."

        return calString

    def updateCalibrationData(self):
        calString = self.Calibration.SerializeToString()
        with open(PulseShim.CalFile, 'wb') as f:
            try:
                f.write(calString)
                print "Updated calibration data"
                print self.Calibration
            except IOError:
                print "Could write cal file."

    def calibrate(self, MPH, timeSec):
        # ignore the getDistance call, just to get a sample and zero everything out
        # because we are ignoring this means that we have the assumption that the app
        # is not running in an other state other than calibrate (which should be safe)
        calString = self.getCalibrationData()

        if calString is not None:
            print "Using previous cal"
            print self.Calibration
            self.calDurationSec = self.Calibration.calDistance.duration
            self.calRevolutions = self.Calibration.calDistance.revolutions
            self.calMiles       = self.Calibration.calDistance.miles
        else:
            print "Updating calibration"
            self.getDistance()
            time.sleep(timeSec)
            revolutions, totalTime = self.getTimedRevolutions()
            calDistance = calibration_pb2.CalDistance()
            self.calDurationSec = totalTime
            self.calRevolutions  = revolutions
            self.calMiles = (MPH/60.0)*(self.calDurationSec/60.0)
            calDistance.completionTimestamp = time.time()
            calDistance.miles = self.calMiles
            calDistance.revolutions = self.calRevolutions
            calDistance.duration = totalTime
            self.Calibration.calDistance.CopyFrom(calDistance)
            self.updateCalibrationData()

        self.calRevToMilesScale = self.calMiles/self.calRevolutions
        
        # Write the new address book back to disk.

        if _debug:
            print "self.calDurationSec", self.calDurationSec
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

        print "self.calDurationSec", t.calDurationSec
        print "self.calRevolutions", t.calRevolutions
        print "self.calMiles", t.calMiles
        print "self.calRevToMilesScale", t.calRevToMilesScale

