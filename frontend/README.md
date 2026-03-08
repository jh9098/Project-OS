# Project OS Frontend

Next.js 15 + TypeScript + Tailwind CSS + React Query 기반 프론트엔드입니다.

## 1. 설치

```bash
npm install
cp .env.example .env.local
npm run dev
```

## 2. 환경변수

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

## 3. 백엔드 연결
백엔드가 먼저 실행 중이어야 합니다.

- Login: `POST /api/v1/auth/login`
- Dashboard: `GET /api/v1/dashboard/summary`
- Projects / Tasks / Relations / Notes API 사용

## 4. 기본 관리자
백엔드 기본값 기준:

- username: `admin`
- password: `admin1234`

## 5. 화면
- `/login`
- `/dashboard`
- `/projects`
- `/tasks`
- `/relations`
- `/notes`
- `/settings`

## 6. 특징
- JWT 토큰 localStorage 저장
- 보호 화면 AuthGuard 처리
- 프로젝트/작업/관계/노트 CRUD 연결
- 프로젝트 상세에서 탭별 관리 가능
