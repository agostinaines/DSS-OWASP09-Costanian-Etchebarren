# Informe del trabajo sobre OWASP A09

## ¿De qué trata el trabajo?

En este trabajo mostramos el problema **OWASP A09: fallos en el registro y
monitoreo de seguridad**. La idea principal es que, si una aplicación no guarda
información sobre lo que pasa, después es muy difícil detectar un ataque o
entender qué salió mal.

Para mostrarlo usamos una aplicación sencilla hecha con Flask. La aplicación
tiene un formulario para iniciar sesión y una página `/home` con información que
debería estar protegida.

## Las dos ramas

El repositorio tiene dos ramas para poder comparar el antes y el después.

### Rama `main`

Esta es la versión vulnerable. Si una persona escribe `/home` directamente en el
navegador puede entrar sin iniciar sesión. Además, esta rama no tiene logs de
seguridad, métricas ni alertas.

### Rama `fixed`

Esta es la versión corregida. Antes de mostrar `/home`, Flask comprueba si hay un
usuario guardado en la sesión:

```python
if 'username' not in session:
    return redirect(url_for('login'))
```

Si no hay una sesión, la aplicación manda al usuario a la página de login y deja
un log del intento. Esta rama también tiene Prometheus, Grafana y una alerta para
los intentos fallidos.

## Herramientas que usamos

- **Flask:** para hacer la aplicación web.
- **Docker Compose:** para levantar todo con un solo comando.
- **Prometheus:** para guardar la cantidad de intentos fallidos.
- **Grafana:** para poder visualizar las métricas.
- **Logging de Python:** para escribir los eventos de seguridad.

Docker Compose levanta tres contenedores: Flask en el puerto `5000`, Prometheus
en el `9090` y Grafana en el `3000`.

## Métrica de intentos fallidos

Cada vez que alguien ingresa un usuario o una contraseña incorrectos, aumenta
este contador:

```text
app_login_failed_total
```

La aplicación muestra sus métricas en <http://localhost:5000/metrics>.
Prometheus entra a esa dirección cada 30 segundos y guarda el valor. La consulta
que usamos en Prometheus es:

```promql
app_login_failed_total
```

## Alerta

En `alert_rules.yml` agregamos la alerta `RepeatedFailedLogins`. Se activa cuando
el contador llega a tres intentos fallidos:

```promql
app_login_failed_total >= 3
```

Prometheus revisa la regla cada 10 segundos. La alerta se puede ver en
<http://localhost:9090/alerts>. Cuando se activa aparece en estado `FIRING`.

Por ahora la alerta se ve dentro de Prometheus, pero no manda correos ni mensajes
porque no agregamos Alertmanager.

## Logs que agregamos

Usamos el módulo `logging` que ya viene con Python. Los logs salen por la consola
del contenedor y se pueden ver con:

```shell
docker compose logs -f flask
```

Se guardan estos eventos:

- `application_start`: la aplicación arrancó.
- `login_success`: alguien inició sesión correctamente.
- `login_failure`: alguien usó credenciales incorrectas.
- `unauthorized_access`: alguien intentó entrar a `/home` sin sesión.
- `logout`: alguien cerró la sesión.
- `http_error`: ocurrió un error HTTP, por ejemplo un `404`.
- `unhandled_exception`: ocurrió un error inesperado en el programa.

Elegimos los niveles `INFO`, `WARNING` y `ERROR` según la importancia del
evento. Un ejemplo real de la prueba fue:

```text
2026-09-10 16:23:08,786 level=WARNING logger=__main__ event=login_failure source_ip=172.20.0.1
```

No guardamos contraseñas, cookies ni el contenido de la sesión. Tampoco guardamos
el usuario escrito en un intento fallido. Solo usamos la IP que ve Flask para
tener un poco de contexto.

También limitamos los archivos de logs de Docker a tres archivos de 10 MB para
que no ocupen espacio sin límite.

## Cómo correr el proyecto

Hay que estar en la rama `fixed` y ejecutar:

Primero se copia `.env.example` como `.env` y se eligen un usuario, una
contraseña y una clave para la sesión. El `.env` está ignorado por Git, así que
esos datos quedan solamente en la computadora.

```shell
docker compose up --build
```

Las direcciones son:

- Aplicación: <http://localhost:5000>
- Métricas: <http://localhost:5000/metrics>
- Prometheus: <http://localhost:9090>
- Alertas: <http://localhost:9090/alerts>
- Grafana: <http://localhost:3000>

Para apagar todo:

```shell
docker compose down
```

## Pruebas que hicimos

Primero probamos la rama `main`. Entramos a `/home` sin iniciar sesión y la
respuesta fue `200`, así que confirmamos la vulnerabilidad.

Después probamos la rama `fixed`:

1. Entramos a `/home` sin sesión y respondió con una redirección `302`.
2. En los logs apareció `unauthorized_access`.
3. Hicimos tres intentos de login incorrectos y los tres respondieron `401`.
4. El contador `app_login_failed_total` llegó a `3`.
5. La alerta `RepeatedFailedLogins` apareció como `FIRING` en Prometheus.
6. También comprobamos que Prometheus y Grafana estaban funcionando.

Para probar otros logs se puede hacer lo siguiente:

- Reiniciar Flask para ver `application_start`.
- Entrar con el usuario y la contraseña definidos en `.env` para ver
  `login_success`.
- Cerrar la sesión para ver `logout`.
- Entrar a una ruta inventada para ver un `http_error` con código `404`.

## Cosas que todavía se podrían mejorar

Este proyecto es una demostración sencilla y no está pensado para producción.
Todavía se podría:

- configurar Grafana automáticamente con un gráfico;
- agregar Alertmanager para mandar notificaciones;
- guardar los logs en un sistema centralizado;
- limitar la cantidad de intentos de login;
- usar un servidor preparado para producción en vez del servidor de Flask;
- fijar las versiones de las imágenes de Docker.

## Conclusión

Con las dos ramas se puede ver claramente la diferencia. En `main` se puede
entrar a una página protegida sin login y no queda información útil. En `fixed`
se controla la sesión, se generan logs, se cuentan los intentos fallidos y se
activa una alerta.

Esto no evita todos los ataques, pero permite detectar mejor lo que está pasando
y tener información para revisar un incidente.
