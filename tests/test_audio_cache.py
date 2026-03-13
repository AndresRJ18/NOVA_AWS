"""Unit tests for AudioCache with LRU eviction."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from mock_interview_coach.voice_interface import AudioCache, CacheStats, CacheEntry
from mock_interview_coach.models import Language


class TestAudioCache:
    """Test suite for AudioCache class."""
    
    def test_initialization(self):
        """Test cache initialization with default and custom parameters."""
        # Default initialization
        cache = AudioCache()
        assert cache.max_size_bytes == 100 * 1024 * 1024  # 100MB
        assert cache._model_id == "amazon.nova-sonic-v1:0"
        
        # Custom initialization
        cache = AudioCache(max_size_bytes=50 * 1024 * 1024, model_id="custom-model")
        assert cache.max_size_bytes == 50 * 1024 * 1024
        assert cache._model_id == "custom-model"
    
    def test_cache_key_generation(self):
        """Test that cache keys are generated consistently and uniquely."""
        cache = AudioCache()
        
        # Same text and language should produce same key
        key1 = cache._generate_cache_key("Hello", Language.ENGLISH)
        key2 = cache._generate_cache_key("Hello", Language.ENGLISH)
        assert key1 == key2
        
        # Different text should produce different key
        key3 = cache._generate_cache_key("Goodbye", Language.ENGLISH)
        assert key1 != key3
        
        # Different language should produce different key
        key4 = cache._generate_cache_key("Hello", Language.SPANISH)
        assert key1 != key4
        
        # Whitespace normalization
        key5 = cache._generate_cache_key("  Hello  ", Language.ENGLISH)
        key6 = cache._generate_cache_key("hello", Language.ENGLISH)
        assert key5 == key6  # Should be normalized to same key
    
    def test_common_phrase_detection(self):
        """Test detection of common phrases for TTL determination."""
        cache = AudioCache()
        
        # English common phrases
        assert cache._is_common_phrase("Welcome to the interview.", Language.ENGLISH)
        assert cache._is_common_phrase("Great job!", Language.ENGLISH)
        assert cache._is_common_phrase("  Great job!  ", Language.ENGLISH)  # With whitespace
        
        # Spanish common phrases
        assert cache._is_common_phrase("Bienvenido a la entrevista.", Language.SPANISH)
        assert cache._is_common_phrase("¡Buen trabajo!", Language.SPANISH)
        
        # Non-common phrases
        assert not cache._is_common_phrase("This is a custom question.", Language.ENGLISH)
        assert not cache._is_common_phrase("Random text", Language.SPANISH)
    
    def test_ttl_determination(self):
        """Test TTL assignment based on phrase type."""
        cache = AudioCache()
        
        # Common phrases should get 24-hour TTL
        ttl_common = cache._get_ttl("Welcome to the interview.", Language.ENGLISH)
        assert ttl_common == 24 * 60 * 60
        
        # Dynamic content should get 1-hour TTL
        ttl_dynamic = cache._get_ttl("Custom question text", Language.ENGLISH)
        assert ttl_dynamic == 60 * 60
    
    def test_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = AudioCache()
        
        text = "Test audio"
        language = Language.ENGLISH
        audio_data = b"fake_audio_data_12345"
        
        # Set audio in cache
        cache.set(text, language, audio_data)
        
        # Get audio from cache
        retrieved = cache.get(text, language)
        assert retrieved == audio_data
        
        # Stats should reflect cache hit
        stats = cache.get_stats()
        assert stats.hits == 1
        assert stats.misses == 0
        assert stats.entry_count == 1
        assert stats.size_bytes == len(audio_data)
    
    def test_cache_miss(self):
        """Test cache miss for non-existent entries."""
        cache = AudioCache()
        
        # Try to get non-existent entry
        result = cache.get("Non-existent text", Language.ENGLISH)
        assert result is None
        
        # Stats should reflect cache miss
        stats = cache.get_stats()
        assert stats.hits == 0
        assert stats.misses == 1
    
    def test_cache_update(self):
        """Test updating an existing cache entry."""
        cache = AudioCache()
        
        text = "Test audio"
        language = Language.ENGLISH
        audio_data_1 = b"audio_v1"
        audio_data_2 = b"audio_v2_longer"
        
        # Set initial audio
        cache.set(text, language, audio_data_1)
        assert cache.get_stats().size_bytes == len(audio_data_1)
        
        # Update with new audio
        cache.set(text, language, audio_data_2)
        
        # Should retrieve updated audio
        retrieved = cache.get(text, language)
        assert retrieved == audio_data_2
        
        # Size should be updated
        assert cache.get_stats().size_bytes == len(audio_data_2)
        
        # Should still have only 1 entry
        assert cache.get_stats().entry_count == 1
    
    def test_lru_eviction(self):
        """Test that oldest entries are evicted when cache is full."""
        # Create small cache (1KB)
        cache = AudioCache(max_size_bytes=1000)
        
        # Add entries that will fill the cache
        for i in range(10):
            text = f"text_{i}"
            audio_data = b"x" * 150  # 150 bytes each
            cache.set(text, Language.ENGLISH, audio_data)
        
        # First entries should be evicted (LRU)
        assert cache.get("text_0", Language.ENGLISH) is None
        assert cache.get("text_1", Language.ENGLISH) is None
        
        # Recent entries should still be present
        assert cache.get("text_9", Language.ENGLISH) is not None
        assert cache.get("text_8", Language.ENGLISH) is not None
        
        # Cache should not exceed max size
        stats = cache.get_stats()
        assert stats.size_bytes <= 1000
    
    def test_lru_ordering_on_access(self):
        """Test that accessing an entry moves it to the end (most recent)."""
        cache = AudioCache(max_size_bytes=400)  # Can fit 4 entries of 100 bytes
        
        # Add 4 entries (400 bytes total, cache is full)
        cache.set("text_0", Language.ENGLISH, b"x" * 100)
        cache.set("text_1", Language.ENGLISH, b"x" * 100)
        cache.set("text_2", Language.ENGLISH, b"x" * 100)
        cache.set("text_3", Language.ENGLISH, b"x" * 100)
        
        # Access text_0 to make it most recent
        # Order is now: text_1, text_2, text_3, text_0 (LRU to MRU)
        cache.get("text_0", Language.ENGLISH)
        
        # Add new entry to trigger eviction
        # This should evict text_1 (the oldest)
        cache.set("text_4", Language.ENGLISH, b"x" * 100)
        
        # text_0 should still be present (was accessed recently)
        assert cache.get("text_0", Language.ENGLISH) is not None
        
        # text_1 should be evicted (least recently used)
        assert cache.get("text_1", Language.ENGLISH) is None
        
        # text_2, text_3, text_4 should be present
        assert cache.get("text_2", Language.ENGLISH) is not None
        assert cache.get("text_3", Language.ENGLISH) is not None
        assert cache.get("text_4", Language.ENGLISH) is not None
    
    def test_expired_entry_removal(self):
        """Test that expired entries are removed on access."""
        cache = AudioCache()
        
        text = "Test audio"
        language = Language.ENGLISH
        audio_data = b"fake_audio_data"
        
        # Set audio in cache
        cache.set(text, language, audio_data)
        
        # Manually expire the entry by modifying created_at
        key = cache._generate_cache_key(text, language)
        entry = cache._cache[key]
        entry.created_at = datetime.now() - timedelta(hours=25)  # Expired (>24h for common phrase)
        
        # Try to get expired entry
        result = cache.get(text, language)
        assert result is None
        
        # Entry should be removed from cache
        assert key not in cache._cache
        assert cache.get_stats().entry_count == 0
    
    def test_clear(self):
        """Test clearing all cache entries."""
        cache = AudioCache()
        
        # Add multiple entries
        for i in range(5):
            cache.set(f"text_{i}", Language.ENGLISH, b"audio_data")
        
        assert cache.get_stats().entry_count == 5
        
        # Clear cache
        cache.clear()
        
        # All entries should be removed
        stats = cache.get_stats()
        assert stats.entry_count == 0
        assert stats.size_bytes == 0
        assert stats.hits == 0
        assert stats.misses == 0
        
        # Entries should not be retrievable
        for i in range(5):
            assert cache.get(f"text_{i}", Language.ENGLISH) is None
    
    def test_empty_audio_data(self):
        """Test that empty audio data is not cached."""
        cache = AudioCache()
        
        # Try to cache empty audio
        cache.set("Test", Language.ENGLISH, b"")
        
        # Should not be in cache
        assert cache.get("Test", Language.ENGLISH) is None
        assert cache.get_stats().entry_count == 0
    
    def test_oversized_audio_data(self):
        """Test that audio larger than max cache size is not cached."""
        cache = AudioCache(max_size_bytes=1000)
        
        # Try to cache audio larger than max size
        large_audio = b"x" * 1500
        cache.set("Large audio", Language.ENGLISH, large_audio)
        
        # Should not be in cache
        assert cache.get("Large audio", Language.ENGLISH) is None
        assert cache.get_stats().entry_count == 0
    
    def test_cache_stats_hit_rate(self):
        """Test cache hit rate calculation."""
        cache = AudioCache()
        
        # Add entry
        cache.set("text", Language.ENGLISH, b"audio")
        
        # 2 hits, 3 misses
        cache.get("text", Language.ENGLISH)  # hit
        cache.get("text", Language.ENGLISH)  # hit
        cache.get("missing1", Language.ENGLISH)  # miss
        cache.get("missing2", Language.ENGLISH)  # miss
        cache.get("missing3", Language.ENGLISH)  # miss
        
        stats = cache.get_stats()
        assert stats.hits == 2
        assert stats.misses == 3
        assert stats.hit_rate == 40.0  # 2/5 = 40%
    
    def test_cache_entry_access_tracking(self):
        """Test that cache entries track access count and last accessed time."""
        cache = AudioCache()
        
        text = "Test audio"
        language = Language.ENGLISH
        audio_data = b"audio_data"
        
        # Set audio
        cache.set(text, language, audio_data)
        
        # Get cache entry
        key = cache._generate_cache_key(text, language)
        entry = cache._cache[key]
        
        # Initially no accesses
        assert entry.access_count == 0
        assert entry.last_accessed is None
        
        # Access the entry
        cache.get(text, language)
        
        # Access count should increment
        assert entry.access_count == 1
        assert entry.last_accessed is not None
        
        # Access again
        cache.get(text, language)
        assert entry.access_count == 2
    
    @pytest.mark.asyncio
    async def test_preload_common_phrases(self):
        """Test preloading common phrases on startup."""
        cache = AudioCache()
        
        # Mock synthesize function
        async def mock_synthesize(text: str, language: Language) -> bytes:
            return f"audio_for_{text}".encode('utf-8')
        
        # Preload for English
        result = await cache.preload_common_phrases(
            mock_synthesize,
            languages=[Language.ENGLISH]
        )
        
        # Should have preloaded all English common phrases
        assert result["en"] == len(cache.COMMON_PHRASES["en"])
        
        # Common phrases should be in cache
        for phrase in cache.COMMON_PHRASES["en"]:
            cached_audio = cache.get(phrase, Language.ENGLISH)
            assert cached_audio is not None
            assert cached_audio == f"audio_for_{phrase}".encode('utf-8')
    
    @pytest.mark.asyncio
    async def test_preload_skips_already_cached(self):
        """Test that preload skips phrases already in cache."""
        cache = AudioCache()
        
        # Pre-cache one phrase
        phrase = cache.COMMON_PHRASES["en"][0]
        cache.set(phrase, Language.ENGLISH, b"existing_audio")
        
        # Mock synthesize function (should not be called for cached phrase)
        call_count = 0
        
        async def mock_synthesize(text: str, language: Language) -> bytes:
            nonlocal call_count
            call_count += 1
            return f"audio_for_{text}".encode('utf-8')
        
        # Preload
        result = await cache.preload_common_phrases(
            mock_synthesize,
            languages=[Language.ENGLISH]
        )
        
        # Should report all phrases as loaded
        assert result["en"] == len(cache.COMMON_PHRASES["en"])
        
        # But synthesize should only be called for non-cached phrases
        assert call_count == len(cache.COMMON_PHRASES["en"]) - 1
        
        # Original cached audio should be preserved
        assert cache.get(phrase, Language.ENGLISH) == b"existing_audio"
    
    @pytest.mark.asyncio
    async def test_preload_handles_synthesis_errors(self):
        """Test that preload continues even if some phrases fail to synthesize."""
        cache = AudioCache()
        
        # Mock synthesize function that fails for specific phrases
        async def mock_synthesize(text: str, language: Language) -> bytes:
            if "Great job" in text:
                raise RuntimeError("Synthesis failed")
            return f"audio_for_{text}".encode('utf-8')
        
        # Preload (should not raise exception)
        result = await cache.preload_common_phrases(
            mock_synthesize,
            languages=[Language.ENGLISH]
        )
        
        # Should have loaded all except the failed one
        assert result["en"] == len(cache.COMMON_PHRASES["en"]) - 1
        
        # Failed phrase should not be in cache
        assert cache.get("Great job!", Language.ENGLISH) is None
        
        # Other phrases should be cached
        assert cache.get("Welcome to the interview.", Language.ENGLISH) is not None
    
    def test_multiple_languages(self):
        """Test cache works correctly with multiple languages."""
        cache = AudioCache()
        
        # Same text in different languages should be cached separately
        text = "Hello"
        audio_en = b"audio_english"
        audio_es = b"audio_spanish"
        
        cache.set(text, Language.ENGLISH, audio_en)
        cache.set(text, Language.SPANISH, audio_es)
        
        # Should retrieve correct audio for each language
        assert cache.get(text, Language.ENGLISH) == audio_en
        assert cache.get(text, Language.SPANISH) == audio_es
        
        # Should have 2 separate entries
        assert cache.get_stats().entry_count == 2
    
    def test_cache_entry_expiration_check(self):
        """Test CacheEntry.is_expired() method."""
        # Create entry with 1-hour TTL
        entry = CacheEntry(
            audio_data=b"audio",
            created_at=datetime.now(),
            ttl_seconds=3600
        )
        
        # Should not be expired immediately
        assert not entry.is_expired()
        
        # Manually set created_at to 2 hours ago
        entry.created_at = datetime.now() - timedelta(hours=2)
        
        # Should be expired now
        assert entry.is_expired()
    
    def test_cache_entry_size_calculation(self):
        """Test CacheEntry.size_bytes() method."""
        audio_data = b"x" * 1234
        entry = CacheEntry(
            audio_data=audio_data,
            created_at=datetime.now(),
            ttl_seconds=3600
        )
        
        assert entry.size_bytes() == 1234


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
