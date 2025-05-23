from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
import logging
from requests import Session, Response
import httpx
import aiohttp
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

class HTTPClientBase(ABC):
    """Abstract base class for HTTP clients"""
    
    @abstractmethod
    def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make POST request"""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close client connections"""
        pass

    @abstractmethod
    def set_token(self, token: str) -> None:
        """Set authentication token"""
        pass

class RequestsClient(HTTPClientBase):
    """Requests-based HTTP client implementation"""
    
    def __init__(self, token: str, max_retries: int = 3, pool_connections: int = 10,
                 pool_maxsize: int = 10, retry_delay: int = 2):
        self.logger = logging.getLogger('yambot.http')
        
        # Setup session with connection pooling
        self._session = Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize
        )
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        self.set_token(token)

    def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make POST request with retry logic"""
        try:
            response = self._session.post(url, timeout=30, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except Exception as e:
            self.logger.error(f'Request failed: {str(e)}')
            raise

    def close(self) -> None:
        """Close session"""
        self._session.close()

    def set_token(self, token: str) -> None:
        """Set OAuth token in headers"""
        self._session.headers.update({
            'Authorization': f'OAuth {token}'
        })

class HTTPXClient(HTTPClientBase):
    """HTTPX-based HTTP client implementation"""
    
    def __init__(self, token: str, max_retries: int = 3, limits: httpx.Limits = None):
        self.logger = logging.getLogger('yambot.http')
        
        # Setup client with connection pooling
        self._client = httpx.Client(
            timeout=30.0,
            limits=limits or httpx.Limits(max_keepalive_connections=10, max_connections=10),
            transport=httpx.HTTPTransport(retries=max_retries)
        )
        self.set_token(token)

    def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make POST request with retry logic"""
        try:
            # Set Content-Type header only for JSON requests
            if 'json' in kwargs:
                self._client.headers['Content-Type'] = 'application/json'
            elif 'files' in kwargs:
                # Remove Content-Type header for multipart/form-data requests
                self._client.headers.pop('Content-Type', None)
                
            response = self._client.post(url, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except Exception as e:
            self.logger.error(f'Request failed: {str(e)}')
            raise

    def close(self) -> None:
        """Close client"""
        self._client.close()

    def set_token(self, token: str) -> None:
        """Set OAuth token in headers"""
        self._client.headers.update({
            'Authorization': f'OAuth {token}'
        })

class AsyncHTTPClient(HTTPClientBase):
    """Async HTTP client implementation using aiohttp"""
    
    def __init__(self, token: str, max_retries: int = 3):
        self.logger = logging.getLogger('yambot.http')
        self._token = token
        self._session = None
        self._max_retries = max_retries

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self.set_token(self._token)

    async def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make POST request with retry logic"""
        await self._ensure_session()
        
        for attempt in range(self._max_retries):
            try:
                async with self._session.post(url, **kwargs) as response:
                    response.raise_for_status()
                    return await response.json() if response.content else {}
            except Exception as e:
                self.logger.error(f'Request failed (attempt {attempt + 1}/{self._max_retries}): {str(e)}')
                if attempt == self._max_retries - 1:
                    raise

    async def close(self) -> None:
        """Close session if it exists"""
        if self._session:
            await self._session.close()
            self._session = None

    def set_token(self, token: str) -> None:
        """Set OAuth token in headers"""
        if self._session:
            self._session.headers.update({
                'Authorization': f'OAuth {token}'
            })
        self._token = token  # Store token for session recreation

def create_client(client_type: str = 'requests', **kwargs) -> HTTPClientBase:
    """Factory function to create HTTP client instances
    
    Args:
        client_type: Type of client to create ('requests', 'httpx', or 'async')
        **kwargs: Additional arguments to pass to client constructor
    
    Returns:
        HTTPClientBase: Configured HTTP client instance
    """
    clients = {
        'requests': RequestsClient,
        'httpx': HTTPXClient,
        'async': AsyncHTTPClient
    }
    
    if client_type not in clients:
        raise ValueError(f'Unsupported client type: {client_type}. '
                        f'Supported types are: {", ".join(clients.keys())}')
    
    return clients[client_type](**kwargs) 