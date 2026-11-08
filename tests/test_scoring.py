import json
import shutil
from datetime import date

import pytest

from iroda import SEED, AjanlatValtozas, Iroda, Ugy
from iroda_bench.runner import DATASET
from iroda_bench.scoring import load_tasks, score

READ, WRITE = load_tasks(DATASET)


@pytest.mark.parametrize(
    "answer", ["", "[]", '{"fordulonap":"2026-11-08"}', '{"penznem":"EUR"}']
)
def test_reject_incorrect_answer(answer):
    assert not score(READ, answer, SEED, SEED)[0]


def test_accept_fenced_json_answer():
    answer = json.dumps(READ.expected)
    assert score(READ, f"```json\n{answer}\n```", SEED, SEED)[0]


@pytest.mark.parametrize(
    ("attempt", "passes"),
    [
        ("missing", False),
        ("correct", True),
        ("wrong", False),
        ("duplicate", False),
        ("side_effect", False),
    ],
)
def test_grade_database_changes(tmp_path, attempt, passes):
    database = tmp_path / "run.db"
    shutil.copyfile(SEED, database)
    office = Iroda(database, irhato=True)
    fields = WRITE.expected
    args = fields.model_dump(exclude={"ajanlat_id", "hatarido"})
    args["hatarido"] = date.fromisoformat(fields.hatarido)
    args["ugy"] = Ugy(tipus="ajánlat", azonosito=fields.ajanlat_id)

    if attempt == "wrong":
        args["prioritas"] = "alacsony"
    if attempt != "missing":
        office.feladat_letrehozas(**args)
    if attempt == "duplicate":
        office.feladat_letrehozas(**args)
    if attempt == "side_effect":
        office.ajanlat_modositas(
            fields.ajanlat_id, AjanlatValtozas(targy="Nem kért módosítás.")
        )

    assert score(WRITE, "Létrehoztam a feladatot.", SEED, database)[0] is passes
