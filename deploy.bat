@echo off
chcp 65001
echo HealthWise AI 백엔드 Railway 배포 스크립트
echo ==========================================

REM Railway CLI 설치 확인
where railway >nul 2>nul
if %errorlevel% neq 0 (
    echo Railway CLI를 설치합니다...
    npm install -g @railway/cli
)

echo.
echo Railway에 로그인합니다...
call railway login

echo.
echo 프로젝트에 연결합니다...
call railway link c16068b5-918e-41b1-bb20-3dddf02e80ad

echo.
echo 서비스를 선택합니다 (healthwise-backend)...
call railway service healthwise-backend

echo.
echo 백엔드를 배포합니다...
call railway up

echo.
echo 배포가 완료되었습니다!
echo URL: https://healthwise-backend-production.up.railway.app
pause
