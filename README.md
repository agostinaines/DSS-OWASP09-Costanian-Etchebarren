# DSS-OWASP09-Costanian-Etchebarren

Trabajo práctico sobre OWASP A09: fallos en el registro y monitoreo de seguridad,
hecho con Flask, Prometheus y Grafana.

## Ejecución

Primero hay que copiar `.env.example` como `.env` y completar sus tres valores.
El archivo `.env` queda solo en la computadora y Git no lo sube.

```shell
docker compose up --build
```

Servicios disponibles:

- Aplicación: <http://localhost:5000>
- Métricas: <http://localhost:5000/metrics>
- Prometheus: <http://localhost:9090>
- Alertas: <http://localhost:9090/alerts>
- Grafana: <http://localhost:3000>

Para seguir los logs de seguridad de la aplicación:

```shell
docker compose logs -f flask
```

El nivel mínimo se configura mediante `LOG_LEVEL` en `docker-compose.yml`.
La alerta `RepeatedFailedLogins` se activa al alcanzar tres intentos fallidos.
Los detalles de la implementación y de la demostración están en
[WRITEUP.md](WRITEUP.md).
