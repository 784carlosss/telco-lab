import os
import socket
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

DATABASE_URL = os.environ["DATABASE_URL"]


def get_conn():
    return psycopg.connect(DATABASE_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lines (
                msisdn TEXT PRIMARY KEY,
                iccid  TEXT NOT NULL,
                plan   TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )
    yield


app = FastAPI(title="Line Activation API", version="0.2.0", lifespan=lifespan)


class LineRequest(BaseModel):
    msisdn: str
    iccid: str
    plan: str


class Line(LineRequest):
    status: str


@app.get("/health")
def health():
    return {"status": "ok", "pod": socket.gethostname()}


@app.post("/lines", status_code=201)
def activate_line(request: LineRequest) -> Line:
    line = Line(**request.model_dump(), status="active")
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO lines (msisdn, iccid, plan, status) VALUES (%s, %s, %s, %s)",
                (line.msisdn, line.iccid, line.plan, line.status),
            )
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Line already exists")
    return line


@app.get("/lines/{msisdn}")
def get_line(msisdn: str) -> Line:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT msisdn, iccid, plan, status FROM lines WHERE msisdn = %s",
            (msisdn,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Line not found")
    return Line(msisdn=row[0], iccid=row[1], plan=row[2], status=row[3])
