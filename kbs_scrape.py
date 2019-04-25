import requests
from bs4 import BeautifulSoup
import re
import pygsheets
import time

# function to get all info from listing page
def processListing(url):
    # variables to store listing info
    viewing = True  # variable for if listing is available for viewing

    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    # check if listing full (property-badge class on span with text Bezichtiging vol)
    try:
        badge = soup.find_all(class_="property-badge", string="Bezichtiging vol")
        if "Bezichtiging vol" in badge[0]:
            viewing = False
    except:
        pass

    # get information from property overview of listing
    overview = soup.find(class_="property-overview")
    variables_scrape = [var.get_text() for var in overview.findChildren("dt")]
    values_scrape = [val.get_text() for val in overview.findChildren("dd")]
    # clean up info
    variables = [var[:-1] for var in variables_scrape]
    values = [re.sub(' +', ' ', val.strip()) for val in values_scrape]
    info = dict(zip(variables, values))
    info['Viewing'] = viewing

    # get info from property description of listing
    description = soup.find(class_="property-description")
    descr_scrape = [descr.get_text() for descr in description.findChildren(class_="kin3")]
    # clean up
    descr = [re.sub(' +', ' ', val.strip()) for val in descr_scrape]
    # insert to dict
    try:
        info['Te huur vanaf'] = descr[0][15:]
    except IndexError:
        info['Te huur vanaf'] = 'null'

    try:
        info['Viewing date'] = descr[1][14:]
    except IndexError:
        info['Viewing date'] = 'null'

    # get title
    title_bs = soup.find(class_="property-title")
    title = title_bs.get_text()
    info['Title'] = title

    return info

# get all values already in storage
def getStorage(sheet):
    # get what is already in db to check
    try:
        db = sheet.get_all_values(include_tailing_empty=False, include_tailing_empty_rows=False)
        stored_urls = [item[0] for item in db]
    except IndexError:
        stored_urls = []

    return stored_urls

# add url to storage if not already there
def addToStorage(sheet, url):
    # get what is already in db to check
    stored_urls = getStorage(sheet)
    # if url not already stored, add
    if url not in stored_urls:
        sheet.insert_rows(row=0, values=[url])


# remove discarded postings from storage
def cleanUpStorage(sheet, scraped_urls):
    # get what is already in db to check
    stored_urls = getStorage(sheet)

    # remove discarded postings
    removal_keys = []
    for old_item in stored_urls:
        if old_item not in scraped_urls:
            # get index number and log for deletion
            key = stored_urls.index(old_item)
            removal_keys.append(key)
    # delete rows from bottom up
    removal_keys.reverse()
    for key in removal_keys:
        sheet.delete_rows(key + 1)


def main():
    # connect to spreadsheet
    SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1hAgcraXM1cO2zipzUASc9mYLTYDjwXboLvJiH-AFnNA/edit#gid=0"
    gc = pygsheets.authorize(service_file='credentials.json')
    sheet = gc.open_by_url(SPREADSHEET_URL).sheet1

    # scrape page
    page = requests.get("https://www.kbsvastgoedbeheer.nl/woningen/?filter-location=99&filter-property-type=&filter-status=&filter-price-from=&filter-price-to=&filter-beds=")
    soup = BeautifulSoup(page.content, 'html.parser')

    # get all links under anchors with property-row-image class
    urls = [a.get('href') for a in soup.find_all(class_="property-row-image")]
    # print('url amount:', len(urls))
    # use links to get more info, filter out unwanted listings, save wanted to db
    for url in urls:
        info = processListing(url)
        # print(info['Viewing'], info['Type'])
        # unwanted: type = Parkeerplaats or Garagebox; Viewing = False
        if info['Viewing'] or info['Type'] in ['Parkeerplaats', 'Garagebox']:
            # print('invalid')
            pass
        else:
            # print('url')
            # check if url already in db, if not add
            addToStorage(sheet, url)

    # send link to slack

    # clean up db storage
    cleanUpStorage(sheet, urls)


if __name__ == "__main__":
    main()