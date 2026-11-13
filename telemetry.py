import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup(service_name):
    """Send traces and metrics to the collector. Returns None when it is not configured."""
    if not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return None

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": os.environ.get("BUILD_ID", "local"),
            "deployment.environment": os.environ.get("APP_ENV", "local"),
        }
    )

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(tracer_provider)

    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(), export_interval_millis=10000
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))

    return tracer_provider