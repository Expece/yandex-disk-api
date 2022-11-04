import datetime

from fastapi import APIRouter, Depends, HTTPException
from app.forms import ImportForm
from app.db.models import connection_db, Item
from starlette import status

from app.validations import validateDate, validateItems
from app.utils.utils import deletingChildrenOfFolder, getLastUpdates, \
    checkFolderForChildren, addItem, updateItem, countSize, updateParentsDate
from app.utils.exceptions import ValidateExeption

BAD_REQUEST_DETAIL = "Невалидная схема документа или входные данные не верны."
NOT_FOUND_DETAIL = "Элемент не найден."

router = APIRouter()


@router.post('/imports', name='')
async def importItem(import_values: ImportForm, database=Depends(connection_db)):
    """
    Хендлер, принимает json, состоящий из items, структура описана forms.py,
    и updateDate, время в string ISO8601. Данные проходят валидацию и добавлятся
    в базу данных. Возвращает код статуса и описание статуса
    """
    try:
        validateDate(import_values.updateDate)
        validateItems(import_values.items, database)
    except ValidateExeption:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=BAD_REQUEST_DETAIL)
    for item in import_values.items:
        existsFile = await database.query(Item).filter(Item.id == item.id).one_or_none()
        if existsFile:
            updateItem(item, import_values.updateDate, database)
        else:
            addItem(item, import_values.updateDate, database)
    await database.commit()
    raise HTTPException(status_code=status.HTTP_200_OK, detail="Вставка или обновление прошли успешно.")


@router.delete('/delete/{id}', name='')
async def deleteItem(item_id: str, date: str = datetime.datetime.now().isoformat(), database=Depends(connection_db)):
    """
    Принимает id элемента, проверяет существует ли такой элемент. Удаляет элемент
    из базы данных и обновляет updateDate у parent(s), если это file, если это folder,
    то удаляет его и все вложенные элементы
    """
    # проверка на существование элемента
    existsFile = await database.query(Item).filter(Item.id == item_id).one_or_none()
    if existsFile:
        if existsFile.type == 'FOLDER':
            deletingChildrenOfFolder(item_id, database)
        updateParentsDate(existsFile.parentId, date, database)
        await database.query(Item).filter(Item.id == item_id).delete()
        await database.commit()
        raise HTTPException(status_code=status.HTTP_200_OK, detail="Удаление прошло успешно.")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND_DETAIL)


@router.get('/nodes/{id}', name='')
async def getNodes(id: str, database=Depends(connection_db)):
    """
    Принимает id элемента, возвращает словарь с данными элемента и childrens,
    если это папка.
    """
    # проверка на существование элемента
    existsItem = await database.query(Item).filter(Item.id == id).one_or_none()
    if existsItem and existsItem.type == 'FILE':
        return {
            'id': existsItem.id,
            'url': existsItem.url,
            'type': existsItem.type,
            'parentId': existsItem.parentId,
            'date': existsItem.updateDate,
            'size': existsItem.size
        }
    elif existsItem and existsItem.type == 'FOLDER':
        response = {
            'id': existsItem.id,
            'url': existsItem.url,
            'type': existsItem.type,
            'parentId': existsItem.parentId,
            'date': existsItem.updateDate,
            'size': existsItem.size,
            'children': []
        }
        checkFolderForChildren(response['children'], id, database)
        response = countSize(response)
        return response
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND_DETAIL)


@router.get('/updates', name='')
async def getUpdates(date: str, database=Depends(connection_db)):
    """
    Принимает дату iso8601, возвращает элементы, которые были обновлены за последние 24ч.
    """
    if not validateDate(date):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=BAD_REQUEST_DETAIL)
    return {'items': getLastUpdates(date, database)}
