import json
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta, datetime
import logging

log_level = logging.INFO
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(name)s -  - %(message)s", level=log_level)

day_before_yesterday = date.today() - timedelta(days=2)
yesterday = date.today() - timedelta(days=1)
today = date.today()
now = datetime.now()

def valid_charge_date(history_obj):
    """Compares a date to today to see if it's in the past."""
    date_string = history_obj['chargeDateRaw']
    d = None
    try:
        d = datetime.strptime(date_string, "%d-%b-%Y")
    except ValueError:
        d = datetime.strptime(date_string, "%m-%d-%Y")
    valid_date = d.date() <= today

    if d.date() == today and history_obj['readDateTime']:
        time_split = history_obj['readDateTime'].split(" ")
        d_hour = int(time_split[0]) if time_split[1] == "AM" else (int(time_split[0]) + 12)
        d = d + timedelta(hours=d_hour+1) # don't want to include current hour
        return d <= now
    
    return valid_date

def strip_future_data(dataset):
    return list(filter(valid_charge_date, dataset))


class KCWater():
    def __init__(self, username, password):
        self.loggedIn = False
        self.session = None
        self.headers = {}
        self.username = username
        self.password = password
        self.account_number = None
        self.customer_id = None
        self.service_id = None
        self.access_token = None
        self.account_port = 1
        self.tokenUrl = "https://my.kcwater.us/rest/oauth/token"
        self.customer_info_url = "https://my.kcwater.us/rest/account/customer/"
        self.hourly_usage_url = "https://my.kcwater.us/rest/usage/month/day"
        self.daily_usage_url = "https://my.kcwater.us/rest/usage/month"

    def get_token(self):
        logging.info("Logging in with username: " + self.username)
        login_payload = {"username": str(self.username), "password": str(self.password), "grant_type": "password"}
        r = self.session.post(url=self.tokenUrl, data=login_payload, headers={"Authorization": "Basic d2ViQ2xpZW50SWRQYXNzd29yZDpzZWNyZXQ="})
        logging.debug("Login response: " + str(r.status_code))
        login_data = r.json()
        self.access_token = login_data['access_token']
        self.customer_id = login_data['user']['customerId']
        self.headers['Authorization'] = "Bearer {}".format(self.access_token)
        self.headers['Content-Type'] = 'application/json'

    def get_customer_info(self):
        info_payload = { "customerId": str(self.customer_id) }
        r = self.session.post(url=self.customer_info_url, data=json.dumps(info_payload), headers=self.headers)
        logging.debug("Customer Info response: " + str(r.status_code))
        customer_info = r.json()
        self.service_id = customer_info['accountSummaryType']['services'][0]['serviceId']
        self.account_number = customer_info['accountContext']['accountNumber']


    def login(self):
        self.session = requests.session()
        self.get_token()
        self.get_customer_info()
        self.loggedIn = self.account_number is not None and self.service_id is not None and self.customer_id is not None and self.access_token is not None


    def get_usage_hourly(self, date=today):
        """Fetches all usage data for a given date by hour."""
        if not self.loggedIn:
            logging.error("Must login first")
            return
        formatted_date = date.strftime("%d-%b-%Y")
        req_payload = {
            "customerId": str(self.customer_id),
            "accountContext": {
                "accountNumber": str(self.account_number),
                "serviceId": str(self.service_id)
            },
            "month": formatted_date,
            "day": formatted_date,
            "port": str(self.account_port)
        }
        usageData = self.session.post(self.hourly_usage_url, data=json.dumps(req_payload), headers=self.headers).json()
        if log_level == logging.DEBUG:
            with open("hourly_output.json", "w") as outfile:
                json.dump(usageData, outfile, indent=4)
                logging.debug("Wrote data to output.json")
            with open("hourly_secondary.json", "w") as outfile:
                json.dump(json.loads(usageData['jsonData']), outfile, indent=4)
                logging.debug("Wrote data to secondary.json")
        return strip_future_data(usageData['history'])

    def get_usage_daily(self, date=today):
        """Fetches all usage data from the given month by day."""
        if not self.loggedIn:
            logging.error("Must login first")
            return
        
        formatted_date = date.strftime("%d-%b-%Y")
        req_payload = {
            "customerId": str(self.customer_id),
            "accountContext": {
                "accountNumber": str(self.account_number),
                "serviceId": str(self.service_id)
            },
            "month": formatted_date
        }
        usageData = self.session.post(self.daily_usage_url, data=json.dumps(req_payload), headers=self.headers).json()
        if log_level == logging.DEBUG:
            with open("daily_output.json", "w") as outfile:
                json.dump(usageData, outfile, indent=4)
                logging.debug("Wrote data to output.json")
            with open("daily_secondary.json", "w") as outfile:
                json.dump(json.loads(usageData['jsonData']), outfile, indent=4)
                logging.debug("Wrote data to secondary.json")
        return strip_future_data(usageData['history'])

def getCreds():
    with open("../credentials.json", 'r') as f:
        return json.loads(f.read())

if __name__ == "__main__":
    # Read the credentials.json file
    creds = getCreds()
    username = creds["username"]
    password = creds["password"]

    kc_water = KCWater(username, password)
    kc_water.login()
    logging.debug("Account Number = {}, service ID = {}, customer ID = {}".format(kc_water.account_number, kc_water.service_id, kc_water.customer_id))

    # Get a list of hourly readings
    hourly_data = kc_water.get_usage_hourly()

    # Get a list of hourly readings
    daily_data = kc_water.get_usage_daily()

    logging.info("Last daily data: {}\n\n".format(daily_data[-1]))
    logging.info("Last hourly data: {}\n\n".format(hourly_data[-1]))
    logging.info("Last daily reading: {} gal for {}".format(daily_data[-1]["gallonsConsumption"], daily_data[-1]["readDate"]))
    logging.info("Last hourly reading: {} gal for {} {}".format(hourly_data[-1]["gallonsConsumption"], hourly_data[-1]["readDate"], hourly_data[-1]["readDateTime"]))

