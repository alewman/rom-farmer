"""
Built-in hooks for common ROM processing tasks.

This module provides ready-to-use hooks for:
- Hash calculation and caching
- Transformation tracking to database
- Progress monitoring and metrics
- File validation
"""

import hashlib
import logging
import time
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from .hooks import Hook, HookContext, HookPoint
from ..metadata.database import MetadataDatabase
from ..metadata.transformation import HashCache, ROMTransformation

logger = logging.getLogger(__name__)


class HashCaptureHook(Hook):
    """Capture file hashes before and after transformations.
    
    This hook calculates CRC32, MD5, SHA1 for files at various stages
    and stores them in the HashCache table for fast lookups.
    
    Features:
    - Calculates hashes for input files
    - Calculates hashes for output files
    - Stores in database with file metadata
    - Checks cache first to avoid recalculation
    - Records calculation time for metrics
    
    Example:
        >>> from romgroomer.metadata.database import MetadataDatabase
        >>> 
        >>> db = MetadataDatabase(Path("metadata.db"))
        >>> hook = HashCaptureHook(db, hash_types=['md5', 'sha1'])
        >>> 
        >>> registry.register('hash_capture', hook, priority=10)
    """
    
    def __init__(
        self,
        database: Optional[MetadataDatabase] = None,
        hash_types: Optional[list[str]] = None,
        use_cache: bool = True,
    ):
        """Initialize hash capture hook.
        
        Args:
            database: Database for storing/retrieving hashes
            hash_types: List of hash types to calculate ('crc32', 'md5', 'sha1', 'sha256')
            use_cache: Whether to check cache before calculating
        """
        super().__init__()
        self.database = database
        self.hash_types = hash_types or ['crc32', 'md5', 'sha1']
        self.use_cache = use_cache
    
    async def before_stage(self, context: HookContext) -> None:
        """Calculate hashes for input file before stage processing.
        
        Args:
            context: Hook context with input file path
        """
        if not context.input_path or not context.input_path.is_file():
            return
        
        logger.debug(f"Calculating hashes for input: {context.input_path}")
        
        # Check cache first
        if self.use_cache and self.database:
            cached = await self._get_cached_hash(context.input_path)
            if cached:
                context.set('input_hashes', {
                    'crc32': cached.crc32,
                    'md5': cached.md5,
                    'sha1': cached.sha1,
                    'sha256': cached.sha256,
                })
                context.set('input_hash_source', 'cache')
                logger.debug(f"Using cached hashes for {context.input_path.name}")
                return
        
        # Calculate hashes
        start_time = time.time()
        hashes = await self._calculate_hashes(context.input_path)
        calc_time = time.time() - start_time
        
        context.set('input_hashes', hashes)
        context.set('input_hash_source', 'calculated')
        context.set('input_hash_calc_time', calc_time)
        
        # Store in cache
        if self.database:
            await self._store_in_cache(context.input_path, hashes, calc_time)
    
    async def after_stage(self, context: HookContext) -> None:
        """Calculate hashes for output file after stage processing.
        
        Args:
            context: Hook context with output file path
        """
        if not context.output_path or not context.output_path.is_file():
            return
        
        logger.debug(f"Calculating hashes for output: {context.output_path}")
        
        # Calculate hashes (don't use cache for fresh output)
        start_time = time.time()
        hashes = await self._calculate_hashes(context.output_path)
        calc_time = time.time() - start_time
        
        context.set('output_hashes', hashes)
        context.set('output_hash_calc_time', calc_time)
        
        # Store in cache
        if self.database:
            await self._store_in_cache(context.output_path, hashes, calc_time)
    
    async def _calculate_hashes(self, file_path: Path) -> dict[str, str]:
        """Calculate hashes for a file.
        
        Args:
            file_path: Path to file to hash
            
        Returns:
            Dictionary of hash_type -> hash_value
        """
        hashes = {}
        
        # Prepare hashers
        hashers = {}
        if 'crc32' in self.hash_types:
            hashers['crc32'] = None  # CRC32 calculated separately
        if 'md5' in self.hash_types:
            hashers['md5'] = hashlib.md5()
        if 'sha1' in self.hash_types:
            hashers['sha1'] = hashlib.sha1()
        if 'sha256' in self.hash_types:
            hashers['sha256'] = hashlib.sha256()
        
        # Read file and update hashers
        crc = 0
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(65536)  # 64KB chunks
                if not chunk:
                    break
                
                # Update CRC32
                if 'crc32' in hashers:
                    import zlib
                    crc = zlib.crc32(chunk, crc)
                
                # Update other hashers
                for name, hasher in hashers.items():
                    if hasher:
                        hasher.update(chunk)
        
        # Get hex digests
        if 'crc32' in hashers:
            hashes['crc32'] = f"{crc & 0xffffffff:08x}"
        if 'md5' in hashers:
            hashes['md5'] = hashers['md5'].hexdigest()
        if 'sha1' in hashers:
            hashes['sha1'] = hashers['sha1'].hexdigest()
        if 'sha256' in hashers:
            hashes['sha256'] = hashers['sha256'].hexdigest()
        
        return hashes
    
    async def _get_cached_hash(self, file_path: Path) -> Optional[HashCache]:
        """Get cached hash from database.
        
        Args:
            file_path: File to look up
            
        Returns:
            HashCache entry if found and still valid
        """
        if not self.database:
            return None
        
        stat = file_path.stat()
        
        with self.database.get_session() as session:
            cached = session.query(HashCache).filter(
                HashCache.file_path == str(file_path),
                HashCache.file_size == stat.st_size,
                HashCache.mtime == stat.st_mtime,
            ).first()
            
            return cached
    
    async def _store_in_cache(
        self,
        file_path: Path,
        hashes: dict[str, str],
        calc_time: float
    ) -> None:
        """Store hash in cache database.
        
        Args:
            file_path: File that was hashed
            hashes: Dictionary of calculated hashes
            calc_time: Time taken to calculate (seconds)
        """
        if not self.database:
            return
        
        stat = file_path.stat()
        
        with self.database.get_session() as session:
            # Create or update cache entry
            cached = session.query(HashCache).filter(
                HashCache.file_path == str(file_path)
            ).first()
            
            if cached:
                # Update existing
                cached.file_size = stat.st_size
                cached.mtime = stat.st_mtime
                cached.crc32 = hashes.get('crc32')
                cached.md5 = hashes.get('md5')
                cached.sha1 = hashes.get('sha1')
                cached.sha256 = hashes.get('sha256')
                cached.calculation_time = int(calc_time)
            else:
                # Create new
                cached = HashCache(
                    file_path=str(file_path),
                    file_size=stat.st_size,
                    mtime=stat.st_mtime,
                    crc32=hashes.get('crc32'),
                    md5=hashes.get('md5'),
                    sha1=hashes.get('sha1'),
                    sha256=hashes.get('sha256'),
                    calculation_time=int(calc_time),
                )
                session.add(cached)
            
            session.commit()


