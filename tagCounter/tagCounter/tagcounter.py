#!/usr/bin/env python3
import os
import datetime
import argparse
import yaml
import sqlite3
from html.parser import HTMLParser
from urllib.parse import urlparse
import urllib.request
from urllib import error
from sqlalchemy import Column, LargeBinary, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.serializer import loads, dumps
from sqlalchemy.orm import sessionmaker
import pickle
from tkinter import *
from tkinter.ttk import *

Base = declarative_base()
# output amount in console mode 0/1
verbosity = 0
close_tags = False

class Urls(Base):
    __tablename__ = 'al_urls'
    site_name = Column(String(50), nullable=False, )
    url = Column(String(250), nullable=False, primary_key=True)
    DT = Column(String(50), nullable=False, primary_key=True)
    tags = Column(LargeBinary)

    def __init__(self, site_name, url, DT, tags):
        self.site_name = site_name
        self.url = url
        self.DT = DT
        self.tags = tags

# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
    def __init__(self):
        self.tags_list = []
        super(MyHTMLParser, self).__init__()

    def handle_starttag(self, tag, attrs):
        if verbosity == 1: print('<',tag, '>')
        self.tags_list.append(tag)

    def handle_endtag(self, tag):
        if verbosity == 1: print('</',tag, '>')
        if close_tags: self.tags_list.append(tag)

def downloadUrl(url:str) -> str:
    # load YAML synonyms
    try:
        with open("synonyms.yaml", 'r') as ymlfile:
            snnm = yaml.load(ymlfile)
    except FileNotFoundError:
        snnm = {'synonyms': {'ggl': 'google.com', 'hbr': 'habr.com', '12f': '12factor.net/ru/config', 'ydx': 'yandex.ru'}}
        # print("can't open synonyms.yaml")
        # sys.exit(2)
    # download html for analizing
    try:
        # check url in synonyms YAML
        if url in snnm['synonyms'] :
            url = snnm['synonyms'][url]
        # check if schema is present. else use http by default
        if urlparse(url).scheme == '':
            response = urllib.request.urlopen(str('http://'+url))
        else:
            response = urllib.request.urlopen(url)
    except error.URLError as e:
        if hasattr(e,'code') :
            print (e.code)
        if hasattr(e,'reason') :
            print (e.reason)
        exit(1)
    except error.HTTPError as e:
        if hasattr(e,'code'):
            print(e.code)
        if hasattr(e,'reason'):
            print(e.reason)
        exit(1)
    # decode response to str
    if response.headers.get_content_charset() == '' or response.headers.get_content_charset() == None :
        return response.read().decode("utf-8")
    else:
        return response.read().decode(response.headers.get_content_charset())

def logg_site_processing(url:str, DT:datetime.datetime):
    # currentDT = datetime.datetime.now()
    with open('tagcounter.log', "a") as f:
        print(DT.strftime("%Y-%m-%d %H:%M:%S"), url, file=f)


def process_tag_calculating(rezults_tag:[]) -> {}:
    # calculate each tags amounts
    print('')
    if verbosity == 1: print(rezults_tag)
    if verbosity == 1: print('Tegs total: ', len(rezults_tag))
    rezults_tag_list = list(dict.fromkeys(rezults_tag))
    if verbosity == 1: print('uniq tags list: ', rezults_tag_list)
    rezults_tag_dict = {r_tag:rezults_tag.count(r_tag) for r_tag in rezults_tag_list}
    print('Tags occurrence    : ', rezults_tag_dict)
    print('Tegs total final: ', sum(rezults_tag_dict.values()))
    return rezults_tag_dict


