import re
import json
from datetime import datetime
import pypdf

PDF_PATH = r"C:\Users\maykon.moraes\.gemini\antigravity\brain\489024fa-3d24-468a-adee-a576b3498293\.user_uploaded\media_1791223263444.pdf"

def extract_text_from_pdf(pdf_path: str) -> str:
    reader = pypdf.PdfReader(pdf_path)
    text_chunks = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text_chunks.append(t)
    return "\n".join(text_chunks)

def parse_esisla_text(text: str) -> dict:
    data = {}
    
    # 1. Protocolo
    m = re.search(r'Protocolo:\s*([0-9]+)', text, re.I)
    if m: data['protocolo'] = m.group(1).strip()
    
    # 2. CPF
    m = re.search(r'CPF:\s*([0-9\s\-]+?)(?:RG:|Nome|$)', text, re.I)
    if m:
        raw_cpf = re.sub(r'\D', '', m.group(1))
        if len(raw_cpf) == 11:
            data['cpf'] = f"{raw_cpf[:3]}.{raw_cpf[3:6]}.{raw_cpf[6:9]}-{raw_cpf[9:]}"
        else:
            data['cpf'] = m.group(1).strip()
            
    # 3. RG
    m = re.search(r'RG:\s*([0-9\.\-\s]+?)(?:Nome Completo|Data|NI|$)', text, re.I)
    if m:
        clean_rg = re.sub(r'[^0-9A-Za-z]', '', m.group(1))
        data['rg'] = clean_rg
        
    # 4. Nome Completo
    m = re.search(r'Nome Completo:\s*([^\n\r]+)', text, re.I)
    if m:
        data['nome_paciente'] = m.group(1).strip()
        
    # 5. Data de Nascimento e Idade
    m = re.search(r'Data de Nascimento:\s*(\d{2}/\d{2}/\d{4})', text, re.I)
    if m:
        data['data_nascimento'] = m.group(1)
        try:
            dt = datetime.strptime(m.group(1), "%d/%m/%Y")
            today = datetime.now()
            age = today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
            if 0 < age < 120:
                data['idade'] = str(age)
        except Exception:
            pass
            
    # 6. NI
    m = re.search(r'NI:\s*([0-9]+)', text, re.I)
    if m: data['ni'] = m.group(1).strip()

    # 7. Sexo (heuristic + text search)
    if re.search(r'Sexo:\s*(?:Feminino\s+)?Masculino\b', text, re.I):
        # Look at the PDF context or spacing
        # If "Masculino" appears or based on patient first name / title
        primeiro_nome = (data.get('nome_paciente') or '').split()[0].upper() if data.get('nome_paciente') else ''
        if primeiro_nome.endswith(('A', 'E', 'IS', 'EL')) and primeiro_nome not in ('ANTONIO', 'JOSE', 'FELIPE', 'ALEXANDRE', 'JORGE'):
            data['sexo'] = 'Feminino'
        else:
            data['sexo'] = 'Masculino'
    else:
        data['sexo'] = 'Masculino'
    
    # 8. Órgão / Secretaria
    m = re.search(r'Org[ãa]o:\s*([^\n\r]+)', text, re.I)
    if m: data['orgao'] = m.group(1).strip()
    
    # 9. UA / Unidade
    m = re.search(r'UA:\s*([^\n\r]+)', text, re.I)
    if m:
        raw_ua = m.group(1).strip()
        data['unidade'] = re.sub(r'\s+', ' ', raw_ua)
    
    # 10. Município
    m = re.search(r'Munic[íi]pio:\s*([^\n\r]+?)(?:Regime Jur[íi]dico|Cargo|$)', text, re.I)
    if m: data['municipio'] = m.group(1).strip()
    
    # 11. Regime Jurídico
    m = re.search(r'Regime Jur[íi]dico:\s*([^\n\r]+)', text, re.I)
    if m: data['regime_juridico'] = m.group(1).strip()
    
    # 12. Cargo
    m = re.search(r'Cargo:\s*([^\n\r]+?)(?:Situa[çc][ãa]o|$)', text, re.I)
    if m:
        raw_cargo = re.sub(r'\s+', ' ', m.group(1).strip())
        cargo_clean = re.sub(r'^\d+\s+', '', raw_cargo)
        data['cargo'] = cargo_clean or raw_cargo
        data['cargo_codigo'] = raw_cargo
        
    # 13. Situação
    m = re.search(r'Situa[çc][ãa]o:\s*([^\n\r]+)', text, re.I)
    if m: data['situacao'] = re.sub(r'\s+', ' ', m.group(1).strip())
    
    # 14. Readaptação: se Readaptação CID1: estiver vazio, é Não
    m_cid_readap = re.search(r'Readapta[çc][ãa]o CID1:\s*([A-Za-z0-9\.]+)?', text, re.I)
    if m_cid_readap and m_cid_readap.group(1) and m_cid_readap.group(1).strip():
        data['readaptado'] = 'Sim'
        data['readaptacao_cid1'] = m_cid_readap.group(1).strip()
    else:
        data['readaptado'] = 'Não'
    
    # 15. CRM Médico Assistente
    m = re.search(r'CRM\s*(?:M[ée]dico)?:\s*([0-9a-zA-Z\/\-]+)', text, re.I)
    if m: data['crm_assistente'] = m.group(1).strip()
    
    # 16. Nome Médico Assistente
    m = re.search(r'Nome do M[ée]dico:\s*([^\n\r]+)', text, re.I)
    if m: data['nome_assistente'] = m.group(1).strip()
    
    # 17. CID 10
    m = re.search(r'CID(?: 10)?:\s*([A-Za-z][0-9]{2,3}(?:\.[0-9]+)?)', text, re.I)
    if m:
        cid_code = m.group(1).strip().upper()
        if len(cid_code) == 4 and '.' not in cid_code:
            cid_code = f"{cid_code[:3]}.{cid_code[3:]}"
        data['cid'] = cid_code
    
    # 18. Nº Dias
    m = re.search(r'N[ºo°]?\s*Dias:\s*(\d+)', text, re.I)
    if m: data['dias_solicitados'] = m.group(1).strip()
    
    # 19. Data de emissão do atestado
    m = re.search(r'Data de emiss[ãa]o do atestado:\s*(\d{2}/\d{2}/\d{4})', text, re.I)
    if m:
        data['data_documento'] = m.group(1).strip()
        try:
            d, mo, y = m.group(1).split('/')
            data['data_documento_iso'] = f"{y}-{mo}-{d}"
        except Exception:
            pass
            
    # 20. Motivo Perícia
    m = re.search(r'Motivo:\s*([^\n\r]+)', text, re.I)
    if m: data['motivo_pericia'] = m.group(1).strip()

    # 21. Tipo Perícia
    m = re.search(r'Tipo:\s*([^\n\r]+)', text, re.I)
    if m: data['tipo_pericia'] = m.group(1).strip()

    # 22. Finalidade
    m = re.search(r'Finalidade:\s*([^\n\r]+)', text, re.I)
    if m: data['finalidade'] = m.group(1).strip()
    
    # 23. Última Licença
    m = re.search(r'Última Licença:\s*(\d+)?.*?In[íi]cio:\s*(\d{2}/\d{2}/\d{4})\s*Fim:\s*(\d{2}/\d{2}/\d{4})', text, re.I)
    if m:
        data['ultima_licenca_dias'] = m.group(1) or ""
        data['ultima_licenca_inicio'] = m.group(2)
        data['ultima_licenca_fim'] = m.group(3)

    return data

if __name__ == "__main__":
    raw_text = extract_text_from_pdf(PDF_PATH)
    res = parse_esisla_text(raw_text)
    print(json.dumps(res, indent=2, ensure_ascii=False))
