# syntax=docker/dockerfile:1
FROM python:3.10-slim-bullseye
# Set the working directory to /app
WORKDIR /app
# Requirements are installed here to ensure they will be cached.
COPY requirements.txt /app/requirements.txt
# Install any needed packages specified in requirements.txt
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt
# Copy the current directory contents into the container at /app
COPY . /app
# Make port 80 available outside this container
EXPOSE 80
# Run app when the container launches
CMD ["flask", "--app", "test_app", "run", "--host", "0.0.0.0", "--port", "80"]