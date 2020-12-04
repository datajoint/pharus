FROM python:3.9.0-slim-buster

RUN pip3 install flask datajoint pyjwt pyjwt[crypto]

WORKDIR /src