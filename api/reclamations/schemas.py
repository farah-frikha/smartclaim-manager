from pydantic import BaseModel


class ReclamationRequest(BaseModel):
    dossier_id: int
    message: str


class ReponseRequest(BaseModel):
    reponse: str