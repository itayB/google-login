The purpose of this example is to demonstrate Prometheus client in aiohttp web server.

We will bring up a simple python aiohttp web-server container, Prometheus server and Grafana.  

```bash
docker-compose build
docker-compose up
```

Open Grafana in http://localhost:3000, add Prometheus data-source (http://prometheus:9000) and create graph with
`request_processing_seconds_count{}` as the metric.

To see the graph, performe some `GET http://localhost/status` via Chrome.


