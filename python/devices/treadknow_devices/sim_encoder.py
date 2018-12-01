import wiringpi

class SimEncoder:
    def __init__(self, gpio = 2, frequency = 100):
        wiringpi.wiringPiSetup()
        self.frequency = frequency
        self.gpio = gpio 
        wiringpi.softToneCreate(self.gpio)
        wiringpi.softToneWrite(self.gpio, self.frequency)

    def __del__(self):
        print "Destory SimEncoder!"
        wiringpi.softToneStop(self.gpio)

    def setFrequency(self, frequency):
        self.frequency = frequency
        wiringpi.softToneWrite(self.gpio, self.frequency)

if __name__ == '__main__':
    Simulator = SimEncoder(25, 1)
    while True:
        pass
