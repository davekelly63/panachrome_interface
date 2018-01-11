#!/usr/bin/env python
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import datetime
import time
import random
from threading import Thread

import observer
from serial_interface import SerialInterface

PORT_NAME = '/dev/panachrome'
BAUD_RATE = 115200


# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None

serial_port = SerialInterface()


def serial_event(data):
    """
    Data received form the serial port
    """

    if data:
        socketio.emit('rx_data', {'data': data}, namespace='/test')


def serial_listener():
    """
    Continuously poll the serial port, replies from the controller
    """

    serial_port.port_name = PORT_NAME
    serial_port.baud_rate = BAUD_RATE
    serial_port.open()
    serial_port.observe('serial_event', serial_received)

        # Just define the callback function

    def serial_received(self, data):
        serial_event(data)



def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    for x in range(1, 20):
        socketio.sleep(0.1)
        count += 1
        dt = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

        socketio.emit('my_response',
                      {'data': 'Server generated event {}\n'.format(dt), 'count': count},
                      namespace='/test')

        socketio.emit('charting', {'data': chart_data()}, namespace='/test')

def chart_data():
    """
    Generate a chart with random values
    """
    data = []

    for x in range(0, 48):
        data.append(random.getrandbits(8))

    return data

@socketio.on('send_command', namespace='/test')
def command_message(message):
    """
    Send button pressed, pass the command to the serial port
    """

    print('Send button')

    if serial_port.is_open():
        serial_port.write(message['data'].encode('latin1'))
    else:
        emit('my_response', {'data': 'Serial port not open\n'})


@socketio.on('my_event', namespace='/test')
def trace_message(message):
    """
    Special handler for the trace button
    """
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': message['data'], 'count': session['receive_count']})


@socketio.on('killing_serial', namespace='/test')
def kill_serial_message(message):
    """
    Special handler for the kill serial button
    """
    print('Killing serial thread')
    emit('my_response', {'data': 'Killing serial thread'})


@socketio.on('connect', namespace='/test')
def test_connect():
    """
    Event generated when new client connects
    """
    global thread
    if thread is None:
        thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected\n', 'count': 0})

    emit('port_name', {'data': str(serial_port.port_name)}, namespace='/test')
    print('Send port name')


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    """
    Event generated when client disconnects
    """
    print('Client disconnected', request.sid)

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


if __name__ == '__main__':
    # Start the serial port listener first
    Thread(target=serial_listener, args=()).start()

    socketio.run(app, host='0.0.0.0', debug=True)
