"""Contains the request and response models for the API"""

from typing import List

from fastapi import HTTPException

from pydantic import BaseModel, field_validator, model_validator, computed_field

from cleanbay.torrent import Category, Torrent

CATEGORY_MAP = {
    "all": Category.ALL,
    "general": Category.GENERAL,
    "cinema": Category.CINEMA,
    "tv": Category.TV,
    "software": Category.SOFTWARE,
    "books": Category.BOOKS,
}


class SearchIn(BaseModel):
    """Used to deserialize the JSON received in the request body

    Attributes:
      search_term (str): The string to search for
      include_categories (list): Categories in which to search
      exclude_categories (list): Categories in which to not search
      include_sites (list): Plugins/services to search
      exclude_sites (list): Plugins/services to not search

    """

    search_term: str
    include_categories: List[str] = []
    exclude_categories: List[str] = []
    include_sites: List[str] = []
    exclude_sites: List[str] = []

    @field_validator("search_term")
    @classmethod
    def validate_search_term_not_empty(cls, search_term: str) -> str:
        if search_term.strip() == "":
            raise HTTPException(status_code=422, detail="No search term given.")
        return search_term

    @field_validator("include_categories", "exclude_categories")
    @classmethod
    def validate_category_names(cls, category_list: list) -> list:
        invalid_categories = list(
            filter(lambda cat: cat not in CATEGORY_MAP, category_list)
        )
        if invalid_categories:
            categories = list(CATEGORY_MAP.keys())
            or_string = f"{', '.join(categories[:-1])} or {categories[-1]}"
            raise HTTPException(
                status_code=422,
                # pylint: disable=line-too-long
                detail=f"No such categories: {', '.join(invalid_categories)}. Perhaps you meant {or_string}",
            )
        return category_list

    @model_validator(mode="after")
    def validate_filter_variant_exclusivity(self) -> "SearchIn":
        if self.include_categories and self.exclude_categories:
            raise HTTPException(
                status_code=422,
                detail="Cannot use include and exclude categories together.",
            )
        if self.include_sites and self.exclude_sites:
            raise HTTPException(
                status_code=422, detail="Cannot use include and exclude sites together."
            )
        return self


class SearchOut(BaseModel):
    status: str = "ok"
    cache_hit: bool
    elapsed: float
    data: List[Torrent]

    @computed_field
    @property
    def length(self) -> int:
        return len(self.data)


class SearchError(BaseModel):
    status: str
    msg: str


class StatusOut(BaseModel):
    status: str
    plugins: List[str]
