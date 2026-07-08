"""Deterministic train/dev/test tasks with machine-checkable outcomes."""

from __future__ import annotations

import random
from collections.abc import Callable

from .executable_models import ExecutableTask
from .models import RouteAction, Workload


_TEMPLATES: dict[str, dict[str, tuple[str, ...]]] = {
    "direct_literal": {
        "train": ("Return the literal answer {answer}.",),
        "dev": ("Respond exactly with the supplied value {answer}.",),
        "test": ("The requested response is {answer}; give only that response.",),
        "challenge": ("Without using any support component, output the supplied token {answer}.",),
    },
    "aggregate": {
        "train": ("Calculate the {operation} of these measurements: {values}.",),
        "dev": ("Using computation, obtain the {operation} for {values}.",),
        "test": ("Determine computationally the {operation} across {values}.",),
        "challenge": ("For the numeric sequence {values}, derive its {operation}.",),
    },
    "filtered_sum": {
        "train": ("Decompose the subgroup: first identify {group} records, then calculate their sum from {rows}.",),
        "dev": ("Separate entries tagged {group} and total only that subset: {rows}.",),
        "test": ("Resolve the subgroup {group} before computing its aggregate in {rows}.",),
        "challenge": ("Among {rows}, restrict analysis to category {group} and obtain its total.",),
    },
    "research_fact": {
        "train": ("Look up the archive and report the {field} for project {subject}.",),
        "dev": ("Consult the frozen source collection: what is {subject}'s {field}?",),
        "test": ("Use the provided evidence index to find {field} associated with {subject}.",),
        "challenge": ("According to the indexed dossier, identify {subject}'s {field}.",),
    },
    "research_multihop": {
        "train": ("Decompose and trace the two-step evidence chain in the archive: which city hosts the lab led by {person}?",),
        "dev": ("Resolve the intermediate organization, then retrieve the city connected to {person}.",),
        "test": ("Trace the two-link evidence chain from {person} to laboratory to city.",),
        "challenge": ("Starting with {person}, discover the laboratory they lead and then where it is based.",),
    },
    "research_conflict": {
        "train": ("Retrieve conflicting archive records and verify the newest status for {subject}.",),
        "dev": ("Retrieve the sources and check recency before reporting {subject}'s status.",),
        "test": ("Resolve conflicting records for {subject}; return the newest supported status.",),
        "challenge": ("Several archive entries disagree about {subject}; report the current status after checking dates.",),
    },
    "research_outage": {
        "train": ("The retrieval tool is unavailable; delegate to the archive specialist for {subject}'s code.",),
        "dev": ("With search offline, route this to the specialist: code for {subject}.",),
        "test": ("Evidence service outage: obtain {subject}'s code through specialist delegation.",),
        "challenge": ("The search endpoint cannot be reached. Ask the domain expert for {subject}'s code.",),
    },
    "document_extract": {
        "train": ("Use document extraction to return the {field} from: {document}",),
        "dev": ("Parse this record and report its {field}: {document}",),
        "test": ("Read the structured document, extracting {field}: {document}",),
        "challenge": ("From this form, pull the value recorded under {field}: {document}",),
    },
    "invoice_reconcile": {
        "train": ("Extract, compute, and verify this invoice because the stated total may be wrong: {document}",),
        "dev": ("Reconcile the invoice by parsing its lines, calculating the total, and checking the stated amount: {document}",),
        "test": ("Audit this billing record: extract the entries, execute the calculation, and verify the payable total: {document}",),
        "challenge": ("The declared amount may not equal the line items. Establish the correct payable bill from: {document}",),
    },
    "date_normalize": {
        "train": ("Extract the date and delegate locale interpretation for this {locale} record: {document}",),
        "dev": ("Parse then send to the locale specialist to normalize the {locale} date: {document}",),
        "test": ("Obtain an ISO date from this {locale} document using extraction and specialist resolution: {document}",),
        "challenge": ("Convert the date in this record to YYYY-MM-DD using its {locale} regional convention: {document}",),
    },
    "crossfield_check": {
        "train": ("Decompose the requested fields, extract them, and verify the identifier from: {document}",),
        "dev": ("Separate the field requirements before parsing and checking this record: {document}",),
        "test": ("Plan the multi-field extraction and validate the combined identifier in: {document}",),
        "challenge": ("Build and check the identifier after locating both region and serial in: {document}",),
    },
}


def _render(kind: str, split: str, **values: object) -> str:
    return _TEMPLATES[kind][split][0].format(**values)


def _direct_task(split: str, index: int, workload: Workload, rng: random.Random) -> ExecutableTask:
    del rng
    answer = f"R{index:03d}"
    return ExecutableTask(
        task_id=f"{split}-{workload.value}-{index:03d}",
        split=split,
        workload=workload,
        prompt=_render("direct_literal", split, answer=answer),
        kind="direct_literal",
        payload={"answer": answer},
        expected_answer=answer,
        required_actions=(),
    )


