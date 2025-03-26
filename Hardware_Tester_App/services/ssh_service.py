import paramiko
from HardwareTester.utils.custom_logger import CustomLogger
from HardwareTester.extensions import db
from HardwareTester.models.device_models import Device

# Initialize logger
logger = CustomLogger.get_logger("ssh_service")


class SSHService:
    def __init__(self, device_id, host=None, port=22, username=None, password=None, key_file=None):
        """
        Initialize the SSH service with a device ID and optional host, port, username, password, and key file.
        """
        self.device_id = device_id
        self.host = host or self.get_device_host(device_id)
        self.port = port
        self.username = username
        self.password = password
        self.key_file = key_file
        self.ssh_client = None

    def get_device_host(self, device_id):
        """
        Retrieve the device host from the database or configuration.
        """
        logger.info(f"Fetching host for device {device_id} from database")
        device = db.session.query(Device).filter_by(device_id=device_id).first()
        if device:
            return device.device_metadata.get("ip_address", "192.168.1.100")
        logger.warning(f"Device {device_id} not found in database, using default IP")
        return "192.168.1.100"

    def connect(self):
        """
        Establish an SSH connection using password or key-based authentication.
        """
        try:
            logger.info(f"Establishing SSH connection to {self.host}:{self.port} for device {self.device_id}")
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_params = {
                "hostname": self.host,
                "port": self.port,
                "username": self.username,
                "timeout": 10
            }
            
            if self.key_file:
                connect_params["key_filename"] = self.key_file
            else:
                connect_params["password"] = self.password
            
            self.ssh_client.connect(**connect_params)
            self.ssh_client.get_transport().set_keepalive(30)
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
        if not self.ssh_client or not self.ssh_client.get_transport() or not self.ssh_client.get_transport().is_active():
            logger.warning("SSH connection lost. Attempting to reconnect.")
            if not self.connect():
                return {"success": False, "error": "Reconnection failed."}
        
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

    def __enter__(self):
        """
        Context manager entry point.
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Context manager exit point, ensuring connection closure.
        """
        self.disconnect()

    def __del__(self):
        """
        Ensure the SSH connection is closed when the object is deleted.
        """
        self.disconnect()
