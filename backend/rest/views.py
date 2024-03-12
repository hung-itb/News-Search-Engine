# coding: utf8

from django.http import JsonResponse
from datetime import datetime
import requests, os, sys, threading, multiprocessing, random
dirname = os.path.dirname(__file__)
sys.path.append(os.path.join(os.path.dirname(dirname), 'crawler'))
from spider_manager import get_spider_status, run_spider, send_stop_request_spider, get_crawl_history, get_crawled_docs, init_spider_manager
init_spider_manager()
from .my_lib import string_utils, datetime_utils, storage, prepare_doc_for_solr

def search_controller(request):
  NUM_ROWS_PER_PAGE = 10
  FIELD_WEIGHTS = {
    'title': 0.6,
    'abstract': 0.3,
    'content': 0.1
  }
  BOOST_EXISTS_DATES = 10
  BOOST_RECENT_DOCS = {
    'smallest_val': 4000,
    'biggest_val': (datetime.now() - datetime(1990, 1, 1)).days,
    'coff': 100
  }
  data = request.GET
  q = data.get('q') or '*:*'
  page = max(int(data.get('page') or '0'), 0)
  category = data.get('category')
  extracted_dates = datetime_utils.extract_dates(q)
  for ov in extracted_dates: q = q.replace(ov, ' ')
  q = ' '.join(string_utils.tokenize_vncore_nlp(q, False))
  if q != '' or len(extracted_dates) != 0:
    q += ' ' + ' '.join(f'{v}^{BOOST_EXISTS_DATES}' for i, v in extracted_dates.items())
  else:
    q = '*:*'
  boost_m = (1 - 1/BOOST_RECENT_DOCS["coff"])/(BOOST_RECENT_DOCS["biggest_val"] - BOOST_RECENT_DOCS["smallest_val"])
  boost_c = 1 - boost_m*BOOST_RECENT_DOCS["biggest_val"]
  solr_params = {
    'q': q,
    'defType': 'edismax',
    'qf': ' '.join(f'{f}^{w}' for f, w in FIELD_WEIGHTS.items()),
    'boost': f'linear(num_days_from_1990_to_created_date,{boost_m},{boost_c})',
    # 'debugQuery': 'true',
    # 'debug.explain.structured': 'true',
    'rows': NUM_ROWS_PER_PAGE,
    'start': page*NUM_ROWS_PER_PAGE,
    'facet': 'true',
    'facet.field': 'category'
  }
  if category:
    solr_params['fq'] = f'category:{category.replace(" ", "_")}'
  url = f'{os.environ.get("SOLR_HOST")}:{os.environ.get("SOLR_PORT")}/solr/{os.environ.get("SOLR_CORE_NAME")}/select?' + '&'.join(f'{pn}={pv}' for pn, pv in solr_params.items())
  response = requests.get(url)
  return JsonResponse(response.json())

def admin_controller(request):
  sub_path = request.get_full_path().replace('crawler', '').replace('/', '')
  if 'start' in sub_path:
    multiprocessing.Process(target=run_spider).start()
    return JsonResponse({})
  elif 'stop' in sub_path:
    send_stop_request_spider()
    return JsonResponse({})
  else:
    indexed_filenames = storage.get('indexed_filenames', default=[])
    not_indexed_filenames = [crawl_time['filename'] for crawl_time in get_crawl_history() if crawl_time['filename'] not in indexed_filenames]
    return JsonResponse({
      'numDocs': requests.get(f'{os.environ.get("SOLR_HOST")}:{os.environ.get("SOLR_PORT")}/solr/{os.environ.get("SOLR_CORE_NAME")}/select?q=*:*&rows=0').json().get('response', {}).get('numFound', -1),
      'crawlStatus': get_spider_status(),
      'crawlHistory': get_crawl_history(),
      'notIndexedFilenames': not_indexed_filenames,
      'indexingDocuments': storage.get('indexing_documents', default=False)
    })

def send_data_to_solr():
  crawl_history = get_crawl_history()
  indexed_filenames = set(storage.get('indexed_filenames', default=[]))
  url = f'{os.environ.get("SOLR_HOST")}:{os.environ.get("SOLR_PORT")}/solr/{os.environ.get("SOLR_CORE_NAME")}/update/json/docs?commit=true'
  for crawl_time in crawl_history:
    filename = crawl_time['filename']
    if filename not in indexed_filenames:
      batch = []
      docs_per_request = int(1000*(0.9 + random.random()*0.2))
      for doc in get_crawled_docs(filename):
        batch.append(prepare_doc_for_solr(doc))
        if len(batch) >= docs_per_request:
          requests.post(url, json=batch)
          batch = []
          docs_per_request = int(1000*(0.9 + random.random()*0.2))
      requests.post(url, json=batch)
      indexed_filenames.add(filename)
      storage.set('indexed_filenames', list(indexed_filenames))
  storage.delete_temp('indexing_documents')

def update_data_solr_controller(request):
  storage.set_temp('indexing_documents', True)
  threading.Thread(target=send_data_to_solr).start()
  return JsonResponse({})
