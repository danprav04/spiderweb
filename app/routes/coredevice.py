from typing import Dict

from app.authentication import user_role_checker, admin_role_checker
from app.models.core_device import CoreDevice as CoreDeviceModel
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_async_db
from app.repositories.coresite_repository import CoreSiteRepository
from app.repositories.coredevice_repository import CoreDeviceRepository
from app.schemas.coredevice import CoreDevice, CoreDeviceCreate

router = APIRouter()

@router.get("/coresite/{coresite_id}/coredevices")
async def get_core_devices(coresite_id: int, db=Depends(get_async_db), current_user: dict = Depends(user_role_checker)):
    """
       Retrieves a list of core devices for a given core site.

       :param coresite_id: a core site id (ex. 1, 2...)
       :param db: takes the database as a dependency
       :param user: takes the bearer token as a dependency
       :return: A list of CoreDevice objects.
       """

    core_device_repository = CoreDeviceRepository(db)
    coredevices = await core_device_repository.get_coresite_coredevices(coresite_id)
    if coredevices:
        return [{
                    key: value
                    for key, value in coredevice.__dict__.items()
                    if key != 'coresite_id'
                } for coredevice in coredevices]
    return []

@router.get("/network/{network_id}/coresite/{coresite_id}/coredevices")
async def get_coresite_coredevices_with_network(network_id: int, coresite_id: int, db=Depends(get_async_db)):
    core_device_repository = CoreDeviceRepository(db)
    coredevices = await core_device_repository.get_coresite_coredevices_with_network(coresite_id, network_id)
    if coredevices:
        return [{
                    key: value
                    for key, value in coredevice.__dict__.items()
                    if key != 'coresite_id'
                } for coredevice in coredevices]
    return []

@router.post("/admin/coredevice/create/")
async def create_coredevice_admin(coredevice: CoreDeviceCreate, current_user: dict = Depends(admin_role_checker), db=Depends(get_async_db)):
    """
    Creates a new coredevice.

    :param coredevice: The coredevice to be created.
    :param current_user: The currently logged-in user, which must be an admin.
    :param db: Takes the database as a dependency.
    :return: The newly created CoreDevice object.
    """
    coredevice_repo = CoreDeviceRepository(db)
    exist = db.query(CoreDeviceModel).filter_by(name=coredevice.name).first()
    if exist:
        raise HTTPException(status_code=400, detail="coredevice already exists.")
    db_coredevice = coredevice_repo.create_coredevice(coredevice, 1, [])
    return db_coredevice

@router.delete("/admin/coredevice/delete/{coredevice_id}")
async def delete_coredevice_admin(coredevice_id: int, current_user: dict = Depends(admin_role_checker), db=Depends(get_async_db)):
    """
    Deletes a coredevice.

    :param coredevice_id: The ID of the coredevice to be deleted.
    :param current_user: The currently logged-in user, which must be an admin.
    :param db: Takes the database as a dependency.
    :return: No content is returned. A successful deletion will result in a 204 No Content status code.
    """
    coredevice_repo = CoreDeviceRepository(db)
    coredevice_model = db.query(CoreDeviceModel).get(coredevice_id)
    if not coredevice_model:
        raise HTTPException(status_code=404, detail='coredevice not found.')
    if coredevice_repo.delete_coredevice(coredevice_id):
        return {"message": "Coredevice deleted successfully"}
    else:
        raise HTTPException(status_code=400, detail="Coredevice is associated with coresite, cannot delete")