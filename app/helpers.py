"""Contains helper functions for the API"""

from typing import Tuple

from cleanbay.torrent import Category

from app.schemas import SearchIn, CATEGORY_MAP


def parse_search_query(sq: SearchIn) -> Tuple:
    s_term = sq.search_term

    # if there's 'all' in the include category list, treat it as if the list was
    # empty, ie, include everything
    i_cats = []
    if any(x in sq.include_categories for x in ["all", "*"]):
        i_cats = CATEGORY_MAP.values()
        i_cats.remove(Category.ALL)
    else:
        i_cats = [CATEGORY_MAP[cat] for cat in sq.include_categories]

    e_cats = [CATEGORY_MAP[cat] for cat in sq.exclude_categories]

    i_sites = sq.include_sites
    e_sites = sq.exclude_sites

    return (s_term, i_cats, e_cats, i_sites, e_sites)
