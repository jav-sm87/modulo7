# Alke Wallet

Billetera digital hecha con Django. Permite registrarse, crear cuentas, hacer depósitos/retiros/transferencias y ver un reporte de movimientos.

## Modelos

- **Cliente** — uno a uno con `User`.
- **Cuenta** — muchas por cliente.
- **Transaccion** — muchas por cuenta, con categorías muchos a muchos.

## Cómo correrlo

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abrir `http://127.0.0.1:8000/`:

- `/registro/` — crear cuenta de usuario
- `/cuentas/` — tus cuentas (CRUD)
- `/reporte/` — consultas personalizadas
- `/admin/` — panel de administración

## Base de datos

SQLite por defecto. Para PostgreSQL, definir `DJANGO_ENV=production` más `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` (ver `alke_wallet/settings.py`).

## Tests

```bash
python manage.py test gestion
```

Resultados en [INFORME_PRUEBAS.md](INFORME_PRUEBAS.md).
