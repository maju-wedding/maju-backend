import pytest
from unittest.mock import patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import UserTypeEnum
from models.users import User


class TestUserRegistration:
    @pytest.mark.asyncio
    async def test_register_success(self, async_client: AsyncClient):
        """새로운 사용자 등록 성공 테스트"""
        user_data = {
            "email": "new_user@example.com",
            "password": "securepassword",
            "nickname": "New User",
            "phone_number": "01098765432",
        }

        response = await async_client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["nickname"] == "New User"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self, async_client: AsyncClient, test_user: User
    ):
        """중복된 이메일로 등록 시도 시 실패 테스트"""
        user_data = {
            "email": "test@example.com",  # 이미 존재하는 이메일
            "password": "securepassword",
            "nickname": "Duplicate User",
            "phone_number": "01011112222",
        }

        response = await async_client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_duplicate_phone(
        self, async_client: AsyncClient, test_user: User
    ):
        """중복된 전화번호로 등록 시도 시 실패 테스트"""
        user_data = {
            "email": "unique@example.com",
            "password": "securepassword",
            "nickname": "Phone Duplicate",
            "phone_number": "01012345678",  # 이미 존재하는 전화번호
        }

        response = await async_client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400
        assert "Phone number already registered" in response.json()["detail"]


class TestUserLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, async_client: AsyncClient, test_user: User):
        """유효한 인증 정보로 로그인 성공 테스트"""
        login_data = {"username": "test@example.com", "password": "testpassword"}

        response = await async_client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["nickname"] == "테스트유저"

    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self, async_client: AsyncClient, test_user: User
    ):
        """잘못된 비밀번호로 로그인 실패 테스트"""
        login_data = {"username": "test@example.com", "password": "wrongpassword"}

        response = await async_client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """존재하지 않는 사용자로 로그인 실패 테스트"""
        login_data = {"username": "nonexistent@example.com", "password": "anypassword"}

        response = await async_client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_social_user_with_password(
        self,
        async_client: AsyncClient,
        test_social_user: User,
        db_session: AsyncSession,
    ):
        """소셜 로그인 사용자가 일반 로그인 시도 시 실패 테스트"""
        login_data = {"username": "social@example.com", "password": "anypassword"}

        response = await async_client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 401
        assert "Please login with social provider" in response.json()["detail"]


