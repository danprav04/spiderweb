import asyncio
import json
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException

from app.authentication import user_role_checker
from app.models.core_device import CoreDevice
from app.repositories.coredevice_repository import CoreDeviceRepository
from app.repositories.site_repository import SiteRepository
from app.database import get_async_db
from app.schemas.site import SiteCreate, Site, SiteDescription
from network.spectrum_topology import export_map

router = APIRouter()

@router.get("/site/{site_id}", response_model=Site)
async def get_site(site_id: int, current_user: dict = Depends(user_role_checker),
                   db=Depends(get_async_db)):
    """
    Retrieves a site by its ID.

    :param site_id: The ID of the site to be retrieved.
    :param db: Takes the database as a dependency.
    :param user: Takes the bearer token as a dependency, representing the currently authenticated user.
    :return: The Site object representing the site with the specified ID.
    """
    repository = SiteRepository(db)
    db_site = await repository.get_site(site_id)  # Make it awaitable
    if db_site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    return db_site


@router.get("/coredevice/{coredevice_id}/sites", response_model=List[Site])
async def get_sites_of_coredevice(coredevice_id: int,
                                  current_user: dict = Depends(user_role_checker),
                                  db=Depends(get_async_db)):
    """
    Retrieves all sites associated with a core device.

    :param coredevice_id: The ID of the core device.
    :param db: Takes the database as a dependency.
    :param user: Takes the bearer token as a dependency, representing the currently authenticated user.
    :return: A list of Site objects representing the sites associated with the core device.
    """
    site_repository = SiteRepository(db)
    db_coredevice = await db.execute(
        db.query(CoreDevice).filter(CoreDevice.id == coredevice_id).first()
    )
    if db_coredevice is None:
        raise HTTPException(status_code=404, detail="Core device not found")

    sites = await site_repository.get_sites_of_coredevice(coredevice_id)
    return sites

@router.get("/sites", response_model=List[Dict[str, str]])
async def get_all_sites(current_user: dict = Depends(user_role_checker),
                        db=Depends(get_async_db)):
    """
    Retrieves all sites with their IDs and names.

    :param user: Takes the bearer token as a dependency, representing the currently authenticated user.
    :return: A list of dictionaries, each containing the ID and name of a site.
    """
    repository = SiteRepository(db)
    db_sites = await repository.get_sites()  # Make it awaitable
    sites = [{"id": str(site.id), "name": site.name} for site in db_sites]
    return sites

@router.post("/site/{site_id}/set-topology")
async def set_topology(site_id: int, current_user: dict = Depends(user_role_checker),
                       db=Depends(get_async_db)):
    """
    Sets the topology of a site.

    :param site_id: The ID of the site.
    :param current_user: The currently authenticated user.
    :return: A message indicating whether the topology was set successfully.
    """
    repository = SiteRepository(db)
    db_site = await repository.get_site(site_id)
    if db_site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    # Get the site name from the database
    site_name = db_site.name

    # Define a timeout in seconds
    timeout = 60  # 1 minute

    # Create a loop to run the export_map function in a separate thread
    loop = asyncio.get_running_loop()
    try:
        # Run the export_map function in a separate thread with a timeout
        topology = await asyncio.wait_for(
            loop.run_in_executor(None, export_map, site_name),
            timeout
        )
    except asyncio.TimeoutError:
        # If the timeout is reached, raise an exception
        raise HTTPException(status_code=500, detail="Failed to set topology due to timeout")

    # Set the topology to the database
    if isinstance(topology, tuple):
        await repository.update_site(
            site_id,
            SiteCreate(
                name=db_site.name,
                topology=json.dumps(topology),
                description=db_site.description
            )
        )
        return {"message": "Topology set successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to set topology")

@router.get("/site/{site_id}/get-topology")
async def get_topology(site_id: int, current_user: dict = Depends(user_role_checker),
                       db=Depends(get_async_db)):
    """
    Gets the topology of a site.

    :param site_id: The ID of the site.
    :param current_user: The currently authenticated user.
    :return: The topology of the site.
    """
    repository = SiteRepository(db)
    db_site = await repository.get_site(site_id)
    if db_site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    try:
        if not db_site.topology or db_site.topology == '':
            raise HTTPException(status_code=404, detail="Topology not found")
        topology = json.loads(db_site.topology)
        return topology
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid topology data")

@router.put("/site/{site_id}/set-description")
async def update_site_description(site_id: int, description: SiteDescription, current_user: dict = Depends(user_role_checker),
                                  db=Depends(get_async_db)):
    """
    Updates the description of a site.

    :param site_id: The ID of the site.
    :param description: The new description of the site.
    :param current_user: The currently authenticated user.
    :return: A message indicating whether the description was updated successfully.
    """
    repository = SiteRepository(db)
    db_site = await repository.get_site(site_id)
    if db_site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    await repository.update_site(
        site_id,
        SiteCreate(
            name=db_site.name,
            topology=db_site.topology,
            description=description.description
        )
    )
    return {"message": "Description updated successfully"}

@router.get("/site/{site_id}/get-description")
async def get_site_description(site_id: int, current_user: dict = Depends(user_role_checker),
                               db=Depends(get_async_db)):
    """
    Gets the description of a site.

    :param site_id: The ID of the site.
    :param current_user: The currently authenticated user.
    :return: The description of the site.
    """
    repository = SiteRepository(db)
    db_site = await repository.get_site(site_id)
    if db_site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    return db_site.description
