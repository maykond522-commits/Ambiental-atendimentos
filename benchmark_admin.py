import time
from app import app, _create_session_token, get_db

with app.test_client() as client:
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT id, nome, email, perfil FROM usuarios WHERE perfil = 'Administrador' LIMIT 1")
        adm = cur.fetchone()
        token = _create_session_token(adm['id'], adm['perfil'], adm['email'], adm['nome'])
        headers = {'Authorization': 'Bearer ' + token}

        t0 = time.time()
        resp1 = client.get('/api/admin/medicos', headers=headers)
        t1 = time.time() - t0
        print('api/admin/medicos:', round(t1, 4), 's', resp1.status_code)

        t0 = time.time()
        resp2 = client.get('/api/admin/medicos/lista-impersonate', headers=headers)
        t2 = time.time() - t0
        print('api/admin/medicos/lista-impersonate:', round(t2, 4), 's', resp2.status_code)

        t0 = time.time()
        resp3 = client.get('/api/atendimentos?page=1&page_size=100', headers=headers)
        t3 = time.time() - t0
        print('api/atendimentos?page=1&page_size=100:', round(t3, 4), 's', resp3.status_code)
