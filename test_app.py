"""Integration tests for the app"""
import re
from os import getenv
from time import sleep

from fastapi.testclient import TestClient

from dotenv import load_dotenv

from app import app


load_dotenv()
cache_timeout = int(getenv('CACHE_TIMEOUT', '5'))

client = TestClient(app)


def test_status():
  response = client.get('/api/v1/status')
  assert response.status_code == 200
  assert response.json()['status'] == 'ok'


def test_empty_search():
  response = client.post('/api/v1/search', json={
    'search_term': '',
    'include_categories': [],
    'exclude_categories': [],
    'include_sites': [],
    'exclude_sites': []
  })

  assert response.status_code == 400


def test_simple_search():
  response = client.post('/api/v1/search', json={
    'search_term': 'star wars',
    'include_categories': [],
    'exclude_categories': [],
    'include_sites': [],
    'exclude_sites': []
  })

  assert response.status_code == 200
  assert response.json()['length'] > 0

  for listing in response.json()['data']:
    assert listing['magnet'].startswith('magnet:?xt=urn:btih') \
      or is_valid_url(listing['magnet'])


def test_include_site():
  response = client.post('/api/v1/search', json={
    'search_term': 'kali',
    'include_categories': ['software'],
    'exclude_categories': [],
    'include_sites': [],
    'exclude_sites': []
  })

  assert response.status_code == 200
  assert response.json()['length'] > 0

  for listing in response.json()['data']:
    assert listing['magnet'].startswith('magnet:?xt=urn:btih') \
      or is_valid_url(listing['magnet'])
    assert listing['uploader'] == 'linuxtracker'


def test_exclude_categories():
  response = client.post('/api/v1/search', json={
    'search_term': 'alpine',
    'include_categories': [],
    'exclude_categories': ['software'],
    'include_sites': [],
    'exclude_sites': []
  })

  assert response.status_code == 200
  assert response.json()['length'] > 0

  for listing in response.json()['data']:
    assert listing['magnet'].startswith('magnet:?xt=urn:btih') \
      or is_valid_url(listing['magnet'])
    assert listing['uploader'] != 'linuxtracker'


def test_include_exclude_categories():
  response = client.post('/api/v1/search', json={
    'search_term': 'alpine',
    'include_categories': ['software'],
    'exclude_categories': ['cinema'],
    'include_sites': [],
    'exclude_sites': []
  })

  assert response.status_code == 400


def test_include_sites():
  response = client.post('/api/v1/search', json={
    'search_term': 'kali',
    'include_categories': [],
    'exclude_categories': [],
    'include_sites': ['linuxtracker'],
    'exclude_sites': []
  })

  assert response.status_code == 200
  assert response.json()['length'] > 0

  for listing in response.json()['data']:
    assert listing['magnet'].startswith('magnet:?xt=urn:btih') \
      or is_valid_url(listing['magnet'])
    assert listing['uploader'] == 'linuxtracker'


def test_exclude_sites():
  response = client.post('/api/v1/search', json={
    'search_term': 'alpine',
    'include_categories': [],
    'exclude_categories': [],
    'include_sites': [],
    'exclude_sites': ['linuxtracker']
  })

  assert response.status_code == 200
  assert response.json()['length'] > 0

  for listing in response.json()['data']:
    assert listing['magnet'].startswith('magnet:?xt=urn:btih') \
      or is_valid_url(listing['magnet'])
    assert listing['uploader'] != 'linuxtracker'


def test_include_exclude_sites():
  response = client.post('/api/v1/search', json={
    'search_term': 'kali',
    'include_categories': [],
    'exclude_categories': [],
    'include_sites': ['linuxtracker'],
    'exclude_sites': ['yts']
  })

  assert response.status_code == 400


def test_advanced_search():
  response = client.post('/api/v1/search', json={
    'search_term': 'star trek',
    'include_categories': ['tv'],
    'exclude_categories': [],
    'include_sites': [],
    'exclude_sites': ['linuxtracker', 'piratebay']
  })

  assert response.status_code == 200
  assert response.json()['length'] > 0
  
  for listing in response.json()['data']:
    assert listing['uploader'] in ['eztv', 'yts']


def test_cache():
  response_first = client.post('/api/v1/search', json={
    'search_term': 'dune',
    'include_categories': [],
    'exclude_categories': [],
    'include_sites': ['yts'],
    'exclude_sites': []
  })

  response_second = client.post('/api/v1/search', json={
    'search_term': 'dune',
    'include_categories': [],
    'exclude_categories': [],
    'include_sites': ['yts'],
    'exclude_sites': []
  })

  assert response_first.json()['cache_hit'] is False
  assert response_second.json()['cache_hit'] is True


def test_cache_timeout():
  response_first = client.post('/api/v1/search', json={
    'search_term': 'godfather',
    'include_categories': [],
    'exclude_categories': [],
    'include_sites': ['yts'],
    'exclude_sites': []
  })

  response_second = client.post('/api/v1/search', json={
    'search_term': 'godfather',
    'include_categories': [],
    'exclude_categories': [],
    'include_sites': ['yts'],
    'exclude_sites': []
  })

  assert response_first.json()['cache_hit'] == False
  assert response_second.json()['cache_hit'] == True
  
  sleep(cache_timeout)

  response_third = client.post('/api/v1/search', json={
    'search_term': 'godfather',
    'include_categories': [],
    'exclude_categories': [],
    'include_sites': ['yts'],
    'exclude_sites': []
  })

  response_fourth = client.post('/api/v1/search', json={
    'search_term': 'godfather',
    'include_categories': [],
    'exclude_categories': [],
    'include_sites': ['yts'],
    'exclude_sites': []
  })

  assert response_third.json()['cache_hit'] == False
  assert response_fourth.json()['cache_hit'] == True

# ================ utility functions =====================

def is_valid_url(url: str) -> bool:
  regex = re.compile(
    r'^(?:http|ftp)s?://' # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
    r'localhost|' #localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
    r'(?::\d+)?' # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)
  return re.match(regex, url) is not None