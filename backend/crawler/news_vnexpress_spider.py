
import scrapy, os, json, datetime

dirname = os.path.dirname(__file__)
folder_path_to_store_data = os.path.join(dirname, 'data')
if not os.path.exists(folder_path_to_store_data):
    os.makedirs(folder_path_to_store_data)

class utils:
    @staticmethod
    def read_file(rel_path = None, abs_path = None, default = None):
        if abs_path is None:
            abs_path = os.path.join(dirname, rel_path)
        if not os.path.exists(abs_path):
            if default is not None:
                return default
            else:
                raise Exception('File not found:', abs_path)
        f = open(abs_path)
        data = f.read()
        f.close()
        return data
    @staticmethod
    def write_file(rel_path = None, abs_path = None, content = '', append = False):
        if abs_path is None:
            abs_path = os.path.join(dirname, rel_path)
        if append and os.path.exists(abs_path):
            f = open(abs_path, 'a')
        else:
            if not os.path.exists(os.path.dirname(abs_path)):
                os.makedirs(os.path.dirname(abs_path))
            f = open(abs_path, 'w')
        f.write(content)
        f.close()
    @staticmethod
    def delete_file(rel_path = None, abs_path = None):
        if abs_path is None:
            abs_path = os.path.join(dirname, rel_path)
        if os.path.exists(abs_path):
            os.remove(abs_path)
    @staticmethod
    def current_datetime_in_GMT_7():
        return datetime.datetime.utcnow() + datetime.timedelta(hours=7)

class custom_set():
    def __init__(self, data = None):
        if data is None:
            self.data = set()
        else:
            self.data = set(hash(i) for i in data)
    def add(self, e):
        self.data.add(hash(e))
    def __contains__(self, e):
        return hash(e) in self.data
    def __len__(self):
        return len(self.data)

