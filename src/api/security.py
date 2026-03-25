"""Security middleware and protection."""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
from src.utils.logger import logger
import re


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware to protect against common attacks."""
    
    # Track request counts per IP
    request_counts = defaultdict(list)
    blocked_ips = set()
    
    # Suspicious patterns
    SUSPICIOUS_PATTERNS = [
        r'\.env',
        r'\.git',
        r'\.aws',
        r'\.ssh',
        r'config\.php',
        r'wp-config',
        r'\.bak',
        r'\.old',
        r'\.save',
        r'\.tmp',
        r'\.backup',
        r'docker-compose',
        r'serverless',
        r'\.\./',
        r'%2e%2e',
        r'proc/self',
        r'etc/passwd',
        r'\.log',
        r'\.sql',
        r'\.zip',
        r'\.tar',
        r'admin',
        r'phpMyAdmin',
        r'actuator',
        r'\.yaml',
        r'\.yml',
    ]
    
    # Blocked paths
    BLOCKED_PATHS = {
        '/.env', '/.git', '/config.php', '/wp-config.php',
        '/admin', '/phpMyAdmin', '/.aws', '/.ssh',
        '/actuator', '/docker-compose.yml'
    }
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        path = request.url.path.lower()
        
        # Check if IP is already blocked
        if client_ip in self.blocked_ips:
            logger.warning(f"🚫 Blocked IP attempted access: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"}
            )
        
        # Check for suspicious patterns
        is_suspicious = False
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                is_suspicious = True
                logger.warning(f"🚨 SECURITY ALERT: Suspicious request from {client_ip}: {path}")
                break
        
        # Check blocked paths
        if any(blocked in path for blocked in self.BLOCKED_PATHS):
            is_suspicious = True
            logger.warning(f"🚨 SECURITY ALERT: Blocked path access from {client_ip}: {path}")
        
        # Rate limiting
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.request_counts[client_ip] = [
            req_time for req_time in self.request_counts[client_ip]
            if req_time > minute_ago
        ]
        
        # Add current request
        self.request_counts[client_ip].append(now)
        
        # Check rate limit (max 60 requests per minute)
        if len(self.request_counts[client_ip]) > 60:
            logger.error(f"⚠️ RATE LIMIT: IP {client_ip} exceeded 60 req/min")
            self.blocked_ips.add(client_ip)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"}
            )
        
        # If suspicious, log and block after multiple attempts
        if is_suspicious:
            suspicious_count = sum(1 for _ in self.request_counts[client_ip])
            if suspicious_count > 5:
                logger.error(f"🚫 BLOCKING IP: {client_ip} - Multiple suspicious requests")
                self.blocked_ips.add(client_ip)
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Access denied"}
                )
            
            # Return 404 for suspicious requests (don't reveal we detected them)
            return JSONResponse(
                status_code=404,
                content={"detail": "Not found"}
            )
        
        # Process normal request
        response = await call_next(request)
        return response


# Helper function to check if path is safe
def is_safe_path(path: str) -> bool:
    """Check if a path is safe from directory traversal."""
    # Normalize path
    normalized = path.lower()
    
    # Check for directory traversal
    dangerous_patterns = ['../', '..\\', '%2e%2e', 'proc/self', 'etc/passwd']
    
    for pattern in dangerous_patterns:
        if pattern in normalized:
            return False
    
    return True


# List of allowed API endpoints
ALLOWED_ENDPOINTS = {
    '/',
    '/health',
    '/health/ready',
    '/health/live',
    '/info',
    '/ui',
    '/assistants',
    '/threads',
    '/runs/wait',
    '/runs/stream',
}


def log_security_event(ip: str, path: str, attack_type: str):
    """Log security events for monitoring."""
    logger.error(f"""
    🚨 SECURITY EVENT
    ─────────────────────────────────
    Type: {attack_type}
    IP: {ip}
    Path: {path}
    Time: {datetime.now().isoformat()}
    ─────────────────────────────────
    """)

