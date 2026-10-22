import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import hashlib
from datetime import datetime
from app import (
    app,
    get_db,
    _utc_now,
    _patient_hash,
    _sync_child_tables,
    _build_deterministic_esisla,
    _gatekeeper_anti_glosa_esisla,
)

# Usuário de teste vinculado ao Administrador e Médico Maykon
USUARIO_ID = "ca26d0b1-25a0-4109-8d67-d192ff1c0c48"
MEDICO_NOME = "Dr. Maykon"
MEDICO_CRM = "158158"

SCENARIOS = [
    {
        "numero": "TESTE-GLOSA-01",
        "nome": "Carlos Alberto Teste da Silva",
        "cpf": "111.222.333-44",
        "sexo": "Masculino",
        "idade": "45",
        "cargo": "Professor de Educação Básica II",
        "tempo_funcao": "12",
        "unidade_tempo": "anos",
        "readaptado": "Não",
        "cid": "M54.5",
        "cid_descricao": "Dor lombar baixa",
        "doenca_motivo": "Lombalgia crônica agudizada",
        "sintomas_limitacoes": "tramadol 50mg 8/8h e ciclobenzaprina 5mg se dor, pct ta com dor na lombar irradiando pra gluteo",
        "antecedentes": "veio com atestado de 15 dias do Dr Fernando CRM 98765, fez RM de coluna lombar acusando protrusao discal focal L4-L5",
        "exame_fisico_descricao": "dor",
        "justificativa": "repouso 15 dias",
        "parecer": "FAVORÁVEL",
        "dias_solicitados": "15",
        "data_documento": "2026-10-21",
        "pressao_sistolica": "13",
        "pressao_diastolica": "8",
        "pulso": "76",
        "altura": "178",
        "peso": "84",
    },
    {
        "numero": "TESTE-GLOSA-02",
        "nome": "Mariana Santos Periciada Teste",
        "cpf": "222.333.444-55",
        "sexo": "Feminino",
        "idade": "38",
        "cargo": "Escrivão de Polícia",
        "tempo_funcao": "7",
        "unidade_tempo": "anos",
        "readaptado": "Não",
        "cid": "F32.2",
        "cid_descricao": "Episódio depressivo grave sem sintomas psicóticos",
        "doenca_motivo": "Transtorno depressivo maior",
        "sintomas_limitacoes": "PCT CHOROSA, MUITA ANSIEDADE, INSÔNIA GRAVE, BEG, TOMA SERTRALINA 100MG PELA MANHÃ E CLONAZEPAM 2MG S/N SE CRISE",
        "antecedentes": "Nega",
        "exame_fisico_descricao": "depressão",
        "justificativa": "concedo afastamento",
        "parecer": "FAVORÁVEL",
        "dias_solicitados": "30",
        "data_documento": "2026-10-21",
        "pressao_sistolica": "12",
        "pressao_diastolica": "8",
        "pulso": "82",
        "altura": "165",
        "peso": "62",
    },
    {
        "numero": "TESTE-GLOSA-03",
        "nome": "Roberto Lima Servidor Teste",
        "cpf": "333.444.555-66",
        "sexo": "Masculino",
        "idade": "42",
        "cargo": "Agente de Organização Escolar",
        "tempo_funcao": "5",
        "unidade_tempo": "anos",
        "readaptado": "Não",
        "cid": "M54.5",
        "cid_descricao": "Dor lombar baixa",
        "doenca_motivo": "Lombalgia referida",
        "sintomas_limitacoes": "Refere dor nas costas ao carregar caixas de merenda. Nega febre ou trauma prévio.",
        "antecedentes": "Nega comorbidades.",
        "exame_fisico_descricao": "Deambula sem claudicação. Lasègue negativo bilateralmente. Ausência de contratura paravertebral. ADM de tronco preservada.",
        "justificativa": "Quadro leve, capacidade laborativa preservada",
        "parecer": "CONTRÁRIO",
        "dias_solicitados": "15",
        "data_documento": "2026-10-21",
        "pressao_sistolica": "120",
        "pressao_diastolica": "80",
        "pulso": "72",
        "altura": "1.72",
        "peso": "76",
    },
    {
        "numero": "TESTE-GLOSA-04",
        "nome": "Luciana Ferreira Periciada Teste",
        "cpf": "444.555.666-77",
        "sexo": "Feminino",
        "idade": "50",
        "cargo": "Investigador de Polícia",
        "tempo_funcao": "18",
        "unidade_tempo": "anos",
        "readaptado": "Sim",
        "atividades_readaptado": "Serviços administrativos internos e atendimento telefônico sem porte de arma externa",
        "cid": "M75.1",
        "cid_descricao": "Síndrome do manguito rotador",
        "doenca_motivo": "Dor em ombro direito",
        "sintomas_limitacoes": "servidora readaptada em funções administrativas internas, veio renovar atestado com USG de ombro direito mostrando tendinopatia sem ruptura, em uso de meloxicam 15mg se dor",
        "antecedentes": "Readaptada desde 2023 por lesão osteomuscular prévia.",
        "exame_fisico_descricao": "Ombro direito com arco doloroso acima de 120 graus, testes de Neer e Hawkins negativos, força muscular preservada grau V para digitação e tarefas de mesa.",
        "justificativa": "Sem perda funcional para as atividades da readaptação",
        "parecer": "CONTRÁRIO",
        "dias_solicitados": "30",
        "data_documento": "2026-10-21",
        "pressao_sistolica": "130",
        "pressao_diastolica": "80",
        "pulso": "74",
        "altura": "1.60",
        "peso": "68",
    },
    {
        "numero": "TESTE-GLOSA-05",
        "nome": "Antônio Marcos Servidor Teste",
        "cpf": "555.666.777-88",
        "sexo": "Masculino",
        "idade": "52",
        "cargo": "Motorista",
        "tempo_funcao": "15",
        "unidade_tempo": "anos",
        "readaptado": "Não",
        "cid": "M23.2",
        "cid_descricao": "Transtorno do menisco devido a ruptura ou lesão antiga",
        "doenca_motivo": "Meniscopatia medial joelho direito",
        "sintomas_limitacoes": "mancando, dor aguda no joelho D ao pisar na embreagem, toma dipirona 1g se dor",
        "antecedentes": "",
        "exame_fisico_descricao": "",
        "justificativa": "afastamento 20 dias",
        "parecer": "FAVORÁVEL",
        "dias_solicitados": "20",
        "data_documento": "2026-10-21",
        "pressao_sistolica": "14",
        "pressao_diastolica": "9",
        "pulso": "80",
        "altura": "170",
        "peso": "88",
    },
    {
        "numero": "TESTE-GLOSA-06",
        "nome": "Patrícia Oliveira Servidora Teste",
        "cpf": "666.777.888-99",
        "sexo": "Feminino",
        "idade": "34",
        "cargo": "Oficial Administrativo",
        "tempo_funcao": "4",
        "unidade_tempo": "anos",
        "readaptado": "Não",
        "cid": "Z76.3",
        "cid_descricao": "Pessoa em boa saúde acompanhando pessoa doente",
        "doenca_motivo": "Acompanhamento de dependente enfermo",
        "sintomas_limitacoes": "Apresentou atestado médico de 5 dias emitido por pediatra para acompanhamento de filho menor hospitalizado com broncopneumonia.",
        "antecedentes": "Nega comorbidades próprias.",
        "exame_fisico_descricao": "Exame físico geral: Bom estado geral, corada, eupneica, sem queixas físicas ou mentais próprias.",
        "justificativa": "Acompanhamento familiar não amparado em licença para tratamento de saúde própria",
        "parecer": "CONTRÁRIO",
        "dias_solicitados": "5",
        "data_documento": "2026-10-21",
        "pressao_sistolica": "110",
        "pressao_diastolica": "70",
        "pulso": "68",
        "altura": "1.68",
        "peso": "59",
    },
]

