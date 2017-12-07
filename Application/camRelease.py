import usb.core
import time


def release(dev):
    '''
        releases a given device within 0.5 seconds
        * if successful return true
        * if unsuccessful return false
    '''
    try:
        dev.reset()
        time.sleep(0.5)
        print "released device"
        return True
    except:
        print "device failed to release"
    return False

if __name__ == "__main__":
    '''
        Set to release attached BFLY cameras from the USB port
    '''
    dev = usb.core.find(find_all=True, idVendor=7696, idProduct=13056)
    for d in dev:
        release(d)
    dev.close()



