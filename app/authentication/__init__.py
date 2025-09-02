from typing import Optional, Dict, AsyncGenerator, Annotated
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from jose import jwt, JWTError
from starlette import status

from app import get_async_db
from app.repositories.user_repository import UserRepository
from network.paramiko_connection_CiscoDevices import create_device, AuthenticationException
from app.config import Config

ALGORITHM = Config().ALGORITHM
TESTING_DEVICE = Config().TESTING_DEVICE
SECRET_KEY = Config().SECRET_KEY
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='/login')


def verify_g(username: str, password: str):
    try:
        create_device(TESTING_DEVICE, username, password)
        return True
    except AuthenticationException:
        return False


def generate_token(secret_key, user_id: int):
    to_encode = {'id': user_id}
    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)


class RoleChecker:
    def __init__(self, required_role: Optional[str] = None):
        self.required_role = required_role

    async def __call__(
        self,
        token: Annotated[str, Depends(HTTPBearer())],
        db: AsyncGenerator = Depends(get_async_db)
    ) -> Dict:
        try:
            payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get('id')

            user_repo = UserRepository(db)
            user = await user_repo.get_user(user_id)

            username = None
            role = None
            if user:
                user_id: int = user.id
                username: str = user.username
                role: str = user.role

            if username is None or role is None:
                raise HTTPException(status_code=401, detail='could not validate user')

            if self.required_role and role not in self.required_role.split(','):
                raise HTTPException(status_code=403, detail='operation not permitted')

            return {'id': user_id, 'sub': username, 'role': role}
        except JWTError as e:
            raise HTTPException(status_code=401, detail=f'could not validate user: {str(e)}')


# Define instances without triggering constructor logic at module level
admin_role_checker = RoleChecker(required_role="admin")
user_role_checker = RoleChecker(required_role="user, admin")
