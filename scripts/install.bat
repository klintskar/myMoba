@echo off
echo Creating virtual environment...
python -m venv myMoba

echo Activating virtual environment...
call myMoba\Scripts\activate.bat

echo Installing requirements...
pip install -r requirements.txt

echo Done!
pause
