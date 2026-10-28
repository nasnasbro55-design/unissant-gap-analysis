import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PIPELINE_DIR = Path(__file__).resolve().parent.parent / "pipeline"
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from pipeline.report import build_report


class ReviewRequest(BaseModel):
    narrative: str


app = FastAPI()
# the React dev server runs on another port; allow local front ends only (set UI_ORIGINS to override)
import os
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("UI_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","), allow_methods=["POST"], allow_headers=["*"])


@app.post("/review")
def create_review(request: ReviewRequest) -> dict:
    return build_report(request.narrative)