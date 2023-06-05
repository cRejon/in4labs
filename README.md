
DIEEC In4Labs base LTI tool
=====

Tested on Raspberry Pi OS Bullseye (64-bit).

# Setup

## Docker
### Installation
Assuming the user is **_pi_** (default)
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
$ docker container stop [CONTAINER]
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

