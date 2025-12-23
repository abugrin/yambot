"""Rate limiter for API requests"""

import time
import threading
from collections import deque
from typing import Optional


class RateLimiter:
    """Rate limiter implementing token bucket algorithm
    
    Limits requests to maximum RPS (requests per second)
    """
    
    def __init__(self, max_rps: int = 20):
        """Initialize rate limiter
        
        Args:
            max_rps (int): Maximum requests per second, default: 20
        """
        self.max_rps = max_rps
        self.min_interval = 1.0 / max_rps
        self.requests = deque()
        self.lock = threading.Lock()
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire permission to make a request
        
        Args:
            timeout (float): Maximum time to wait in seconds, None for no limit
            
        Returns:
            bool: True if permission acquired, False if timeout
        """
        start_time = time.time()
        
        while True:
            with self.lock:
                now = time.time()
                
                # Remove requests older than 1 second
                while self.requests and self.requests[0] < now - 1.0:
                    self.requests.popleft()
                
                # Check if we can make a request
                if len(self.requests) < self.max_rps:
                    self.requests.append(now)
                    return True
            
            # Check timeout
            if timeout is not None and (time.time() - start_time) >= timeout:
                return False
            
            # Wait before retrying
            time.sleep(self.min_interval)
    
    def reset(self):
        """Reset rate limiter"""
        with self.lock:
            self.requests.clear()

