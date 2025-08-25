from app.solver import solve_sample
from run_solver import sample_instance

def test_solver_basic():
    turmas, salas, timeslots, professors, weights = sample_instance()
    ok, allocs, status = solve_sample(turmas, salas, timeslots, professors, turma_weights=weights, time_limit=5)
    assert ok is True
    # deve alocar todas as turmas
    assert len(allocs) == len(turmas)
    # verificar conflito de sala/ts e professor/ts
    seen_room_ts = set()
    seen_prof_ts = set()
    turma_map = {t["id"]: t for t in turmas}
    for a in allocs:
        key_room = (a["sala_id"], a["timeslot_id"])
        assert key_room not in seen_room_ts
        seen_room_ts.add(key_room)
        prof = turma_map[a["turma_id"]]["professor_id"]
        key_prof = (prof, a["timeslot_id"])
        assert key_prof not in seen_prof_ts
        seen_prof_ts.add(key_prof)
