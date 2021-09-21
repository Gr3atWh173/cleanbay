# CleanBay
A metasearch engine for torrents

## Current Status

### Backend
- Implement plugins
  - [x] 1337x 
  - [x] The Pirate Bay 
  - [x] YTS 
  - [x] EZTV 
  - [ ] More...
- [x] Implement async 
- [ ] Add support for categories

### Frontend
- [ ] Decide how to approach it

### Setup
1. Clone this repo
```
git clone https://github.com/gr3atwh173/cleanbay.git
```

2. Install requirements
```
cd cleanbay
pip install -r requirements.txt
```

3. Run the web API
```
uvicorn app:app --reload
```

### API endpoints
1. `GET /api/v1/search/{search_query}` returns JSON with the following structure: 
  ```json
  {
      "search_query": "...",
      "listings_length": 123, // number of results
      "cache_hit": true, // if the results are from the cache
      "listings": [
        {
          "name": "...",
          "magnet": "...",
          "seeders": 12345,
          "leechers": 1234,
          "size": "...", // could also be a number
          "uploader": "...",
          "uploaded_at": "..."
        },
        ...
      ]
  }
  
  ```
**Note**: This structure would likely be changed in the future.

### How to make plugins

`backend/abstract_plugin.py` has the interface that plugins must implement. For examples see `backend/plugins/` 
