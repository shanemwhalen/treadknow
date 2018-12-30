import wiringpi
import weakref
import threading
import time
import os
import calibration_pb2

_linearEncoder = None

def doNothing():
    pass

class LinearEncoder():
    # constants
    PulsesPerRev = 200.0
    Debug = True 
    CalFile = "/tmp/treadknow.cal"

    def __init__(self, gpio = 0):
        global _linearEncoder

        # singleton
        if _linearEncoder is not None:
            raise Exception("Already created!")

        _linearEncoder = weakref.ref(self)

        # safety
        self.lock = threading.Lock()

        # tracking
        self.prevSampleTime = 0
        self.prevNumPulses = 0
        self.numPulses = 0

        # calibrations
        self.Calibration = calibration_pb2.Calibration()
        self.calMiles = None;
        self.calDurationSec = None;
        self.calRevolutions = None;
        self.calRevToMilesScale = 0.0;

        # GPIO
        wiringpi.wiringPiSetup()
        self.gpio = gpio
        wiringpi.wiringPiISR(self.gpio, wiringpi.INT_EDGE_FALLING, LinearEncoder._myInterrupt)
        wiringpi.piHiPri(99)

    def __del__(self):
        global _linearEncoder
        print "Destory LinearEncoder!"
        _linearEncoder = None
        # TODO there is no way to remove the interrupt
        #wiringpi.wiringPiISR(self.gpio, wiringpi.INT_EDGE_FALLING, doNothing)

    @staticmethod
    def _myInterrupt():
        _linearEncoder().incrementCounter()

    def incrementCounter(self):
        self.numPulses += 1
        #print "a:", self.numPulses

    def getTimedRevolutions(self):
        self.lock.acquire()
        curTime = time.time()
        totalTime = curTime - self.prevSampleTime
        self.prevSampleTime = curTime
        curPulses = self.numPulses - self.prevNumPulses
        self.prevNumPulses = self.numPulses
        self.lock.release()
        revolutions = curPulses/LinearEncoder.PulsesPerRev
        if LinearEncoder.Debug:
            print "curPulses", curPulses
            print "revolutions", revolutions 
            print "totalTime", totalTime 
        return revolutions, totalTime

    def getDistance(self):
        revolutions, totalTime = self.getTimedRevolutions()
        return revolutions * self.calRevToMilesScale

    def getCalibrationData(self):
        calString = None
        if os.path.exists(LinearEncoder.CalFile):
            with open(LinearEncoder.CalFile, 'rb') as f:
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
        with open(LinearEncoder.CalFile, 'wb') as f:
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

        if LinearEncoder.Debug:
            print "self.calDurationSec", self.calDurationSec
            print "self.calRevolutions", self.calRevolutions
            print "self.calMiles", self.calMiles
            print "self.calRevToMilesScale", self.calRevToMilesScale

if __name__ == '__main__':
    LinearEncoder = LinearEncoder(2)
    while True:
        time.sleep(1)
