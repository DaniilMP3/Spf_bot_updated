from os import getenv
from dotenv import load_dotenv

load_dotenv()

JITSI_MAX_ROOMS = 5
JITSI_MEETING_TIME = 900

JITSI_SECRET = getenv("JITSI_SECRET")
JITSI_APP_ID = getenv("JITSI_APP_ID")
JITSI_DOMAIN = getenv("JITSI_DOMAIN")

MAX_IN_QUEUE_TIME = 1800 #If user in queue > this time --> this user will be chosen as candidate for next user
QUEUE_TIMEOUT = 3600 #If user in queue >= this time --> this user will be deleted from queue
MIN_TIME_BEFORE_MEETING = 180 #If time users match >= this constant - move to one point right in time table
