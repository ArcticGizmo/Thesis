import sys
import serial

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "Error [current Baud] [desired Baud]"
    else:
        serialObj = serial.Serial(port="/dev/ttyS0", baudrate=int(sys.argv[1]))
        string = " @(" + str(sys.argv[2]) + ",0,F) "
        print string
        serialObj.write(string)
        serialObj.close()
        print "Changed from ", sys.argv[1], " to ", sys.argv[2]
