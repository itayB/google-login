from prometheus_client import Histogram


def create_metrics():
    return {
        'request_latency': Histogram(
            'request_latency', 'Request latency', ['user_id', 'endpoint']
        )
    }
