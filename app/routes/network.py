from fastapi import APIRouter, Depends, HTTPException
from typing import Dict

from app.authentication import user_role_checker, admin_role_checker
from app.database import get_async_db
from app.repositories.network_repository import NetworkRepository
from app.schemas.network import Network, NetworkCreate
from app.models.network import Network as NetworkModel

router = APIRouter()

@router.get("/networks/")
async def get_networks(current_user: dict = Depends(user_role_checker), db=Depends(get_async_db)):
    """
    Retrieves a list of networks.

    :param db: takes the database as a dependency
    :param user: takes the bearer token as a dependency
    :return: A list of Network objects.
    """
    network_repository = NetworkRepository(db)
    networks = await network_repository.get_networks()
    return [{"id": network.id, "name": network.name} for network in networks]

@router.get("/network/{network_id}/coresites")
async def get_network_coresites(network_id: int, current_user: dict = Depends(user_role_checker), db=Depends(get_async_db)):
    """
    Retrieves a list of core sites for a given network.

    :param network_id: a network id (ex. 1, 2, 3)
    :param db: takes the database as a dependency
    :param user: takes the bearer token as a dependency
    :return: A list of CoreSite objects.
    """
    network_repository = NetworkRepository(db)
    coresites = await network_repository.get_coresites(network_id)
    return [{"id": core_site.id, "name": core_site.name} for core_site in coresites]


@router.post("/admin/network/create/")
async def create_network_admin(network: NetworkCreate, current_user: dict = Depends(admin_role_checker), db=Depends(get_async_db)):
    """
    Creates a new network.

    :param network: The network to be created.
    :param current_user: The currently logged-in user, which must be an admin.
    :param db: Takes the database as a dependency.
    :return: The newly created Network object.
    """
    network_repo = NetworkRepository(db)
    exist = await db.execute(db.query(NetworkModel).filter_by(name=network.name).statement)
    exist = exist.scalars().first()
    if exist:
        raise HTTPException(status_code=400, detail="network already exists.")
    db_network = await network_repo.create_network(network)
    return db_network

@router.delete("/admin/network/delete/{network_id}")
async def delete_network_admin(network_id: int, current_user: dict = Depends(admin_role_checker), db=Depends(get_async_db)):
    """
    Deletes a network.

    :param network_id: The ID of the network to be deleted.
    :param current_user: The currently logged-in user, which must be an admin.
    :param db: Takes the database as a dependency.
    :return: No content is returned. A successful deletion will result in a 204 No Content status code.
    """
    network_repo = NetworkRepository(db)
    network_model = await db.execute(db.query(NetworkModel).filter_by(id=network_id).statement)
    network_model = network_model.scalars().first()
    if not network_model:
        raise HTTPException(status_code=404, detail='network not found.')
    if await network_repo.delete_network(network_id):
        return {"message": "Network deleted successfully"}
    else:
        raise HTTPException(status_code=400, detail="Network is associated with coresite or coredevice, cannot delete")