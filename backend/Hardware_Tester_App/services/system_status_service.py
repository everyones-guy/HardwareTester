import os
import psutil
import platform
from datetime import datetime
from Hardware_Tester_App.utils.custom_logger import CustomLogger

# Initialize logger
logger = CustomLogger.get_logger("system_status_service")


class SystemStatusService:
    @staticmethod
    def get_system_info() -> dict:
        """
        Retrieve basic system information.
        :return: Dictionary containing system info.
        """
        try:
            system_info = {
                "os": platform.system(),
                "os_version": platform.version(),
                "os_release": platform.release(),
                "hostname": platform.node(),
                "architecture": platform.architecture()[0],
                "processor": platform.processor(),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
            }
            logger.info("Retrieved system information successfully.")
            return {"success": True, "system_info": system_info}
        except Exception as e:
            logger.error(f"Failed to retrieve system information: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_memory_status() -> dict:
        """
        Retrieve memory usage details.
        :return: Dictionary containing memory status.
        """
        try:
            memory = psutil.virtual_memory()
            memory_status = {
                "total": SystemStatusService.convert_bytes(memory.total),
                "available": SystemStatusService.convert_bytes(memory.available),
                "used": SystemStatusService.convert_bytes(memory.used),
                "percent": f"{memory.percent}%",
            }
            logger.info("Retrieved memory status successfully.")
            return {"success": True, "memory_status": memory_status}
        except Exception as e:
            logger.error(f"Failed to retrieve memory status: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_cpu_status() -> dict:
        """
        Retrieve CPU usage details.
        :return: Dictionary containing CPU status.
        """
        try:
            cpu_status = {
                "cores": psutil.cpu_count(logical=False),
                "logical_cores": psutil.cpu_count(logical=True),
                "usage_percent": f"{psutil.cpu_percent(interval=1)}%",
            }
            logger.info("Retrieved CPU status successfully.")
            return {"success": True, "cpu_status": cpu_status}
        except Exception as e:
            logger.error(f"Failed to retrieve CPU status: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_disk_status() -> dict:
        """
        Retrieve disk usage details.
        :return: Dictionary containing disk status.
        """
        try:
            partitions = psutil.disk_partitions()
            disk_status = []
            for partition in partitions:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_status.append({
                    "device": partition.device,
                    "mount_point": partition.mountpoint,
                    "file_system": partition.fstype,
                    "total": SystemStatusService.convert_bytes(usage.total),
                    "used": SystemStatusService.convert_bytes(usage.used),
                    "free": SystemStatusService.convert_bytes(usage.free),
                    "percent": f"{usage.percent}%",
                })
            logger.info("Retrieved disk status successfully.")
            return {"success": True, "disk_status": disk_status}
        except Exception as e:
            logger.error(f"Failed to retrieve disk status: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_network_status() -> dict:
        """
        Retrieve network usage details.
        :return: Dictionary containing network status.
        """
        try:
            net_io = psutil.net_io_counters()
            network_status = {
                "bytes_sent": SystemStatusService.convert_bytes(net_io.bytes_sent),
                "bytes_received": SystemStatusService.convert_bytes(net_io.bytes_recv),
                "packets_sent": net_io.packets_sent,
                "packets_received": net_io.packets_recv,
                "errors_in": net_io.errin,
                "errors_out": net_io.errout,
                "dropped_in": net_io.dropin,
                "dropped_out": net_io.dropout,
            }
            logger.info("Retrieved network status successfully.")
            return {"success": True, "network_status": network_status}
        except Exception as e:
            logger.error(f"Failed to retrieve network status: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def convert_bytes(size: int) -> str:
        """
        Convert bytes to a human-readable format.
        :param size: Size in bytes.
        :return: Human-readable size.
        """
        try:
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024:
                    return f"{size:.2f} {unit}"
                size /= 1024
        except Exception as e:
            logger.error(f"Error converting bytes: {e}")
        return "Unknown"

    @staticmethod
    def get_full_system_status() -> dict:
        """
        Retrieve a full system status report.
        :return: Dictionary containing all system status information.
        """
        try:
            status = {
                "system_info": SystemStatusService.get_system_info(),
                "cpu_status": SystemStatusService.get_cpu_status(),
                "memory_status": SystemStatusService.get_memory_status(),
                "disk_status": SystemStatusService.get_disk_status(),
                "network_status": SystemStatusService.get_network_status(),
            }
            logger.info("Retrieved full system status successfully.")
            return {"success": True, "status": status}
        except Exception as e:
            logger.error(f"Failed to retrieve full system status: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_detailed_metrics() -> dict:
        """
        Fetch detailed metrics for system monitoring.
        :return: Dictionary containing detailed system metrics.
        """
        try:
            metrics = {
                "cpu_count": psutil.cpu_count(logical=True),
                "cpu_freq": psutil.cpu_freq()._asdict(),
                "memory": {
                    "total": SystemStatusService.convert_bytes(psutil.virtual_memory().total),
                    "available": SystemStatusService.convert_bytes(psutil.virtual_memory().available),
                    "used": SystemStatusService.convert_bytes(psutil.virtual_memory().used),
                    "percent": f"{psutil.virtual_memory().percent}%",
                },
                "disk_partitions": [
                    {
                        "device": p.device,
                        "mountpoint": p.mountpoint,
                        "fstype": p.fstype,
                        "usage": {
                            "total": SystemStatusService.convert_bytes(psutil.disk_usage(p.mountpoint).total),
                            "used": SystemStatusService.convert_bytes(psutil.disk_usage(p.mountpoint).used),
                            "free": SystemStatusService.convert_bytes(psutil.disk_usage(p.mountpoint).free),
                            "percent": f"{psutil.disk_usage(p.mountpoint).percent}%",
                        },
                    }
                    for p in psutil.disk_partitions()
                ],
                "network_io": psutil.net_io_counters()._asdict(),
            }
            logger.info("Retrieved detailed system metrics successfully.")
            return {"success": True, "metrics": metrics}
        except Exception as e:
            logger.error(f"Failed to retrieve detailed metrics: {e}")
            return {"success": False, "error": str(e)}