class NewsSpider(scrapy.Spider):
    name = 'news_vnexpress_spider'
    BASE_URL = 'https://vnexpress.net'
    PARAGRAPH_SPLIT = '$$$'*4
    REQUEST_MADE_FREQUENCE_TO_CHECK_STOP_SIGNAL = 10

    def start_requests(self):
        now = utils.current_datetime_in_GMT_7()
        filename = f'news_{now.strftime("%Y%m%d%H%M%S")}.jsonl'
        self.path_to_save_data = os.path.join(folder_path_to_store_data, 'news', filename)
        utils.write_file(rel_path='crawler_status.txt', content=json.dumps({
            'start_at': str(now),
            'status': 'crawling',
            'filename': filename
        }))
        
        # Init variables
        self.visited_urls = custom_set(utils.read_file(abs_path=os.path.join(folder_path_to_store_data, 'visited_urls.txt'), default='').split('\n'))
        self.visited_urls_this_section = set()
        self.num_made_requests_this_section = 0
        self.not_saved_crawled_docs = []
        self.num_crawled_docs = 0
        self.num_yielded_request = 0
        self.max_num_yielded_request = 10e10
        self.candidate_urls_for_future_crawl = []
        self.stopped = False

        # Start make requests
        stored_candidate_urls = [url for url in utils.read_file(abs_path=os.path.join(folder_path_to_store_data, 'candidate_urls.txt'), default='').split('\n') if url != '']
        limit_num_stored_candidate_urls = 500
        stored_candidate_urls_this_session = stored_candidate_urls[:limit_num_stored_candidate_urls]
        stored_candidate_urls = stored_candidate_urls[limit_num_stored_candidate_urls:]
        utils.write_file(abs_path=os.path.join(folder_path_to_store_data, 'candidate_urls.txt'), content='\n'.join(stored_candidate_urls) + '\n')
        for url in stored_candidate_urls_this_session:
            yield scrapy.Request(url=url, callback=self.parse_article, meta={'max_retry_times': 0})
        yield scrapy.Request(url=self.BASE_URL, callback=self.parse_list_news_page, meta={'max_retry_times': 5}, dont_filter=True)

    def has_stop_signal(self):
        return utils.read_file('stop.txt', default='False') != 'False'

    def classify_and_format_urls(self, urls):
        news_urls = []
        list_news_urls = []
        not_useable_urls = []
        for url in urls:
            url = url.split('#')[0]
            if url == '' or 'the-thao/f1/topcharts' in url or 'error' in url:
                not_useable_urls.append(url)
                continue
            if 'https://vnexpress.net' not in url:
                if url[0] == '/':
                    url = 'https://vnexpress.net' + url
                else:
                    not_useable_urls.append(url)
                    continue
            if '.html' in url or '.htm' in url:
                news_urls.append(url)
            else:
                list_news_urls.append(url)
        return news_urls, list_news_urls, not_useable_urls

    def mark_url_as_visited(self, url):
        self.visited_urls.add(url)
        self.visited_urls_this_section.add(url)

    def parse_list_news_page(self, res):
        urls = res.css('a::attr(href)').getall()
        news_urls, list_news_urls, _ = self.classify_and_format_urls(urls)
        urls = [[url, 1] for url in news_urls] + [[url, 2] for url in list_news_urls]
        urls = [ele for ele in urls if ele[0] not in self.visited_urls]

        for url, type in urls:
            if type == 1: self.mark_url_as_visited(url)
            self.num_made_requests_this_section += 1
            if self.num_made_requests_this_section > self.REQUEST_MADE_FREQUENCE_TO_CHECK_STOP_SIGNAL:
                self.num_made_requests_this_section = 0
                crawler_status = json.loads(utils.read_file(rel_path='crawler_status.txt'))
                crawler_status['num_crawled_docs'] = self.num_crawled_docs
                if not self.stopped and self.has_stop_signal():
                    self.stopped = True
                    utils.delete_file('stop.txt')
                    crawler_status['status'] = 'stopping'
                utils.write_file(rel_path='crawler_status.txt', content=json.dumps(crawler_status))
            if self.stopped or self.num_yielded_request >= self.max_num_yielded_request:
                if type == 1: self.candidate_urls_for_future_crawl.append(url)
            else:
                self.num_yielded_request += 1
                yield scrapy.Request(url=url, callback=self.parse_article if type == 1 else self.parse_list_news_page, meta={'max_retry_times': 0})

    def article_type(self, article_children):
        has_silde_show = False
        for child in article_children:
            if child.root.tag == 'p' and child.attrib.get('class') == 'Normal': return 1
            if child.attrib.get('class') is not None and 'item_slide_show' in child.attrib.get('class'):
                has_silde_show = True
        if has_silde_show:
            return 2
        return -1

    def parse_article(self, res):
        result = {}
        result['url'] = res.url
        header_content = res.css('.header-content')
        if len(header_content) == 1:
            category_tree_ele = header_content.css('.breadcrumb')
            if len(category_tree_ele) == 1:
                result['category-tree'] = '/'.join(category_tree_ele.css('li a::text').getall())
            date_ele = header_content.css('.date')
            if len(date_ele) == 1:
                result['created-at'] = date_ele.css('.date::text').get()
        title_ele = res.css('.title-detail')
        if len(title_ele) == 1:
            result['title'] = title_ele.css('.title-detail::text').get()
        description_ele = res.css('.description')
        if len(description_ele) == 1:
            result['description'] = description_ele.css('.description::text').get()
        main_article = res.css('article.fck_detail')
        if len(main_article) == 1:
            article_children = main_article.css('article.fck_detail > *')
            article_type = self.article_type(article_children)
            if article_type == 1:
                p_tags = [ele for ele in article_children if ele.root.tag == 'p']
                if p_tags[-1].css('p strong::text').get() is not None:
                    result['author'] = p_tags[-1].css('p strong::text').get()
                    p_tags.pop()
                elif article_children[-1].css('p strong').get() is not None:
                    result['author'] = article_children[-1].css('p strong::text').get()
                result['content'] = self.PARAGRAPH_SPLIT.join(p.css('p::text').get() for p in p_tags if p.css('p::text').get() if not None and p_tags if p.css('p::text').get().strip() != '')
            if article_type == 2:
                content_containers = [ele for ele in article_children if ele.attrib.get('class') is not None and 'item_slide_show' in ele.attrib.get('class')]
                content = ''
                for content_container in content_containers:
                    original_contents = content_container.css('.desc_cation p::text').getall()
                    existed = set()
                    for original_content in original_contents:
                        original_content = original_content.strip()
                        if original_content != '' and original_content not in existed:
                            if content != '': content += self.PARAGRAPH_SPLIT
                            content += original_content
                            existed.add(original_content)
                result['content'] = content
                author_wrapper_candidates = [ele for ele in article_children if ele.attrib.get('class') is not None and 'width-detail-photo' in ele.attrib.get('class')]
                if len(author_wrapper_candidates) != 0:
                    author_name = author_wrapper_candidates[-1].css('p strong::text').get()
                    if author_name is not None:
                        result['author'] = author_name
        important_keys_pairs = [['title', 'description'], ['title', 'content']]
        valid = False
        for important_keys in important_keys_pairs:
            sub_valid = True
            for key in important_keys:
                if key not in result:
                    sub_valid = False
                    break
            if sub_valid:
                valid = True
                break
        if valid:
            self.num_crawled_docs += 1
            self.not_saved_crawled_docs.append(result)
            if self.num_crawled_docs%100 == 0 and self.num_crawled_docs >= 1000:
                head, tail = [1000, 5], [20000, 1]
                coff = ((head[1]-tail[1])/(head[0]-tail[0]))*self.num_crawled_docs + head[1] - head[0]*((head[1]-tail[1])/(head[0]-tail[0]))
                self.max_num_yielded_request = max(self.max_num_yielded_request, int(self.num_crawled_docs*coff))
            if len(self.not_saved_crawled_docs) > 1000:
                utils.write_file(abs_path=self.path_to_save_data, content='\n'.join(json.dumps(doc) for doc in self.not_saved_crawled_docs) + '\n', append=True)
                self.not_saved_crawled_docs = []
        for req in self.parse_list_news_page(res):
            yield req

    def closed(self, reason):
        utils.delete_file('stop.txt')
        utils.write_file(abs_path=self.path_to_save_data, content='\n'.join(json.dumps(doc) for doc in self.not_saved_crawled_docs) + '\n', append=True)
        utils.write_file(abs_path=os.path.join(folder_path_to_store_data, 'visited_urls.txt'), content='\n'.join(set(self.visited_urls_this_section)) + '\n', append=True)
        utils.write_file(abs_path=os.path.join(folder_path_to_store_data, 'candidate_urls.txt'), content='\n'.join(set(self.candidate_urls_for_future_crawl)) + '\n', append=True)

        crawler_status = json.loads(utils.read_file(rel_path='crawler_status.txt'))
        crawler_status['status'] = 'stopped'
        utils.write_file(rel_path='crawler_status.txt', content=json.dumps(crawler_status))
        utils.write_file(abs_path=os.path.join(folder_path_to_store_data, 'crawl_history.txt'), append=True, content=json.dumps({
            'start': crawler_status['start_at'],
            'end': str(utils.current_datetime_in_GMT_7()),
            'num_crawled_docs': self.num_crawled_docs,
            'filename': crawler_status['filename']
        }) + '\n')
