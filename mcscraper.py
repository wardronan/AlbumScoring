# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 11:57:25 2020

@author: eeron
"""

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen, urlparse, urljoin
import re
import time
import csv
import numpy as np
import datetime

class AlbumReview:
    def __init__(self, artist, album, reviewer, score, review):
        self.artist = artist
        self.album = album
        self.reviewer = reviewer
        self.score = score
        self.review = review

    def __str__(self):
        return f'Artist: {self.artist}, Album: {self.album}, Reviewer: {self.reviewer}, Score: {self.score}, Review: {self.review}'
    
    def __repr__(self):
        return (f'{self.__class__.__name__}('f'{self.artist!r}, {self.album!r}, {self.reviewer!r}, {self.score!r}, {self.review!r} )')

def scrape_mc_page(url):
    req = Request(url, headers = {'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    page_soup = BeautifulSoup(webpage, "html.parser")
    
    critic_names= []
    critic_scores = []
    critic_reviews = []
    review_list = []
    
    artist = page_soup.find('span',{'class':'band_name'}).text.strip()
    album = page_soup.find('div',{'class':'product_title'}).text.strip()

    containers = page_soup.findAll('div', {'class':'review_section'})    
    for container in containers:
    
        if re.search('<div class="source">',str(container)) == None : ##only grab critic reviews, not user reviews
            continue
        
        critic_name_soup = container.findAll('div', {'class':'source'})
        for name in critic_name_soup:
            #critic_name = re.sub('<[^>]+>', '', str(name))
            critic_name = name.text
            critic_names.append(critic_name)
            
        critic_score_soup = container.findAll('div', {'class':'review_grade'})
        for score in critic_score_soup:
            #critic_score = re.sub('<[^>]+>', '', str(score))
            critic_score = re.search('\d+', str(score))
            critic_scores.append(critic_score.group(0))
        
        critic_review_soup = container.findAll('div', {'class':'review_body'})
        for review in critic_review_soup:
            #critic_review = re.sub('<[^>]+>', '', str(review))
            #critic_review = re.sub('\n', '', str(critic_review))
            critic_review = review.text.strip()
            critic_reviews.append(critic_review)
    
    for i in zip(critic_names, critic_scores, critic_reviews):
        review_list.append(AlbumReview(artist,album,i[0],i[1],i[2]))
    
    return(review_list)



def save_reviews_to_csv_file(review_list, file_name):
    with open(file_name, 'a+', newline='') as csvfile: #w will overwrite entire file, 'a+' will append but need to fix header
        fieldnames = ['artist', 'album','reviewer', 'score', 'review']#list(review_list[0].__dict__.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        #writer.writeheader()

        for review in review_list:
            writer.writerow({'artist': review.artist, 'album': review.album, 
                         'reviewer':review.reviewer, 'score':review.score, 'review':review.review})

def initialize_review_csv (file_name):
    with open(file_name, 'w', newline='') as csvfile: #w will overwrite entire file, 'a+' will append but need to fix header
        fieldnames = ['artist', 'album','reviewer', 'score', 'review']#list(review_list[0].__dict__.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
            
def initialize_scraped_url_csv(file_name):
    with open(file_name, 'w', newline='') as csvfile: #w will overwrite entire file, 'a+' will append but need to fix header
        fieldnames = ['artist', 'album','url','created_at']#list(review_list[0].__dict__.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
            
def scrape_and_write(url, review_file, url_file):
    
    review_list = scrape_mc_page(url)
    save_reviews_to_csv_file(review_list, review_file)
    
    with open(url_file, 'a+', newline='') as url_file:
        fieldnames = ['artist', 'album','url', 'created_at']
        writer = csv.DictWriter(url_file, fieldnames=fieldnames)
        writer.writerow({'artist': review_list[0].artist, 'album': review_list[0].album, 
            'url': url, 'created_at': datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')})
        print(str(datetime.datetime.now()))
        
def get_critic_review_links(url):
    
    req = Request(url, headers = {'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")
    link_list = []
    
    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        
        if href == "" or href is None:
        # href empty tag
            continue
            # join the URL if it's relative (not absolute link)
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        # remove URL GET parameters, URL fragments, etc.
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path

        if re.search('critic-reviews',str(href)) != None and href not in link_list:

            link_list.append(href)
            
    return (link_list)

def get_next_page_link(url):
    
    req = Request(url, headers = {'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")
    
    next_section = soup.find('a', {'class':'action', 'rel':'next'})
    href = urljoin(url, next_section.attrs.get("href"))

    parsed_href = urlparse(href)
    # remove URL GET parameters, URL fragments, etc.
    print(parsed_href)
    href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path +"?"+ parsed_href.query
    return href

    
def scrape_many(url, scrape_next=False):
    url_list = get_critic_review_links(url)
    missed =[]
    for i, url in enumerate(url_list):
        
        time.sleep(np.random.normal(6,1))
        print(url)
        try:
            scrape_and_write(url, 'reviews_2019.csv', 'scraped_urls_2019.csv')
        except Exception:
            missed.append(url)
            continue
    if scrape_next == True:
        try:
            next_url = get_next_page_link(url)
            scrape_many(next_url)
        except Exception:
            print('no NEXT link')
    print('DONE\nMISSED:'+str(missed))

def getnexts(url):
    next_url = get_next_page_link(url)
    print(next_url)
    print(type(url))
    print(type(next_url))
    time.sleep(np.random.normal(6,1))
    try:
        getnexts(next_url)
    except Exception:
        print('done')
    #getnexts(next_url)
#this input works:     
# https://www.metacritic.com/browse/albums/score/metascore/year/filtered?year_selected=2019&distribution=&sort=desc&view=detailed&page=1
# https://www.metacritic.com/browse/albums/score/metascore/year/filtered?year_selected=2019&distribution=&sort=desc&view=detailed&page=2
    
#   https://www.metacritic.com/browse/albums/score/metascore/year/filtered?year_selected=2019&distribution=&sort=desc&view=detailed
#   https://www.metacritic.com/browse/albums/score/metascore/year/filtered?year_selected=2019&distribution=&sort=desc&view=detailed&page=1
##  https://www.metacritic.com/browse/albums/score/metascore/year/filtered?year_selected=2019&distribution=&sort=desc&view=detailed
#   https://www.metacritic.com/browse/albums/score/metascore/year/filtered?year_selected=2019&distribution=&sort=desc&view=detailed&page=2   
    
# https://www.metacritic.com/browse/albums/score/metascore/year/filteredyear_selected=2019&distribution=&sort=desc&view=detailed&page=3page=1'
# https://www.metacritic.com/browse/albums/score/metascore/year/filtered?year_selected=2019&distribution=&sort=desc&view=detailed&page=3
def argfunc(*input):
    for i in input:
        print(i)
