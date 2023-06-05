from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import datetime
import RPi.GPIO as GPIO
import schedule
import time
import pytz
import threading
import re
import requests

# API calls:
# PUT http://{host_ip}:5000/api/control?temp=normal or (temp=low)
# PUT http://{host_ip}:5000/api/heattime?hours=8 (time between 0 and 23))
# GET http://{host_ip}:5000/api/positions
# PUT http://{host_ip}:5000/api/positions?position1=45 (or position2)
# GET http://{host_ip}:5000/api/test
# GET http://{host_ip}:5000/api/times
# PUT http://{host_ip}:5000/api/update_times?time1=21:00&time2=05:00


# Set the time zone to Finnish time (Eastern European Time) for datetime
finnish_tz = pytz.timezone('Europe/Helsinki')

time1 = '22:00'
time2 = '06:00'
price_check_time = '18:30'
hours = 8
servo_position1= 135
servo_position2= 45
app = Flask(__name__)
servo_pin = 18  # Replace with your chosen GPIO pin number


class ServoController:
    def __enter__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(servo_pin, GPIO.OUT)
        self.servo = GPIO.PWM(servo_pin, 50)  # 50 Hz frequency
        self.servo.start(0)
        return self.servo

    def __exit__(self, exc_type, exc_value, traceback):
        self.servo.stop()
        GPIO.cleanup()


def set_angle(servo, angle):
    duty = int(angle) / 18 + 2
    GPIO.output(servo_pin, True)
    servo.ChangeDutyCycle(duty)
    time.sleep(1)
    GPIO.output(servo_pin, False)
    servo.ChangeDutyCycle(0)
    time.sleep(1)


def set_to_normal():
    global servo_position1
    with ServoController() as servo:
        set_angle(servo, servo_position1)
    current_time = datetime.datetime.now(finnish_tz).time()
    print(current_time, ' Temperature request set to NORMAL. Servo position at ' + str(servo_position1) + ' degrees.')


def set_to_low():
    global servo_position2
    with ServoController() as servo:
        set_angle(servo, servo_position2)
    current_time = datetime.datetime.now(finnish_tz).time()
    print(current_time, ' Temperature request set to LOW. Servo position at ' + str(servo_position2) + ' degrees.')


def is_time_valid(time):
    pattern = r'^([0-1][0-9]|2[0-3]):([0-5][0-9])$'
    match = re.match(pattern, time)
    if match:
        return True
    else:
        return False


