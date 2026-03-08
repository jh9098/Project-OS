# Project OS Backend (FastAPI)

## 1) 설치
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## 2) 환경변수
`.env.example`를 복사해서 `.env` 생성

```bash
# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env
```

## 3) 실행
```bash
uvicorn app.main:app --reload
```

## 4) 접속
- Swagger: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## 5) 기본 관리자
- username: admin
- password: admin1234

## 6) 샘플 데이터 입력
```bash
python seed_sample_data.py
```
