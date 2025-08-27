In4Labs base LTI tool  [![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]
=====
# Description
Implementation of a [LTI 1.3 tool](https://www.imsglobal.org/activity/learning-tools-interoperability) with Python Flask for Raspberry Pi. It brings together the common functionalities for all In4Labs Arduino Labs: _login, time slot reservation_ and _access control_. The specific functionalities of each Lab must be implemented inside a Docker container that will be run by this tool.  
It's intended to function with a Moodle, instaled in a local server, that works as a _LTI consumer_ for the tool. This Moodle also works as a [_LTI provider_](https://docs.moodle.org/402/en/Publish_as_LTI_tool) for others Learning Management Systems (LMS), centralizing access to all LTI tools (Labs) developed and allowing dynamic registration.  
Tested on Raspberry Pi OS Bullseye (64-bit). Requires Python >=3.9.
# Setup Raspberry Pi
The best way to burn the Raspberry Pi OS image is using [Raspberry Pi Imager](https://www.raspberrypi.org/software/). In advanced options, select _Enable SSH_ and _Time zone_ to your local time zone.  
## Docker installation
1. Install Docker through its bash script selecting the version to **25.0.5**:
``` bash
sudo apt update
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh --version 25.0.5
```
2. Manage Docker as a non-root user:
```  bash
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```
## Install this tool and its Python dependencies
Clone this project inside HOME directory and create a virtual environment to install the tool dependencies.
``` bash
sudo apt install -y git python3-venv
git clone https://github.com/cRejon/in4labs.git $HOME/in4labs
cd $HOME/in4labs && python3 -m venv venv
. venv/bin/activate
(venv) pip install -r requirements.txt
```
## Generate JWT RS256 key and JWKS
Create the necessary keys for LTI protocol in the app folder.
``` bash
cd $HOME/in4labs/in4labs_app
ssh-keygen -t rsa -b 4096 -m PEM -f jwtRS256.key
# Don't add passphrase
openssl rsa -in jwtRS256.key -pubout -outform PEM -out jwtRS256.key.pub
```
## Labs installation
It is possible to run several Labs in the same machine and all of them must be included in the **_in4labs_app/labs_** folder. A sample laboratory named _example_lab_ is provided for testing purposes, so its associated folder <ins>should be removed</ins> in production. Clone the Labs you want to install and follow the instructions provided in their respective README files (Arduino board connections, extra configuration).  
For example, to use the _Internet of Things Lab_ and the _Cybersecurity Lab_ in the same physical mounting, run the following commands:
``` bash
cd $HOME/in4labs/in4labs_app/labs
rm -rf example_lab
git clone https://github.com/cRejon/in4labs_IoT.git
git clone https://github.com/cRejon/in4labs_cybersecurity.git
```
Then, edit the **_in4labs_app/config.py_** file and fill it with the correspondig configuration. The `duration` is common for Labs in the same mountig and the URL to the webcam's HLS stream (over HTTPS) must be provided by the user. This tool uses the port 8000 to serve the main app, so use the range 8001-8010 to set a unique `host_port` for each montage. The `lab_name` must be equal to the name given to the Lab repository and the `mounting_id` must match the one defined in the `mountings` section.  
``` python
labs_config = {
    'server_name': 'rasp1',
    'mountings': [{
        'id': '1', 
        'duration': 10, # minutes
        'cam_url': 'https://ULR_TO_WEBCAM/stream.m3u8',
        'host_port' : 8001,
    },],
    'labs': [{
        'lab_name' : 'in4labs_IoT',
        'html_name' : 'Laboratory of Internet of Things',
        'description' : 'This lab performs IoT experiments on Arduino devices',
        'mounting_id': '1',
    },{
        'lab_name' : 'in4labs_cybersecurity',
        'html_name' : 'Laboratory of Cybersecurity',
        'description' : 'This lab performs cybersecurity experiments on Arduino devices.',
        'mounting_id' : '1',
    }],
}
```
### Create Docker images
Docker images for Labs must be built before the first time the tool is run. The production server (Gunicorn) does not manage this process correctly, so this functionality is included in the **_create_images.py_** script. <u>Inside the virtual environment</u>, run:
``` bash
(venv) python $HOME/in4labs/create_images.py
```
This process can take a long time, so be patient.
## Running Gunicorn server on boot
1. Create a systemd service file:
``` bash
sudo nano /etc/systemd/system/gunicorn.service
```
2. Add the following content to the file (replace `<your_username>` with your actual OS username):
```
[Unit]
Description=In4Labs App
After=network.target

[Service]
User=<your_username>
WorkingDirectory=/home/<your_username>/in4labs
ExecStart=/home/<your_username>/in4labs/venv/bin/gunicorn \
  --workers 2 \
  --timeout 1800 \
  --bind 0.0.0.0:8000 \
  -m 007 in4labs_app:app
Restart=always

[Install]
WantedBy=multi-user.target
```
3. Reload systemd daemon:
``` bash
sudo systemctl daemon-reload
```
4. Start and enable the service:
``` bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```
5. Check the status of the service:
``` bash
sudo systemctl status gunicorn
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
   - Platform ID: MOODLE_HOST
   - Client ID: CLIENT_ID
   - Deployment ID: DEPLOYMENT_ID
   - Public keyset URL: MOODLE_HOST/mod/lti/certs.php
   - Access token URL: MOODLE_HOST/mod/lti/token.php
   - Authentication request URL: MOODLE_HOST/mod/lti/auth.php
5. To add the tool to a course follow the instruction in this [link](https://docs.moodle.org/402/en/External_tool).

## Tool
Edit again the **_config.py_** file inside _in4labs_app_ directory and change the variables of the **_Config_** object to those required.
### Flask settings
Change the development variables to those needed in production, including the use of HTTPS. 
### LTI settings
Fill the string variables *MOODLE_HOST*, *CLIENT_ID*, and *DEPLOYMENT_ID* with the above information obtained in Moodle.
# License
This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg
