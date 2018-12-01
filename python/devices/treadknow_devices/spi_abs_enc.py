__author__ = "Shane Whalen"
__copyright__ = "Copyright (C) 2018 Shane Whalen"
__license__ = "GNU GENERAL PUBLIC LICENSE"
__version__ = "2.0"

# EMS22A - 30-C28-LS6
# 10 data bits

import time
import spidev

# Extra spew when True
debug = False

class EMS22A30:
    def __init__(self, bus, device):
        # Device is hooked up to /dev/spidev0.0
        
        self.spi = spidev.SpiDev()
        
        self.spi.open(bus, device)
        
        # Tclk/2 = 500ns --> Tclk = 1us --> f = 1MHz
        # No need to go that fast, 200MHz
        self.spi.max_speed_hz = 200000
        # CPOL = 0
        # CPHA = 1
        self.spi.mode = 1

        self.hex_result_offset = 0

    def __del__(self):
        print "Destory!"
        if self.spi:
            self.spi.close()
    
    def calibrate(self):
        # Get default reading, this is our cheap calibration for now
        result = self.spi.readbytes(2)
        self.hex_result_offset = (result[0] << 8 | result[1]) >> 6
    
    def getSample(self):
        # No output, just read the input
        result = self.spi.readbytes(2)
    
        # 16 bits of data, but only 10 of those bits are data (the first 10 receieved)
        raw = (result[0] << 8 | result[1])
        # 16 - 10 = 6
        hex_result_raw = raw >> 6
        # 1024 is full scale, and the range is a full rotation (360 deg)
        deg_raw = ((hex_result_raw/1024.0) * 360)
     
        # Add in the calibrated data and wrap around
        hex_result = (((hex_result_raw - self.hex_result_offset) + 1024) % 1024)
        # Calculate the actual result
        deg = ((hex_result/1024.0) * 360)
    
        # All 1's + Parity should be even or there was an error transmitting
        parity_err = (bin(raw).count("1") % 2) != 0
    
        if debug:
            print "0x%03x" % hex_result_raw,
            print "%7.3lf" % deg_raw,
            print "0x%03x" % hex_result,
            print "S1 (end of offset comp) = %x" % ((result[1] >> 5) & 1),
            print "S2 (Cordic overflow) = %x" % ((result[1] >> 4) & 1),
            print "S3 (linearity alarm) = %x" % ((result[1] >> 3) & 1),
            print "S4 (increase mag) = %x" % ((result[1] >> 2) & 1),
            print "S5 (decrease mag) = %x" % ((result[1] >> 1) & 1),
            print "P1 (parity) = %x (count %02d)" % ((result[1] >> 0) & 1, bin(raw).count("1")),
        
    
        if parity_err:
            print "parity error for above result!"
            return 0
        
        return deg

if __name__ == '__main__':
    Encoder = EMS22A30(0, 0)
    Encoder.calibrate();

    while True:
        print "Degress from start: %7.3lf" % Encoder.getSample()
