# [Cold Switch Network Contol](https://github.com/lafefspietz/cold-switch-network-control)

HTML control panel sends signals via web socket to Python loop which controls a set of 4 MM4250 switches. The pair in the middle are controlled together by one controller split from one micro-D to a pair of cables at the bottom of the dilution refrigerator. The other two are controlled by the MEMSDuino Arduino-based controller. The commercial controller uses HID and the MEMSDuino use a single character sent down the serial line. The exact code here is using the hardware ID's of the Arduino Mega boards in the MEMSDuino. 

This repo is for debugging only and is not the final product. It is to break out the development into separate elements so that they are easier to understand and put into the final product, which will be the web-based front end of a quantum network analyzer.

To run, set up a local web server and run it and then open a miniforge prompt, go to the folder where everythnig is, and run instrument.py. That has a loop which controls the hardware and listens for instructions from instrument.html.  

![](screenshot.png)

![](schematic.png)

 - [instrument.html](instrument.html)
 - [instrument.css](instrument.css)
 - [instrument.js](instrument.js)
 - [instrument.json](instrument.json)
 - [instrument.py](instrument.py)
 