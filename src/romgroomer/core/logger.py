"""Core logging infrastructure with Rich formatting and comprehensive file logging."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)
from rich.theme import Theme


class RomGroomerLogger:
    """
    Enterprise-grade logging system with Rich console output and detailed file logging.
    
    Features:
    - Beautiful console output with color and formatting
    - Detailed file logging with rotation
    - Progress bars for long operations
    - Structured logging with context
    - Performance metrics
    """

    # Custom theme for ROM Groomer
    THEME = Theme({
        "info": "cyan",
        "warning": "yellow",
        "error": "red bold",
        "success": "green bold",
        "highlight": "magenta",
        "path": "blue",
        "region": "yellow",
        "language": "cyan",
        "hash": "dim",
    })

    def __init__(
        self,
        name: str = "romgroomer",
        log_dir: Optional[Path] = None,
        level: int = logging.INFO,
        enable_file_logging: bool = True,
    ):
        """
        Initialize the logger.
        
        Args:
            name: Logger name
            log_dir: Directory for log files (default: ~/.local/share/romgroomer/logs)
            level: Logging level
            enable_file_logging: Enable file logging
        """
        self.name = name
        self.level = level
        self.console = Console(theme=self.THEME)
        
        # Setup log directory
        if log_dir is None:
            log_dir = Path.home() / ".local" / "share" / "romgroomer" / "logs"
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Python logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers.clear()
        
        # Console handler with Rich formatting
        console_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
        )
        console_handler.setLevel(level)
        self.logger.addHandler(console_handler)
        
        # File handler with detailed formatting
        if enable_file_logging:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = self.log_dir / f"romgroomer_{timestamp}.log"
            
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)  # Always log everything to file
            
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            self.info(f"Log file: [path]{log_file}[/path]")
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self.logger.error(message, extra=kwargs)
    
    def success(self, message: str, **kwargs: Any) -> None:
        """Log success message with green styling."""
        self.console.print(f"[success]✓[/success] {message}")
        self.logger.info(f"SUCCESS: {message}", extra=kwargs)
    
    def section(self, title: str) -> None:
        """Print a section header."""
        self.console.rule(f"[bold]{title}[/bold]", style="info")
        self.logger.info(f"=== {title} ===")
    
    def progress(
        self,
        description: str = "Processing...",
        total: Optional[int] = None,
    ) -> Progress:
        """
        Create a progress bar for long operations.
        
        Args:
            description: Progress bar description
            total: Total number of items (None for indeterminate)
            
        Returns:
            Rich Progress instance
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console,
            transient=False,
        )
    
    def print_table(self, *args: Any, **kwargs: Any) -> None:
        """Print a Rich table."""
        self.console.print(*args, **kwargs)
    
    def print_tree(self, *args: Any, **kwargs: Any) -> None:
        """Print a Rich tree."""
        self.console.print(*args, **kwargs)
    
    def exception(self, message: str, exc_info: bool = True) -> None:
        """Log exception with full traceback."""
        self.logger.exception(message, exc_info=exc_info)
        self.console.print_exception(show_locals=True)


# Global logger instance
_global_logger: Optional[RomGroomerLogger] = None


def get_logger(
    name: str = "romgroomer",
    log_dir: Optional[Path] = None,
    level: int = logging.INFO,
) -> RomGroomerLogger:
    """
    Get or create the global logger instance.
    
    Args:
        name: Logger name
        log_dir: Directory for log files
        level: Logging level
        
    Returns:
        RomGroomerLogger instance
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = RomGroomerLogger(name=name, log_dir=log_dir, level=level)
    
    return _global_logger
