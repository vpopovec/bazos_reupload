import re
import requests


def get_all_main_cats():
    headers = {
        'authority': 'www.bazos.sk',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'en-US,en;q=0.9',
        'referer': 'https://motocykle.bazos.sk/',
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

    resp = requests.get('https://www.bazos.sk/', headers=headers).text
    main_cats = re.findall(r'<a href="https://([a-z]+).bazos.sk/"', resp)
    main_cats = [c for c in main_cats if c != 'www']
    return list(set(main_cats))


def scrape_main_cats(main_categories):
    sub_categories = {}
    for category in main_categories:
        sub_categories[category] = {}
        authority = f"{category}.bazos.sk"
        headers = {
            'authority': authority,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'en-US,en;q=0.9',
            'if-modified-since': 'Thu, 02 Feb 2023 14:13:45 GMT',
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

        resp = requests.get(f'https://{authority}/', headers=headers).text
        sub_cat_names = re.findall(r'<a href="/([a-z]+)/">', resp)

        for sub_c in sub_cat_names:
            sub_c_link = f'https://{authority}/{sub_c}/'
            sub_id, sub_title = scrape_sub_cat(sub_c_link, headers)
            sub_categories[category][sub_title] = sub_id

    return sub_categories


def scrape_sub_cat(url, headers):
    resp = requests.get(url, headers=headers).text
    try:
        id_ = re.findall(r"catnas=(\d+)", resp)[0]
    except:
        id_ = ''
    try:
        title = re.findall(r'<h1 class="nadpiskategorie">([^<]+)</h1>', resp)[0]
    except:
        title = ''
    return id_, title


if __name__ == '__main__':
    main_cats = get_all_main_cats()
    sub_cats = scrape_main_cats(main_cats)
    print(f"SUB CATEGORIES: {sub_cats}")
