from fastcrud import FastCRUD

from models.checklists import Checklist, ChecklistCategory


class ChecklistCRUD(FastCRUD):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


checklists_crud = ChecklistCRUD(Checklist)
checklist_categories_crud = ChecklistCRUD(ChecklistCategory)
