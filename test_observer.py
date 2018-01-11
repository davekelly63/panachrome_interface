# Test Observer class

from observer import Observer, Event
import time

def Sender():
    print('Send data generator')
    for x in range(1, 10):
        #print ('Generating event for ' + str(x))
        Event('serial_event', x)



def SerialReceived(data):
    print(data)

class Test(Observer):

    def __init__(self):
        Observer.__init__(self) # Observer's init needs to be called


    def data_received(self, value):
        SerialReceived(value)


if __name__ == "__main__":

    test = Test()
    test.observe('serial_event', test.data_received)

    Sender()


