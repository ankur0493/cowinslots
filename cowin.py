from datetime import date
import hashlib
import requests
import json
import time

BASE_URL = "https://cdn-api.co-vin.in/api/v2"

AUTH_BASE = BASE_URL + "/auth/public"
GENERATE_OTP = AUTH_BASE + "/generateOTP"
CONFIRM_OTP = AUTH_BASE + "/confirmOTP"

METADATA_BASE = BASE_URL + "/admin/location"
STATES_LIST = METADATA_BASE + "/states"
DISTRICT_LIST = METADATA_BASE + "/districts/{state_id}"

APPOINTMENT_BASE = BASE_URL + "/appointment/sessions"
SESSIONS_BY_PIN = APPOINTMENT_BASE + "/calendarByPin"
SESSIONS_BY_DISTRICT = APPOINTMENT_BASE + "/calendarByDistrict"
SESSIONS_BY_CENTER = APPOINTMENT_BASE + "calenderByCenter"


class Cowin:
    def __init__(self, mobile_number):
        self.mobile_number = mobile_number
        self.token = ""
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0",
        }


    def sendOtp(self):
        payload = {
            "mobile": self.mobile_number,
        }
        resp = requests.post(
            GENERATE_OTP, data=json.dumps(payload), headers=self.headers)
        print(resp.content)
        transaction_id = resp.json().get("txnId")
        return transaction_id


    def confirmOtp(self, transaction_id, otp):
        payload = {
            "otp": hashlib.sha256(otp.encode("utf-8")).hexdigest(),
            "txnId": transaction_id,
        }
        resp = requests.post(
            CONFIRM_OTP, data=json.dumps(payload), headers=self.headers)
        self.token = resp.json().get("token")
        print("Token: {}".format(self.token))
        self.headers["Authorization"] = "Bearer {}".format(self.token)


    def _filter_available_sessions_by_age(self, centers, age):
        if age not in [18, 45]:
            raise Exception("Invalid age")
        available_sessions = []
        for center in centers:
            if center.get("fee_type") != "Free":
                continue
            for session in center.pop("sessions"):
                if session.get("min_age_limit") == age and session.get("available_capacity"):
                    available_sessions.append([center, session])
        return available_sessions


    def get_available_sessions_by_district(self, district_id, age):
        query_params = {
            "district_id": district_id,
            "date": date.today().strftime("%d-%m-%Y"),
        }
        resp = requests.get(
            SESSIONS_BY_DISTRICT, params=query_params, headers=self.headers)
        centers = json.loads(resp.content).get("centers")
        return self._filter_available_sessions_by_age(centers, age)


if __name__ == "__main__":
    mobile_number = input("Please enter your mobile number: ")
    cowin = Cowin(mobile_number)
    transaction_id = cowin.sendOtp(mobile_number)
    if transaction_id:
        otp = input("Enter the OTP received on {}: ".format(mobile_number))
        cowin.confirmOtp(transaction_id, otp)
    districts = {
        "Panipat": [195, 18],
        "East Delhi": [145, 18],
        "South Delhi": [149, 18],
        "South East Delhi": [144, 18],
        "Ghaziabad": [651, 18],
        "Gautam Budha Nagar": [650, 18],
        "Agra": [622, 18],
        "Lucknow": [670, 18],
        "Nainital": [709, 18],
    }
    while True:
        for district_name, district_id_age in districts.items():
            available_sessions = cowin.get_available_sessions_by_district(
                district_id_age[0], district_id_age[1])
            if available_sessions:
                for center, session in available_sessions:
                    print("{} slots are available in "
                          "{} in center {} on {}".format(
                            session["available_capacity"], district_name,
                            center["name"], session["date"]))
                print("\n\n\n\n")
        print("Sleeping for 3 minutes...")
        time.sleep(180)