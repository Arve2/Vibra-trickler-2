# In general...
The Vibra-trickler 2 is an affordable DIY auto-trickler with a mobile/web GUI for handloaders. This is achieved by...
- weighing gunpowder with a **load cell**
- converting the weight to numbers using **HX711**,
- setting up a **Raspberry Pi (Zero)** to
   - read weight input,
   - handle logic and web GUI with **Node-Red**,
   - control output power with **GPIO PWM**, thus
- trickling gunpowder at varying speed with a **vibrator motor**.

## Video on operations:
<a href="https://youtu.be/tTNcfGOGy2k"><img src="https://img.youtube.com/vi/tTNcfGOGy2k/sddefault.jpg" width="400" ></a>

## The kit:
![Overview](media/Overview.jpg)

## Past and (no) planned development
This project is an improvement on my old [Vibra-trickler 1](https://www.youtube.com/watch?v=v3MtZg-lgy8) project. It's main feature was turning any balance scale into an auto-trickler. It's main _drawbacks_ were
1. having to trickle slooowly due to physical latency of the scale,
1. a lot of job hours and fiddling to reproduce the kit.

As far as my personal interest goes, the project is "done". All the drawings, circuits, mobile web app and software works fine. But the time gained is only about 5s compared to my old Vibra-trickler 1. Hence, I wont't spend more time polishing or packaging the design further.

# Disclaimer
I thought I was the only person foolish enough to combine gunpowder and electronics. Now you have read this far, so I hope you know what you are doing. Use everything described below is at your own risk. Proceed with caution! 

# Bill of material
- [RPi](https://www.electrokit.com/raspberry-pi-zero-w-board)
- [HX711](https://www.ebay.com/itm/295617541450)
- [load cell](https://www.aliexpress.com/item/32736635992.html) - the smaller range, the more sensitive!
- 78L05
- LM2596 or similar
- Small DC vibrator motor
- a known weight
- powder hopper, preferrably with baffle for consistant flow
- **@ToDo:** More

# How to...
Below, i will 
- describe the steps to build and configure a vibra-trickler 2.
- use `192.168.0.66` as the IP address of the RPi. Your's will differ, so replace with your own RPi IP accordingly.
- use [pin numbers](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header) 1...40 when describing physical GPIO pins.

## Connect hardware
Note that...
- the HX711 needs a separate high precision voltage regulator, hence a 78L05 or similar. 
- the RPi and vibrator draws more current, hence an LM2596 regulator or similar. 
- the load cell and 78L05 should be close to the HX711, preferably [like this](media/HX711-loadcell-assembly.jpg)

More nerding about hardware design considerations later. For now 'just'...
1. Mount vibrator motor on the powder hopper's feeding tube.
1. Connect power supply and LM2596 regulator on a breadboard > Adjust the regulated voltage to **5,1V** > _Disconnect_ power supply.
1. Connect all other components according to the circuit design below.
![Circuit design](media/Circuit-design.jpg)

## Install and configure operating system
Vibra-trickler uses Raspberry Pi Lite - i.e. SSH/CLI only. It might work on desktop Linux flavours as well, but no Linux GUI is needed. (We will install Node-Red with it's web-GUI later.)
1. On a PC, use [Raspberry Pi Imager](https://www.raspberrypi.com/documentation/computers/getting-started.html#install-using-imager) to 
   - configure **user** `pi` and set a **password**, 
   - set **Wifi** connection to your home network, 
   - enable **SSH** and
   - write **Raspberry OS Lite** on an SD card
1. Insert SD card in RPi.
1. Start up the RPi (breadboard power supply). 
1. Find the RPi's **IP adress** on a monitor or in your home DHCP server. _My RPi IP addres was `192.168.0.66`. Replace with your own accordingly in the rest of this document._
1. `ssh pi@192.168.0.66` _You should now be logged in to your RPi. The commands below are for the RPi SSH console._
1. `sudo apt-get update` _Update APT_
1. `sudo apt-get upgrade` _Upgrade Linux_
1. `sudo raspi-config` > System > Network at boot > No _Speeds up boot by not waiting for network._

## Install WiringPi
WiringPi is used for controlling GPIO pins, e.g. HX711 input from load cell and PWM output to vibrator. More info at http://wiringpi.com/. 
1. `wget https://project-downloads.drogon.net/wiringpi-latest.deb`
1. `sudo dpkg -i wiringpi-latest.deb`
1. `gpio -v` _Should show version 2.52 or later._

## Connect a power button (optional)
_This is not required, but you might go crazy without it. It's also a sanity check for WiringPi. Shorting pin 5 to GND is the default start-trigger for RPi. Let's make it STOP the RPi as well..._
1. Connect **pin 5** --> standard (n/o) **push-button** --> **GND**. _See circuit design._
1. `sudo nano /usr/local/bin/safeshutdown.sh` > Insert the script block below > Save and exit Nano (Ctrl X > Y > Enter)
   ```bash
   #!/bin/bash
   gpio -g mode 3 up #Pull-up pin 5 (GPIO #3) to 1
   gpio -g wfi 3 falling #Wait For falling to 0
   sudo poweroff
   ```
1. `sudo chmod a+x /usr/local/bin/safeshutdown.sh` _Make it executable._
1. `sudo nano /etc/rc.local` > Insert `/usr/local/bin/safeshutdown.sh &` just above the line "exit 0" > Save and exit Nano. _This will start safeshutdown.sh in the background, after reboot_
1. `sudo reboot`
1. Test shutdown by pressing the button once. Wait until the green LED is completely off.
1. Start the RPi again by pressing the button once more. Wait until the green LED is completely on.

## Calibrate PWM for the vibrator
_Pin 12 corresponds to gpio #18, which supports PWM (Pulse Width Modification) of output. The 2k2 resistor restricts the output current to a GPIO-safe level (3,3V / 2200ohm = 1,5mA). The BC547**C** transistor amplifies it to 630mA (1,5mA x 420hfe = 630mA) - over six times the vibrator current draw. The 220uF capacitor smooths out PWM spikes. The diode shorts out any flyback current TO the RPi from the vibrator motor. Now let's figure out the max and min PWM levels._
1. Connect a volt meter over the vibrator motor.
1. Get specified max voltage from data sheet of virator motor.
1. `gpio -g mode 18 pwm` _Set pin 12 to PWM mode._
1. `gpio -g pwm 18 512 && sleep 1 && gpio -g pwm 18 0` _Run for one second at 50% duty cycle._
   - Adjust the `512` part of the command _down_ and repeat it until the motor no longer vibrates. Then up a bit until it starts again. This is your **minimum PWM duty cycle**.
   - Adjust the `512` part of the command _up_ and repeat it until the volt meter hits vibrator max voltage. This is your **maximum PWM duty cycle**.

For reference, min and max duty cycle for my kit is
- min: `gpio -g pwm 18 200` --> 1,1V --> Powder flow 1,5gr/s.
- max: `gpio -g pwm 18 800` --> 3,8V --> Powder flow 8,5gr/s.

## Test and calibrate HX711 with load cell
The HX711 excites the load cell's Wheatstone bridge with 5V and measures it's output voltage. The voltage is converted to numbers and sent to RPi pin 29, using pin 31 for clock/trigger. The [HX711 library](https://github.com/gandalf15/HX711) from Gandalf15 is used to receive the readings in RPi. `.\scripts\hx-start.py` will be used 
1. `sudo apt-get install git -y` _Install Git_
1. `pip3 install 'git+https://github.com/gandalf15/HX711.git#egg=HX711&subdirectory=HX711_Python3'` _Pip-install from Gandalf15's Git_
1. First, try some readings from the HX711 manually:
   - `python3` to open a Python console. In it, run these commands:
      ```python
      import RPi.GPIO as gpio
      gpio.setmode(gpio.BOARD) #Use physical pin numbers
      from hx711 import HX711
      hx = HX711(dout_pin=29, pd_sck_pin=31)
      hx.reset() #This, and some other commands, returns FALSE if successful
      hx._read() #Get one raw reading
      hx.get_data_mean(5) #Get average from 5 readings
      gpio.cleanup() #Reset GPIO pins
      ```
   - Press `Ctrl C` to exit the Python console.
1. Make sure you are in the home directory i.e. default path for Node-RED: `cd ~/`
1. Download python script from GitHub to get continuous HX711 readings: `curl -O https://raw.githubusercontent.com/Arve2/Vibra-trickler-2/main/scripts/hx-start.py` _This will be used below, and also by Node-RED later._
1. Run the script: `python3 hx-start.py` _This should produce a continous flow of readings._
1. Note the values and approximate a rough median (in my case 1278000). This will be your **start payload** for Node-RED deviation filter later.
1. Place some weight on the scale. The readings should increase following the weight. If the readings _decrease:_ Reverse the load cell by switching A+/A- terminals, or simply turn it upside down.
1. Press `Ctrl C` to exit the Python console.

## Install Node-RED
[Node-RED](https://nodered.org/) is a great graphic automation tool in Node-JS server. It's [Dashboard](https://flows.nodered.org/node/node-red-dashboard) makes for a stylish mobile web GUI. The steps below are based on [this guide](https://nodered.org/docs/getting-started/raspberrypi) for Node-RED on RPi, including some tweaks.
1. Download and install:
    ```bash
    curl https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered --output noderedinstaller.sh
    bash noderedinstaller.sh --confirm-pi --allow-low-ports --confirm-install
    ```
1. _Be patient. Especially over SSH - connection might drop while install is actually going just fine._
1. Answer No to "customize settings now". 
1. Start Node-RED manually first time to try it: `node-red-pi --max-old-space-size=256`
1. On PC, browse to http://192.168.0.66:1880. _You should now see the Node-red flow editor. This is the "admin" part._
1. Stop Node-RED with `Ctrl C`
1. Use Nano to tweak the settings a bit: `nano ~/.node-red/settings.js` > Change/set the following properties... 
   - `flowFilePretty: true` _Good for export/editing._
   - `uiPort: process.env.PORT || 80` _Use default HTTP port._
   - `httpAdminRoot: '/admin'` _More intuitive, since the frontend is `ui` by default_
   - `debugUseColors: true` _Helpful for troubleshooting._
1. Save and exit Nano (Ctrl X > Y > Enter)
1. Autostart Node-red on boot: `sudo systemctl enable nodered.service` _Note: `max-old-space-size=256` seems to be default for nodered.service, at least after usin noderedinstaller.sh as above._
1. Reboot RPi using fancy button or `sudo reboot`
1. You should now be able to browse from PC to the Node-RED admin GUI at http://192.168.0.66/admin

## Import Vibratrickler flow in Node-RED
Now that Node-RED is installed, it will be used to handle the flow of HX711 input, filtering, logics, PWM output and web GUI. In the admin GUI...
1. Click the pancake-stack at the top right > `Import` > `Select a file to import` > Browse to `.\flows.json` > `Import` > Finnish import process. You should now see a flow like this:
![Node-RED admin](media/Web-GUI_admin.jpg)
1. Double-click the node `Reset variables`. After `Set / msg.payload / to the value` > Replace the default (127800) to the start payload noted earlier > Click `Done`. _Two nodes down the flow, large deviations from this value will be blocked, so it needs to be adjusted to each indivitual kit._
1. Double-click the node `Weight in. PWM out` and...
   - At line 24 replace the payload `650` with your PWM max duty cycle noted earlier - max speed.
   - At line 34 replace the payload `325` with your PWM min duty cycle noted earlier, or a bit higher - slow and intermittant speed.
1. Click `Deploy` at the top right to deploy the imported flow to the server. 

## Throw powder
1. Fill the powder hopper. I suggest chia- or poppy-seeds or alike - NOT gunpowder this first try.
1. Browse to the Node-RED GUI at http://192.168.0.66/ui, from PC or smartphone.
1. Tare and Calibrate just like a normal digital powder scale.
1. Set target weight and Throw.
![Node-RED user](media/Web-GUI_user.jpg)

The above will probably _not_ work right out of the box. 
- If the powder flow during first phase is too fast, the target weight will be overshot before the vibrator has time to slow down from max speed. Edit the node `Weight in. PWM out` >  line 22 > `10.5` grains margin to a higher margin.
- The reverse applies if the vibrator slows down waaaay before the target weight - try a lower margin.
- If the vibrator runs too slow or too fast during the second phase, edit the slow vib setting at line 34.
- Remember to `Deploy` again after each change. The scale will re-zero itself 10s after deploy.

# Hardware design and considerations
**@ToDo:**
- Powder pan / stirrup with pictures
- 3D prints
- Accuracy improvements
- Powder hopper, vibrations, feeding tube, holes, angle
- Details/description of flow