import sys
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

PIPELINE_DIR = Path(__file__).resolve().parent.parent / "pipeline"
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from pipeline.report import build_report


class ReviewRequest(BaseModel):
    narrative: str


app = FastAPI()


@app.post("/review")
def create_review(request: ReviewRequest) -> dict:
    return build_report(request.narrative)