import paramiko
from HardwareTester.utils.custom_logger import CustomLogger

# Initialize logger
logger = CustomLogger.get_logger("ssh_service")


class SSHService:
    def __init__(self, device_id, host=None, port=22):
        """
        Initialize the SSH service with a device ID and optional host and port.
        """
        self.device_id = device_id
        self.host = host or self.get_device_host(device_id)
        self.port = port
        self.ssh_client = None

    def get_device_host(self, device_id):
        """
        Retrieve the device host from the database or configuration.
        """
        # Replace this with your actual database or configuration logic
        logger.info(f"Fetching host for device {device_id}")
        return "192.168.1.100"  # Mocked host address

    def connect(self, username, password):
        """
        Establish an SSH connection.
        """
        try:
            logger.info(f"Establishing SSH connection to {self.host}:{self.port} for device {self.device_id}")
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(
                hostname=self.host,
                port=self.port,
                username=username,
                password=password,
                timeout=10
            )
            logger.info(f"SSH connection established to {self.host} for device {self.device_id}")
            return True
        except paramiko.AuthenticationException as e:
            logger.error(f"Authentication failed for device {self.device_id}: {e}")
            return False
        except paramiko.SSHException as e:
            logger.error(f"SSH error for device {self.device_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error connecting to device {self.device_id}: {e}")
            return False

    def execute_command(self, command):
        """
        Execute a command on the remote device.
        """
        if not self.ssh_client:
            raise ConnectionError("SSH connection not established.")

        try:
            logger.info(f"Executing command on {self.device_id}: {command}")
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            output = stdout.read().decode("utf-8").strip()
            error = stderr.read().decode("utf-8").strip()

            if error:
                logger.warning(f"Command error on {self.device_id}: {error}")
                return {"success": False, "error": error}

            logger.info(f"Command executed successfully on {self.device_id}: {output}")
            return {"success": True, "output": output}
        except Exception as e:
            logger.error(f"Error executing command on {self.device_id}: {e}")
            return {"success": False, "error": str(e)}

    def disconnect(self):
        """
        Close the SSH connection.
        """
        if self.ssh_client:
            self.ssh_client.close()
            logger.info(f"SSH connection to {self.host} closed for device {self.device_id}")
            self.ssh_client = None
        else:
            logger.warning(f"No SSH connection to close for device {self.device_id}")

    def __del__(self):
        """
        Ensure the SSH connection is closed when the object is deleted.
        """
        self.disconnect()