class TestSocialLogin:
    @pytest.mark.asyncio
    @patch("core.oauth_client.OAuthClient.get_tokens")
    @patch("core.oauth_client.OAuthClient.get_user_info")
    async def test_social_login_new_user(
        self, mock_get_user_info, mock_get_tokens, async_client: AsyncClient
    ):
        """소셜 로그인 - 새로운 사용자 테스트"""
        # Mock setup
        mock_get_tokens.return_value = {"access_token": "dummy_token"}
        mock_get_user_info.return_value = {
            "id": 12345,
            "kakao_account": {
                "email": "new_social@example.com",
                "profile": {"nickname": "New Social User"},
                "has_phone_number": True,
                "phone_number": "+82 10-9876-5432",
            },
        }

        login_data = {
            "code": "authorization_code",
            "state": "random_state",
            "provider": "kakao",
        }

        response = await async_client.post("/api/v1/auth/social-login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    @patch("core.oauth_client.OAuthClient.get_tokens")
    @patch("core.oauth_client.OAuthClient.get_user_info")
    async def test_social_login_existing_user(
        self,
        mock_get_user_info,
        mock_get_tokens,
        async_client: AsyncClient,
        test_social_user: User,
    ):
        """소셜 로그인 - 기존 사용자 테스트"""
        # Mock setup
        mock_get_tokens.return_value = {"access_token": "dummy_token"}
        mock_get_user_info.return_value = {
            "id": 12345,
            "kakao_account": {
                "email": "social@example.com",  # 기존 소셜 사용자 이메일
                "profile": {"nickname": "소셜유저"},
                "has_phone_number": True,
                "phone_number": "+82 10-8765-4321",
            },
        }

        login_data = {
            "code": "authorization_code",
            "state": "random_state",
            "provider": "kakao",
        }

        response = await async_client.post("/api/v1/auth/social-login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["nickname"] == "소셜유저"

    @pytest.mark.asyncio
    @patch(
        "core.oauth_client.OAuthClient.get_tokens",
        side_effect=Exception("Invalid authorization code"),
    )
    async def test_social_login_invalid_code(
        self, mock_get_tokens, async_client: AsyncClient
    ):
        """소셜 로그인 - 잘못된 인증 코드 테스트"""
        login_data = {
            "code": "invalid_code",
            "state": "random_state",
            "provider": "kakao",
        }

        response = await async_client.post("/api/v1/auth/social-login", json=login_data)

        assert response.status_code == 400
        assert "Invalid authorization code" in response.json()["detail"]


class TestGuestLogin:
    @pytest.mark.asyncio
    async def test_guest_login_success(self, async_client: AsyncClient):
        """게스트 로그인 성공 테스트"""
        response = await async_client.post("/api/v1/auth/guest-login")

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["nickname"] is not None  # 닉네임이 생성되었는지 확인


class TestUserManagement:
    @pytest.mark.asyncio
    async def test_get_user_profile(
        self, authorized_client: AsyncClient, test_user: User
    ):
        """인증된 사용자 프로필 조회 테스트"""
        response = await authorized_client.get("/api/v1/users/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["nickname"] == "테스트유저"
        assert data["user_type"] == "local"

    @pytest.mark.asyncio
    async def test_get_profile_unauthorized(self, async_client: AsyncClient):
        """인증되지 않은 사용자의 프로필 조회 실패 테스트"""
        response = await async_client.get("/api/v1/users/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_user_profile(
        self, authorized_client: AsyncClient, test_user: User
    ):
        """사용자 프로필 업데이트 테스트"""
        update_data = {
            "nickname": "Updated User",
            "service_policy_agreement": True,
            "privacy_policy_agreement": True,
            "third_party_information_agreement": True,
        }

        response = await authorized_client.patch("/api/v1/users/me", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["nickname"] == "Updated User"

        # 변경사항이 데이터베이스에 반영되었는지 확인
        response = await authorized_client.get("/api/v1/users/me")
        data = response.json()
        assert data["nickname"] == "Updated User"

    @pytest.mark.asyncio
    async def test_delete_user_account(
        self,
        authorized_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """사용자 계정 삭제 테스트"""
        response = await authorized_client.delete("/api/v1/users/me")

        assert response.status_code == 200

        # 사용자가 DB에서 삭제되었거나 비활성화되었는지 확인
        user = await db_session.get(User, test_user.id)
        if user:
            assert user.is_deleted == True
            assert user.is_active == False
            assert user.deleted_datetime is not None


class TestTokenValidation:
    @pytest.mark.asyncio
    async def test_valid_token(self, authorized_client: AsyncClient):
        """유효한 토큰으로 보호된 엔드포인트 접근 테스트"""
        response = await authorized_client.get("/api/v1/users/me")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_expired_token(self, async_client: AsyncClient, test_user: User):
        """만료된 토큰으로 보호된 엔드포인트 접근 실패 테스트"""
        from core.security import create_access_token
        from datetime import timedelta

        # 이미 만료된 토큰 생성
        expired_token = create_access_token(
            subject=test_user.email,
            expires_delta=timedelta(seconds=-1),
            user_type=UserTypeEnum.local,
        )

        async_client.headers = {"Authorization": f"Bearer {expired_token}"}
        response = await async_client.get("/api/v1/users/me")

        assert response.status_code == 401
        assert "Token has expired" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_token_format(self, async_client: AsyncClient):
        """잘못된 형식의 토큰으로 보호된 엔드포인트 접근 실패 테스트"""
        async_client.headers = {"Authorization": "Bearer invalidtoken"}
        response = await async_client.get("/api/v1/users/me")

        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]
