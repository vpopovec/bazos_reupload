import json
import aiohttp
import asyncio
from helpers import *
from dotenv import load_dotenv
from upload_ad import upload_ad

load_dotenv()
email = os.environ['EMAIL']
phone = os.environ['CISLO'].replace(' ', '')
ad_password = os.environ['INZERAT_HESLO']

ADS_DIR = 'inzeraty'
create_directory(ADS_DIR)

HEADERS = {
        'authority': 'www.bazos.sk',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'origin': 'https://www.bazos.sk',
        'referer': 'https://www.bazos.sk/moje-inzeraty.php',
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


def main():
    validate_user_input(email, phone)
    session = load_session()

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
        download_ad(session, ad_link)
        success = delete_ad(session, ad_link)

        if success:
            ads_to_upload.append(get_id_from_link(ad_link))
        if not success:
            print(f"Couldn't remove ad number {get_id_from_link(ad_link)}")

    save_session(session)
    for ad_id in ads_to_upload:
        resp, ad_title = upload_ad(session, ad_id)
        success = 'SUCCESSFUL' if 'Inzerát bol vložený' in resp else 'FAILED'
        print(f"UPLOADING OF {ad_title} {success}")


def download_ad(session, url):
    authority = re.findall(r"https://([^/]*)/", url)[0]
    headers = {
        'authority': authority,
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'if-modified-since': 'Tue, 31 Jan 2023 06:38:54 GMT',
        'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    }

    ad_id = re.findall(r"\d+", url)[0]
    txt = session.get(f"https://{authority}/inzerat/{ad_id}/.php", headers=headers).text

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

    for url, img_content in images:
        file_name = url.split('img/')[1].split('/')[0] + ".jpg"
        with open(f"{ad_path}{os.path.sep}{file_name}", mode='wb') as wf:
            wf.write(img_content)


def delete_ad(session, url):
    authority = re.findall(r"https://([^/]*)/", url)[0]
    ad_id = re.findall(r"\d+", url)[0]
    headers = {
        'authority': authority,
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'en-US,en;q=0.9',
        'if-modified-since': 'Sun, 22 Jan 2023 23:19:32 GMT',
        'referer': 'https://www.bazos.sk/',
        'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-site',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    }

    response = session.get('https://elektro.bazos.sk/zmazat/146856117.php', headers=headers)

    headers = {
        'authority': authority,
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'origin': f'https://{authority}',
        'referer': url,
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

    data = {
        'heslobazar': ad_password,
        'idad': ad_id,
        'administrace': 'Zmazať',
    }

    resp = session.post('https://elektro.bazos.sk/deletei2.php', headers=headers, data=data).text
    if 'Inzerát bol vymazaný z nášho bazáru.' in resp:
        return True


async def download_images(urls):
    async with aiohttp.ClientSession() as session:
        coros = (fetch_image(session, url) for url in urls)
        res = await asyncio.gather(*coros)
    return res


async def fetch_image(session, url):
    async with session.get(url, timeout=10) as response:
        if response.status == 200:
            img_content = await response.read()
            return [url, img_content]


def get_my_ads(session):
    headers = {
        'authority': 'www.bazos.sk',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'en-US,en;q=0.9',
        'referer': 'https://www.bazos.sk/',
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

    txt = session.get('https://www.bazos.sk/moje-inzeraty.php', headers=headers).text
    return txt


def send_authentication(session):
    data = {
        'mail': email,
        'telefon': phone,
        'Submit': 'Overiť',
    }

    response = session.post('https://www.bazos.sk/moje-inzeraty.php', headers=HEADERS, data=data)
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

    response = session.post('https://www.bazos.sk/moje-inzeraty.php', headers=HEADERS, data=data)
    txt = response.text
    if is_error(txt):
        err = get_error_msg(txt)
        raise TimeoutError(f"ERROR: {err}")
    return txt


if __name__ == '__main__':
    main()