class TransformationTrackingHook(Hook):
    """Track ROM transformations in the database.
    
    This hook creates ROMTransformation records for each processing pipeline,
    linking source ROM hashes to transformed file hashes with full metadata.
    
    Features:
    - Records source → final transformations
    - Captures tool name, version, and parameters
    - Links to game metadata if available
    - Records processing duration
    - Enables reverse lookup (final → source)
    
    Example:
        >>> db = MetadataDatabase(Path("metadata.db"))
        >>> hook = TransformationTrackingHook(db)
        >>> 
        >>> registry.register('transformation', hook, priority=20)
    """
    
    def __init__(self, database: MetadataDatabase):
        """Initialize transformation tracking hook.
        
        Args:
            database: Database for storing transformation records
        """
        super().__init__()
        self.database = database
        self.start_time = None
    
    async def before_pipeline(self, context: HookContext) -> None:
        """Record pipeline start time.
        
        Args:
            context: Hook context
        """
        self.start_time = time.time()
        context.set('transformation_start', self.start_time)
    
    async def after_pipeline(self, context: HookContext) -> None:
        """Record transformation in database after successful pipeline.
        
        Args:
            context: Hook context with transformation results
        """
        if not context.output_path:
            return
        
        # Calculate duration
        duration = int(time.time() - self.start_time) if self.start_time else 0
        
        # Get hashes from HashCaptureHook (if present)
        input_hashes = context.get('input_hashes', {})
        output_hashes = context.get('output_hashes', {})
        
        # Get transformation metadata
        transformations = context.pipeline_context.get('transformations', [])
        transformation_tool = ' → '.join(transformations) if transformations else 'unknown'
        
        # Create transformation record
        with self.database.get_session() as session:
            transformation = ROMTransformation(
                source_md5=input_hashes.get('md5'),
                source_sha1=input_hashes.get('sha1'),
                source_sha256=input_hashes.get('sha256'),
                source_crc32=input_hashes.get('crc32'),
                final_md5=output_hashes.get('md5'),
                final_sha1=output_hashes.get('sha1'),
                final_sha256=output_hashes.get('sha256'),
                final_crc32=output_hashes.get('crc32'),
                transformation_tool=transformation_tool,
                transformation_version=None,  # TODO: Get from tools
                transformation_params=None,  # TODO: Capture parameters
                transformation_duration_seconds=duration,
            )
            
            session.add(transformation)
            session.commit()
            
            logger.info(
                f"Recorded transformation: {context.input_path.name} → "
                f"{context.output_path.name} ({duration}s)"
            )


