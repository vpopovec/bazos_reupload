import json
import aiohttp
import asyncio

import requests

from helpers import *
from dotenv import load_dotenv
from upload_ad import upload_ad

load_dotenv()
email = os.environ['EMAIL']
phone = os.environ['CISLO'].replace(' ', '')
ad_password = os.environ['INZERAT_HESLO']

ADS_DIR = 'inzeraty'
create_directory(ADS_DIR)


def main():
    validate_user_input(email, phone)
    session = load_session()
    # THE PROBLEM DOESN'T LIE WITH SESSION COOKIES... MAYBE HASH ID ?

    resp = get_my_ads(session)
    if not already_logged_in(resp):
        send_authentication(session)
        phone_key = input_phone_key()
        print(f'phone key: {phone_key}')

        resp = send_phone_key(session, phone_key)
        save_session(session)

    ad_links = get_ad_links(resp)
    print(f"AD LINKS {ad_links}")

    ads_to_upload = []
    for ad_link in ad_links:
        downloaded = download_ad(session, ad_link)
        if not downloaded:
            print(f"Couldn't download ad number {get_id_from_link(ad_link)}")
            continue
        success = delete_ad(session, ad_link)

        if success:
            ads_to_upload.append(get_id_from_link(ad_link))
        if not success:
            print(f"Couldn't remove ad number {get_id_from_link(ad_link)}")

    save_session(session)
    for ad_id in ads_to_upload:
        resp, ad_title = upload_ad(session, ad_id)
        success = 'SUCCESSFUL' if 'Inzerát bol vložený' in resp else 'FAILED'
        if success == 'FAILED':
            print(resp)
        print(f"UPLOADING OF {ad_title} {success}")


def download_ad(session, url):
    authority = re.findall(r"https://([^/]*)/", url)[0]

    ad_id = get_id_from_link(url)
    txt = session.get(f"https://{authority}/inzerat/{ad_id}/.php", headers=get_headers(authority)).text

    location_raw = txt.split('Lokalita:<')[-1].split('<tr>')[0]

    img_links_preview = re.findall(r'src="https://www.bazos.sk/img/([^"]*)"', txt.split('<div class="podobne">')[0])
    img_links_preview = [f"https://www.bazos.sk/img/{i}" for i in img_links_preview if 't/' in i]

    info = {'ad_header': txt.split('class=nadpisdetail>')[1].split('</')[0],
            'ad_description': txt.split('class=popisdetail>')[1].split('</')[0],
            'advertiser': txt.split('Meno:')[1].split('</a>')[0].split('>')[-1],
            'authority': authority,
            'category': txt.split('Hlavná stránka')[1].split('</a>')[2].split('>')[-1],
            'zip_code': re.findall(r">(\d{3}.?\d{2})<", location_raw)[0],
            'city': location_raw.split('</a>')[-2].split('>')[-1],
            'price': txt.split('Cena:')[-1].split('</b>')[0].split('<b>')[-1].strip(),
            'img_links': [i.replace('t/', '/') for i in img_links_preview]}

    ad_path = f"{ADS_DIR}{os.path.sep}{ad_id}"
    create_directory(ad_path)

    with open(f'{ad_path}{os.path.sep}info.json', 'w', encoding='utf8') as wf:
        json.dump(info, wf)

    images = asyncio.run(download_images(info['img_links']))
    images = [i for i in images if i]
    if not images:
        return

    for url, img_content in images:
        file_name = url.split('img/')[1].split('/')[0] + ".jpg"
        with open(f"{ad_path}{os.path.sep}{file_name}", mode='wb') as wf:
            wf.write(img_content)
    return True


def delete_ad(session, url):
    authority = re.findall(r"https://([^/]*)/", url)[0]
    ad_id = get_id_from_link(url)

    session.get(f'https://{authority}/zmazat/{ad_id}.php', headers=get_headers(authority))

    data = {
        'heslobazar': ad_password,
        'idad': ad_id,
        'administrace': 'Zmazať',
    }

    resp = session.post(f'https://{authority}/deletei2.php', headers=get_headers(authority, url), data=data).text
    if 'Inzerát bol vymazaný z nášho bazáru.' in resp:
        return True


async def download_images(urls):
    for i in range(5):
        try:
            async with aiohttp.ClientSession() as session:
                coros = (fetch_image(session, url) for url in urls)
                res = await asyncio.gather(*coros)
        except:
            if i == 4:
                print("Couldn't download images")

    if not all(res):
        print(f"Not all images could be downloaded, check your internet connection and try again")
        return []
    return res


async def fetch_image(session, url):
    async with session.get(url, timeout=10) as response:
        if response.status == 200:
            img_content = await response.content.read()
            return [url, img_content]


def get_my_ads(session):
    txt = session.get('https://www.bazos.sk/moje-inzeraty.php', headers=get_headers()).text
    return txt


def send_authentication(session):
    data = {
        'mail': email,
        'telefon': phone,
        'Submit': 'Overiť',
    }

    response = session.post('https://www.bazos.sk/moje-inzeraty.php', headers=get_headers(), data=data)
    txt = response.text
    if is_error(txt):
        print(f"ERROR: {txt}")
        err = get_error_msg(txt)
        raise TimeoutError(f"ERROR: {err}")


def send_phone_key(session, key):
    data = {
        'klic': key,
        'klictelefon': get_international_number(phone),
        'Submit': 'Odoslať',
    }

    response = session.post('https://www.bazos.sk/moje-inzeraty.php', headers=get_headers(), data=data)
    txt = response.text
    if is_error(txt):
        err = get_error_msg(txt)
        raise TimeoutError(f"ERROR: {err}")
    return txt


if __name__ == '__main__':
    main()