def store_sql3_pickle(site_name:str, url:str, DT:datetime.datetime, rezult_dict:{}):
    # Pickle + sqlite3
    p_dict = pickle.dumps(rezult_dict, protocol=pickle.HIGHEST_PROTOCOL)

    conn = sqlite3.connect('tagcounter.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS urls
                (site text, url text, date text, tags blob)''')
    c.execute("INSERT INTO urls (site, url, date, tags) VALUES ( ?, ?, ?, ?)", \
        ( site_name , url, DT, p_dict))
    conn.commit()
    conn.close()

def read_sql3_pickle(url:str):
    # Pickle + sqlite3
    # p_dict = pickle.dumps(rezult_dict, protocol=pickle.HIGHEST_PROTOCOL)
    conn = sqlite3.connect('tagcounter.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS urls
                (site text, url text, date text, tags blob)''')
    c.execute(str("SELECT * FROM urls WHERE url = '" + url + "'"))
    records = c.fetchall()

    if len(records) == 0:
        print("No records in SQLite3 DB about URL: ", url)
    for row in records:
        print("Site from SQLite3 = ", row[0], )
        print("URL               = ", row[1])
        print("Parsing date      = ", row[2])
        pickle_rezults_tag_dict = pickle.loads(row[3])
        print("Tags occurrence   : ", pickle_rezults_tag_dict)
        print('Tegs total final  : ', sum(pickle_rezults_tag_dict.values()))
        print()
    conn.commit()
    conn.close()
    return pickle_rezults_tag_dict

def store_alchemy_pickle(site_name:str, url:str, DT:datetime.datetime, rezult_dict:{}):
    engine = create_engine('sqlite:///tagcounter.db')
    Base.metadata.create_all(engine)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    # Insert an record in the table
    new_urls = Urls( site_name, url, DT, dumps(rezult_dict))
    session.add(new_urls)
    session.commit()
    session.close()

def read_alchemy_pickle(url:str):
    engine = create_engine('sqlite:///tagcounter.db')
    Base.metadata.create_all(engine)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    session.query(Urls).all()
    ourSites = session.query(Urls).filter(Urls.url==url)

    if ourSites.count() == 0:
        print("No records in SQLAlchemy DB about URL: ", url)
    for row in ourSites:
        print("Site from SQLAlchemy = ", row.site_name )
        print("URL                  = ", row.url)
        print("Parsing date         = ", row.DT)
        pickle_rezults_tag_dict = loads(row.tags)
        print("Tags occurrence      : ", pickle_rezults_tag_dict)
        print('Tegs total final     : ', sum(pickle_rezults_tag_dict.values()))
        print()
    session.close()
    return pickle_rezults_tag_dict

def ProcessGET(url:str) -> {}:
    # GET
    # download url
    webContent = downloadUrl(url)
    # write operation into log file
    currentDT = datetime.datetime.now()
    logg_site_processing(url, currentDT)

    # instantiate the parser and fed it some HTML
    parser = MyHTMLParser()
    # parse HTML and collect tags info
    parser.feed(webContent)

    # calculate each tags amounts
    print('TAG counting for URL:\n' + url )

    rezult_dict = process_tag_calculating(parser.tags_list)

    # store rezults into sqlite3 with pickle
    if urlparse(url).scheme == '':
        store_sql3_pickle(urlparse(str('http://'+url)).hostname, url, currentDT.strftime("%Y-%m-%d %H:%M:%S"), rezult_dict)
    else:
        store_sql3_pickle(urlparse(url).hostname, url, currentDT.strftime("%Y-%m-%d %H:%M:%S"), rezult_dict)
    print('------------ SQLite3 stored --------------------------------------------------------------------------------')
    if urlparse(url).scheme == '':
        store_alchemy_pickle(urlparse(str('http://'+url)).hostname, url, currentDT.strftime("%Y-%m-%d %H:%M:%S"), rezult_dict)
    else:
        store_alchemy_pickle(urlparse(url).hostname, url, currentDT.strftime("%Y-%m-%d %H:%M:%S"), rezult_dict)
    print('------------ Alchemy stored --------------------------------------------------------------------------------')
    return rezult_dict

def ProcessVIEW(url:str) -> {}:
    # store rezults into sqlite3 with pickle
    rezult_dict = read_sql3_pickle(url)
    print('------------ SQLite3 --------------------------------------------------------------------------------')
    read_alchemy_pickle(url)
    print('------------ Alchemy --------------------------------------------------------------------------------')
    return rezult_dict

