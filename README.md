# GVE DevNet Catalyst to Meraki Migration
This repository contains a web app that will assist in applying a Catalyst switch configuration to a Meraki switch. Specifically, the app will copy the configuration of the Gigabit ports to the Meraki switch. The configuration that gets copied over is the port description/name, data vlan, voice vlan, shutdown status, and access/trunk mode. The code is built from the [Catalyst to Meraki Migration Tool](https://github.com/fadysharobeem/Catalyst_to_Meraki_Migration_tool).

## Contacts
* Danielle Stacy

## Solution Components
* Meraki
* Catalyst
* Python 3.9
* Flask

## Prerequisites
#### Meraki API Keys
In order to use the Meraki API, you need to enable the API for your organization first. After enabling API access, you can generate an API key. Follow these instructions to enable API access and generate an API key:
1. Login to the Meraki dashboard.
2. In the left-hand menu, navigate to `Organization > Settings > Dashboard API access.`
3. Click on `Enable access to the Cisco Meraki Dashboard API.`
4. Go to `My Profile > API access.`
5. Under API access, click on `Generate API key.`
6. Save the API key in a safe place. The API key will only be shown once for security purposes, so it is very important to take note of the key then. In case you lose the key, then you have to revoke the key and a generate a new key. Moreover, there is a limit of only two API keys per profile.

> For more information on how to generate an API key, please click [here](https://developer.cisco.com/meraki/api-v1/#!authorization/authorization). 

> Note: You can add your account as Full Organization Admin to your organizations by following the instructions [here](https://documentation.meraki.com/General_Administration/Managing_Dashboard_Access/Managing_Dashboard_Administrators_and_Permissions).

#### Meraki Switch Serial
In order for the API calls to successfully change the configuration of the Meraki switches, you will need to provide the serial numbers of the Meraki switches. If you have switches in a stack, be sure to input the serials of the Meraki switches in the order that they correspond to the Catalyst switch stack. 
To find the serial of the Meraki switches, follow these steps:
1. Login to the Meraki dashboard.
2. In the left-hand menu, navigate to `Organization > Configure > Inventory.`
3. This will display a table of all the devices in your inventory, and one of the columns of the table is the serial number of the device. You can sort the inventory by model or search for MS in the search box to neatly organize all the switches together and copy their serial numbers.

#### Catalyst Configuration
This web app requires a file containing the running configuration of the Catalyst switch that will be used as the base for the Meraki switch configuration. Be sure that you have exported the Catalyst configuration that you wish to migrate to Meraki to a readable file.

## Installation/Configuration
1. Clone this repository with `git clone [repository name]`
2. Set up a Python virtual environment. Make sure Python 3 is installed in your environment, and if not, you may download Python [here](https://www.python.org/downloads/). Once Python 3 is installed in your environment, you can activate the virtual environment with the instructions found [here](https://docs.python.org/3/tutorial/venv.html).
3. Install the requirements with `pip3 install -r requirements.txt`


## Usage
To start the web app, use the command:
```
$ flask run
```

Once the web app is running, open your browser and visit the address 127.0.0.1:5000 or localhost:5000.

#### Home page
On the home page, enter the API key, configuration file of the Catalyst switch, and the number of Meraki switches you have in your stack. Once you have entered the number of switches in the stack, you can enter the serial numbers of the switches. Be sure to enter the serials in the order that the switches map to the Catalyst switch stack. If you only have one switch, then enter the number 1, and one box will appear to enter the serial number. The steps to retrieve the information required on this page are described in the Prerequisites section.

#### Confirm Catalyst configuration parse
After you click `Start Migration` on the home page, you will be taken to a page that displays how the Catalyst configuration was parsed. Check that the configuration looks how you would expect it to, and then click `Confirm` if all looks correct. If something looks off, you can click `Back` to return to the Home page and double check the Catalyst configuration.

#### Meraki configuration confirmation
Once the `Confirm` button is clicked, the Catalyst configuration will be applied to the Meraki switches. As the API calls are made, a loading screen will be displayed. Once all the API calls are completed, a confirmation page will appear that displays the serial numbers of the switches and which of their ports have been successfully configured. If there was an error configuring one of the ports, the error message will display on the command line.


# Screenshots

![/IMAGES/0image.png](/IMAGES/0image.png)

#### Home page
![/IMAGES/home.png](/IMAGES/home.png)

#### Configuration confirmation page
![/IMAGES/config_confirmation.png](/IMAGES/config_confirmation.png)

#### Loading screen
![/IMAGES/loading_screen.png](/IMAGES/loading_screen.png)

#### Final confirmation page
![/IMAGES/final_confirmation.png](/IMAGES/final_confirmation.png)

#### Meraki ports before running the app
![/IMAGES/unconfigured_meraki_switchports.png](/IMAGES/unconfigured_meraki_switchports.png)

#### Meraki ports after running the app
![/IMAGES/configured_meraki_switchports.png](/IMAGES/configured_meraki_switchports.png)

#### Command line after running app
![/IMAGES/command_line_printout.png](/IMAGES/command_line_printout.png)

### LICENSE

Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

### CODE_OF_CONDUCT

Our code of conduct is available [here](CODE_OF_CONDUCT.md)

### CONTRIBUTING

See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER:
<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.
