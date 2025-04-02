from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from cruds.suggest_search_keywords import suggest_search_keywords_crud
from schemes.suggest_search_keywords import SuggestSearchKeywordRead

router = APIRouter()


@router.get("", response_model=list[SuggestSearchKeywordRead])
async def list_suggest_search_keywords(
    session: AsyncSession = Depends(get_session),
):
    results = await suggest_search_keywords_crud.get_multi(
        session,
        offset=0,
        limit=10,
        schema_to_select=SuggestSearchKeywordRead,
        return_as_model=True,
    )

    return results.get("data", [])