class ProgressMonitorHook(Hook):
    """Monitor and log processing progress.
    
    This hook provides detailed logging and optional callback functions
    for monitoring pipeline progress.
    
    Features:
    - Logs pipeline start/end
    - Logs each stage execution
    - Tracks timing for each stage
    - Optional callbacks for custom progress handling
    - Aggregates metrics for reporting
    
    Example:
        >>> def on_stage_complete(stage_name, duration):
        ...     print(f"Completed {stage_name} in {duration:.2f}s")
        >>> 
        >>> hook = ProgressMonitorHook(on_stage_complete=on_stage_complete)
        >>> registry.register('progress', hook, priority=30)
    """
    
    def __init__(
        self,
        on_pipeline_start: Optional[callable] = None,
        on_pipeline_complete: Optional[callable] = None,
        on_stage_start: Optional[callable] = None,
        on_stage_complete: Optional[callable] = None,
    ):
        """Initialize progress monitor hook.
        
        Args:
            on_pipeline_start: Callback when pipeline starts
            on_pipeline_complete: Callback when pipeline completes
            on_stage_start: Callback when stage starts
            on_stage_complete: Callback when stage completes
        """
        super().__init__()
        self.on_pipeline_start = on_pipeline_start
        self.on_pipeline_complete = on_pipeline_complete
        self.on_stage_start = on_stage_start
        self.on_stage_complete = on_stage_complete
        self.stage_start_times = {}
    
    async def before_pipeline(self, context: HookContext) -> None:
        """Log pipeline start.
        
        Args:
            context: Hook context
        """
        logger.info(f"Starting pipeline: {context.input_path}")
        
        if self.on_pipeline_start:
            self.on_pipeline_start(context.input_path)
    
    async def after_pipeline(self, context: HookContext) -> None:
        """Log pipeline completion.
        
        Args:
            context: Hook context with results
        """
        logger.info(
            f"Pipeline complete: {context.input_path} → {context.output_path} "
            f"({context.duration:.2f}s)"
        )
        
        if self.on_pipeline_complete:
            self.on_pipeline_complete(context.output_path, context.duration)
    
    async def before_stage(self, context: HookContext) -> None:
        """Log stage start and record timing.
        
        Args:
            context: Hook context with stage information
        """
        self.stage_start_times[context.stage_name] = time.time()
        
        logger.debug(f"Stage start: {context.stage_name}")
        
        if self.on_stage_start:
            self.on_stage_start(context.stage_name)
    
    async def after_stage(self, context: HookContext) -> None:
        """Log stage completion with timing.
        
        Args:
            context: Hook context with stage results
        """
        start_time = self.stage_start_times.get(context.stage_name)
        duration = time.time() - start_time if start_time else 0
        
        logger.debug(f"Stage complete: {context.stage_name} ({duration:.2f}s)")
        
        if self.on_stage_complete:
            self.on_stage_complete(context.stage_name, duration)
    
    async def on_error(self, context: HookContext) -> None:
        """Log pipeline errors.
        
        Args:
            context: Hook context with error information
        """
        logger.error(
            f"Pipeline failed: {context.input_path} - {context.error}",
            exc_info=context.error
        )


class ValidationHook(Hook):
    """Validate files before and after processing.
    
    This hook performs various validation checks to ensure file integrity
    and correct processing.
    
    Features:
    - File existence check
    - Format validation
    - Size sanity checks
    - Custom validation functions
    
    Example:
        >>> def validate_size(path):
        ...     return path.stat().st_size > 1024  # At least 1KB
        >>> 
        >>> hook = ValidationHook(custom_validators=[validate_size])
        >>> registry.register('validation', hook, priority=40)
    """
    
    def __init__(
        self,
        min_size: int = 0,
        max_size: Optional[int] = None,
        allowed_extensions: Optional[list[str]] = None,
        custom_validators: Optional[list[callable]] = None,
    ):
        """Initialize validation hook.
        
        Args:
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes (None = no limit)
            allowed_extensions: List of allowed file extensions
            custom_validators: List of custom validation functions
        """
        super().__init__()
        self.min_size = min_size
        self.max_size = max_size
        self.allowed_extensions = allowed_extensions
        self.custom_validators = custom_validators or []
    
    async def validate_input(self, context: HookContext) -> bool:
        """Validate input file.
        
        Args:
            context: Hook context with input file
            
        Returns:
            True if validation passed
        """
        if not context.input_path or not context.input_path.exists():
            logger.error(f"Input file does not exist: {context.input_path}")
            return False
        
        if not context.input_path.is_file():
            logger.error(f"Input is not a file: {context.input_path}")
            return False
        
        # Check size
        size = context.input_path.stat().st_size
        if size < self.min_size:
            logger.error(f"Input file too small: {size} < {self.min_size}")
            return False
        
        if self.max_size and size > self.max_size:
            logger.error(f"Input file too large: {size} > {self.max_size}")
            return False
        
        # Check extension
        if self.allowed_extensions:
            if context.input_path.suffix not in self.allowed_extensions:
                logger.error(
                    f"Invalid file extension: {context.input_path.suffix} "
                    f"(allowed: {self.allowed_extensions})"
                )
                return False
        
        # Custom validators
        for validator in self.custom_validators:
            if not validator(context.input_path):
                logger.error(f"Custom validation failed for {context.input_path}")
                return False
        
        return True
    
    async def validate_output(self, context: HookContext) -> bool:
        """Validate output file.
        
        Args:
            context: Hook context with output file
            
        Returns:
            True if validation passed
        """
        if not context.output_path or not context.output_path.exists():
            logger.error(f"Output file was not created: {context.output_path}")
            return False
        
        # Check size
        size = context.output_path.stat().st_size
        if size < self.min_size:
            logger.error(f"Output file too small: {size} < {self.min_size}")
            return False
        
        return True
