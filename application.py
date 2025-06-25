# Elastic Beanstalk는 기본적으로 application.py에서 application 변수를 찾습니다.

from src.main import app

# Elastic Beanstalk가 인식할 수 있도록 application 변수로 export
application = app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(application, host="0.0.0.0", port=8000)
