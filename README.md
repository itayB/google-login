The purpose of this example is to demonstrate Prometheus client in aiohttp web server.

We will bring up a simple python aiohttp web-server container, Prometheus server and Grafana.  

```bash
docker-compose build
docker-compose up
```

Open Grafana in http://localhost:3000, add Prometheus data-source (http://prometheus:9090) and create graph with
`request_processing_seconds_count{}` as the metric.

To see the graph, perform some `GET http://localhost/status` via Chrome.


We will try to measure the 99 percentile, base on [histogram](https://prometheus.io/docs/prometheus/latest/querying/functions/#histogram_quantile) and this [post](https://povilasv.me/prometheus-tracking-request-duration/).

### Testing
Run `mypy google_login` for a type checking.

