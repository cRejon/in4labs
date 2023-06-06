DIEEC In4Labs base LTI tool
=====
Implementation of a [LTI 1.3 tool](https://www.imsglobal.org/activity/learning-tools-interoperability) with Python for Raspberry Pi.  
It brings together the common functionalities for all Labs: _login, time slot reservation_ and _access control_. The specific functionalities of each Lab must be implemented inside a Docker container that will be run by this tool.  
It`s intended to function with an internal Moodle that works as a _LTI consumer_ for the tool. This Moodle also works as a [_LTI provider_](https://docs.moodle.org/402/en/Publish_as_LTI_tool) for others Learning Management Systems (LMS), centralizing access to all LTI tools (Labs) developed and allowing dynamic registration.  
Tested on Raspberry Pi OS Bullseye (64-bit).

# Setup
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
$ docker image ls
```
To list all container (running and stopped)
```
$ docker container ls -a
```
To stop a container 
```
$ docker container stop [CONTAINER_NAME]
```
## Flask app
Requires Python >=3.9
### Installation
From the project directory execute
```
$ pip install -r requirements.txt
```
### Configuration
Edit **_config.py_** file and change the secret key and

### Running
1. Run application
```
$ gunicorn -w 1 -b 0.0.0.0 in4labs_app:app
```
2. On Moodle,

