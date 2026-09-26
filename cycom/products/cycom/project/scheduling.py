"""
Critical Path Method scheduling for a project's task graph.

Finish-to-start dependencies only (the overwhelmingly common case;
start-to-start / lag are deliberately out of scope rather than half-built).

Two passes, standard CPM:
  forward  -> earliest start / earliest finish
  backward -> latest start / latest finish, and therefore slack
A task with zero slack is on the critical path: slipping it slips the whole
project, which is the one thing a Gantt chart is actually for.

Durations are in calendar days. Working-calendar scheduling (skipping
weekends/holidays) is a real want but needs a per-tenant calendar, so it is
not faked here -- the numbers mean calendar days and say so.
"""
from __future__ import annotations

from datetime import date, timedelta


class DependencyCycle(ValueError):
    """The dependency graph contains a cycle, so no valid order exists."""

    def __init__(self, task_ids):
        self.task_ids = task_ids
        super().__init__(
            "Task dependencies form a cycle; no schedule exists. Involved tasks: "
            + ", ".join(str(t) for t in task_ids)
        )


def _topological_order(nodes: dict, predecessors: dict) -> list:
    """Kahn's algorithm. Returns ids in dependency order, raising if the
    graph can't be ordered (i.e. there's a cycle)."""
    remaining = {tid: set(preds) for tid, preds in predecessors.items()}
    ready = [tid for tid, preds in remaining.items() if not preds]
    order = []
    while ready:
        tid = ready.pop(0)
        order.append(tid)
        for other, preds in remaining.items():
            if tid in preds:
                preds.discard(tid)
                if not preds and other not in order and other not in ready:
                    ready.append(other)
    if len(order) != len(nodes):
        raise DependencyCycle(sorted(set(nodes) - set(order), key=str))
    return order


def compute_schedule(tasks, project_start: date | None = None) -> dict:
    """
    tasks: iterable of Task with .id, .duration_days, .start_date and a
    prefetched .depends_on.

    Returns {"tasks": [...], "project_start", "project_finish",
             "duration_days", "critical_count"} with one entry per task
    carrying early/late start/finish, slack and is_critical.
    """
    task_list = list(tasks)
    if not task_list:
        return {
            "tasks": [], "project_start": None, "project_finish": None,
            "duration_days": 0, "critical_count": 0,
        }

    nodes = {t.id: t for t in task_list}
    known = set(nodes)
    # Dependencies pointing outside this project's task set are ignored
    # rather than crashing the whole schedule for one stale link.
    predecessors = {
        t.id: [d.id for d in t.depends_on.all() if d.id in known] for t in task_list
    }
    successors: dict = {tid: [] for tid in nodes}
    for tid, preds in predecessors.items():
        for p in preds:
            successors[p].append(tid)

    order = _topological_order(nodes, predecessors)

    # Anchor: the earliest explicitly-set start, else today.
    explicit_starts = [t.start_date for t in task_list if t.start_date]
    anchor = project_start or (min(explicit_starts) if explicit_starts else date.today())

    # ── forward pass ────────────────────────────────────────────────────
    early_start: dict = {}
    early_finish: dict = {}
    for tid in order:
        task = nodes[tid]
        duration = max(int(task.duration_days or 1), 1)
        preds = predecessors[tid]
        if preds:
            # successor starts the day after its last predecessor finishes
            es = max(early_finish[p] for p in preds) + timedelta(days=1)
            # an explicit start later than the dependency allows still wins:
            # someone has deliberately delayed this task
            if task.start_date and task.start_date > es:
                es = task.start_date
        else:
            es = task.start_date or anchor
        early_start[tid] = es
        early_finish[tid] = es + timedelta(days=duration - 1)

    project_finish = max(early_finish.values())

    # ── backward pass ───────────────────────────────────────────────────
    late_finish: dict = {}
    late_start: dict = {}
    for tid in reversed(order):
        task = nodes[tid]
        duration = max(int(task.duration_days or 1), 1)
        succs = successors[tid]
        lf = (min(late_start[s] for s in succs) - timedelta(days=1)) if succs else project_finish
        late_finish[tid] = lf
        late_start[tid] = lf - timedelta(days=duration - 1)

    rows = []
    for t in task_list:
        slack = (late_start[t.id] - early_start[t.id]).days
        rows.append({
            "id": str(t.id),
            "name": t.name,
            "stage": t.stage,
            "assignee": t.assignee,
            "duration_days": max(int(t.duration_days or 1), 1),
            "early_start": early_start[t.id].isoformat(),
            "early_finish": early_finish[t.id].isoformat(),
            "late_start": late_start[t.id].isoformat(),
            "late_finish": late_finish[t.id].isoformat(),
            "slack_days": slack,
            "is_critical": slack == 0,
            "depends_on": [str(p) for p in predecessors[t.id]],
            "due_date": t.due_date.isoformat() if t.due_date else None,
            # the schedule says one thing, the promised date says another
            "overruns_due_date": bool(t.due_date and early_finish[t.id] > t.due_date),
        })

    rows.sort(key=lambda r: (r["early_start"], r["name"]))
    project_start_actual = min(early_start.values())
    return {
        "tasks": rows,
        "project_start": project_start_actual.isoformat(),
        "project_finish": project_finish.isoformat(),
        "duration_days": (project_finish - project_start_actual).days + 1,
        "critical_count": sum(1 for r in rows if r["is_critical"]),
    }


def would_create_cycle(task, new_dependency_ids) -> bool:
    """True if adding these dependencies to `task` would make the graph
    unschedulable. Checked before saving so a cycle can never be stored."""
    target = task.id
    seen = set()
    stack = list(new_dependency_ids)
    while stack:
        current = stack.pop()
        if current == target:
            return True
        if current in seen:
            continue
        seen.add(current)
        stack.extend(
            type(task).objects.filter(pk=current).values_list("depends_on", flat=True)
        )
    return False
