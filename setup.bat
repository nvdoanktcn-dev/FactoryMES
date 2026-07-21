@echo off
cd /d D:\FactoryMES

echo Creating virtual environment...

python -m venv .venv

call .venv\Scripts\activate

echo Installing libraries...

python -m pip install --upgrade pip

pip install PySide6 SQLAlchemy pandas openpyxl matplotlib

pip freeze > requirements.txt

echo Setup completed.

pause