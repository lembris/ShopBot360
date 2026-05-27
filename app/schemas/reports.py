from pydantic import BaseModel


class ReportSummary(BaseModel):
    today: str
    week: str
