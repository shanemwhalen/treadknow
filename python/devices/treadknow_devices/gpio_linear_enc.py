import wiringpi
import weakref

_linearEncoder = None

class LinearEncoder():
    def __init__(self, gpio = 0):
        global _linearEncoder
        if _linearEncoder is not None:
            raise Exception("Already created!")
        wiringpi.wiringPiSetup()
        self.counter = 0
        self.gpio = gpio
        wiringpi.wiringPiISR(self.gpio, wiringpi.INT_EDGE_FALLING, LinearEncoder._myInterrupt)
        _linearEncoder = weakref.ref(self)

    def __del__(self):
        global _linearEncoder
        print "Destory LinearEncoder!"
        _linearEncoder = None

    @staticmethod
    def _myInterrupt():
        _linearEncoder().incrementCounter()

    def incrementCounter(self):
        self.counter = self.counter + 1
        print "a:", self.counter

if __name__ == '__main__':
    LinearEncoder = LinearEncoder(0)
    while True:
        pass
