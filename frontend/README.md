# Project OS Frontend

Next.js 15 + TypeScript + Tailwind CSS + React Query 기반 프론트엔드입니다.

## 1. 설치

```bash
npm install
npm run dev
```

## 2. 실행 모드

현재는 **완전 로컬 모드**입니다.

- 외부 서버(Render 포함)로 API 요청을 보내지 않습니다.
- 프로젝트/작업/관계/노트 데이터는 브라우저 `localStorage`에 저장됩니다.
- 데이터 키: `project_os_local_db`

## 3. 로그인/인증

- 인증 토큰/사용자 정보도 `localStorage`에 저장됩니다.
- 네트워크 로그인 API 호출 없이 화면 동작이 가능합니다.

## 4. 화면

- `/login`
- `/dashboard`
- `/projects`
- `/tasks`
- `/relations`
- `/notes`
- `/settings`

## 5. 특징

- 완전 로컬 CRUD
- 페이지 새로고침 후에도 로컬 데이터 유지
- React Query 캐시 무효화로 화면 자동 갱신
