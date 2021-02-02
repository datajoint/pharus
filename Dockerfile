FROM python:3.9.0-slim-buster
RUN apt update && apt install git -y
RUN pip3 install \
        flask datajoint==0.13.dev2 pyjwt pyjwt[crypto]

WORKDIR /src