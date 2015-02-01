#!/bin/bash
add-apt-repository ppa:builds/sphinxsearch-daily
apt-get update
apt-get install python-pip python3-pip python3-bs4 sphinxsearch
pip3 install cherrypy PyMySQL mako PyYAML
