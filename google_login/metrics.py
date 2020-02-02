from prometheus_client import Histogram


def create_metrics():
    return {
        'request_latency': Histogram(
            'request_latency',
            'Request latency',
            ['user_id', 'endpoint'],
            buckets=(.025, .05, .1, .2, float("inf"))
        )
    }
