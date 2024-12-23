# src/utils/security.py

from typing import Dict, Optional, List
import logging
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from passlib.context import CryptContext
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class SecurityManager:
    """מנהל אבטחה ואותנטיקציה"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
        
        # הגדרות JWT
        self.JWT_SECRET_KEY = None
        self.JWT_ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        
        # חיבור ל-Redis למניעת כפילות טוקנים
        self.redis_client = None
        
        # חיבור ל-Key Vault
        self.key_vault_client = None

    async def initialize(
        self,
        key_vault_url: str,
        redis_url: str
    ):
        """אתחול מנהל האבטחה"""
        try:
            # התחברות ל-Key Vault
            credential = DefaultAzureCredential()
            self.key_vault_client = SecretClient(
                vault_url=key_vault_url,
                credential=credential
            )
            
            # קבלת סוד JWT מ-Key Vault
            self.JWT_SECRET_KEY = (
                await self.key_vault_client.get_secret("jwt-secret")
            ).value
            
            # התחברות ל-Redis
            self.redis_client = await redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            logger.info("Security manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize security manager: {str(e)}")
            raise

    async def create_access_token(
        self,
        data: Dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """יצירת טוקן גישה"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            
        to_encode.update({"exp": expire})
        token = jwt.encode(
            to_encode,
            self.JWT_SECRET_KEY,
            algorithm=self.JWT_ALGORITHM
        )
        
        # שמירת הטוקן ב-Redis
        await self.redis_client.set(
            f"token:{token}",
            "valid",
            ex=int(expires_delta.total_seconds() if expires_delta else self.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        )
        
        return token

    async def verify_token(self, token: str) -> Dict:
        """אימות טוקן וקבלת המידע ממנו"""
        try:
            # בדיקה אם הטוקן תקף ב-Redis
            if not await self.redis_client.exists(f"token:{token}"):
                raise HTTPException(
                    status_code=401,
                    detail="Token has been revoked or is invalid"
                )
            
            payload = jwt.decode(
                token,
                self.JWT_SECRET_KEY,
                algorithms=[self.JWT_ALGORITHM]
            )
            return payload
            
        except jwt.ExpiredSignatureError:
            await self.redis_client.delete(f"token:{token}")
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials"
            )

    async def revoke_token(self, token: str):
        """ביטול טוקן"""
        await self.redis_client.delete(f"token:{token}")

    async def verify_api_key(
        self,
        api_key: str = Security(APIKeyHeader(name="X-API-Key"))
    ) -> bool:
        """אימות מפתח API"""
        try:
            # בדיקה מול Key Vault
            stored_key = (
                await self.key_vault_client.get_secret("api-key")
            ).value
            return api_key == stored_key
            
        except Exception as e:
            logger.error(f"API key verification failed: {str(e)}")
            return False

    async def hash_password(self, password: str) -> str:
        """הצפנת סיסמה"""
        return self.pwd_context.hash(password)

    async def verify_password(
        self,
        plain_password: str,
        hashed_password: str
    ) -> bool:
        """אימות סיסמה"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_permissions(self, user_type: str) -> List[str]:
        """קבלת הרשאות לפי סוג משתמש"""
        permissions = {
            "admin": [
                "read:all",
                "write:all",
                "delete:all",
                "manage:system"
            ],
            "agent": [
                "read:assigned",
                "write:assigned",
                "update:knowledge"
            ],
            "user": [
                "read:own",
                "write:own"
            ]
        }
        return permissions.get(user_type, [])

    async def check_permission(
        self,
        token: str,
        required_permission: str
    ) -> bool:
        """בדיקת הרשאה ספציפית"""
        try:
            payload = await self.verify_token(token)
            user_permissions = self.get_permissions(payload.get("user_type", "user"))
            return required_permission in user_permissions
            
        except Exception:
            return False

class RateLimiter:
    """מגביל קצב פניות"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        
        # הגדרות ברירת מחדל
        self.default_limits = {
            "api": {
                "requests": 100,
                "period": 3600  # שעה
            },
            "user": {
                "requests": 50,
                "period": 3600
            }
        }

    async def check_rate_limit(
        self,
        key: str,
        limit_type: str = "api"
    ) -> bool:
        """בדיקת מגבלת קצב"""
        try:
            redis_key = f"rate_limit:{limit_type}:{key}"
            current = await self.redis_client.get(redis_key)
            
            if current is None:
                # ראשונה בתקופה
                await self.redis_client.setex(
                    redis_key,
                    self.default_limits[limit_type]["period"],
                    1
                )
                return True
                
            current = int(current)
            if current >= self.default_limits[limit_type]["requests"]:
                return False
                
            await self.redis_client.incr(redis_key)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            return True  # במקרה של שגיאה, אפשר גישה

    async def reset_limit(self, key: str, limit_type: str = "api"):
        """איפוס מונה הגבלת קצב"""
        try:
            await self.redis_client.delete(f"rate_limit:{limit_type}:{key}")
        except Exception as e:
            logger.error(f"Failed to reset rate limit: {str(e)}")