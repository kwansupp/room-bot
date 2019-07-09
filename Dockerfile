FROM resin/raspberrypi3-python

COPY app /home

# update repo
RUN sudo apt-get update
RUN sudo apt-get upgrade

# install dependencies
RUN pip install requests
RUN pip install beautifulsoup4
RUN pip install pygsheets
RUN pip install slackclient



