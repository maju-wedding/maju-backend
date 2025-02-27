# Python 베이스 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# Poetry 설치
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:${PATH}"


# Poetry 설정: 가상환경 생성하지 않기
RUN poetry config virtualenvs.create false
# 의존성 파일 복사 및 설치
RUN poetry install --no-interaction --no-ansi

# 스크립트에 실행 권한 부여
RUN chmod +x /app/scripts/prestart.sh

# 필요한 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 포트 노출
EXPOSE 8000

ENV ENVIRONMENT=production

# prestart.sh 스크립트 실행 후 FastAPI 실행
CMD ["/bin/bash", "-c", "/app/scripts/prestart.sh && poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000"]