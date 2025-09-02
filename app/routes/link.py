# app/routes/link.py
import json
from dataclasses import asdict
from datetime import datetime
from http import HTTPStatus
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.authentication import user_role_checker
from app.models.link import Link
from app.repositories.link_repository import LinkRepository
from app.database import get_async_db
from app.repositories.user_repository import UserRepository
from app.schemas.link import *
from typing import Optional

from network.config import INTERFACE_STATES, OSPF_STATES, MPLS_STATES

router = APIRouter()

@router.get("/link/{link_id}", response_model=Link)
async def get_link(
    link_id: int,
    db=Depends(get_async_db),
    current_user: dict = Depends(user_role_checker)
):
    """
    Retrieves a link by its ID.

    :param link_id: The ID of the link to be retrieved.
    :param db: Takes the database as a dependency, for storing and retrieving link data.
    :param current_user: Takes the bearer token as a dependency.
    :return: The Link object representing the link with the specified ID,
            with attributes 'id', 'url', and 'description'.
    """

    repository = LinkRepository(db)
    db_link = await repository.get_link(link_id)  # Added await

    if db_link is None:
        raise HTTPException(status_code=404, detail="Link not found")

    return db_link


@router.get("/links")
async def get_filtered_links(
        skip: int = Query(0, ge=0),
        limit: int = Query(20),
        coredevice_id: Optional[int] = None,
        neighbor_site_id: Optional[str] = None,
        neighbor_coredevice_id: Optional[str] = None,
        filters: LinkBase = Depends(),
        start_date: Optional[str] = Query(None),
        end_date: Optional[str] = Query(None),
        crawler_cycle: Optional[int] = Query(None),
        db=Depends(get_async_db),
        current_user: dict = Depends(user_role_checker)
):
    link_repo = LinkRepository(db)

    # Parse date range
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Please use YYYY-MM-DD.")
    else:
        start_date = None
        end_date = None

    # Get links
    links = await link_repo.get_links(skip, limit, coredevice_id,
                                neighbor_site_id='*' if neighbor_site_id == '*' else neighbor_site_id,
                                neighbor_coredevice_id='*' if neighbor_coredevice_id == '*' else neighbor_coredevice_id,
                                filters=filters, start_date=start_date, end_date=end_date, crawler_cycle=crawler_cycle
)  # Added await

    return [link.to_dict() for link in links]


@router.get("/coredevice/{coredevice_id}/links-to-end-sites")
async def get_links_to_end_sites(
    coredevice_id: Optional[int] = None,
    db=Depends(get_async_db),
    current_user: dict = Depends(user_role_checker)
):
    link_repo = LinkRepository(db)
    links = await link_repo.get_links_to_end_sites(coredevice_id)  # Added await

    return [link.to_dict() for link in links]


@router.get("/interface-states")
async def get_interface_states(current_user: dict = Depends(user_role_checker), db=Depends(get_async_db)):
    return INTERFACE_STATES


@router.get("/ospf-states")
async def get_ospf_states(current_user: dict = Depends(user_role_checker), db=Depends(get_async_db)):
    return OSPF_STATES


@router.get("/mpls-states")
async def get_mpls_states(current_user: dict = Depends(user_role_checker), db=Depends(get_async_db)):
    return MPLS_STATES


@router.get("/favorite-links")
async def get_favorite_links(current_user: dict = Depends(user_role_checker), db=Depends(get_async_db)):
    """
    Retrieves a list of favorite links for the current user.

    :param current_user: The current user.
    :param db: The database.
    :return: A list of favorite links for the current user.
    """
    user_repo = UserRepository(db)
    return await user_repo.get_user_links(user_id=current_user.get('id'))  # Added await


@router.post("/add-favorite-link/{link_id}")
async def add_favorite_link(link_id: int, current_user: dict = Depends(user_role_checker), db=Depends(get_async_db)):
    """
    Adds a link to the current user's favorite links.

    :param link_id: The ID of the link to be added.
    :param current_user: The current user.
    :param db: The database.
    :return: A success message if the link is added successfully.
    """
    link_repo = LinkRepository(db)
    user_repo = UserRepository(db)
    link = await link_repo.get_link(link_id)  # Added await
    user = await user_repo.get_user(current_user["id"])  # Added await
    if link and user:
        await user_repo.add_link_to_user(user.id, link.id)  # Added await
        return {"message": "Link added to favorites successfully"}
    else:
        raise HTTPException(status_code=404, detail="Link or user not found")


@router.delete("/delete-favorite-link/{link_id}")
async def delete_favorite_link(link_id: int, current_user: dict = Depends(user_role_checker), db=Depends(get_async_db)):
    """
    Deletes a link from the current user's favorite links.

    :param link_id: The ID of the link to be deleted.
    :param current_user: The current user.
    :param db: The database.
    :return: A success message if the link is deleted successfully.
    """
    link_repo = LinkRepository(db)
    user_repo = UserRepository(db)
    link = await link_repo.get_link(link_id)  # Added await
    user = await user_repo.get_user(current_user["id"])  # Added await
    if link and user:
        await user_repo.remove_link_from_user(user.id, link.id)  # Added await
        return {"message": "Link removed from favorites successfully"}
    else:
        raise HTTPException(status_code=404, detail="Link or user not found")


@router.get("/links/topology")
async def get_links_with_neighbors(db=Depends(get_async_db)):
    link_repo = LinkRepository(db)
    links = await link_repo.get_links_with_neighbors()  # Added await

    return links