def _aggregate_task(split: str, index: int, rng: random.Random) -> ExecutableTask:
    values = [rng.randint(3, 40) for _ in range(7)]
    operation = ("sum", "maximum", "mean")[index % 3]
    if operation == "sum":
        answer = str(sum(values))
    elif operation == "maximum":
        answer = str(max(values))
    else:
        answer = f"{sum(values) / len(values):.2f}"
    return ExecutableTask(
        task_id=f"{split}-data_analysis-{index:03d}",
        split=split,
        workload=Workload.DATA_ANALYSIS,
        prompt=_render(
            "aggregate", split, operation=operation, values=", ".join(map(str, values))
        ),
        kind="aggregate",
        payload={"values": values, "operation": operation},
        expected_answer=answer,
        required_actions=(RouteAction.EXECUTE_CODE,),
    )


def _filtered_task(split: str, index: int, rng: random.Random) -> ExecutableTask:
    group = ("amber", "blue", "green")[index % 3]
    rows = [(rng.choice((group, "other")), rng.randint(2, 25)) for _ in range(8)]
    if all(label != group for label, _ in rows):
        rows[0] = (group, rows[0][1])
    answer = str(sum(value for label, value in rows if label == group))
    rendered_rows = "; ".join(f"{label}:{value}" for label, value in rows)
    return ExecutableTask(
        task_id=f"{split}-data_analysis-{index:03d}",
        split=split,
        workload=Workload.DATA_ANALYSIS,
        prompt=_render("filtered_sum", split, group=group, rows=rendered_rows),
        kind="filtered_sum",
        payload={"rows": rows, "group": group},
        expected_answer=answer,
        required_actions=(RouteAction.DECOMPOSE, RouteAction.EXECUTE_CODE),
    )


def _research_fact_task(split: str, index: int, rng: random.Random) -> ExecutableTask:
    del rng
    subject = f"Orion-{index:02d}"
    answer = f"CODE-{100 + index}"
    docs = [
        {"subject": subject, "field": "code", "value": answer, "year": 2026},
        {"subject": f"Decoy-{index:02d}", "field": "code", "value": "NONE", "year": 2026},
    ]
    return ExecutableTask(
        task_id=f"{split}-research-{index:03d}",
        split=split,
        workload=Workload.RESEARCH,
        prompt=_render("research_fact", split, field="code", subject=subject),
        kind="research_fact",
        payload={"subject": subject, "field": "code", "documents": docs},
        expected_answer=answer,
        required_actions=(RouteAction.USE_TOOL,),
    )


def _research_multihop_task(split: str, index: int, rng: random.Random) -> ExecutableTask:
    del rng
    person = f"Lead-{index:02d}"
    lab = f"Lab-{index:02d}"
    city = ("Montreal", "Nairobi", "Oslo", "Lima")[index % 4]
    docs = [
        {"subject": person, "field": "leads", "value": lab, "year": 2026},
        {"subject": lab, "field": "city", "value": city, "year": 2026},
    ]
    return ExecutableTask(
        task_id=f"{split}-research-{index:03d}",
        split=split,
        workload=Workload.RESEARCH,
        prompt=_render("research_multihop", split, person=person),
        kind="research_multihop",
        payload={"person": person, "lab": lab, "documents": docs},
        expected_answer=city,
        required_actions=(RouteAction.DECOMPOSE, RouteAction.USE_TOOL),
    )


def _research_conflict_task(split: str, index: int, rng: random.Random) -> ExecutableTask:
    del rng
    subject = f"Program-{index:02d}"
    old, current = ("paused", "active") if index % 2 else ("active", "completed")
    docs = [
        {"subject": subject, "field": "status", "value": old, "year": 2023},
        {"subject": subject, "field": "status", "value": current, "year": 2026},
    ]
    return ExecutableTask(
        task_id=f"{split}-research-{index:03d}",
        split=split,
        workload=Workload.RESEARCH,
        prompt=_render("research_conflict", split, subject=subject),
        kind="research_conflict",
        payload={"subject": subject, "documents": docs},
        expected_answer=current,
        required_actions=(RouteAction.USE_TOOL, RouteAction.VERIFY),
    )


def _research_outage_task(split: str, index: int, rng: random.Random) -> ExecutableTask:
    del rng
    subject = f"Atlas-{index:02d}"
    answer = f"SP-{300 + index}"
    return ExecutableTask(
        task_id=f"{split}-research-{index:03d}",
        split=split,
        workload=Workload.RESEARCH,
        prompt=_render("research_outage", split, subject=subject),
        kind="research_outage",
        payload={"subject": subject, "specialist_answer": answer},
        expected_answer=answer,
        required_actions=(RouteAction.DELEGATE,),
        unavailable_actions=(RouteAction.USE_TOOL,),
    )


