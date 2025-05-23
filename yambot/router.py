from collections.abc import Callable
import logging
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum, auto

from .types import Update
import re


class HandlerType(Enum):
    """Enum defining the supported handler types"""
    BUTTON = auto()
    COMMAND = auto()
    TEXT = auto()
    REGEX = auto()
    ANY = auto()


class Router:
    """A message router that dispatches updates to registered handlers based on matching criteria.
    
    The router supports different types of handlers:
    - Button handlers: Match callback data from button presses
    - Command handlers: Match exact command strings
    - Text handlers: Match exact text strings
    - Regex handlers: Match text using regular expressions
    - Any handlers: Catch-all handlers for unmatched updates
    
    Handlers are processed in order of registration, with ANY handlers processed last.
    """

    def __init__(self, log_level: int = logging.INFO):
        """Initialize the router.
        
        Args:
            log_level: The logging level to use. Defaults to INFO.
        """
        self._handlers: List[Tuple[Dict[str, Any], Callable]] = []
        self._allowed_commands = {
            'button': HandlerType.BUTTON,
            'command': HandlerType.COMMAND,
            'text': HandlerType.TEXT,
            'regex': HandlerType.REGEX,
            'any': HandlerType.ANY
        }
        self._logger = logging.getLogger('yambot')
        self._logger.setLevel(log_level)

    def add_handler(self, **kwargs) -> Callable:
        """Decorator for registering message handlers.
        
        Args:
            kwargs: Handler configuration with one of the following keys:
                - text (str): Exact text to match
                - command (str): Command string to match
                - regex (str): Regular expression pattern to match
                - button (str): Button callback data to match (requires 'cmd' in callback_data)
                - any (bool): If True, matches any unhandled update
                
        Returns:
            Callable: Decorator function
            
        Raises:
            ValueError: If no valid handler type is specified or if handler configuration is invalid
        """
        def decorator(func: Callable) -> Callable:
            handler_types = [cmd for cmd in self._allowed_commands if cmd in kwargs]
            if not handler_types:
                raise ValueError(
                    f'Handler type not supported: {kwargs.keys()}, '
                    f'supported types: {list(self._allowed_commands.keys())}')
            
            # Validate handler configuration
            if 'regex' in kwargs:
                try:
                    re.compile(kwargs['regex'])
                except re.error as e:
                    raise ValueError(f'Invalid regex pattern: {e}')
            
            self._logger.debug(f'Registering handler: {func.__name__} with config: {kwargs}')
            self._handlers.append((kwargs, func))
            return func

        return decorator

    def remove_handler(self, handler_func: Callable) -> bool:
        """Remove a registered handler.
        
        Args:
            handler_func: The handler function to remove
            
        Returns:
            bool: True if handler was removed, False if not found
        """
        initial_length = len(self._handlers)
        self._handlers = [(cfg, func) for cfg, func in self._handlers if func != handler_func]
        return len(self._handlers) < initial_length

    def get_updates(self):
        """Get updates from the message source.
        
        This method should be implemented by subclasses.
        
        Raises:
            NotImplementedError: Always, as this is an abstract method
        """
        raise NotImplementedError("Subclasses must implement get_updates()")

    def _process_update(self, update: Update) -> bool:
        """Process a single update through registered handlers.
        
        Args:
            update: The update to process
            
        Returns:
            bool: True if the update was handled, False otherwise
        """
        try:
            # First try specific handlers
            for cmd, func in self._handlers:
                if self._match_any_handler(cmd):
                    continue
                if self._check_handler(cmd, update):
                    self._logger.debug(f'Handler matched: {func.__name__}')
                    func(update)
                    return True

            # Then try ANY handlers
            for cmd, func in self._handlers:
                if self._match_any_handler(cmd):
                    self._logger.debug(f'ANY handler matched: {func.__name__}')
                    func(update)
                    return True

            self._logger.debug(f'No handler found for update: {update}')
            return False
            
        except Exception as e:
            self._logger.error(f'Error processing update: {e}', exc_info=True)
            return False

    def _check_handler(self, cmd: Dict[str, Any], update: Update) -> bool:
        """Check if an update matches a handler's criteria.
        
        Args:
            cmd: Handler configuration dictionary
            update: Update to check
            
        Returns:
            bool: True if the update matches the handler criteria
        """
        text = update.text

        # Button handler
        if update.callback_data and 'cmd' in update.callback_data and 'button' in cmd:
            return cmd['button'] == update.callback_data['cmd']

        # Text handler
        if cmd.get('text'):
            return text == cmd['text']

        # Regex handler
        if cmd.get('regex'):
            pattern = re.compile(cmd['regex'])
            return bool(pattern.match(text)) if text else False

        # Command handler
        if cmd.get('command'):
            return text == cmd['command']

        return False

    @staticmethod
    def _match_any_handler(cmd: Dict[str, Any]) -> bool:
        """Check if a handler is an ANY type handler.
        
        Args:
            cmd: Handler configuration dictionary
            
        Returns:
            bool: True if the handler is an ANY type handler
        """
        return bool(cmd.get('any', False))

    def list_handlers(self) -> List[Tuple[Dict[str, Any], Callable]]:
        """Get a list of all registered handlers.
        
        Returns:
            List of tuples containing handler configurations and their functions
        """
        for handler in self._handlers:
            self._logger.debug(f'Handler: {handler[1].__name__} with config: {handler[0]}')
        return self._handlers.copy()  # Return a copy to prevent modification

    def clear_handlers(self) -> None:
        """Remove all registered handlers."""
        self._handlers.clear()
        self._logger.debug('All handlers cleared')
