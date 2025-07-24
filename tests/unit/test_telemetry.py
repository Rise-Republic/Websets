import importlib
import pytest

@pytest.mark.unit
def test_configure_tracing_enabled(mocker, mock_settings):
    telemetry = importlib.reload(importlib.import_module("app.telemetry"))
    telemetry.settings.enable_tracing = True

    fastapi_patch = mocker.patch.object(
        telemetry.FastAPIInstrumentor, "instrument_app"
    )
    httpx_instance = mocker.MagicMock()
    mocker.patch.object(
        telemetry, "HTTPXClientInstrumentor", return_value=httpx_instance
    )
    logging_instance = mocker.MagicMock()
    mocker.patch.object(
        telemetry, "LoggingInstrumentor", return_value=logging_instance
    )
    # Patch OTLP exporter and related classes to avoid side effects
    mocker.patch.object(telemetry, "OTLPSpanExporter")
    mocker.patch.object(telemetry, "TracerProvider")
    mocker.patch.object(telemetry, "BatchSpanProcessor")
    mocker.patch.object(telemetry.trace, "set_tracer_provider")
    mocker.patch.object(telemetry.Resource, "create", return_value=mocker.MagicMock())

    app = mocker.MagicMock()
    telemetry.configure_tracing(app)

    fastapi_patch.assert_called_once_with(app)
    httpx_instance.instrument.assert_called_once_with()
    logging_instance.instrument.assert_called_once_with(set_logging_format=True)


@pytest.mark.unit
def test_configure_tracing_disabled(mocker, mock_settings):
    telemetry = importlib.reload(importlib.import_module("app.telemetry"))
    telemetry.settings.enable_tracing = False

    fastapi_patch = mocker.patch.object(
        telemetry.FastAPIInstrumentor, "instrument_app"
    )
    httpx_patch = mocker.patch.object(telemetry, "HTTPXClientInstrumentor")
    logging_patch = mocker.patch.object(telemetry, "LoggingInstrumentor")
    mocker.patch.object(telemetry, "OTLPSpanExporter")
    mocker.patch.object(telemetry, "TracerProvider")
    mocker.patch.object(telemetry, "BatchSpanProcessor")
    mocker.patch.object(telemetry.trace, "set_tracer_provider")
    mocker.patch.object(telemetry.Resource, "create", return_value=mocker.MagicMock())

    telemetry.configure_tracing(mocker.MagicMock())

    fastapi_patch.assert_not_called()
    httpx_patch.assert_not_called()
    logging_patch.assert_not_called()
