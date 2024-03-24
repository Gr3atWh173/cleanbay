# Cleanbay

A metasearch engine for torrents

**Note**: The frontend code lives in
[this repo](https://github.com/gr3atwh173/cleanbay-frontend)

0. [Supported trackers](#supported-trackers)
1. [Live instances](#live-instances)
2. [Setup](#setup)
3. [API Endpoints](#api-endpoints)
4. [Contributing](#contributing)

## Supported trackers

Currently supported trackers are:

1. Piratebay
2. YTS
3. EZTV
4. LinuxTracker
5. Libgen
6. Nyaa

## Live instances

You can find a running instance at:

1. https://testbay.onrender.com or,
2. https://cleanbay.netlify.app if you prefer a frontend

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

_Optional_: Create a `.env` file with the following parameters in the project
root:

```
# directory where the plugins are located
# must have a __init__.py file
PLUGINS_DIRECTORY="./backend/plugins"

# rate limiting by IP
RATE_LIMIT="100/minute"

# cache size in 'entries'
CACHE_SIZE=128

# time (in seconds) before a cache item is invalidated
CACHE_TIMEOUT=300

# domain allowed to make cross-origin requests to the server
# '*' allows for any domain to request data
ALLOWED_ORIGIN="*"
```

3. Run the web API

```
poetry run uvicorn app.main:app
```

## API endpoints

>**NOTE**: See the [auto-generated swagger docs](https://testbay.onrender.com/docs) for more up-to-date documentation

1. `POST /api/v1/search/` expects

```json
{
  "search_term": "...",
  "include_categories": ["cinema", "tv"],
  "exclude_categories": [],
  "include_sites": ["linuxtracker", "piratebay"],
  "exclude_sites": []
}
```

and returns JSON with the following structure:

```json
{
  "status": "ok",
  "length": 123,
  "cache_hit": true,
  "elapsed": 2.324,
  "data": [
    {
      "name": "...",
      "magnet": "...",
      "seeders": 12345,
      "leechers": 1234,
      "size": "...",
      "uploader": "...",
      "uploaded_at": "..."
    }
  ]
}
```

in case of an error, the following is returned:

```json
{
  "status": "error",
  "msg": "why it happened"
}
```

---

**NOTE**

Categories are mapped like so:

```
"all" or "*" => ALL: Everything under the sun
"general"    => GENERAL: Plugins that track everything
"cinema"     => CINEMA: Plugins that track movies
"tv"         => TV: Plugins that track shows on TV, OTT or anything that's not a movie
"software"   => SOFTWARE: Plugins that track software excluding games
"books"      => BOOKS: Plugins that index books or audiobooks
```

---

2. `GET /api/v1/status` returns JSON with the following structure

```json
{
  "status": "ok", // or "not ok"
  "plugins": ["loaded", "plugins"]
}
```

## Contributing

### How you can contribute

This is a non-exhaustive list:

1. Make a plugin (or two, or three, or four...)
2. Add new features to the backend, or make existing ones better!
3. Make a better frontend.
4. Write better documentation for the API.
5. Bug fixes, refactors, etc.
6. Suggest a feature.

In any case, thanks for contributing!

### How to contribute

Before making a change, please first discuss the change you want to make via raising an issue.

1. Fork and clone the repo
2. Run `poetry install` to install tha dependencies
3. Create a branch for your PR with `git checkout -b your-branch-name`
4. Code your changes.
5. Push the changes to your fork
6. Make a pull request!
