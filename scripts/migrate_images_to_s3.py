# scripts/migrate_images_to_s3.py
import asyncio
import io
from datetime import datetime
from typing import Optional, List, Dict, Any

import aiohttp
import boto3
import psycopg2
from PIL import Image
from botocore.exceptions import ClientError
from psycopg2.extras import RealDictCursor

from core.config import settings

# 설정값들
AWS_S3_BUCKET = "serenade-prod-images"  # S3 버킷명
AWS_REGION = "ap-northeast-2"  # AWS 리전
CLOUDFRONT_DOMAIN = "d8erw6l13w214.cloudfront.net"  # CloudFront 도메인 (배포 후 설정)
USE_CLOUDFRONT = True  # CloudFront 사용 여부
MAX_CONCURRENT_DOWNLOADS = 10  # 동시 다운로드 수
CHUNK_SIZE = 100  # 한 번에 처리할 이미지 수


# PostgreSQL 연결 정보 (환경변수에서 가져오기)
DB_CONFIG = {
    "host": settings.POSTGRES_SERVER,
    "database": settings.POSTGRES_DB,
    "user": settings.POSTGRES_USER,
    "password": settings.POSTGRES_PASSWORD,
    "port": settings.POSTGRES_PORT,
}


class ImageMigrator:
    def __init__(self):
        # S3 클라이언트 초기화
        self.s3_client = boto3.client("s3", region_name=AWS_REGION)
        self.session = None

        # 통계용 변수들
        self.stats = {"total": 0, "success": 0, "failed": 0, "skipped": 0, "errors": []}

    def get_db_connection(self):
        """PostgreSQL 연결"""
        try:
            conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
            return conn
        except Exception as e:
            print(f"❌ 데이터베이스 연결 실패: {e}")
            raise

    def generate_s3_key(
        self,
        image_id: int,
        product_id: int,
        product_venue_id: int = None,
        image_type: str = None,
    ) -> str:
        """S3 키 생성 (경로 구조: product_id/venue_id/image_type_image_id.webp)"""
        # 이미지 타입을 파일명에 포함
        if image_type:
            # 이미지 타입을 안전한 파일명으로 변환
            safe_type = "".join(
                c if c.isalnum() or c in "-_" else "_" for c in image_type
            )
            filename = f"{safe_type}_{image_id}.webp"
        else:
            filename = f"{image_id}.webp"

        # 기본 경로: products/{product_id}
        path_parts = ["products", str(product_id)]

        # venue_id가 있으면 추가
        if product_venue_id:
            path_parts.append(f"venue_{product_venue_id}")
        else:
            path_parts.append("common")  # venue가 없는 공통 이미지

        # 최종 경로 생성
        path_parts.append(filename)
        return "/".join(path_parts)

    def generate_s3_url(self, s3_key: str) -> str:
        """S3 또는 CloudFront URL 생성"""
        if USE_CLOUDFRONT and CLOUDFRONT_DOMAIN:
            return f"https://{CLOUDFRONT_DOMAIN}/{s3_key}"
        else:
            return f"https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"

    async def download_image(
        self, session: aiohttp.ClientSession, url: str
    ) -> Optional[bytes]:
        """이미지 다운로드"""
        try:
            # 타임아웃 설정 (연결 10초, 읽기 30초)
            timeout = aiohttp.ClientTimeout(connect=10, total=30)

            async with session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    print(f"  ⚠️  HTTP {response.status}: {url}")
                    return None

        except asyncio.TimeoutError:
            print(f"  ⏰ 타임아웃: {url}")
            return None
        except Exception as e:
            print(f"  ❌ 다운로드 실패: {url} - {e}")
            return None

    def convert_to_webp(self, image_data: bytes, quality: int = 85) -> Optional[bytes]:
        """이미지를 WebP로 변환"""
        try:
            # PIL로 이미지 열기
            with Image.open(io.BytesIO(image_data)) as img:
                # RGBA를 RGB로 변환 (WebP 호환성을 위해)
                if img.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    if img.mode in ("RGBA", "LA"):
                        background.paste(
                            img, mask=img.split()[-1] if img.mode == "RGBA" else None
                        )
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                # WebP로 변환
                output = io.BytesIO()
                img.save(output, format="WEBP", quality=quality, optimize=True)
                return output.getvalue()

        except Exception as e:
            print(f"  ❌ 이미지 변환 실패: {e}")
            return None

    def upload_to_s3(self, s3_key: str, image_data: bytes) -> bool:
        """S3에 이미지 업로드"""
        try:
            self.s3_client.put_object(
                Bucket=AWS_S3_BUCKET,
                Key=s3_key,
                Body=image_data,
                ContentType="image/webp",
                CacheControl="max-age=31536000",  # 1년 캐시
                Metadata={
                    "uploaded_at": datetime.now().isoformat(),
                    "converted_format": "webp",
                },
            )
            return True

        except ClientError as e:
            print(f"  ❌ S3 업로드 실패: {e}")
            return False
        except Exception as e:
            print(f"  ❌ 업로드 오류: {e}")
            return False

    def update_image_url_in_db(self, image_id: int, new_url: str):
        """데이터베이스의 이미지 URL 업데이트"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            update_query = """
                UPDATE product_images 
                SET image_url = %s, updated_datetime = %s 
                WHERE id = %s
            """

            cursor.execute(update_query, (new_url, datetime.now(), image_id))
            conn.commit()

            cursor.close()
            conn.close()
            return True

        except Exception as e:
            print(f"  ❌ DB 업데이트 실패: {e}")
            return False

    async def process_image(
        self, session: aiohttp.ClientSession, image_record: Dict[str, Any]
    ) -> bool:
        """단일 이미지 처리"""
        image_id = image_record["id"]
        product_id = image_record["product_id"]
        product_venue_id = image_record.get("product_venue_id")
        original_url = image_record["image_url"]
        image_type = image_record.get("image_type", "general")

        print(
            f"  📥 처리 중: ID={image_id}, Product={product_id}, Venue={product_venue_id}, Type={image_type}"
        )
        print(f"      원본: {original_url}")

        # S3 키 생성
        s3_key = self.generate_s3_key(
            image_id, product_id, product_venue_id, image_type
        )
        s3_url = self.generate_s3_url(s3_key)

        print(f"      저장 경로: {s3_key}")

        # S3에 이미 존재하는지 확인
        try:
            self.s3_client.head_object(Bucket=AWS_S3_BUCKET, Key=s3_key)
            print(f"  ⚠️  이미 존재함, 스킵: {s3_key}")

            # DB URL만 업데이트
            if self.update_image_url_in_db(image_id, s3_url):
                self.stats["skipped"] += 1
                return True
            else:
                self.stats["failed"] += 1
                return False

        except ClientError:
            # 파일이 존재하지 않음, 계속 진행
            pass

        # 1. 이미지 다운로드
        image_data = await self.download_image(session, original_url)
        if not image_data:
            self.stats["failed"] += 1
            self.stats["errors"].append(
                f"다운로드 실패: ID={image_id}, URL={original_url}"
            )
            return False

        # 2. WebP로 변환
        webp_data = self.convert_to_webp(image_data)
        if not webp_data:
            self.stats["failed"] += 1
            self.stats["errors"].append(f"변환 실패: ID={image_id}")
            return False

        # 3. S3 업로드
        if not self.upload_to_s3(s3_key, webp_data):
            self.stats["failed"] += 1
            self.stats["errors"].append(f"S3 업로드 실패: ID={image_id}, Key={s3_key}")
            return False

        # 4. DB URL 업데이트
        if not self.update_image_url_in_db(image_id, s3_url):
            self.stats["failed"] += 1
            self.stats["errors"].append(f"DB 업데이트 실패: ID={image_id}")
            return False

        print(f"  ✅ 완료: {s3_url}")
        self.stats["success"] += 1
        return True

    async def process_image_batch(self, image_records: List[Dict[str, Any]]):
        """이미지 배치 처리"""
        connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT_DOWNLOADS)
        timeout = aiohttp.ClientTimeout(total=60)

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            # 세마포어로 동시 다운로드 수 제한
            semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

            async def process_with_semaphore(image_record):
                async with semaphore:
                    return await self.process_image(session, image_record)

            # 모든 이미지 병렬 처리
            tasks = [process_with_semaphore(record) for record in image_records]
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_image_records(
        self, offset: int = 0, limit: int = CHUNK_SIZE
    ) -> List[Dict[str, Any]]:
        """DB에서 이미지 레코드 조회"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, image_url, image_type, product_id, product_venue_id
            FROM product_images 
            WHERE is_deleted = false 
            AND image_url IS NOT NULL 
            AND image_url != ''
            ORDER BY product_id, product_venue_id, image_type, id
            LIMIT %s OFFSET %s
        """

        cursor.execute(query, (limit, offset))
        records = cursor.fetchall()

        cursor.close()
        conn.close()

        return [dict(record) for record in records]

    def get_total_count(self) -> int:
        """전체 이미지 수 조회"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT COUNT(*) as total
            FROM product_images 
            WHERE is_deleted = false 
            AND image_url IS NOT NULL 
            AND image_url != ''
        """

        cursor.execute(query)
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        return result["total"]

    async def run_migration(self):
        """마이그레이션 실행"""
        print("🚀 이미지 마이그레이션 시작")
        print(f"📊 대상 버킷: {AWS_S3_BUCKET}")
        print(f"🔧 설정: 동시처리={MAX_CONCURRENT_DOWNLOADS}, 배치크기={CHUNK_SIZE}")

        # 전체 이미지 수 확인
        total_count = self.get_total_count()
        self.stats["total"] = total_count

        print(f"📈 총 처리 대상: {total_count}개 이미지")

        if total_count == 0:
            print("❌ 처리할 이미지가 없습니다.")
            return

        # 배치 단위로 처리
        offset = 0
        batch_num = 1

        while offset < total_count:
            print(f"\n📦 배치 {batch_num} 처리 중 (오프셋: {offset})")

            # 배치 데이터 조회
            image_records = self.get_image_records(offset, CHUNK_SIZE)

            if not image_records:
                break

            # 배치 처리
            await self.process_image_batch(image_records)

            # 진행률 출력
            processed = min(offset + CHUNK_SIZE, total_count)
            progress = (processed / total_count) * 100
            print(f"📊 진행률: {processed}/{total_count} ({progress:.1f}%)")

            offset += CHUNK_SIZE
            batch_num += 1

        # 최종 결과 출력
        self.print_final_stats()

    def print_final_stats(self):
        """최종 통계 출력"""
        print("\n" + "=" * 60)
        print("🎉 마이그레이션 완료!")
        print("=" * 60)
        print(f"📊 총 처리 대상: {self.stats['total']}개")
        print(f"✅ 성공: {self.stats['success']}개")
        print(f"⚠️  스킵: {self.stats['skipped']}개")
        print(f"❌ 실패: {self.stats['failed']}개")

        if self.stats["errors"]:
            print(f"\n❌ 오류 목록 (최대 10개):")
            for error in self.stats["errors"][:10]:
                print(f"  - {error}")

            if len(self.stats["errors"]) > 10:
                print(f"  ... 외 {len(self.stats['errors']) - 10}개 더")

        success_rate = (
            (self.stats["success"] / self.stats["total"]) * 100
            if self.stats["total"] > 0
            else 0
        )
        print(f"\n📈 성공률: {success_rate:.1f}%")


async def main():
    """메인 함수"""
    try:
        migrator = ImageMigrator()
        await migrator.run_migration()

    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n❌ 마이그레이션 실패: {e}")
        raise


if __name__ == "__main__":
    # 스크립트 실행
    asyncio.run(main())
