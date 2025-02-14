from fastcrud import FastCRUD

from models.checklist import UserChecklist, SuggestChecklist


class ChecklistCRUD(FastCRUD):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


suggest_checklists_crud = ChecklistCRUD(SuggestChecklist)
user_checklists_crud = ChecklistCRUD(UserChecklist)
