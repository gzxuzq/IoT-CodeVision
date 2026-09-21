@echo off
chcp 65001 >nul
echo 码视野 IoT 官网 - 博文更新工具
echo =====================================
echo.
echo [1] 手动运行一次更新（生成新博文+编译+推送）
echo [2] 只编译静态页（不生成新文章）
echo [3] 查看当前文章数量
echo [4] 退出
echo.
set /p choice=请选择操作 (1/2/3/4): 

if "%choice%"=="1" (
  echo.
  echo 正在运行 Agnes AI 自动更新...
  python auto_update_iot.py
  pause
) else if "%choice%"=="2" (
  echo.
  echo 正在编译静态页...
  python build_static_posts.py
  pause
) else if "%choice%"=="3" (
  echo.
  python -c "import json; posts=json.load(open('posts_index.json','r',encoding='utf-8')); print(f'当前共 {len(posts)} 篇文章'); [print(f'  {p[\"date\"]} - {p[\"title\"][:50]}') for p in posts[:10]]"
  pause
) else (
  exit
)
