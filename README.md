# Heat pump control
A program for Raspberry Pi 1 B+ to control a servo which turns a potentiometer of a ground-source heat pump's temperature offset. It aimes to optimize electricity bill, so that the heat pump is run on the lowest electricity prices. 

Price info is retrieved from www.sahkonhinta-api.fi which collects Nordpool spot prices and provides them easily via API. As usually new prices are published in the afternoon, the program checks the prices and makes time adjustments for the next 24 hours on 18:30 Finnish time. It then selects the lowest possible average price of the user given time span. So for example if the user has set the heating must be on normal level 8 hours and the lowest average price for 8 hours period is between 23:00 and 07:00, the start time for the heating will be at 23:00 and stop time at 07:00.

If prices for some reason cannot be updated (for example www.sahkonhinta-api.fi is down), the program will select the the start and stop times so that the middle of the time span is at 02:00. So for example if the user has set the heating must be on normal level 8 hours, the start will be at 22:00 and stop at 06:00.

Program has an API that you can access on you local network with HTTP calls. Possible calls are:

Setting the low or normal value of the heat pump's temperature:

PUT http://{host_ip}:5000/api/control?temp=normal or (temp=low)


Setting the time span when heating should be on (NORMAL):

PUT http://{host_ip}:5000/api/heattime?hours=8 (time between 0 and 23)


Checking the servo positions:

GET http://{host_ip}:5000/api/api/positions


Setting the servo positions for LOW and NORMAL operation:

UT http://{host_ip}:5000/api/api/positions?position1=45 (or position2)


To test if the API is working:

GET http://{host_ip}:5000/api/test


To check the times that are set for the servo scheduled control:

GET http://{host_ip}.199:5000/api/times


If you want to override the set times for the servo scheduled control. Time1 for NORMAL operation and time2 for LOW operation:

PUT http://{host_ip}:5000/api/update_times?time1=21:00&time2=05:00
