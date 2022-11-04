import re

from app.db.models import Item
from app.forms import ItemForm
from app.utils.exceptions import ValidateExeption, NotFoundExeption
from app.utils.utils import findFoldersInImports


def validateDate(s: str) -> bool:
    """Проверяет соответствует ли дата фомату ISO8601"""
    regular = r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])' \
            r'T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|' \
            r'[01][0-9]):[0-5][0-9])?$'
    match_iso8601 = re.compile(regular).match
    try:
        if match_iso8601(s) is not None:
            return True
    except:
        pass
    raise ValidateExeption("Invalid date")


def validateFile(item: ItemForm) -> bool:
    """Валидация файла"""
    if item.url != None and (len(item.url) <= 255):
        if item.size and item.size > 0:
            return True
    raise ValidateExeption("Invalid file")


def validateFolder(item: ItemForm) -> bool:
    """Валидация папки"""
    if not item.url:
        if not item.size:
            return True
    raise ValidateExeption("Invalid folder")


def validateItems(items: list[ItemForm], database) -> bool:
    """Валидация данных"""
    # проверка id на уникальность
    item_id_set = set([item.id for item in items])
    if len(item_id_set) != len(items):
        raise ValidateExeption("Invalid item")
    importFolders = findFoldersInImports(items)
    for item in items:
        if item.id:
            # проверка существования поля parent
            parent = database.query(Item).filter(Item.id == item.parentId).one_or_none()
            if not item.parentId or item.parentId == "0" or parent or (item.parentId in importFolders):
                if item.type == 'FILE':
                    if validateFile(item):
                        continue
                elif item.type == 'FOLDER':
                    if validateFolder(item):
                        continue
            raise ValidateExeption("Invalid item")
        raise ValidateExeption("Invalid item")
    return True

def validateUrl(url_headers:list[str], database):
    if url_headers[-1] == "":
        url_headers.pop(-1)

    if not (url_headers and url_headers[0].lower() == 'home'):
        raise ValidateExeption("Invalid item")
    if "" in url_headers:
        raise ValidateExeption("Invalid item")

    for i in range(1, len(url_headers)):
        item = database.query(Item).filter(Item.id == url_headers[i]).one_or_none()
        if item:
            if item.type == 'FOLDER':
                if i + 1 < len(url_headers):
                    next_item = database.query(Item).filter(Item.id == url_headers[i+1]).one_or_none()
                    if next_item:
                        if item.id == next_item.parentId:
                            continue
                        else:
                            raise ValidateExeption("Invalid item")
                    else:
                        raise NotFoundExeption("Item not found")   
                else:
                    continue
            else:
                raise ValidateExeption("Invalid item")
        else:
            raise NotFoundExeption("Item not found")