# Updates time1 and time2 with start and stop time of hours with lowest average electricity price in the given time span between today 19:00 and tomorrow 18:00.
def start_stop_times(hours):
    global time1
    global time2 
    hours += 1
    # Calculate the current and next day
    current_date = datetime.date.today()
    next_date = current_date + datetime.timedelta(days=1)
    # Create the time range string
    time_range = f"{current_date.isoformat()}T19:00_{next_date.isoformat()}T07:00"
    url = 'https://www.sahkohinta-api.fi/api/v1/halpa'
    params = {
        'tunnit': hours,
        'tulos': 'sarja',
        'aikaraja': time_range
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        # Extract the timestamps and convert them to datetime objects
        timestamps = [datetime.datetime.fromisoformat(entry['aikaleima_suomi']) for entry in data]
        # Find the earliest and latest timestamps
        start_time = min(timestamps).strftime("%H:%M")
        stop_time = max(timestamps).strftime("%H:%M")
        # Update time1 and time2 with new values
        time1 = start_time
        time2 = stop_time
        current_time = datetime.datetime.now(finnish_tz).time()
        print(current_time, ' Start and stop times updated based on electricity prices: Start:' + time1 + ', Stop:' + time2)
    else:
        # Convert time string to datetime object
        time_obj = datetime.strptime('02:00:00', '%H:%M:%S')
        # Calculate the modified times
        time1 = (time_obj - timedelta(hours=hours/2)).strftime('%H:%M')
        time1 = (time_obj + timedelta(hours=hours/2)).strftime('%H:%M')
        print(current_time, " Electricity prices couldn't be updated. Maybe www.sahkonhpinta-api.fi is down. Times set to: Start:" + time1 + ', Stop:' + time2)


def is_valid_hour(value):
    try:
        hour = int(value)  # Convert the value to an integer
        return 0 <= hour <= 23  # Check if it is between 0 and 23
    except ValueError:
        return False  # Return False if the conversion to int fails

    
# Schedule tasks
schedule.every().day.at(price_check_time, 'Europe/Helsinki').do(start_stop_times, hours).tag('start_stop_times')
schedule.every().day.at(time1, 'Europe/Helsinki').do(set_to_normal).tag('set_to_normal')
schedule.every().day.at(time2, 'Europe/Helsinki').do(set_to_low).tag('set_to_low')


# API endpoint for setting the temperature to LOW or NORMAL
@app.route('/api/control', methods=['PUT'])
def control():
    global servo_position1
    global servo_position2
    try:   
        temp = request.args.get('temp') 
        if temp == 'normal':
            set_to_normal()
            return 'Temperature request set to NORMAL. Servo position at ' + str(servo_position1) + ' degrees.'
        if temp == 'low':
            set_to_low()
            return 'Temperature request set to LOW. Servo position at ' +  str(servo_position2) + ' degrees.'
        return 'Invalid request. Accepted requests are "/api/control?temp=normal" or "/api/control?temp=low"', 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400  # Return error message with 400 Bad Request status


@app.route('/api/heattime', methods=['PUT'])
def heating_hours():
    global hours
    try:   
        new_hours = request.args.get('hours') 
        if 'hours' in request.args and is_valid_hour(new_hours): 
            hours = new_hours
            return 'Heating time set to ' + str(hours) + ' hours.'
        return 'Invalid request. Heating time can be between 0 and 23 hours as integer.', 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400  # Return error message with 400 Bad Request status
    

# API endpoint for checking the NORMAL and LOW servo positions
@app.route('/api/positions', methods=['GET'])
def get_servo_position():
    try:
        global servo_position1
        global servo_position2
        return 'Servo position1 (NORMAL): ' + str(servo_position1) + ' degrees. Servo position2 (LOW): ' + str(servo_position2) + ' degrees.'
    except Exception as e:
        return jsonify({'error': str(e)}), 400  # Return error message with 400 Bad Request status


# API endpoint for changing the servo angles
@app.route('/api/positions', methods=['PUT'])
def put_servo_position():
    global servo_position1
    global servo_position2
    try: 
        new_position1 = request.args.get('position1')
        new_position2 = request.args.get('position2')
        if 'position1' in request.args:    
            if int(new_position1) >= 0 and int(new_position1) <= 180:
                servo_position1 = new_position1
                return 'Servo position1 (NORMAL) set to ' + str(servo_position1) + ' degrees.'   
            else:
                return 'Invalid position. Position should be between 0 and 180 degrees.', 400   
        if 'position2' in request.args: 
            if int(new_position2) >= 0 and int(new_position2) <= 180:
                servo_position2 = new_position2
                return 'Servo position2 (LOW) set to ' + str(servo_position2) + ' degrees.'   
            else:
                return 'Invalid position. Position should be between 0 and 180 degrees.', 400
            # If neither 'position1' nor 'position2' is present in the request arguments
        return 'Invalid request. Missing position parameter. You should use "position1=x" or "position2=x", x being the angle in degrees between 0 and 180.', 400    
    except Exception as e:
        return jsonify({'error': str(e)}), 400  # Return error message with 400 Bad Request status


# API endpoint for testing if the API works
@app.route('/api/test', methods=['GET'])
def test_api():
    try:
        return 'API seems to be working.'
    except Exception as e:
        return jsonify({'error': str(e)}), 400  # Return error message with 400 Bad Request status


# API endpoint for checking the times set
@app.route('/api/times', methods=['GET'])
def check_time():
    global time1
    global time2
    try:
        return 'Times set for changing the temperature are: to NORMAL@' + time1 + ', to LOW@' + time2
    except Exception as e:
        return jsonify({'error': str(e)}), 400  # Return error message with 400 Bad Request status

# API endpoint to update task times
@app.route('/api/update_times', methods=['PUT'])
def update_tasks():
    global time1
    global time2
    new_time1 = time1
    new_time2 = time2
    try:
        if 'time1' in request.args and is_time_valid(request.args['time1']) is False or 'time2' in request.args and is_time_valid(request.args['time2']) is False:
            return 'Invalid request. Time should be between 00:00 and 23:59 in the format of HH:MM', 400
        if 'time1' in request.args and is_time_valid(request.args['time1']):
            new_time1 = request.args['time1']
            schedule.clear('set_to_normal')
            schedule.every().day.at(new_time1, 'Europe/Helsinki').do(set_to_normal).tag('set_to_normal')
            current_time = datetime.datetime.now(finnish_tz).time()
            print(current_time, 'Time1 changed to', new_time1)
        if 'time2' in request.args and is_time_valid(request.args['time2']):
            new_time2 = request.args['time2']
            schedule.clear('set_to_low')
            schedule.every().day.at(new_time2, 'Europe/Helsinki').do(set_to_low).tag('set_to_low')
            current_time = datetime.datetime.now(finnish_tz).time()
            print(current_time, 'Time2 changed to', new_time2)
        # Update global variables only if a time is provided
        time1 = new_time1
        time2 = new_time2
        return 'Time(s) updated successfully. Times set for changing the temperature are: to NORMAL@' + time1 + ', to LOW@' + time2
    except Exception as e:
        return jsonify({'error': str(e)}), 400  # Return error message with 400 Bad Request status

def run_flask_app():
    app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    # Start Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()

    # Main loop to execute scheduled tasks
    while True:
        schedule.run_pending()
        time.sleep(1)

