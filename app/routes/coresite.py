from fastapi import APIRouter, Depends, HTTPException

from app.authentication import user_role_checker, admin_role_checker
from app.database import get_async_db
from app.repositories.coredevice_repository import CoreDeviceRepository
from app.schemas.coredevice import CoreDevice
from app.repositories.coresite_repository import CoreSiteRepository
from app.schemas.coresite import CoreSite, CoreSiteCreate
from app.models.core_site import CoreSite as CoreSiteModel
from typing import Dict

router = APIRouter()

@router.get("/coresite/{coresite_id}/coredevices")
async def get_core_devices(coresite_id: int, db=Depends(get_async_db), current_user: dict = Depends(user_role_checker)):
    """
    Retrieves a list of core devices for a given core site.

    :param coresite_id: a core site id (ex. 1, 2...)
    :param db: takes the database as a dependency
    :param user: takes the bearer token as a dependency
    :return: A list of dictionaries, each containing the id, name, and ip of a core device.
    """

    core_device_repository = CoreDeviceRepository(db)
    return [{"id": core_device.id, "name": core_device.name, "ip": core_device.ip} for core_device in core_device_repository.get_coresite_coredevices(coresite_id)]

@router.post("/admin/coresite/create/")
async def create_coresite_admin(coresite: CoreSiteCreate, current_user: dict = Depends(admin_role_checker), db=Depends(get_async_db)):
    """
    Creates a new coresite.

    :param coresite: The coresite to be created.
    :param current_user: The currently logged-in user, which must be an admin.
    :param db: Takes the database as a dependency.
    :return: The newly created CoreSite object.
    """
    coresite_repo = CoreSiteRepository(db)
    exist = db.query(CoreSiteModel).filter_by(name=coresite.name).first()
    if exist:
        raise HTTPException(status_code=400, detail="coresite already exists.")
    db_coresite = coresite_repo.create_coresite(coresite, [])
    return db_coresite

@router.delete("/admin/coresite/delete/{coresite_id}")
async def delete_coresite_admin(coresite_id: int, current_user: dict = Depends(admin_role_checker), db=Depends(get_async_db)):
    """
    Deletes a coresite.

    :param coresite_id: The ID of the coresite to be deleted.
    :param current_user: The currently logged-in user, which must be an admin.
    :param db: Takes the database as a dependency.
    :return: No content is returned. A successful deletion will result in a 204 No Content status code.
    """
    coresite_repo = CoreSiteRepository(db)
    coresite_model = db.query(CoreSiteModel).get(coresite_id)
    if not coresite_model:
        raise HTTPException(status_code=404, detail='coresite not found.')
    if coresite_repo.delete_coresite(coresite_id):
        return {"message": "Coresite deleted successfully"}
    else:
        raise HTTPException(status_code=400, detail="Coresite is associated with coredevice, cannot delete")