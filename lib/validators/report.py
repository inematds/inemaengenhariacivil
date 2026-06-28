"""Modelos da saída de validação."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Status = Literal["ok", "warning", "fail"]


class Check(BaseModel):
    name: str
    status: Status
    detail: str


class ValidationReport(BaseModel):
    passed: bool
    checks: list[Check]
    warnings: list[str] = []
