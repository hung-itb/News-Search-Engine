
from news_vnexpress_spider import NewsSpider, utils, folder_path_to_store_data
import json, os
from twisted.internet import reactor
from scrapy.crawler import CrawlerProcess

def init_spider_manager():
    # delete some file
    utils.delete_file('crawler_status.txt')
    utils.delete_file('stop.txt')

spider_status_cache = {}
def get_spider_status():
    global spider_status_cache
    status_json = utils.read_file('crawler_status.txt', default='{}')
    if status_json == '':
        return spider_status_cache
    status = json.loads(status_json)
    if utils.read_file('stop.txt', default='False') == 'True':
        status['status'] = 'stopping'
    spider_status_cache = status
    return status

def run_spider():
    spider_status = get_spider_status()
    if spider_status.get('status', None) in ['crawling', 'stopping']: return
    utils.write_file(rel_path='crawler_status.txt', content=json.dumps({ 'status': 'crawling' }))
    utils.delete_file('stop.txt')
    process = CrawlerProcess()
    process.crawl(NewsSpider)
    if True or not reactor.running:
        process.start(install_signal_handlers=False, stop_after_crawl=False)

def send_stop_request_spider():
    spider_status = get_spider_status()
    if spider_status.get('status', None) in [None, 'stopping']: return
    utils.write_file('stop.txt', content='True')

def get_crawl_history():
    return [json.loads(line) for line in utils.read_file(abs_path=os.path.join(folder_path_to_store_data, 'crawl_history.txt'), default='').split('\n') if line != '']

def get_crawled_docs(filename):
    for line in utils.read_file(abs_path=os.path.join(folder_path_to_store_data, 'news', filename), default='').split('\n'):
        if line != '':
            yield json.loads(line)
