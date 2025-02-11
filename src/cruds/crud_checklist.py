from fastcrud import FastCRUD

from models.checklist import UserChecklist, SuggestChecklist


class ChecklistCRUD(FastCRUD):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


suggest_checklist_item_crud = ChecklistCRUD(SuggestChecklist)
user_checklist_crud = ChecklistCRUD(UserChecklist)
