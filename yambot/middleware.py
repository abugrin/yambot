"""Middleware system for processing updates"""

from typing import Callable, List, Optional
from .types import Update
import logging


class Middleware:
    """Base middleware class"""
    
    def process(self, update: Update, handler: Callable) -> Optional[any]:
        """Process update before passing to handler
        
        Args:
            update (Update): Update object
            handler (Callable): Handler function to call
            
        Returns:
            Optional[any]: Result from handler or None to stop processing
        """
        return handler(update)


class LoggingMiddleware(Middleware):
    """Middleware for logging updates"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger('yambot.middleware')
    
    def process(self, update: Update, handler: Callable) -> Optional[any]:
        """Log update and pass to handler"""
        self.logger.info(f'Processing update {update.update_id} from {update.from_m.login or update.from_m.from_id}')
        try:
            result = handler(update)
            self.logger.debug(f'Update {update.update_id} processed successfully')
            return result
        except Exception as e:
            self.logger.error(f'Error processing update {update.update_id}: {e}')
            raise


class FilterMiddleware(Middleware):
    """Middleware for filtering updates"""
    
    def __init__(self, filter_func: Callable[[Update], bool]):
        """Initialize filter middleware
        
        Args:
            filter_func: Function that returns True if update should be processed
        """
        self.filter_func = filter_func
    
    def process(self, update: Update, handler: Callable) -> Optional[any]:
        """Filter update before passing to handler"""
        if self.filter_func(update):
            return handler(update)
        return None


class MiddlewareManager:
    """Manager for middleware chain"""
    
    def __init__(self):
        self.middlewares: List[Middleware] = []
    
    def add(self, middleware: Middleware):
        """Add middleware to chain
        
        Args:
            middleware (Middleware): Middleware to add
        """
        self.middlewares.append(middleware)
    
    def process(self, update: Update, handler: Callable) -> Optional[any]:
        """Process update through middleware chain
        
        Args:
            update (Update): Update object
            handler (Callable): Final handler function
            
        Returns:
            Optional[any]: Result from handler or None if stopped by middleware
        """
        def chain_handler(update: Update) -> Optional[any]:
            # Build chain from last to first
            current_handler = handler
            for middleware in reversed(self.middlewares):
                # Capture current handler in closure
                def make_wrapped_handler(mw, h):
                    return lambda u: mw.process(u, h)
                current_handler = make_wrapped_handler(middleware, current_handler)
            return current_handler(update)
        
        return chain_handler(update)

