"""
Authentication and Role-Based Access Control (RBAC) Module for OptRail-AI
Indian Railways Operational Roles:
- CONTROLLER: Chief Section Controller / Sr. DOM (Traffic Operations)
- PWAY_ENGINEER: Senior Section Engineer / Track (Civil Engineering)
- OHE_ENGINEER: Senior Section Engineer / Traction (Electrical OHE)
- SAFETY_AUDITOR: Divisional Safety Officer / CRS (Safety Directorate)
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

SECRET_KEY = os.getenv("OPTRAIL_SECRET_KEY", "optrail-ai-railway-jwt-secret-key-sih-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

# Indian Railways Operational Role Hierarchy
class RailwayRoles:
    CONTROLLER = "CONTROLLER"
    PWAY_ENGINEER = "PWAY_ENGINEER"
    OHE_ENGINEER = "OHE_ENGINEER"
    SAFETY_AUDITOR = "SAFETY_AUDITOR"

# Role Definitions and Granular Permissions
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    RailwayRoles.CONTROLLER: [
        "optimize:run",
        "schedule:approve",
        "schedule:reject",
        "scenario:run",
        "task:create",
        "task:view",
        "asset:view",
        "conflict:view",
        "benchmark:view"
    ],
    RailwayRoles.PWAY_ENGINEER: [
        "task:create",
        "task:view",
        "asset:view",
        "schedule:view",
        "benchmark:view"
    ],
    RailwayRoles.OHE_ENGINEER: [
        "task:create",
        "task:view",
        "asset:view",
        "schedule:view",
        "benchmark:view"
    ],
    RailwayRoles.SAFETY_AUDITOR: [
        "safety:audit",
        "conflict:view",
        "schedule:view",
        "asset:view",
        "benchmark:view"
    ]
}

# Pre-hashed password for "password123"
DEFAULT_HASH = hash_password("password123")

# Seeded Indian Railways Personas
USERS_DB: Dict[str, Dict[str, Any]] = {
    "controller": {
        "username": "controller",
        "password_hash": DEFAULT_HASH,
        "full_name": "Rajesh Sharma",
        "designation": "Chief Section Controller (Sr. DOM)",
        "department": "Traffic Operations (DOM)",
        "division": "Delhi Division / Northern Railway",
        "badge_id": "IR-DOM-0442",
        "role": RailwayRoles.CONTROLLER,
        "avatar_color": "from-blue-600 to-indigo-600",
        "can_optimize": True,
        "can_approve_blocks": True
    },
    "pway_engineer": {
        "username": "pway_engineer",
        "password_hash": DEFAULT_HASH,
        "full_name": "Arun Verma",
        "designation": "Sr. Section Engineer / Permanent Way (Civil)",
        "department": "Civil Engineering (P-Way)",
        "division": "Ghaziabad Sub-Division",
        "badge_id": "IR-DEN-1108",
        "role": RailwayRoles.PWAY_ENGINEER,
        "avatar_color": "from-amber-600 to-orange-600",
        "can_optimize": False,
        "can_approve_blocks": False
    },
    "ohe_engineer": {
        "username": "ohe_engineer",
        "password_hash": DEFAULT_HASH,
        "full_name": "Priya Nair",
        "designation": "Sr. Section Engineer / Traction & OHE (Electrical)",
        "department": "Electrical TRD (DEE)",
        "division": "Aligarh Sub-Division",
        "badge_id": "IR-DEE-3391",
        "role": RailwayRoles.OHE_ENGINEER,
        "avatar_color": "from-cyan-600 to-blue-500",
        "can_optimize": False,
        "can_approve_blocks": False
    },
    "safety_auditor": {
        "username": "safety_auditor",
        "password_hash": DEFAULT_HASH,
        "full_name": "V. K. Meena",
        "designation": "Divisional Safety Officer (CRS Inspectorate)",
        "department": "Safety & Inspection Directorate",
        "division": "Northern Railway Zone",
        "badge_id": "IR-CRS-0019",
        "role": RailwayRoles.SAFETY_AUDITOR,
        "avatar_color": "from-purple-600 to-pink-600",
        "can_optimize": False,
        "can_approve_blocks": False
    }
}

class LoginRequest(BaseModel):
    username: str
    password: str

class SwitchRoleRequest(BaseModel):
    username: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def get_user_profile(user_dict: dict) -> dict:
    profile = {k: v for k, v in user_dict.items() if k != "password_hash"}
    profile["permissions"] = ROLE_PERMISSIONS.get(user_dict["role"], [])
    return profile

def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Returns authenticated user profile.
    If no token is supplied, defaults to Controller (seamless demo mode fallback),
    while preserving strict role verification if a token is present.
    """
    if not token:
        # Default fallback to Controller so unauthenticated inspection scripts don't break
        default_user = USERS_DB["controller"]
        return get_user_profile(default_user)
    
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    if username not in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in railway personnel database",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return get_user_profile(USERS_DB[username])

def require_roles(allowed_roles: List[str]):
    """
    Dependency factory checking if current user has one of the allowed roles.
    """
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation restricted to roles: {', '.join(allowed_roles)}. Your active role is {user_role} ({current_user.get('designation')})."
            )
        return current_user
    return role_checker

def require_permission(permission: str):
    """
    Dependency factory checking if current user has a specific permission.
    """
    def permission_checker(current_user: dict = Depends(get_current_user)):
        permissions = current_user.get("permissions", [])
        if permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: '{permission}'. Only Section Controllers can execute this action."
            )
        return current_user
    return permission_checker
