@echo off
setlocal
echo ==================================================
echo    MOTION WEAVE - PRODUCTION DEPLOYMENT (WIN)
echo ==================================================

:: 1. Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed or not in PATH.
    echo    Please install Docker Desktop for Windows.
    pause
    exit /b 1
)

:: 2. Setup Directories
if not exist "models_cache" mkdir models_cache
if not exist "backend\outputs" mkdir backend\outputs
if not exist "backend\uploads" mkdir backend\uploads

:: 3. Build & Launch
echo [3/4] Building Containers...
docker-compose down
docker-compose up --build -d

:: 4. Validation
echo [4/4] Validating...
timeout /t 10 /nobreak
for /f "tokens=*" %%i in ('docker ps -qf "name=motion_weave_api"') do set CONTAINER_ID=%%i

if "%CONTAINER_ID%"=="" (
    echo ❌ API Container not running. Check logs: docker-compose logs api
    pause
    exit /b 1
)

echo Running Health Check...
docker exec %CONTAINER_ID% python scripts/health_check.py

echo ==================================================
echo ✅ DEPLOYMENT COMPLETE
echo    UI Studio: http://localhost:3000
echo ==================================================
pause
