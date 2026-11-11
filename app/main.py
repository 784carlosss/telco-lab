from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Line Activation API", version="0.1.0")


class LineRequest(BaseModel):
    msisdn: str
    iccid: str
    plan: str


class Line(LineRequest):
    status: str


lines: dict[str, Line] = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/lines", status_code=201)
def activate_line(request: LineRequest) -> Line:
    if request.msisdn in lines:
        raise HTTPException(status_code=409, detail="Line already exists")
    line = Line(**request.model_dump(), status="active")
    lines[request.msisdn] = line
    return line


@app.get("/lines/{msisdn}")
def get_line(msisdn: str) -> Line:
    if msisdn not in lines:
        raise HTTPException(status_code=404, detail="Line not found")
    return lines[msisdn]
