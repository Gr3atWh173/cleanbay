# CleanBay
A metasearch engine for torrents

## Current Status

### Backend
- Implement plugins [x]
  - 1337x [x]
  - The Pirate Bay [x]
  - YTS [x]
  - EZTV [x]
  - More... [ ]
- Implement async [x]
- Add support for categories [ ]

### Frontend
- Decide how to approach it [ ]

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

3. Run the test
```
python --version # => Python 3.8.1
python app.py
```

### How to make plugins

`backend/abstract_plugin.py` has the interface that plugins must implement. For examples see `backend/plugins/` 
