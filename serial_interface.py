# Serial interface
# Class for serial interface to the end product.
# Creates callback events when we receive edata from the serial port

import serial
import os
import time
from threading import Thread
import glob
import io
from observer import Event, Observer

class SerialInterface(Observer):
    """
    Doc
    """

    # region fields

    __serial_port = serial.Serial()
    __sio = sio = io.TextIOWrapper(io.BufferedReader(__serial_port))        # Use a buffered reader on the serial port
    __stop_polling = False  # To stop polling the serial port thread

    #end region


    def __init__(self):
        Observer.__init__(self) # Observer's init needs to be called
        self.__serial_port.port = ""
        self.__serial_port.baudrate = 576000
        self.__serial_port.timeout = 0.1

    #region properties

    def __set_port(self, value):
        self.__port_name = value

    def __get_port(self):
        return self.__port_name

    port_name = property(__get_port, __set_port)

    def __set_baud_rate(self, value):
        self.__baud_rate = value

    def __get_baud_rate(self):
        return self.__baud_rate

    baud_rate = property(__get_baud_rate, __set_baud_rate)

    def __set_timeout(self, value):
        self.__timeout = value

    def __get_timeout(self):
        return self.__timeout

    timeout = property(__get_timeout, __set_timeout)

    #endregion


    #region methods

    def closing_app(self):
        # Been signalled that the app is closing, finish the polling thread and close the port
        # to reduce the number of errors after the close
        self.__stop_polling = True
        self.close()


    def open(self):
        """
        Open the serial port set in the port_name property
        """

        # Close it first, so the port and baud can be set
        #
        try:
            self.__serial_port.close()
        except serial.SerialException:
            pass

        if len(self.port_name) > 0:
            # noinspection PyUnusedLocal
            try:
                self.__serial_port.port = self.port_name
                self.__serial_port.baudrate = self.baud_rate
                self.__serial_port.timeout = self.timeout
                self.__serial_port.open()
                Thread(target=self.__poll_port).start()
                self.__stop_polling = False
                print('opened com port ' + self.port_name)
            except serial.SerialException as ex:
                pass

    def close(self):
        """
        Close the current serial port
        """
        self.__stop_polling = True  # Flag the polling thread to finish
        self.__serial_port.close()


    def is_open(self):
        """
        return the state of the serial port
        """

        return self.__serial_port.isOpen


    def write(self, data):
        """
        Write the string data to the serial port. If the data is not terminated with a CR, append it
        as the controller only responds on receipt of the CR
        """
        if data[-1] != '\r':
            data += '\r'

        # Encode the data into bytes
        command = data.encode('latin1')

        print('Command sent ' + command)
        try:
            self.__serial_port.write(command)
        except serial.SerialException as ex:
            print('Bad news in writing to the serial port')
            print(ex)

        # Allow a little time for the controller to action the command, else when sending
        # 2 consecutive commands the second is missed
        time.sleep(0.1)

    def readline(self):
        """
        Read back a CR terminated line of data from the port
        """
        return self.__serial_port.readline().decode('utf8')

    def read(self):
        """
        Read back all existing data in the serial port buffer
        """
        return self.__serial_port.read().decode('utf8')

    def flush(self):
        """
        As it says
        """
        self.__serial_port.flush()

    #endregion

    #region private methods

    def __poll_port(self):
        """
        Poll the serial port on a regular basis to check for data in the buffer
        Implemented in a separate thread
        """

        while True:

            time.sleep(0.05)

            if self.__stop_polling:
                self.close()
                return

            if self.__serial_port.isOpen():
                # Serial port data is binary, so must be converted to string for manipulation
                rx_data = self.__serial_port.readline().decode("utf-8")

                Event('serial_event', rx_data)

    #endregion



