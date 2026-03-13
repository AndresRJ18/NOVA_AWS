"""Audio Cache with LRU eviction for Nova Sonic responses.

This module provides an in-memory LRU cache for audio responses to reduce
API calls and improve latency. It supports TTL-based expiration and preloading
of common phrases.
"""

import hashlib
import logging
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

from mock_interview_coach.models import Language

# Configure logger
logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Statistics for cache performance monitoring."""
    hits: int
    misses: int
    size_bytes: int
    entry_count: int
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as a percentage."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100.0


@dataclass
class CacheEntry:
    """A single cache entry with audio data and metadata."""
    audio_data: bytes
    created_at: datetime
    ttl_seconds: int
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if this cache entry has expired based on TTL."""
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now() > expiry_time
    
    def size_bytes(self) -> int:
        """Get the size of this entry in bytes."""
        return len(self.audio_data)


class AudioCache:
    """LRU cache for audio responses with TTL-based expiration.
    
    This cache stores synthesized audio to reduce API calls to Nova Sonic.
    It uses an LRU (Least Recently Used) eviction policy and supports
    different TTLs for common phrases vs dynamic content.
    
    Attributes:
        max_size_bytes: Maximum cache size in bytes
        _cache: OrderedDict storing cache entries (LRU order)
        _stats: Cache performance statistics
        _model_id: Nova Sonic model ID for cache key generation
    """
    
    # Common phrases that should be cached with longer TTL (24 hours)
    COMMON_PHRASES = {
        "en": [
            "Welcome to the interview.",
            "Let's begin.",
            "Great job!",
            "Thank you for your response.",
            "Let's move on to the next question.",
            "That's correct.",
            "Can you elaborate on that?",
            "Excellent answer.",
            "The interview is complete.",
            "Thank you for participating.",
        ],
        "es": [
            "Bienvenido a la entrevista.",
            "Comencemos.",
            "¡Buen trabajo!",
            "Gracias por tu respuesta.",
            "Pasemos a la siguiente pregunta.",
            "Eso es correcto.",
            "¿Puedes elaborar sobre eso?",
            "Excelente respuesta.",
            "La entrevista está completa.",
            "Gracias por participar.",
        ]
    }
    
    # TTL values
    COMMON_PHRASE_TTL = 24 * 60 * 60  # 24 hours
    DYNAMIC_CONTENT_TTL = 60 * 60     # 1 hour
    
    def __init__(
        self,
        max_size_bytes: int = 100 * 1024 * 1024,  # 100MB default
        model_id: str = "amazon.nova-sonic-v1:0"
    ):
        """Initialize the audio cache.
        
        Args:
            max_size_bytes: Maximum cache size in bytes (default: 100MB)
            model_id: Nova Sonic model ID for cache key generation
        """
        self.max_size_bytes = max_size_bytes
        self._model_id = model_id
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = CacheStats(hits=0, misses=0, size_bytes=0, entry_count=0)
        
        logger.info(
            f"AudioCache initialized with max_size={max_size_bytes / (1024*1024):.1f}MB, "
            f"model_id={model_id}"
        )
    
    def _generate_cache_key(self, text: str, language: Language) -> str:
        """Generate a cache key from text, language, and model ID.
        
        The cache key is a hash of the text, language, and model ID to ensure
        uniqueness across different inputs and model versions.
        
        Args:
            text: Text content
            language: Language of the text
            
        Returns:
            SHA256 hash as hex string
        """
        # Normalize text (strip whitespace, lowercase)
        normalized_text = text.strip().lower()
        
        # Create composite key
        key_components = f"{normalized_text}|{language.value}|{self._model_id}"
        
        # Generate hash
        hash_obj = hashlib.sha256(key_components.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def _is_common_phrase(self, text: str, language: Language) -> bool:
        """Check if text is a common phrase that should have longer TTL.
        
        Args:
            text: Text to check
            language: Language of the text
            
        Returns:
            True if text is a common phrase, False otherwise
        """
        normalized_text = text.strip()
        language_code = language.value
        
        # Check if language has common phrases defined
        if language_code not in self.COMMON_PHRASES:
            return False
        
        # Check if text matches any common phrase (case-insensitive)
        return any(
            normalized_text.lower() == phrase.lower()
            for phrase in self.COMMON_PHRASES[language_code]
        )
    
    def _get_ttl(self, text: str, language: Language) -> int:
        """Determine TTL for a cache entry based on content type.
        
        Args:
            text: Text content
            language: Language of the text
            
        Returns:
            TTL in seconds
        """
        if self._is_common_phrase(text, language):
            return self.COMMON_PHRASE_TTL
        return self.DYNAMIC_CONTENT_TTL
    
    def _evict_lru(self) -> None:
        """Evict the least recently used entry from the cache."""
        if not self._cache:
            return
        
        # Remove the first (oldest) entry from OrderedDict
        key, entry = self._cache.popitem(last=False)
        self._stats.size_bytes -= entry.size_bytes()
        self._stats.entry_count -= 1
        
        logger.debug(
            f"Evicted LRU entry: key={key[:16]}..., "
            f"size={entry.size_bytes()} bytes, "
            f"access_count={entry.access_count}"
        )
    
    def _evict_expired(self) -> None:
        """Remove all expired entries from the cache."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            entry = self._cache.pop(key)
            self._stats.size_bytes -= entry.size_bytes()
            self._stats.entry_count -= 1
            
            logger.debug(
                f"Evicted expired entry: key={key[:16]}..., "
                f"age={(datetime.now() - entry.created_at).total_seconds():.0f}s"
            )
    
    def _make_space(self, required_bytes: int) -> None:
        """Make space in the cache by evicting entries.
        
        This method first removes expired entries, then evicts LRU entries
        until there's enough space for the new entry.
        
        Args:
            required_bytes: Number of bytes needed
        """
        # First, remove expired entries
        self._evict_expired()
        
        # Then evict LRU entries until we have enough space
        while self._cache and (self._stats.size_bytes + required_bytes > self.max_size_bytes):
            self._evict_lru()
    
    def get(self, text: str, language: Language) -> Optional[bytes]:
        """Retrieve audio data from cache.
        
        Args:
            text: Text that was synthesized
            language: Language of the text
            
        Returns:
            Audio data bytes if found and not expired, None otherwise
        """
        key = self._generate_cache_key(text, language)
        
        # Check if key exists
        if key not in self._cache:
            self._stats.misses += 1
            logger.debug(f"Cache miss: key={key[:16]}...")
            return None
        
        entry = self._cache[key]
        
        # Check if entry is expired
        if entry.is_expired():
            # Remove expired entry
            self._cache.pop(key)
            self._stats.size_bytes -= entry.size_bytes()
            self._stats.entry_count -= 1
            self._stats.misses += 1
            
            logger.debug(
                f"Cache miss (expired): key={key[:16]}..., "
                f"age={(datetime.now() - entry.created_at).total_seconds():.0f}s"
            )
            return None
        
        # Update access metadata
        entry.access_count += 1
        entry.last_accessed = datetime.now()
        
        # Move to end (most recently used)
        self._cache.move_to_end(key)
        
        # Update stats
        self._stats.hits += 1
        
        logger.debug(
            f"Cache hit: key={key[:16]}..., "
            f"access_count={entry.access_count}, "
            f"size={entry.size_bytes()} bytes"
        )
        
        return entry.audio_data
    
    def set(self, text: str, language: Language, audio_data: bytes) -> None:
        """Store audio data in cache.
        
        Args:
            text: Text that was synthesized
            language: Language of the text
            audio_data: Audio data bytes to cache
        """
        if not audio_data:
            logger.warning("Attempted to cache empty audio data")
            return
        
        key = self._generate_cache_key(text, language)
        ttl = self._get_ttl(text, language)
        
        # Check if entry already exists
        is_update = key in self._cache
        if is_update:
            # Update existing entry
            old_entry = self._cache[key]
            self._stats.size_bytes -= old_entry.size_bytes()
        
        # Create new entry
        entry = CacheEntry(
            audio_data=audio_data,
            created_at=datetime.now(),
            ttl_seconds=ttl,
            access_count=0,
            last_accessed=None
        )
        
        # Make space if needed
        entry_size = entry.size_bytes()
        if entry_size > self.max_size_bytes:
            logger.warning(
                f"Audio data ({entry_size} bytes) exceeds max cache size "
                f"({self.max_size_bytes} bytes), not caching"
            )
            return
        
        self._make_space(entry_size)
        
        # Add to cache
        self._cache[key] = entry
        self._stats.size_bytes += entry_size
        
        # Only increment entry count if this is a new entry
        if not is_update:
            self._stats.entry_count += 1
        
        logger.debug(
            f"Cached audio: key={key[:16]}..., "
            f"size={entry_size} bytes, "
            f"ttl={ttl}s, "
            f"is_common={self._is_common_phrase(text, language)}"
        )
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        entry_count = len(self._cache)
        size_bytes = self._stats.size_bytes
        
        self._cache.clear()
        self._stats = CacheStats(hits=0, misses=0, size_bytes=0, entry_count=0)
        
        logger.info(
            f"Cache cleared: removed {entry_count} entries, "
            f"freed {size_bytes / 1024:.1f}KB"
        )
    
    def get_stats(self) -> CacheStats:
        """Get cache performance statistics.
        
        Returns:
            CacheStats object with current statistics
        """
        return CacheStats(
            hits=self._stats.hits,
            misses=self._stats.misses,
            size_bytes=self._stats.size_bytes,
            entry_count=self._stats.entry_count
        )
    
    async def preload_common_phrases(
        self,
        synthesize_func,
        languages: Optional[list[Language]] = None
    ) -> Dict[str, int]:
        """Preload common phrases into the cache on startup.
        
        This method synthesizes and caches common phrases to improve
        initial response times.
        
        Args:
            synthesize_func: Async function to synthesize speech (text, language) -> bytes
            languages: List of languages to preload (default: all available)
            
        Returns:
            Dictionary mapping language codes to number of phrases preloaded
        """
        if languages is None:
            languages = [Language.ENGLISH, Language.SPANISH]
        
        preload_count = {}
        
        for language in languages:
            language_code = language.value
            
            if language_code not in self.COMMON_PHRASES:
                logger.warning(f"No common phrases defined for language: {language_code}")
                continue
            
            phrases = self.COMMON_PHRASES[language_code]
            loaded = 0
            
            for phrase in phrases:
                try:
                    # Check if already cached
                    if self.get(phrase, language) is not None:
                        loaded += 1
                        continue
                    
                    # Synthesize and cache
                    audio_data = await synthesize_func(phrase, language)
                    self.set(phrase, language, audio_data)
                    loaded += 1
                    
                    logger.debug(f"Preloaded phrase: '{phrase}' ({language_code})")
                    
                except Exception as e:
                    logger.error(
                        f"Failed to preload phrase '{phrase}' ({language_code}): {e}"
                    )
            
            preload_count[language_code] = loaded
            logger.info(
                f"Preloaded {loaded}/{len(phrases)} common phrases for {language_code}"
            )
        
        return preload_count
