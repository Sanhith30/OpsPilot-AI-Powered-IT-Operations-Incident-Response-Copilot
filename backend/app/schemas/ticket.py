from typing import Literal
from pydantic import BaseModel,ConfigDict
TicketPriority=Literal["LOW","MEDIUM","HIGH","URGENT"]
TicketStatus=Literal["OPEN","IN_PROGRESS","BLOCKED","RESOLVED","CLOSED"]
class TicketCreate(BaseModel):
    model_config=ConfigDict(extra="forbid")
    ticket_number:str
    title:str
    priority:TicketPriority
    incident_id:int
    assigned_team_id:int|None=None
    assigned_user_id:int|None=None
    description:str|None=None
    comment_text:str|None=None
class TicketResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    ticket_id:int
    ticket_number:str
    incident_id:int
    title:str
    description:str|None
    priority:str
    status:str
    assigned_team_id:int|None
    assigned_user_id:int|None
    created_by:int
