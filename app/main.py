"""Serves the API that enables searching the backend"""

from itertools import chain
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from cleanbay.backend import Backend, InvalidSearchError
from cleanbay.plugins_manager import NoPluginsError, PluginsManager
from cleanbay.cache_manager import LFUCache

from app.settings import settings
from app.schemas import SearchIn, SearchOut, SearchError, StatusOut
from app.helpers import parse_search_query

# initialize tha app and the backend
cache_manager = LFUCache(settings.cache_size, settings.cache_timeout)
plugins_manager = PluginsManager(settings.plugins_directory)
backend = Backend(settings.session_timeout, cache_manager, plugins_manager)

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# this is primarily for backwards compat with the frontend
@app.exception_handler(HTTPException)
def http_exception_handler(
    req: Request, exc: HTTPException  # pylint: disable=unused-argument
) -> JSONResponse:
    return JSONResponse({"status": "error", "msg": exc.detail}, exc.status_code)


# routes


@app.get("/api/v1/status", response_model=StatusOut)
@limiter.limit(settings.rate_limit)
def status(request: Request, response: Response):  # pylint: disable=unused-argument
    """Returns the current status and list of available plugins"""
    plugins, is_ok = backend.state()
    status_word = "ok" if is_ok else "not ok"

    return StatusOut(status=status_word, plugins=list(plugins))


@app.post(
    "/api/v1/search",
    response_model=SearchOut,
    responses={422: {"model": SearchError}},
)
@limiter.limit(settings.rate_limit)
async def search(
    request: Request, response: Response, sq: SearchIn
):  # pylint: disable=unused-argument
    """Searches the relevant plugins for torrents"""
    is_valid, msg = validate(sq)
    if not is_valid:
        response.status_code = 422
        raise HTTPException(status_code=422, detail=msg)

    s_term, i_cats, e_cats, i_sites, e_sites = parse_search_query(sq)

    start_time = datetime.now()
    try:
        listings, cache_hit = await backend.search(
            search_term=s_term,
            include_categories=i_cats,
            exclude_categories=e_cats,
            include_sites=i_sites,
            exclude_sites=e_sites,
        )
    except NoPluginsError as exc:
        raise HTTPException(status_code=500, detail="No searchable plugins.") from exc
    except InvalidSearchError as exc:
        response.status_code = 400
        raise HTTPException(status_code=422, detail="Invalid search.") from exc
    elapsed = datetime.now() - start_time

    return SearchOut(
        status="ok", data=listings, cache_hit=cache_hit, elapsed=elapsed.total_seconds()
    )


def validate(sq: SearchIn) -> bool:
    indexed_sites = list(backend.state()[0])
    for site in chain(sq.include_sites, sq.exclude_sites):
        if site not in indexed_sites:
            or_string = f'{", ".join(indexed_sites[:-1])} or {indexed_sites[-1]}'
            return (
                False,
                f'For now, "{site}" is not indexed. Perhaps you meant {or_string}',
            )
    return True, ""


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, reload=True)
