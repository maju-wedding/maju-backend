import ssl
from typing import Any

import aiohttp
import certifi

from core.config import settings
from core.enums import SocialProviderEnum
from core.exceptions import InvalidAuthorizationCode, InvalidToken


class OAuthClient:
    def __init__(
        self,
        client_id: str,
        client_secret_id: str,
        authentication_uri: str,
        resource_uri: str,
        verify_uri: str,
    ) -> None:
        self._client_id = client_id
        self._client_secret_id = client_secret_id
        self._authentication_uri = authentication_uri
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

    async def _request_post_to(self, url: str, payload=None) -> dict | None:
        conn = self._get_connector_for_ssl()
        async with aiohttp.ClientSession(connector=conn) as session:
            async with session.post(url, data=payload) as resp:
                return None if resp.status != 200 else await resp.json()

    async def get_tokens(self, code: str, state: str | None) -> dict:
        tokens = await self._request_get_to(
            url=f"{self._authentication_uri}/token",
            params={
                "client_id": self._client_id,
                "client_secret": self._client_secret_id,
                "grant_type": "authorization_code",
                "code": code,
                "state": state,
            },
        )

        if tokens is None:
            raise InvalidAuthorizationCode

        if tokens.get("access_token") is None or tokens.get("refresh_token") is None:
            raise InvalidAuthorizationCode

        return tokens

    async def refresh_access_token(self, refresh_token: str) -> dict:
        tokens = await self._request_post_to(
            url=f"{self._authentication_uri}/token",
            payload={
                "client_id": self._client_id,
                "client_secret": self._client_secret_id,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )

        if tokens is None:
            raise InvalidToken
        return tokens

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
            "email": raw_user_info["kakao_account"]["email"],
            "id": raw_user_info["id"],
            "mobile": raw_user_info.get("mobile", ""),
            "name": raw_user_info.get("name"),
            "profile_image": raw_user_info.get("profile_image"),
            "age": raw_user_info.get("age"),
            "birthday": raw_user_info.get("birthday"),
            "gender": raw_user_info.get("gender"),
        }
    elif provider == SocialProviderEnum.naver:
        user_info = raw_user_info["response"]
        return {
            "email": user_info["email"],
            "id": user_info["id"],
            "mobile": user_info.get("mobile", ""),
            "name": user_info.get("name"),
            "profile_image": user_info.get("profile_image"),
            "age": user_info.get("age"),
            "birthday": user_info.get("birthday"),
            "gender": user_info.get("gender"),
        }
    else:
        raise ValueError(f"Unsupported provider: {provider}")


naver_client = OAuthClient(
    client_id=settings.NAVER_CLIENT_ID,
    client_secret_id=settings.NAVER_CLIENT_SECRET_ID,
    authentication_uri="https://nid.naver.com/oauth2.0",
    resource_uri="https://openapi.naver.com/v1/nid/me",
    verify_uri="https://openapi.naver.com/v1/nid/verify",
)

kakao_client = OAuthClient(
    client_id=settings.KAKAO_CLIENT_ID,
    client_secret_id=settings.KAKAO_CLIENT_SECRET_ID,
    authentication_uri="https://kauth.kakao.com/oauth",
    resource_uri="https://kapi.kakao.com/v2/user/me",
    verify_uri="https://kapi.kakao.com/v1/user/access_token_info",
)
