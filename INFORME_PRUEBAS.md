# Informe de pruebas — Alke Wallet

Comando: `python manage.py test gestion`

Resultado: **12/12 pruebas OK**

## Cobertura

| Prueba | Qué valida |
|---|---|
| `test_relacion_uno_a_uno_cliente_usuario` | Relación uno a uno `Cliente` ↔ `User` |
| `test_relacion_muchos_a_uno_cuenta_cliente` | Relación muchos a uno `Cuenta` → `Cliente` |
| `test_relacion_muchos_a_muchos_transaccion_categoria` | Relación muchos a muchos `Transaccion` ↔ `CategoriaTransaccion` |
| `test_crud_actualizar_y_eliminar_cuenta` | Update y delete de `Cuenta` vía ORM |
| `test_consulta_filter_e_istartswith` | Filtro `filter(nombre__istartswith=...)` |
| `test_consulta_raw` | Consulta SQL personalizada con `raw()` |
| `test_crear_cuenta_via_vista` | Create de `Cuenta` vía vista (CSRF + login) |
| `test_lista_de_cuentas_requiere_login` | `/cuentas/` redirige si no hay sesión |
| `test_deposito_actualiza_saldo` | Un depósito suma correctamente al saldo |
| `test_retiro_sin_saldo_suficiente_falla` | Un retiro mayor al saldo se rechaza |
| `test_eliminar_cuenta_via_vista` | Delete de `Cuenta` vía vista |
| `test_no_puede_ver_cuenta_de_otro_cliente` | Un cliente no puede ver cuentas ajenas (404) |

## Pruebas manuales adicionales

- Login/logout y registro de usuario nuevo probados contra el servidor real (`runserver`), incluyendo verificación del token CSRF en los formularios.
- Rutas protegidas (`/cuentas/`) redirigen a `/accounts/login/` cuando no hay sesión activa.
- Archivos estáticos (`/static/css/estilo.css`) se sirven correctamente.
