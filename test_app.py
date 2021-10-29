"""Integration tests for the app"""
from fastapi.testclient import TestClient

from app import app


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
    assert listing['magnet'].startswith('magnet:?xt=urn:btih')


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
    assert listing['magnet'].startswith('magnet:?xt=urn:btih')
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
    assert listing['magnet'].startswith('magnet:?xt=urn:btih')
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
    assert listing['magnet'].startswith('magnet:?xt=urn:btih')
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
    assert listing['magnet'].startswith('magnet:?xt=urn:btih')
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
