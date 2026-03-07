"""
Caching service for project matching results.
"""

import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from .base_matcher import MatchResult, JobContext

class MatchingCacheService:
    """Service for caching project matching results."""
    
    def __init__(self, redis_url: str = None, default_ttl: int = 3600):
        self.default_ttl = default_ttl  # 1 hour default
        self.memory_cache = {}  # Fallback memory cache
        self.redis_client = None
        
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()  # Test connection
                logger.info("Redis cache connected successfully")
            except Exception as e:
                logger.warning(f"Redis connection failed, using memory cache: {e}")
        else:
            logger.info("Using memory cache for matching results")
    
    def generate_cache_key(
        self, 
        user_id: str, 
        job_context: JobContext, 
        algorithm_name: str,
        algorithm_version: str
    ) -> str:
        """Generate a unique cache key for matching results."""
        
        # Create a hash of the job context for consistent keys
        job_data = {
            'job_id': job_context.job_id,
            'title': job_context.title,
            'description': job_context.description,
            'required_skills': sorted(job_context.required_skills),
            'preferred_skills': sorted(job_context.preferred_skills),
            'category': job_context.category
        }
        
        job_hash = hashlib.md5(
            json.dumps(job_data, sort_keys=True).encode()
        ).hexdigest()[:12]
        
        return f"match:{user_id}:{job_hash}:{algorithm_name}:{algorithm_version}"
    
    def get_cached_results(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached matching results."""
        
        try:
            if self.redis_client:
                # Try Redis first
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    results = json.loads(cached_data)
                    logger.info(f"Cache hit (Redis): {cache_key}")
                    return results
            
            # Fallback to memory cache
            if cache_key in self.memory_cache:
                cache_entry = self.memory_cache[cache_key]
                if datetime.now() < cache_entry['expires_at']:
                    logger.info(f"Cache hit (Memory): {cache_key}")
                    return cache_entry['data']
                else:
                    # Expired, remove from memory cache
                    del self.memory_cache[cache_key]
            
            logger.info(f"Cache miss: {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None
    
    def cache_results(
        self, 
        cache_key: str, 
        results: List[MatchResult], 
        ttl: int = None
    ) -> bool:
        """Cache matching results."""
        
        ttl = ttl or self.default_ttl
        
        try:
            # Convert MatchResult objects to serializable format
            serializable_results = []
            for result in results:
                serializable_result = {
                    'project_id': result.project.id,
                    'project_title': result.project.title,
                    'confidence_score': result.confidence_score,
                    'explanation': result.explanation,
                    'matching_keywords': result.matching_keywords,
                    'similarity_breakdown': result.similarity_breakdown,
                    'cached_at': datetime.now().isoformat()
                }
                serializable_results.append(serializable_result)
            
            if self.redis_client:
                # Cache in Redis
                self.redis_client.setex(
                    cache_key, 
                    ttl, 
                    json.dumps(serializable_results)
                )
                logger.info(f"Cached results in Redis: {cache_key}")
            
            # Also cache in memory as backup
            self.memory_cache[cache_key] = {
                'data': serializable_results,
                'expires_at': datetime.now() + timedelta(seconds=ttl)
            }
            
            # Clean up old memory cache entries
            self._cleanup_memory_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Error caching results: {e}")
            return False
    
    def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cached results for a user."""
        
        invalidated_count = 0
        
        try:
            if self.redis_client:
                # Find and delete Redis keys
                pattern = f"match:{user_id}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    invalidated_count += self.redis_client.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} Redis cache entries for user {user_id}")
            
            # Clean memory cache
            keys_to_delete = [
                key for key in self.memory_cache.keys() 
                if key.startswith(f"match:{user_id}:")
            ]
            
            for key in keys_to_delete:
                del self.memory_cache[key]
                invalidated_count += 1
            
            logger.info(f"Invalidated {invalidated_count} total cache entries for user {user_id}")
            return invalidated_count
            
        except Exception as e:
            logger.error(f"Error invalidating user cache: {e}")
            return 0
    
    def _cleanup_memory_cache(self):
        """Clean up expired entries from memory cache."""
        
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if now >= entry['expires_at']
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        
        stats = {
            'memory_cache_size': len(self.memory_cache),
            'redis_available': self.redis_client is not None
        }
        
        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats['redis_used_memory'] = info.get('used_memory_human', 'N/A')
                stats['redis_connected_clients'] = info.get('connected_clients', 0)
            except Exception as e:
                stats['redis_error'] = str(e)
        
        return stats
