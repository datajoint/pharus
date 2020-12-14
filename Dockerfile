FROM python:3.9.0-slim-buster
RUN apt update && apt install git -y
RUN pip3 install flask git+https://github.com/datajoint/datajoint-python.git pyjwt pyjwt[crypto]

WORKDIR /src