class tagCountGUI(Frame):
    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.initUI()

    def initUI(self):
        # preparing data
        try:
            with open("synonyms.yaml", 'r') as ymlfile:
                snnm = yaml.load(ymlfile)
        except FileNotFoundError:
            # print("can't open synonyms.yaml")
            # sys.exit(2)
            snnm = {'synonyms': {'ggl': 'google.com', 'hbr': 'habr.com', '12f': '12factor.net/ru/config', 'ydx': 'yandex.ru'}}

        Synframe = LabelFrame( text=" Select synonym: ")
        Synframe.grid( row=0, column=0, columnspan=3, padx=2, pady=2 )

        self.cb = Combobox( Synframe, values = list(snnm['synonyms'].values()), height=5, state='readonly')
        self.cb.current(0)
        b_SELECT = Button( Synframe, text='Choose URL', command=self.set_url)

        Label( Synframe, text="Select URL:").grid(column=0, row=0, padx=2, pady=2 )
        self.cb.grid(row=0, column=1, columnspan=2, padx=2, pady=2 )
        b_SELECT.grid( row=0, column=3, padx=2, pady=2  )

        mainframe = LabelFrame( text=" Input URL and choose action: " )
        mainframe.grid( row=1, column=0, columnspan=3, padx=2, pady=2 )

        self.entry_message = StringVar()
        e = Entry( mainframe, textvariable=self.entry_message, width=35)
        b_OK = Button( mainframe, text='Process ', command=self.ProcessURL)
        b = Button( mainframe, text="Show from base", command=self.SearchInDB)

        Label( mainframe, text="Edit URL:").grid( row=0, column=0, padx=2, pady=2 )
        e.grid( row=0, column=1, columnspan=3, padx=2, pady=2 )
        b_OK.grid( row=1, column=0, padx=2, pady=2 )
        b.grid( row=1, column=3, sticky='E', padx=2, pady=2 )

        labelframe = LabelFrame()
        labelframe.grid( row=3, column=0, columnspan=4, sticky='W', padx=2, pady=2 )

        self.lb_out = Message(labelframe )
        self.lb_out.grid( row=0, column=0, sticky='W', pady=2, padx=2 )

    def set_url(self):
        self.entry_message.set(self.cb.get())

    def ProcessURL(self):
        ProcessingUrl = self.entry_message.get()
        if ProcessingUrl == '':
            self.lb_out.config(text='Please type or choose URL to process!')
        else:
            self.lb_out.config(text='Processing URL: \t'+ ProcessingUrl)
            rezult_dict = ProcessGET(ProcessingUrl)
            self.lb_out.config(text=print_dict(rezult_dict, ProcessingUrl))

    def SearchInDB(self):
        ProcessingUrl = self.entry_message.get()
        if ProcessingUrl == '':
            self.lb_out.config(text='Please type or choose URL to process!')
        else:
            self.lb_out.config(text='Searching in DB for info about URL: \t'+ ProcessingUrl)
            rezult_dict = ProcessVIEW(ProcessingUrl)
            self.lb_out.config(text=print_dict(rezult_dict, ProcessingUrl))

def print_dict( output_dict, url ) -> str:
    message_text = 'TAG counting for URL:\n' + url + '\n\n'
    for key, value in output_dict.items():
        message_text += str(key) + '\t\t\t\t\t' + str(value) + '  \n'
    message_text += '\n'
    message_text += 'Разом:\t\t\t\t\t' + str(sum(output_dict.values()))
    return message_text

def main():
    # # procassing input parameters
    parser = argparse.ArgumentParser(description='Programm to count HTML tags in html files from address')
    parser.add_argument('--get', help='gathering info about this site')
    parser.add_argument('--view', help='displaying info about this site from DB')
    args = parser.parse_args()

    if args.get == '' :
        print('you should pass an argument for --get. see next time. bye')
        exit(0)
    if args.view == '' :
        print('you should pass an argument for --view. see next time. bye')
        exit(0)

    if not args.get and not args.view:
            root = Tk()
            root.title("tagCounter")
            window = tagCountGUI(root)
            window.mainloop()
    if args.get:
        ProcessGET(args.get)
    if args.view:
        ProcessVIEW(args.view)


if __name__ == "__main__":
    # execute only if run as a script
    main()
