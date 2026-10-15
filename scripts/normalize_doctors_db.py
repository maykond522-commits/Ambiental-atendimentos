import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("DATABASE_URL not set")
    exit(1)

conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute("SELECT medico, COUNT(*) FROM atendimentos GROUP BY medico ORDER BY 2 DESC")
print("ANTES:")
for row in cur.fetchall():
    print(" ", row)

# 1. Patricia Nalin
cur.execute("""
    UPDATE atendimentos
    SET medico = 'PATRICIA NALIN DE LUCENA - CRM: 145669',
        usuario_id = COALESCE(usuario_id, 'ce132f72-e281-4eae-8919-b6e9d1a83643')
    WHERE medico ILIKE '%PATRICIA NALIN DE LUCENA%'
      AND medico != 'PATRICIA NALIN DE LUCENA - CRM: 145669'
""")
print(f"Patricia updated: {cur.rowcount} rows")

# 2. Wania Sanches Picasso
cur.execute("""
    UPDATE atendimentos
    SET medico = 'WANIA SANCHES PICASSO - CRM: 79775',
        usuario_id = COALESCE(usuario_id, '5bd2be7c-913b-428a-8d46-12930c5004a6')
    WHERE medico ILIKE '%WANIA SANCHES PICASSO%'
      AND medico != 'WANIA SANCHES PICASSO - CRM: 79775'
""")
print(f"Wania updated: {cur.rowcount} rows")

# 3. Maria das Graças
cur.execute("""
    UPDATE atendimentos
    SET medico = 'MARIA DAS GRAÇAS - CRM: 148311',
        usuario_id = COALESCE(usuario_id, 'f01d46fe-0e9a-477a-a02e-1aa0b068e82f')
    WHERE medico ILIKE '%MARIA DAS GRA%'
      AND medico != 'MARIA DAS GRAÇAS - CRM: 148311'
""")
print(f"Maria updated: {cur.rowcount} rows")

conn.commit()

cur.execute("SELECT medico, COUNT(*) FROM atendimentos GROUP BY medico ORDER BY 2 DESC")
print("DEPOIS:")
for row in cur.fetchall():
    print(" ", row)

conn.close()
