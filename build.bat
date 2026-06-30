@echo off
REM Build Hearsay with PyInstaller (onedir mode)
REM Run from the project root: build.bat
REM
REM This produces a CPU-capable build. The app detects an NVIDIA GPU at runtime
REM via nvidia-smi + CTranslate2 (no PyTorch). For a GPU-accelerated EXE, first
REM   pip install -r requirements-gpu.txt
REM then add the CUDA libraries to the bundle by appending these flags below:
REM   --collect-all "nvidia" ^
REM (the nvidia-cublas-cu12 / nvidia-cudnn-cu12 wheels must be installed first).

echo Building Hearsay...

pyinstaller --noconfirm --onedir --windowed ^
    --name "Hearsay" ^
    --icon "src\assets\icon.ico" ^
    --add-data "src\assets;assets" ^
    --hidden-import "faster_whisper" ^
    --hidden-import "ctranslate2" ^
    --hidden-import "pyaudiowpatch" ^
    --hidden-import "sounddevice" ^
    --hidden-import "customtkinter" ^
    --hidden-import "pystray" ^
    --collect-all "customtkinter" ^
    --collect-all "faster_whisper" ^
    --collect-all "ctranslate2" ^
    src\hearsay\__main__.py

echo.
if %ERRORLEVEL% EQU 0 (
    echo Build succeeded! Output in dist\Hearsay\
) else (
    echo Build FAILED.
)
