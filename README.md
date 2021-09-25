# CleanBay
A metasearch engine for torrents

Contents
1. [Current Status](#current-status)
2. [Setup](#setup)
3. [API Endpoints](#api-endpoints)
4. [How to make plugins](#how-to-make-plugins)

## Current Status

### Backend
1. Implement plugins
  - [x] 1337x 
  - [x] The Pirate Bay 
  - [x] YTS 
  - [x] EZTV 
  - [ ] More...
2. [x] Implement async 
3. [x] Add support for categories

### Frontend
- [ ] Decide how to approach it

## Setup
1. Clone this repo
```
git clone https://github.com/gr3atwh173/cleanbay.git
```

2. Install with [Poetry](https://pypi.org/project/poetry/)
```
cd cleanbay
poetry install
```

3. Run the web API
```
poetry run uvicorn app:app --reload
```

## API endpoints
1. `GET /api/v1/search/{search_query}&category=0` returns JSON with the following structure:
  ```json
  {
      "search_query": "...",
      "category": 0,
      "listings_length": 123,
      "cache_hit": true,
      "listings": [
        {
          "name": "...",
          "magnet": "...",
          "seeders": 12345,
          "leechers": 1234,
          "size": "...", 
          "uploader": "...",
          "uploaded_at": "..."
        },
        ...
      ]
  }
  ```
---
**NOTE**

Categories are mapped like so:
```
0 => ALL: Everything under the sun
1 => GENERAL: Plugins that track everything
2 => CINEMA: Plugins that track movies
3 => TV: Plugins that track shows on TV, OTT or anything that's not a movie
```
---

2. `GET /api/v1/status` returns JSON with the following structure
  ```json
  {
    "status": "ok", // or "not ok"
    "plugins": [
      "loaded",
      "plugins"
    ]
  }
  ```

## How to make plugins

`backend/abstract_plugin.py` has the interface that plugins must implement. For examples see `backend/plugins/` 
