"""Deterministic scoring over the final answer and private run database."""

import json
import sqlite3
from collections import Counter
from contextlib import closing
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class TaskSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    prompt: str


class AnswerTask(TaskSpec):
    kind: Literal["answer"]
    expected: dict[str, str | int]


class TaskFields(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    ajanlat_id: int
    felelos_id: int
    cim: str
    leiras: str
    hatarido: str
    prioritas: str
    allapot: str


class InsertTask(TaskSpec):
    kind: Literal["task_insert"]
    expected: TaskFields


TaskCase = Annotated[AnswerTask | InsertTask, Field(discriminator="kind")]
TASK_CASE = TypeAdapter(TaskCase)


def load_tasks(path: Path) -> list[AnswerTask | InsertTask]:
    cases = [
        TASK_CASE.validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not cases or len({case.id for case in cases}) != len(cases):
        raise ValueError("Task dataset must be nonempty and have unique IDs.")
    return cases


def score(
    case: AnswerTask | InsertTask, answer: str, seed: Path, database: Path
) -> tuple[bool, str]:
    if isinstance(case, AnswerTask):
        answer = answer.strip()
        if answer.startswith("```json\n") and answer.endswith("\n```"):
            answer = answer.removeprefix("```json\n").removesuffix("\n```")
        try:
            parsed = json.loads(answer)
        except ValueError:
            return False, "Expected a JSON object."
        if not isinstance(parsed, dict) or any(
            type(parsed.get(key)) is not type(value) or parsed[key] != value
            for key, value in case.expected.items()
        ):
            return False, "Answer fields do not match."
        return True, "Answer fields match."

    with (
        closing(sqlite3.connect(f"{seed.as_uri()}?mode=ro", uri=True)) as before,
        closing(sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)) as after,
    ):
        after.row_factory = sqlite3.Row
        new_rows = after.execute(
            "SELECT * FROM feladat WHERE id > ?",
            before.execute("SELECT max(id) FROM feladat").fetchone(),
        ).fetchall()
        if len(new_rows) != 1:
            return False, "Expected exactly one new office task."
        new_row = new_rows[0]
        if any(
            new_row[key] != value for key, value in case.expected.model_dump().items()
        ):
            return False, "The new office task has incorrect fields."

        for (table,) in before.execute(
            "SELECT name FROM sqlite_schema WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ):
            quoted_table = '"' + table.replace('"', '""') + '"'
            query = f"SELECT * FROM {quoted_table}"
            if table == "feladat":
                rows = after.execute(query + " WHERE id != ?", (new_row["id"],))
            else:
                rows = after.execute(query)
            if Counter(map(tuple, rows)) != Counter(before.execute(query)):
                return False, f"Unexpected changes in {table}."
        return True, "Exactly the requested office task was added."
