from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from core.security import verify_firebase_token, create_access_token, initialize_firebase, verify_token
from core.config import settings
from db.database import get_db
from db.crud import get_user_by_firebase_uid, create_user

router = APIRouter()
security = HTTPBearer()

# Initialize Firebase
initialize_firebase()


class FirebaseLogin(BaseModel):
    id_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        # Verify JWT token
        payload = verify_token(credentials.credentials)
        firebase_uid = payload.get("sub")
        
        if firebase_uid is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Get user from database
        user = get_user_by_firebase_uid(db, firebase_uid)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login_with_firebase(login_data: FirebaseLogin, db: Session = Depends(get_db)):
    try:
        # Verify Firebase token
        decoded_token = verify_firebase_token(login_data.id_token)
        firebase_uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        
        if not firebase_uid or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Firebase token"
            )
        
        # Get or create user
        user = get_user_by_firebase_uid(db, firebase_uid)
        if not user:
            user = create_user(db, firebase_uid, email)
        
        # Create access token
        access_token = create_access_token(data={"sub": firebase_uid})
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "firebase_uid": current_user.firebase_uid,
        "created_at": current_user.created_at
    }


@router.post("/logout")
async def logout():
    # In a stateless JWT system, logout is handled client-side
    # This endpoint can be used for logging or cleanup if needed
    return {"message": "Logout successful"}
