@echo off
echo Updating all Python libraries in the current environment...

:: Step 1: Get a list of outdated libraries and save the names to a temporary file
pip list --outdated --format=columns | findstr /v "Package Version" > outdated.txt

:: Step 2: Update each library
for /f "tokens=1" %%i in (outdated.txt) do (
    echo Updating %%i...
    pip install --upgrade %%i
)

:: Step 3: Clean up temporary files
echo Cleaning up temporary files...
del outdated.txt

:: Step 4: Completion message
echo Update complete. Press any key to exit.
pause >nul
