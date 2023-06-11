DIEEC In4Labs base LTI tool
=====
# Description
Implementation of a [LTI 1.3 tool](https://www.imsglobal.org/activity/learning-tools-interoperability) with Python Flask for Raspberry Pi.  
It brings together the common functionalities for all Labs: _login, time slot reservation_ and _access control_. The specific functionalities of each Lab must be implemented inside a Docker container that will be run by this tool.  
It's intended to function with a Moodle, instaled in a local server, that works as a _LTI consumer_ for the tool. This Moodle also works as a [_LTI provider_](https://docs.moodle.org/402/en/Publish_as_LTI_tool) for others Learning Management Systems (LMS), centralizing access to all LTI tools (Labs) developed and allowing dynamic registration.  
Tested on Raspberry Pi OS Bullseye (64-bit).  
Requires Python >=3.9.

# Setup Raspberry Pi
## Docker
### Installation
Assuming the user is **pi** (default)
```
$ sudo apt update
$ curl -fsSL https://get.docker.com -o get-docker.sh
$ sudo sh get-docker.sh
$ sudo usermod -aG docker pi
$ rm get-docker.sh
```
### Some useful commands
To list all images
```
docker image ls
```
To list all container (running and stopped)
```
docker container ls -a
```
To stop a container 
```
docker container stop [CONTAINER]
```
## Flask app + Gunicorn server
### Installation
For convenience, copy the project inside _/home/pi_ folder and from there, execute
```
$ cd in4labs
$ python -m venv venv
$ . venv/bin/activate
(venv) $ pip install -r requirements.txt
(venv) $ deactivate
```
### Running on boot
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
WorkingDirectory=/home/pi/in4lab
ExecStart=/home/pi/in4lab/venv/bin/gunicorn --workers 2 --bind 0.0.0.0:8000 -m 007 in4labs_app:app
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

# Lab configuration
The two main parameters to configure the tool are the IP for Moodle (**MOODLE_HOST**) and the IP for the tool (**TOOL_HOST**).
## Moodle 
To install Moodle in Ubuntu follow instructions in the [installation guide](https://docs.moodle.org/402/en/Step-by-step_Installation_Guide_for_Ubuntu).  
To add a new LTI tool, log in as an admin and follow the next steps:
1. Navigate to **_Site Administration -> Plugins -> Activity Modules -> External Tool -> Manage Tools_**
2. Click **_Configure a tool manually_** 
3. Enter the following information in the **_External tool configuration_** form: 
   #### Tool settings
   - Tool name: LAB_NAME
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

## Raspberry Pi
Edit **_config.py_** file inside _in4lab_app_ directory and change the variables of the **Config** object to those required by the Lab. LTI settings must be filled in with the information obtained in Moodle.
```
# LTI settings
lti_config = {
    "http://MOODLE_HOST/moodle": [{
        "default": True,
        "client_id": "CLIENT_ID",
        "auth_login_url": "http://MOODLE_HOST/moodle/mod/lti/auth.php",
        "auth_token_url": "http:/MOODLE_HOST/moodle/mod/lti/token.php",
        "auth_audience": None,
        "key_set_url": "http://MOODLE_HOST/moodle/mod/lti/certs.php",
        "key_set": None,
        "private_key_file": None,
        "public_key_file": None,
        "deployment_ids": ["DEPLOYMENT_ID"]
    }]
}
```


