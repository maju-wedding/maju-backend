from fastcrud import FastCRUD

from models.checklist import DefaultChecklistItem, CustomChecklistItem, UserChecklist


class ChecklistCRUD(FastCRUD):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


default_checklist_item_crud = ChecklistCRUD(DefaultChecklistItem)
custom_checklist_item_crud = ChecklistCRUD(CustomChecklistItem)
user_checklist_crud = ChecklistCRUD(UserChecklist)
