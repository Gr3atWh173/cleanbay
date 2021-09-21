"""Serves the API that enables searching the backend"""
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder

#from typing import Optional

from backend import Backend


app = FastAPI()
backend = Backend()


@app.get('/')
def index():
  return {'status': 'ok'}


@app.get('/api/v1/search/{search_query}')
async def search(search_query: str):
  (listings, from_cache) = await backend.search(search_query)
  return {
    'search_query': search_query,
    'listings_length': len(listings),
    'cache_hit': from_cache,
    'listings': jsonable_encoder(listings)
  }

