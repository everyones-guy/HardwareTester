
import subprocess

def execute_device(json_file):
    csharp_runner_path = "C:/Path/To/DeviceRunner.exe"

    try:
        result = subprocess.run(
            [csharp_runner_path, json_file],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Device executed successfully:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing device:\n{e.stderr}")