def _document_extract_task(split: str, index: int, rng: random.Random) -> ExecutableTask:
    del rng
    field = ("Account", "Region", "Owner")[index % 3]
    answer = f"V-{index:03d}"
    document = f"Record ID: D-{index:03d}; {field}: {answer}; Status: valid"
    return ExecutableTask(
        task_id=f"{split}-document_processing-{index:03d}",
        split=split,
        workload=Workload.DOCUMENT_PROCESSING,
        prompt=_render("document_extract", split, field=field, document=document),
        kind="document_extract",
        payload={"field": field, "document": document},
        expected_answer=answer,
        required_actions=(RouteAction.USE_TOOL,),
    )


def _invoice_task(split: str, index: int, rng: random.Random) -> ExecutableTask:
    items = [rng.randint(4, 35) for _ in range(4)]
    computed = sum(items)
    stated = computed + (3 if index % 2 else -2)
    document = f"Invoice I-{index:03d}; Items: {','.join(map(str, items))}; Stated total: {stated}"
    return ExecutableTask(
        task_id=f"{split}-document_processing-{index:03d}",
        split=split,
        workload=Workload.DOCUMENT_PROCESSING,
        prompt=_render("invoice_reconcile", split, document=document),
        kind="invoice_reconcile",
        payload={"document": document, "items": items, "stated_total": stated},
        expected_answer=str(computed),
        required_actions=(
            RouteAction.USE_TOOL,
            RouteAction.EXECUTE_CODE,
            RouteAction.VERIFY,
        ),
    )


def _date_task(split: str, index: int, rng: random.Random) -> ExecutableTask:
    del rng
    day = 10 + index % 15
    month = 1 + index % 9
    year = 2024 + index % 3
    locale = "EU" if index % 2 else "US"
    raw = f"{day:02d}/{month:02d}/{year}" if locale == "EU" else f"{month:02d}/{day:02d}/{year}"
    expected = f"{year}-{month:02d}-{day:02d}"
    document = f"Case C-{index:03d}; Date: {raw}; Locale: {locale}"
    return ExecutableTask(
        task_id=f"{split}-document_processing-{index:03d}",
        split=split,
        workload=Workload.DOCUMENT_PROCESSING,
        prompt=_render("date_normalize", split, locale=locale, document=document),
        kind="date_normalize",
        payload={"document": document, "raw_date": raw, "locale": locale},
        expected_answer=expected,
        required_actions=(RouteAction.USE_TOOL, RouteAction.DELEGATE),
    )


def _crossfield_task(split: str, index: int, rng: random.Random) -> ExecutableTask:
    del rng
    region = ("NE", "SW", "CE")[index % 3]
    serial = f"{8000 + index}"
    document = f"Asset record; Region={region}; Serial={serial}; Owner=Team-{index % 5}"
    return ExecutableTask(
        task_id=f"{split}-document_processing-{index:03d}",
        split=split,
        workload=Workload.DOCUMENT_PROCESSING,
        prompt=_render("crossfield_check", split, document=document),
        kind="crossfield_check",
        payload={"document": document, "region": region, "serial": serial},
        expected_answer=f"{region}-{serial}",
        required_actions=(
            RouteAction.DECOMPOSE,
            RouteAction.USE_TOOL,
            RouteAction.VERIFY,
        ),
    )


_BUILDERS: dict[Workload, tuple[Callable[..., ExecutableTask], ...]] = {
    Workload.DATA_ANALYSIS: (_direct_task, _aggregate_task, _filtered_task),
    Workload.RESEARCH: (
        _direct_task,
        _research_fact_task,
        _research_multihop_task,
        _research_conflict_task,
        _research_outage_task,
    ),
    Workload.DOCUMENT_PROCESSING: (
        _direct_task,
        _document_extract_task,
        _invoice_task,
        _date_task,
        _crossfield_task,
    ),
}


def generate_executable_tasks(
    split: str,
    tasks_per_workload: int,
    seed: int = 2701,
) -> list[ExecutableTask]:
    """Generate a balanced split while holding prompt templates out by split."""
    if split not in {"train", "dev", "test", "challenge"}:
        raise ValueError("split must be train, dev, test, or challenge")
    if tasks_per_workload < 5:
        raise ValueError("tasks_per_workload must be at least 5")
    rng = random.Random(f"{seed}:{split}")
    tasks: list[ExecutableTask] = []
    for workload in Workload:
        builders = _BUILDERS[workload]
        for index in range(tasks_per_workload):
            builder = builders[index % len(builders)]
            if builder is _direct_task:
                task = builder(split, index, workload, rng)
            else:
                task = builder(split, index, rng)
            tasks.append(task)
    return tasks
