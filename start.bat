@echo off
echo Setting Flet mirror to Tsinghua...
set FLET_PYPI_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple
set FLET_STORAGE_DIR=%USERPROFILE%\.flet

echo Starting Local Data Dual-Mode Workbench...
flet run main.py