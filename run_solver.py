from app.solver import solve_sample

def sample_instance():
    salas = [
        {"id": 1, "nome": "Sala A", "capacidade": 40, "tem_computador": True},
        {"id": 2, "nome": "Sala B", "capacidade": 25, "tem_computador": False},
        {"id": 3, "nome": "Lab TI", "capacidade": 20, "tem_computador": True},
    ]
    professors = [
        {"id": 1, "nome": "Prof A"},
        {"id": 2, "nome": "Prof B"},
    ]
    timeslots = [
        {"id": 1, "descricao": "Segunda/M1"},
        {"id": 2, "descricao": "Segunda/M2"},
        {"id": 3, "descricao": "Terca/M1"},
    ]
    turmas = [
        {"id": 101, "codigo": "BCC101", "numero_alunos": 30, "precisa_computador": False, "professor_id": 1},
        {"id": 102, "codigo": "BCC102", "numero_alunos": 20, "precisa_computador": True, "professor_id": 1},
        {"id": 103, "codigo": "BCC103", "numero_alunos": 18, "precisa_computador": True, "professor_id": 2},
    ]
    # exemplo de pesos: prioriza a turma 102
    weights = {101: 0, 102: 10, 103: 1}
    return turmas, salas, timeslots, professors, weights

def main():
    turmas, salas, timeslots, professors, weights = sample_instance()
    ok, allocs, status = solve_sample(turmas, salas, timeslots, professors, turma_weights=weights, time_limit=5)
    print("Status:", status)
    if not ok:
        print("Sem solução:", allocs)
        return
    print("Alocações encontradas:")
    for a in allocs:
        t = next(tu for tu in turmas if tu["id"] == a["turma_id"])
        s = next(sa for sa in salas if sa["id"] == a["sala_id"])
        ts = next(x for x in timeslots if x["id"] == a["timeslot_id"])
        print(f"  Turma {t['codigo']} -> Sala {s['nome']} @ {ts['descricao']}")

if __name__ == "__main__":
    main()
