from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from app.forms import ImportForm
from app.db.models import connection_db, Item
from starlette import status

from app.validations import validateDate, validateItems, validateUrl
from app.utils.utils import deletingChildrenOfFolder, getLastUpdates, \
    checkFolderForChildren, addItem, updateItem, countSize, updateParentsDate
from app.utils.exceptions import ValidateExeption, NotFoundExeption

BAD_REQUEST_DETAIL = "Невалидная схема документа или входные данные не верны."
NOT_FOUND_DETAIL = "Элемент не найден."

router = APIRouter()


@router.post('/imports', name='')
def importItem(import_values: ImportForm, database=Depends(connection_db)):
    """
    Импортирует элементы файловой системы. Элементы импортированные повторно обновляют текущие.
    Изменение типа элемента с папки на файл и с файла на папку не допускается.
    Порядок элементов в запросе является произвольным.

    - id каждого элемента является уникальным среди остальных элементов
    - поле id не может быть равно null
    - родителем элемента может быть только папка
    - принадлежность к папке определяется полем parentId
    - элементы могут не иметь родителя (при обновлении parentId на null элемент остается без родителя)
    - поле url при импорте папки всегда должно быть равно null
    - размер поля url при импорте файла всегда должен быть меньше либо равным 255
    - поле size при импорте папки всегда должно быть равно null
    - поле size для файлов всегда должно быть больше 0
    - при обновлении элемента обновленными считаются **все** их параметры
    - при обновлении параметров элемента обязательно обновляется поле **date** в соответствии с временем обновления
    - в одном запросе не может быть двух элементов с одинаковым id
    - дата обрабатывается согласно ISO 8601 (такой придерживается OpenAPI). Если дата не удовлетворяет данному формату, ответом будет код 400.
    """
    try:
        validateDate(import_values.updateDate)
        validateItems(import_values.items, database)
    except ValidateExeption:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=BAD_REQUEST_DETAIL)
    
    for item in import_values.items:
        existsFile = database.query(Item).filter(Item.id == item.id).one_or_none()
        if existsFile:
            updateItem(item, import_values.updateDate, database)
        else:
            addItem(item, import_values.updateDate, database)
    
    database.commit()
    raise HTTPException(status_code=status.HTTP_200_OK, detail="Вставка или обновление прошли успешно.")


@router.delete('/delete/{id}', name='')
def deleteItem(item_id: str, date: str = datetime.now().isoformat(), database=Depends(connection_db)):
    """
    Удалить элемент по идентификатору. При удалении папки удаляются все дочерние элементы.
    Доступ к истории обновлений удаленного элемента невозможен.
    """
    # проверка на существование элемента
    existsFile = database.query(Item).filter(Item.id == item_id).one_or_none()
    if existsFile:
        if existsFile.type == 'FOLDER':
            deletingChildrenOfFolder(item_id, database)
        updateParentsDate(existsFile.parentId, date, database)
        database.query(Item).filter(Item.id == item_id).delete()
        database.commit()
        raise HTTPException(status_code=status.HTTP_200_OK, detail="Удаление прошло успешно.")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND_DETAIL)


@router.get('/nodes/{id}', name='')
def getNodes(id: str, database=Depends(connection_db)):
    """
    Получить информацию об элементе по идентификатору. При получении информации о папке также 
    предоставляется информация о её дочерних элементах.

    - для пустой папки поле children равно пустому массиву, а для файла равно null
    - размер папки - это суммарный размер всех её элементов. Если папка не содержит элементов, 
    то размер равен 0. При обновлении размера элемента, суммарный размер папки, которая содержит 
    этот элемент, тоже обновляется.
    """
    # проверка на существование элемента
    existsItem = database.query(Item).filter(Item.id == id).one_or_none()
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
def getUpdates(date: str, database=Depends(connection_db)):
    """
    Получение списка **файлов**, которые были обновлены за последние 24 часа включительно 
    [date - 24h, date] от времени переданном в запросе.
    """
    if not validateDate(date):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=BAD_REQUEST_DETAIL)
    return {'items': getLastUpdates(date, database)}


@router.get('/children', name='')
def getChildren(url:str, database=Depends(connection_db)):
    """
    Вводите путь -> показывает вложенные файлы. Начинать с home/
    """
    url_headers = url.strip().split('/')
    response = {'url_headings': url_headers, 'items':[url_headers[-1]]}

    try:
        validateUrl(url_headers, database)
    except ValidateExeption:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=BAD_REQUEST_DETAIL)
    except NotFoundExeption:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND_DETAIL)

    if len(url_headers) == 1:
        response['items'] = database.query(Item).filter(Item.parentId == None).all()
        return response
    last_header = url_headers[-1]
    response['items'] = database.query(Item).filter(Item.parentId == last_header).all()

    return response

    # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=BAD_REQUEST_DETAIL)