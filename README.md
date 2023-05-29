# Heat pump control
Program to control a servo which turns potentiometer of ground-source heat pump's temperature offset. It is aimed for optimizing electrical bill so the heat pump is run mainly at night when the price of exchange electricity is low.
At this point it is only time controlled, so the pump will turn to low temperature setting during the day and to normal temperature setting at night when the electricity is cheaper.
Future implementation will include the time's to be set based on the price of electricity in the exchange.

It has an API that you can access on you local network with HTTP calls. Possible calls are:

Setting the low or normal value of the heat pump's temperature:

PUT http://{host_ip}:5000/api/control?temp=normal or (temp=low)


Checking the servo positions:

GET http://{host_ip}:5000/api/api/positions


Setting the servo positions for LOW and NORMAL operation:

PUT http://{host_ip}:5000/api/api/positions?position1=45 (or position2)


To test if the API is working:

GET http://{host_ip}:5000/api/test


To check the times that are set for the servo scheduled control:

GET http://{host_ip}.199:5000/api/times


To set the times for the servo scheduled control:

PUT http://{host_ip}:5000/api/update_times?time1=21:00&time2=05:00
