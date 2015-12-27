from bs4 import BeautifulSoup
from urllib2 import urlopen
from pymongo import MongoClient
import re
import logging

# Every product seems to have a product ASIN id, when substituted in the following link, we get reviews for that product
# product_asin = "B011RG8SOU"
amazon_link = "http://www.amazon.in/product-reviews/%s/ref=cm_cr_pr_viewopt_srt?ie=UTF8&showViewpoints=1&sortBy=helpful&pageNumber=%d"

logging.basicConfig(filename='revmine.log', level=logging.DEBUG)

client = MongoClient('mongodb://localhost:27017/')

db = client.revmine
reviews = db.reviews
done = db.done
queue = db.queue
#New Collection for Recommended Proucts
recom = db.recom

#queue.insert_one({'_id':'B011RG8SOU'})
def main():
    """
    While we have Product asin codes in the mongo queue, scrape their product review pages
    and add 'also seen' products to the queue
    """
    while queue.find({}).count > 0:
        orig_product = queue.find_one()['_id']
        doit()
        for i in queue.find():
            recomProd(i['_id'],orig_product)        


def doit():
    # picking an object from the queue
    product_asin = queue.find_one()['_id']
    logging.info("Read next value from queue")
        
    logging.info("Start loading reviews")
    li = {}
    li["_id"] = product_asin

    # Page 1 soup!
    url_ = amazon_link % (product_asin, 1)
    print "Trying " + url_ + " now!"
    soup = BeautifulSoup(urlopen(url_).read())
    li['title'] = soup('span', {'class': 'a-text-ellipsis'})[0].a.text

    # will scrape reviews' text
    for j, row in enumerate(soup('span', {'class': 'review-text'})):
        li[str(j + 1)] = row.text
    
    logging.info("adding entries to queue")

    for div in soup('div', {'class': 'description'}):
        link = div.a['href']
        logging.info("adding " + link + " to queue")
        # extracts product asin
        id = re.search(r'.*?//.*?/.*?/dp/(.*?)/.*', link)
        if (done.find({'_id': id.group(1)}).count() == 1):
            continue
        queue.insert_one({'link': link, '_id': id.group(1)})

    for i in xrange(2, 6):
        url_ = amazon_link % (product_asin, i)
        print "Trying " + url_ + " now!"
        soup = BeautifulSoup(urlopen(url_).read())

        for j, row in enumerate(soup('span', {'class': 'review-text'})):
            li[str(j + 10*(i-1))] = row.text

    inserted_review = reviews.insert_one(li).inserted_id
    logging.info("reviews loaded into db for " + li['title'])

    logging.info("removing entry from queue")
    queue.remove({"_id": product_asin}, 1)
    
        

    assert(inserted_review == product_asin)


def recomProd(product_asin, orig_product):
    
    li = {}
    li["_id"] = product_asin
    li["recom_by"] = orig_product

    #Getting the title
    url_ = amazon_link % (product_asin, 1)
    soup = BeautifulSoup(urlopen(url_).read())
    li['title'] = soup('span', {'class': 'a-text-ellipsis'})[0].a.text

    #Extracting the reviews
    for i in range(1,6,1): 
        url_ = amazon_link % (product_asin, i)
        print "Trying " + url_ + " now!"
        soup = BeautifulSoup(urlopen(url_).read())
        for j, row in enumerate(soup('span', {'class': 'review-text'})):
            li[str(j +10*(i-1))] = row.text

    #Inserting into the Recom collection
    inserted_review = recom.insert_one(li).inserted_id
    logging.info("reviews loaded into recom for " + li['title'])

    logging.info("removing entry from queue")
    queue.remove({"_id": product_asin}, 1)

if __name__ == '__main__':
    main()
