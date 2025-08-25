from ortools.sat.python import cp_model
from typing import List, Dict, Tuple, Optional

def solve_sample(
    turmas: List[Dict],
    salas: List[Dict],
    timeslots: List[Dict],
    professors: List[Dict],
    turma_weights: Optional[Dict[int, int]] = None,
    time_limit: int = 10,
) -> Tuple[bool, List[Dict], str]:
    """
    Monta e resolve um problema simples de timetabling com CP-SAT.

    Entradas (exemplos de dicionários):
      turma: {"id": 1, "codigo": "BCC101", "numero_alunos": 30, "precisa_computador": False, "professor_id": 1}
      sala: {"id": 1, "nome": "Lab1", "capacidade": 40, "tem_computador": True}
      timeslot: {"id": 1, "descricao": "Segunda/M1"}
      professor: {"id": 1, "nome": "Prof A"}

    Retorna:
      (sucesso_bool, lista_alocacoes, status_string)
      cada alocacao: {"turma_id": ..., "sala_id": ..., "timeslot_id": ...}
    """
    model = cp_model.CpModel()
    # Pré-filtra pares inviáveis (capacidade / computador)
    feasible_pairs = []  # tuples (t_id, s_id, ts_id)
    sala_map = {s["id"]: s for s in salas}
    turma_map = {t["id"]: t for t in turmas}

    for t in turmas:
        for s in salas:
            if s["capacidade"] < t["numero_alunos"]:
                continue
            if t.get("precisa_computador", False) and not s.get("tem_computador", False):
                continue
            for ts in timeslots:
                feasible_pairs.append((t["id"], s["id"], ts["id"]))

    # se alguma turma não tiver pares factíveis -> infeasible imediata
    turma_has_pair = {t["id"]: False for t in turmas}
    for (t_id, s_id, ts_id) in feasible_pairs:
        turma_has_pair[t_id] = True
    for t_id, ok in turma_has_pair.items():
        if not ok:
            return False, [], f"Turma {t_id} sem sala/ts factível (inviável)."

    # Cria variáveis apenas para pares factíveis
    x = {}
    for (t_id, s_id, ts_id) in feasible_pairs:
        x[(t_id, s_id, ts_id)] = model.NewBoolVar(f"x_t{t_id}_r{s_id}_ts{ts_id}")

    # 1) Cada turma atribuir exatamente 1 (sala,timeslot)
    for t in turmas:
        vars_for_t = [v for (tid, _, _), v in x.items() if tid == t["id"]]
        model.Add(sum(vars_for_t) == 1)

    # 2) Sala/Timeslot: no máximo 1 turma por (sala, timeslot)
    # para cada par (s, ts)
    s_ts_map = {}
    for (t_id, s_id, ts_id), var in x.items():
        s_ts_map.setdefault((s_id, ts_id), []).append(var)
    for key, varlist in s_ts_map.items():
        model.Add(sum(varlist) <= 1)

    # 3) Conflito professor: professor não pode ter 2 turmas no mesmo timeslot
    prof_ts_map = {}
    for (t_id, s_id, ts_id), var in x.items():
        prof_id = turma_map[t_id]["professor_id"]
        prof_ts_map.setdefault((prof_id, ts_id), []).append(var)
    for key, varlist in prof_ts_map.items():
        model.Add(sum(varlist) <= 1)

    # 4) (Opcional) Balanceamento simples: evitar usar salas muito maiores com penalidade
    # Transformamos em objetivo linear: minimizar soma( (capacidade - numero_alunos) * x )
    # Como CP-SAT maximiza por padrão, vamos transformar para maximizar -penalidade
    penalty_terms = []
    for (t_id, s_id, ts_id), var in x.items():
        cap = sala_map[s_id]["capacidade"]
        needed = turma_map[t_id]["numero_alunos"]
        slack = max(0, cap - needed)
        # peso negativo para minimizar slack total
        weight = -slack
        penalty_terms.append((weight, var))

    # 5) Objetivo: se turma_weights fornecido, prioriza certas turmas; também inclui penalty
    objective_terms = []
    if turma_weights:
        for (t_id, s_id, ts_id), var in x.items():
            w = turma_weights.get(t_id, 0)
            # preferir alocar turmas com peso maior
            objective_terms.append((w, var))
    # adiciona penalty_terms (balanceamento)
    objective_terms.extend(penalty_terms)

    # Se houver termos no objetivo, constrói objetivo linear
    if objective_terms:
        model.Maximize(sum(w * var for (w, var) in objective_terms))
    # Senão, sem objetivo (resolver apenas satisfação das restrições)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return False, [], f"Solver returned status {status}"

    # Recolhe alocações
    allocations = []
    for (t_id, s_id, ts_id), var in x.items():
        if solver.Value(var) == 1:
            allocations.append({"turma_id": t_id, "sala_id": s_id, "timeslot_id": ts_id})

    return True, allocations, "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
