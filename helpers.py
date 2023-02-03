import pickle
import re
import traceback
import requests
import os


def create_directory(directory):
    if not os.path.exists(f"{directory}"):
        os.mkdir(f"{directory}")


def get_id_from_link(url):
    return re.findall(r'\d+', url)[0]


def is_error(txt):
    return 1 if '<span class="ztop">' in txt and '<span class="ztop">*<' not in txt else 0


def get_error_msg(txt):
    return txt.split('<span class="ztop">')[1].split('</span>')[0]


def get_international_number(phone_num):
    phone_codes = {"SK": 421}
    country = "SK"
    return f"+{phone_codes[country]}{phone_num[1:]}"


def phone_key_correct(k):
    return 1 if len(k) == 7 and all([i.isdigit() for i in k]) else 0


def input_phone_key():
    while True:
        try:
            phone_key = input("Please enter Key from SMS: ")
            if phone_key_correct(phone_key):
                return phone_key
            print("Wrong phone key format, try again")
        except:
            traceback.print_exc()


def validate_user_input(email, phone):
    if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
        raise ValueError("Invalid email address format")

    if not re.fullmatch(r"\d{10}", phone):
        raise ValueError("Invalid phone number format, use 09XX XXX XXX")


def load_session():
    session = requests.Session()
    try:
        with open('session_cookies.txt', 'rb') as f:
            session.cookies.update(pickle.load(f))
    except FileNotFoundError:
        pass
    return session


def save_session(session):
    with open('session_cookies.txt', 'wb') as f:
        pickle.dump(session.cookies, f)


def already_logged_in(txt):
    if 'Nikto zatiaľ užívateľa nehodnotil.' in txt:
        return 1


def get_ad_links(resp):
    adverts_num = 0
    if 'Všetky inzeráty užívateľa' in resp:
        adverts_num = int(resp.split('Všetky inzeráty užívateľa (')[1].split(')')[0])
    print(f"Number of adverts {adverts_num}")

    ads = re.findall(r"https://[a-z]+.bazos.sk/zmazat/\d+.php", resp)
    ads = list(set(ads))
    return ads
