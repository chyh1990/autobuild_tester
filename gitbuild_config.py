import os, sys

PORT_NUMBER = 8080
CLIENT_IPS = set(['207.97.227.253', '50.57.128.197', '108.171.174.178', '127.0.0.1']) 
REPO_NAME = 'autobuild_tester'
LOCAL_REPO = 'autobuild_tester'
REPORT_DIR =  os.path.join(os.getcwd(), "report")
LOG_FILENAME = os.path.join(REPORT_DIR, "list.txt")
LOG_FILE = open(LOG_FILENAME, "a+")


