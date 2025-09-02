import os
from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException
from app.authentication import verify_g, generate_token, admin_role_checker
from app.repositories.user_repository import UserRepository
from app.database import get_async_db
from app.schemas.user import UserCreate, LoginRequest

router = APIRouter()

SECRET_KEY = os.environ.get('SECRET_KEY')


@router.post("/login")
async def login(request: LoginRequest, db=Depends(get_async_db)):
    """
    Authenticates a user and returns an access token.
    :param request: A request containing the username and password to be used for authentication.
    :param db: Takes the database as a dependency.
    :return: A dictionary containing the access token and its type.
    """
    user_repo = UserRepository(db)
    username = request.username
    password = request.password

    if verify_g(username, password):
        user = await user_repo.get_user_by_username(username)  # Added await here
        if not user:
            result = await user_repo.create_user(UserCreate(username=username))  # Added await here
            user = result['user']
        token = generate_token(secret_key=SECRET_KEY, user_id=user.id)
        return [{"access_token": token, "token_type": "bearer"}, {"role": user.role}]
    else:
        raise HTTPException(status_code=401, detail="Incorrect username or password")


@router.get("/users/")
async def get_all_users(current_user: dict = Depends(admin_role_checker), db=Depends(get_async_db)):
    """
    Returns a list of all users.
    :param current_user: The currently logged-in user, which must be an admin.
    :return: A list of all users.
    """
    user_repo = UserRepository(db)
    try:
        users = await user_repo.get_users()  # Added await here
        return [{"id": user.id, "username": user.username, "role": user.role} for user in users]
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/users/{user_id}/make-admin")
async def make_user_admin(user_id: int, current_user: dict = Depends(admin_role_checker), db=Depends(get_async_db)):
    """
    Makes a user an admin.
    :param user_id: The ID of the user to make an admin.
    :param current_user: The currently logged-in user, which must be an admin.
    :return: A success message.
    """
    user_repo = UserRepository(db)
    try:
        user = await user_repo.get_user(user_id)  # Added await here
        if user:
            result = await user_repo.update_user(user_id,
                                                 UserCreate(username=user.username, role="admin"))  # Added await here
            return {"message": f"User {user.username} is now an admin"}
        else:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))