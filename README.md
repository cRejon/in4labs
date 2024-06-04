In4Labs base LTI tool  [![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]
=====
# Description
Implementation of a [LTI 1.3 tool](https://www.imsglobal.org/activity/learning-tools-interoperability) with Python Flask for Raspberry Pi. It brings together the common functionalities for all In4Labs Arduino Labs: _login, time slot reservation_ and _access control_. The specific functionalities of each Lab must be implemented inside a Docker container that will be run by this tool.  
It's intended to function with a Moodle, instaled in a local server, that works as a _LTI consumer_ for the tool. This Moodle also works as a [_LTI provider_](https://docs.moodle.org/402/en/Publish_as_LTI_tool) for others Learning Management Systems (LMS), centralizing access to all LTI tools (Labs) developed and allowing dynamic registration.  
Tested on Raspberry Pi OS Bullseye (64-bit). For convenience, set the user name as **pi** (default).  
Requires Python >=3.9.

# Setup Raspberry Pi
## Docker installation
```
$ sudo apt update
$ curl -fsSL https://get.docker.com -o get-docker.sh
$ sudo sh get-docker.sh
$ sudo apt-get install -y uidmap
$ dockerd-rootless-setuptool.sh install
$ rm get-docker.sh
```
## Python dependencies
Copy this project inside _/home/pi_ folder and from there, create
a virtual environment and install the tool dependencies.
```
$ cd in4labs
$ sudo apt install -y python3-venv
$ python3 -m venv venv
$ . venv/bin/activate
(venv) $ pip install -r requirements.txt
```
## Generate JWT RS256 key and JWKS
Create the necessary keys for LTI protocol in the *config* folder.
```
$ cd in4labs_app/config
$ ssh-keygen -t rsa -b 4096 -m PEM -f jwtRS256.key
# Don't add passphrase
$ openssl rsa -in jwtRS256.key -pubout -outform PEM -out jwtRS256.key.pub
```
## Labs installation
There are two example Labs in the _labs_ folder, delete them and copy the ones you want to install.
### Create Docker images
Docker images must be built before the first time the tool is run. The production server (Gunicorn) does not manage this process correctly, so this functionality is included in the **_create_images.py_** script.  
In the project folder and inside the virtual environment, run:
```
(venv) $ python create_images.py
```
This process can take a long time, so be patient.
## Running Gunicorn server on boot
1. Create a systemd service file:
```
$ sudo nano /etc/systemd/system/gunicorn.service
```
2. Add the following content to the file:
```
[Unit]
Description=In4Labs App
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/in4labs
ExecStart=/home/pi/in4labs/venv/bin/gunicorn --workers 2 --timeout 1800 --bind 0.0.0.0:8000 -m 007 in4labs_app:app
Restart=always

[Install]
WantedBy=multi-user.target
```
3. Reload systemd daemon:
```
$ sudo systemctl daemon-reload
```
4. Start and enable the service:
```
$ sudo systemctl start gunicorn
$ sudo systemctl enable gunicorn
```
5. Check the status of the service:
```
$ sudo systemctl status gunicorn
```

# Configuration
The two main parameters to configure this tool are the public IPs for Moodle (**MOODLE_HOST**) and for the tool (**TOOL_HOST**).
## Moodle
To install Moodle in Ubuntu follow instructions in the [installation guide](https://docs.moodle.org/402/en/Step-by-step_Installation_Guide_for_Ubuntu).  
To add a new LTI tool, log in as an admin and follow the next steps:
1. Navigate to **_Site Administration -> Plugins -> Activity Modules -> External Tool -> Manage Tools_**
2. Click **_Configure a tool manually_** 
3. Enter the following information in the **_External tool configuration_** form: 
   #### Tool settings
   - Tool name: TOOL_NAME
   - Tool URL: http://TOOL_HOST/launch
   - LTI version: LTI 1.3
   - Public key type: Keyset URL
   - Public keyset: http://TOOL_HOST/jwks
   - Initiate login URL: http://TOOL_HOST/login
   - Redirection URI: http://TOOL_HOST/launch
   - Tool configuration usage: Show as preconfigured tool when adding an external tool
   - Default launch container: New window
   - Do NOT check "Supports Deep Linking"
   #### Services
   - IMS LTI Assignment and Grade Services: Do not use this service
   - IMS LTI Names and Role Provisioning: Use this service to retrieve members' information as per privacy settings 
   - Tool Settings: Do not use this service
   #### Privacy
   - Share launcher's name with tool: Always
   - Share launcher's email with tool: Always
   - Accept grades from the tool: Never
  
4. When complete, click **Save changes** and the tool should appear. In its upper right corner, click in the **View configuration details** icon to obtain the necessary information to configure the tool. It will look similar to this:
   - Platform ID: http://MOODLE_HOST/moodle
   - Client ID: CLIENT_ID
   - Deployment ID: DEPLOYMENT_ID
   - Public keyset URL: http://MOODLE_HOST/moodle/mod/lti/certs.php
   - Access token URL: http://MOODLE_HOST/moodle/mod/lti/token.php
   - Authentication request URL: http://MOODLE_HOST/moodle/mod/lti/auth.php
5. To add the tool to a course follow the instruction in this [link](https://docs.moodle.org/402/en/External_tool).

## Tool
Edit **_config.py_** file inside _config_ directory and change the variables of the **_Config_** object to those required.
### Flask settings
Change the development variables to those needed in production, including the use of HTTPS. 
### LTI settings
Fill the string variables *MOODLE_HOST*, *CLIENT_ID*, and *DEPLOYMENT_ID* with the above information obtained in Moodle.
### Labs settings
The *lab_name* variables must have the same name as the folders installed in the *labs* directory. The *nat_port* is the port that the gateway will use to redirect the traffic to the Docker container.
# License
This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg
