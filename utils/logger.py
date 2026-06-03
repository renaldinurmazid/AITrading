import logging
import colorlog
from pathlib import Path

def setup_logger(log_file: str = "logs/ea_trading.log") -> logging.Logger:
    # Ensure logs folder exists in the current workspace directory
    Path("logs").mkdir(exist_ok=True)

    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s]%(reset)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG":    "cyan",
            "INFO":     "green",
            "WARNING":  "yellow",
            "ERROR":    "red",
            "CRITICAL": "bold_red",
        }
    )

    handler_console = colorlog.StreamHandler()
    handler_console.setFormatter(formatter)

    handler_file = logging.FileHandler(log_file, encoding="utf-8")
    handler_file.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s"
    ))

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup_logger is called multiple times
    if not logger.handlers:
        logger.addHandler(handler_console)
        logger.addHandler(handler_file)
        
    return logger
