import requests
import json
import os
import smtplib
from bs4 import BeautifulSoup

CACHE_FILE = '.cache'
GMAIL_EMAIL = os.environ['GMAIL_EMAIL']
GMAIL_APP_PASSWORD = os.environ['GMAIL_APP_PASSWORD']
RECIPIENTS_LIST = os.environ['RECIPIENTS_LIST'].splitlines()


def get_clearance_listings():
    url = 'https://westkoastbotanicals.com/product-category/clearance/'
    response = requests.get(url)

    bs = BeautifulSoup(response.content, 'html.parser')

    all_products = bs.find('ul', class_='products')
    listings = all_products.findAll('li', class_='product')

    clearance_listings = []

    for listing in listings:
        name = listing.find(class_='woocommerce-loop-product__title').string

        price_parent = listing.findAll(
            class_='woocommerce-Price-amount amount')[1]
        price_parent = price_parent.find('bdi').contents
        price = price_parent[1]

        oos = 'outofstock' in listing['class']

        # Do not include if out of stock.
        if oos:
            continue

        clearance_listing = {
            'name': name,
            'price': price,
        }

        clearance_listings.append(clearance_listing)

    return clearance_listings


def get_cached_clearance_listings() -> dict:
    if not os.path.exists(CACHE_FILE):
        return {}

    with open(CACHE_FILE, 'r') as f:
        contents = f.read()

    clearance_listings = json.loads(contents)

    return clearance_listings


def pretty_listings(listings: dict) -> str:
    result = ''

    for listing in listings:
        result += f'''\
{listing['name']}: ${listing['price']}
'''

    return result


def send_email(listings: dict):
    print('Emailing listings...')
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)

        sent_from = GMAIL_EMAIL
        to = RECIPIENTS_LIST
        pretty_listings_text = pretty_listings(listings)
        email_text = f'Subject: West Koast Clearance Listings\n\n{
            pretty_listings_text}'

        server.sendmail(sent_from, to, email_text)
        server.close()
    except Exception as e:
        print('Something went wrong with sending email...')
        print(e)


def update_cache(clearance_listings: dict):
    with open(CACHE_FILE, 'w') as f:
        contents = json.dumps(clearance_listings)
        f.write(contents)


if __name__ == '__main__':
    cached_clerance_listings = get_cached_clearance_listings()
    clearance_listings = get_clearance_listings()

    if cached_clerance_listings != clearance_listings and clearance_listings != []:
        print('New listings found:')
        print(pretty_listings(clearance_listings))

        send_email(clearance_listings)

    update_cache(clearance_listings)
