from datetime import datetime, timedelta
from app.forms import ItemForm
from app.db.models import Item


def addItem(item: ItemForm, updateDate, database) -> None:
    """Добавляет item в базу"""
    database.add(Item(
        id=item.id,
        parentId=item.parentId,
        url=item.url,
        size=item.size,
        type=item.type,
        updateDate=updateDate
    ))
    updateParentsDate(item.parentId, updateDate, database)


def updateParentsDate(parentId: str | None, updateDate: str, database) -> None:
    """Обновляет updateDate у parent в базе"""
    parent = database.query(Item).filter(Item.id == parentId).one_or_none()
    if parent:
        database.query(Item).filter(Item.id == parentId).update({
            'id': parent.id,
            'updateDate': updateDate
        }, synchronize_session="fetch")
        if parent.parentId:
            updateParentsDate(parent.parentId, updateDate, database)


def findFoldersInImports(items: list):
    """Ищет папки в списке items"""
    folders = []
    for item in items:
        if item.type == 'FOLDER':
            folders.append(item.id)
    return folders


def updateItem(item: ItemForm, updateDate, database) -> None:
    """Обновляет item в базе"""
    database.query(Item).filter(Item.id == item.id).update({
        'id': item.id,
        'parentId': item.parentId,
        'url': item.url,
        'size': item.size,
        'type': item.type,
        'updateDate': updateDate},
        synchronize_session="fetch")


def getDateAndYesterday(date: str) -> tuple[datetime, datetime]:
    """Возвращает дату и дату-24ч в datetime"""
    if date[-1] == 'Z':
        date = date[:-1]
    dateStr = date.split('T')[0] + ' ' + date.split('T')[1]
    try:
        date_datetime = datetime.strptime(dateStr, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        date_datetime = datetime.strptime(dateStr, "%Y-%m-%d %H:%M:%S")
    yesterday = date_datetime - timedelta(days=1)
    return date_datetime, yesterday


def checkForDay(date: datetime, yesterday: datetime, item_date: str) -> bool:
    """Проверят, лежит ли дата в диапазоне 24ч"""
    if item_date[-1] == 'Z':
        item_date = item_date[:-1]
    item_date_str = item_date.split('T')[0] + ' ' + item_date.split('T')[1]
    try:
        item_date_datetime = datetime.strptime(item_date_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        item_date_datetime = datetime.strptime(item_date_str, "%Y-%m-%d %H:%M:%S")
    return yesterday <= item_date_datetime <= date


def getLastUpdates(date: str, database) -> list[dict]:
    """Возвращает список элементов, которые были обновлены за последние 24ч"""
    ans = []
    date_d, yesterday = getDateAndYesterday(date)
    items = database.query(Item).all()
    for item in items:
        if checkForDay(date_d, yesterday, item.updateDate):
            ans.append({
                'id': item.id,
                'url': item.url,
                'date': item.updateDate,
                'parentId': item.parentId,
                'size': item.size,
                'type': item.type
            })
    return ans


def deletingChildrenOfFolder(item_id: str, database) -> None:
    """Удаляет элементы, вложенные в папку"""
    children = database.query(Item).filter(Item.parentId == item_id).all()
    for i in range(len(children)):
        if children[i].type == 'FOLDER':
            deletingChildrenOfFolder(children[i].id, database)
        database.query(Item).filter(Item.id == children[i].id).delete()


def countSize(response: dict) -> dict:
    size = 0
    for i in response['children']:
        if i.get('type') == 'FOLDER':
            countSize(i)
        if i.get('size'):
            size += i.get('size')
        response['size'] = size
    return response



def checkFolderForChildren(ans: list, item_id: str, database) -> list:
    """Возвращает элементы, вложенные в папку"""
    children = database.query(Item).filter(Item.parentId == item_id).all()
    for i in range(len(children)):
        ans.append({
            'id': children[i].id,
            'url': children[i].url,
            'type': children[i].type,
            'parentId': children[i].parentId,
            'date': children[i].updateDate,
            'size': children[i].size,
            'children': None
        })
        if children[i].type == 'FOLDER':
            ans[i]['children'] = []
            checkFolderForChildren(ans[i]['children'], children[i].id, database)
    return ans