def seed_attendances():
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        now = _utc_now()
        
        results = []
        for s in SCENARIOS:
            rid = s["numero"]
            
            # 1. Constrói o payload enriquecido
            p_dict = dict(s)
            p_dict["atendimento"] = rid
            p_dict["medico"] = MEDICO_NOME
            p_dict["crm_responsavel"] = MEDICO_CRM
            p_dict["data_atendimento"] = "2026-10-21"
            p_dict["hora_atendimento"] = "09:00"
            
            # 2. Executa a geração e o gatekeeper anti-glosa
            doc = _build_deterministic_esisla(p_dict)
            doc_final = _gatekeeper_anti_glosa_esisla(doc, p_dict)
            
            p_dict["ficha_esisla"] = doc_final
            p_dict["aux"] = dict(p_dict)
            p_dict["aux"]["ficha_esisla"] = doc_final
            p_dict["aux"]["nomePaciente"] = s["nome"]
            p_dict["aux"]["cpfPaciente"] = s["cpf"]
            p_dict["aux"]["queixaDuracao"] = s["sintomas_limitacoes"]
            p_dict["aux"]["antecedentes"] = s["antecedentes"]
            p_dict["aux"]["exameFisicoDescricao"] = s["exame_fisico_descricao"]
            p_dict["aux"]["justificativa"] = s["justificativa"]
            p_dict["aux"]["diasSolicitados"] = s["dias_solicitados"]
            p_dict["aux"]["parecer"] = s["parecer"]
            p_dict["aux"]["cid"] = s["cid"]
            
            payload_json_str = json.dumps(p_dict, ensure_ascii=False)
            p_hash = _patient_hash(p_dict)
            
            # 3. Upsert na tabela atendimentos
            cur.execute(
                """
                INSERT INTO atendimentos (
                    id, numero, payload_json, status, paciente_nome_hash,
                    paciente_nome, paciente_cpf, medico, cid, unidade,
                    completude, alertas, inconsistencias, criado_em, atualizado_em,
                    finalizado_em, usuario_id, versao, atualizado_por
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    numero = EXCLUDED.numero,
                    payload_json = EXCLUDED.payload_json,
                    status = EXCLUDED.status,
                    paciente_nome = EXCLUDED.paciente_nome,
                    paciente_cpf = EXCLUDED.paciente_cpf,
                    medico = EXCLUDED.medico,
                    cid = EXCLUDED.cid,
                    atualizado_em = EXCLUDED.atualizado_em
                """,
                (
                    rid, rid, payload_json_str, "FINALIZADO", p_hash,
                    s["nome"], s["cpf"], f"{MEDICO_NOME} - CRM: {MEDICO_CRM}", s["cid"], "Ambulatório Central SP",
                    100.0, 0, 0, now, now, now, USUARIO_ID, 1, USUARIO_ID
                )
            )
            
            _sync_child_tables(db, rid, p_dict)
            db.commit()
            results.append({
                "numero": rid,
                "nome": s["nome"],
                "cargo": s["cargo"],
                "cid": s["cid"],
                "parecer": s["parecer"],
                "ficha": doc_final
            })
            print(f"[OK] Inserido com sucesso: {rid} - {s['nome']} ({s['cid']} - {s['parecer']})")
            
        cur.close()
        return results

if __name__ == "__main__":
    seeded = seed_attendances()
    print(f"\n[SUCESSO] Total de {len(seeded)} atendimentos de teste gravados no banco de dados!")
