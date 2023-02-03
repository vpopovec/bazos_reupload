import requests
import os
import json
import re
import urllib3
import glob
from dotenv import load_dotenv

ADS_DIR = 'inzeraty'
load_dotenv()
email = os.environ['EMAIL']
phone = os.environ['CISLO'].replace(' ', '')
ad_password = os.environ['INZERAT_HESLO']
with open('categories.json', encoding='utf8') as rf:
    CATEGORIES = json.load(rf)


def upload_pic(pic_path, info):
    headers = {
        'authority': info['authority'],
        'accept': 'application/json',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'origin': f'https://{info["authority"]}',
        'referer': f'https://{info["authority"]}/pridat-inzerat.php',
        'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    file_name = pic_path.split(os.path.sep)[-1]

    fields = {
        "file[0]": (file_name, open(f'{pic_path}', 'rb').read(), 'image/jpeg'),
    }

    boundary = '----WebKitFormBoundary1GVHUvw40yqeLBTz'
    body, header = urllib3.encode_multipart_formdata(fields, boundary=boundary)
    headers['content-type'] = header

    r = requests.post('https://elektro.bazos.sk/upload.php', data=body, headers=headers)

    ids = r.json()
    return ids[0]


def upload_photos(ad_path, info):
    pic_paths = glob.glob(f"{ad_path}{os.path.sep}*")
    pic_paths = [p for p in pic_paths if re.fullmatch(rf'{ad_path}{os.path.sep}\d+\.\w+', p)]
    ids = []
    print(f"total pictures: {len(pic_paths)}")
    for pic_p in pic_paths:
        ids.append(upload_pic(pic_p, info))
    return ids


def upload_ad(session, ad_id):
    try:
        ad_path = f"{ADS_DIR}{os.path.sep}{ad_id}"
        with open(f'{ad_path}{os.path.sep}info.json', encoding='utf8') as rf:
            info = json.load(rf)
    except FileNotFoundError:
        print(f"Ad number {ad_id} not found")
        return

    boundary = '----WebKitFormBoundarycyOShvTm9V30Zg0B'
    headers = {
        'authority': info['authority'],
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'content-type': f'multipart/form-data; boundary={boundary}',
        'origin': f'https://{info["authority"]}',
        'referer': f'https://{info["authority"]}/pridat-inzerat.php',
        'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    }

    try:
        price = re.findall(r'\d+', info["price"])[0]
    except:
        print("PRICE MUST BE AN INTEGER")
        return

    info['zip_code'] = info['zip_code'].replace(' ', '')

    main_cat = info['authority'].split('.')[0]
    sub_cat = info['category']
    if main_cat not in CATEGORIES or sub_cat not in CATEGORIES[main_cat]:
        print(f"CAN'T UPLOAD {main_cat} {sub_cat} MISSING CATEGORY ID")
        return '', info['ad_header']
    category_id = CATEGORIES[main_cat][sub_cat]

    fields = [
        ('category', category_id),  # Convert info['category'] to a number
        ('nadpis', info['ad_header']),
        ('popis', info['ad_description']),
        ('cena', price),
        ('cenavyber', '1'),  # Fixed amount
        ('lokalita', info['zip_code']),
        ('jmeno', info['advertiser']),
        ('telefoni', phone),
        ('maili', email),
        ('heslobazar', ad_password),
        ('werfhgfda', 'regsgtr'),
        ('Submit', 'Odoslať')
    ]
    photo_ids = upload_photos(ad_path, info)

    for photo_id in photo_ids[::-1]:
        fields.insert(-6, ('files[]', photo_id))

    data, header = urllib3.encode_multipart_formdata(fields, boundary=boundary)
    headers['content-type'] = header

    response = session.post(f'https://{info["authority"]}/insert.php', headers=headers, data=data)

    return response.text, info['ad_header']
