import ssl
from typing import Any

import aiohttp
import certifi

from core.enums import SocialProviderEnum, GenderEnum
from core.exceptions import InvalidToken


class OAuthClient:
    def __init__(
        self,
        resource_uri: str,
        verify_uri: str,
    ) -> None:
        self._resource_uri = resource_uri
        self._verify_uri = verify_uri
        self._header_name = "Authorization"
        self._header_type = "Bearer"

    def _get_connector_for_ssl(self) -> aiohttp.TCPConnector:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        return aiohttp.TCPConnector(ssl=ssl_context)

    async def _request_get_to(self, url: str, params=None, headers=None) -> dict | None:
        conn = self._get_connector_for_ssl()
        async with aiohttp.ClientSession(connector=conn) as session:
            async with session.get(url, params=params, headers=headers) as resp:
                return None if resp.status != 200 else await resp.json()

    async def get_user_info(self, access_token: str) -> dict:
        headers = {self._header_name: f"{self._header_type} {access_token}"}
        user_info = await self._request_get_to(url=self._resource_uri, headers=headers)
        if user_info is None:
            raise InvalidToken
        return user_info

    async def is_authenticated(self, access_token: str) -> bool:
        headers = {self._header_name: f"{self._header_type} {access_token}"}
        res = await self._request_get_to(
            url=self._verify_uri,
            headers=headers,
        )
        return res is not None


def extract_user_data(
    provider: SocialProviderEnum, raw_user_info: dict[str, Any]
) -> dict[str, Any]:
    """Extract standardized user data from provider-specific response"""
    if provider == SocialProviderEnum.kakao:
        return {
            "id": raw_user_info["id"],
            "email": raw_user_info["kakao_account"]["email"],
            "mobile": raw_user_info.get("mobile", ""),
            "name": raw_user_info["kakao_account"]["profile"].get("nickname", ""),
            "profile_image": raw_user_info["kakao_account"]["profile"].get(
                "profile_image_url", ""
            ),
            "age": raw_user_info.get("age"),
            "birthday": raw_user_info.get("birthday"),
            "gender": raw_user_info.get("gender"),
        }
    elif provider == SocialProviderEnum.naver:
        user_info = raw_user_info["response"]
        gender = user_info.get("gender")
        gender = GenderEnum.male if gender == "M" else GenderEnum.female
        return {
            "email": user_info["email"],
            "id": user_info["id"],
            "mobile": user_info.get("mobile", ""),
            "name": user_info.get("name"),
            "profile_image": user_info.get("profile_image"),
            "age": user_info.get("age"),
            "birthday": user_info.get("birthday"),
            "gender": gender,
        }
    else:
        raise ValueError(f"Unsupported provider: {provider}")


naver_client = OAuthClient(
    resource_uri="https://openapi.naver.com/v1/nid/me",
    verify_uri="https://openapi.naver.com/v1/nid/verify",
)

kakao_client = OAuthClient(
    resource_uri="https://kapi.kakao.com/v2/user/me",
    verify_uri="https://kapi.kakao.com/v1/user/access_token_info",
)
