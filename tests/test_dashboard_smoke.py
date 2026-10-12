from streamlit.testing.v1 import AppTest


def test_dashboard_loads_without_runtime_errors():
    app = AppTest.from_file(
        "dashboard/app.py",
        default_timeout=30,
    ).run()

    assert not app.exception, [
        str(error.value) for error in app.exception
    ]