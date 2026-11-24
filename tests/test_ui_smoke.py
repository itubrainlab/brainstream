"""The main window opens on a project, connects simulated devices and
draws their views (offscreen)."""
import time

from PySide6.QtWidgets import QApplication

from brainstream.project import Project
from brainstream.ui import theme
from brainstream.ui.forms import ConfigForm
from brainstream.ui.main_window import MainWindow


def test_main_window_simulated(tmp_path):
    app = QApplication.instance() or QApplication([])
    theme.apply(app)
    project = Project.create(tmp_path / "p", "P")
    project.add_device("unicorn", {})
    project.add_device("gp3", {})
    project.add_device("lsl", {})
    project.add_device("polar", {})
    project.add_device("shimmer", {})
    project.add_device("hiamp", {})
    project.add_device("webcam", {})
    project.add_device("obs", {})
    window = MainWindow(project, simulate=True)
    window.show()
    # Connect all: one g.Pype pipeline, started once with every device.
    window.pipeline.connect(list(window.devices.values()))
    assert window.pipeline.devices == list(window.devices.values())
    assert all(d.session is window.pipeline
               for d in window.devices.values())
    deadline = time.time() + 2
    while time.time() < deadline:
        app.processEvents()
        time.sleep(0.02)
    for key, page in window.pages.items():
        window.column.select(key)
        page.refresh()
    window._refresh_status()
    assert all(d.running for d in window.devices.values())
    window.close()
    assert not any(d.running for d in window.devices.values())


def test_simulate_flag_is_shown_and_not_saved(tmp_path):
    """Started with --simulate, every page says so and shows its device
    simulated, but the project keeps its own settings."""
    app = QApplication.instance() or QApplication([])
    project = Project.create(tmp_path / "p", "P")
    project.add_device("webcam", {"simulate": False})
    window = MainWindow(project, simulate=True)
    page = window.pages["webcam"]
    assert not page.forced.isHidden()
    assert "simulated" in page.state_label.text()
    box = next(f.fields["simulate"] for f in page.findChildren(ConfigForm)
               if "simulate" in f.fields)
    assert box.isChecked() and not box.isEnabled()
    window.close()
    assert Project.load(project.path).devices["webcam"]["simulate"] is False

    window = MainWindow(Project.load(project.path), simulate=False)
    page = window.pages["webcam"]
    assert page.forced.isHidden()
    assert "simulated" not in page.state_label.text()
    window.close()


def _connected_window(tmp_path):
    app = QApplication.instance() or QApplication([])
    project = Project.create(tmp_path / "p", "P")
    project.add_device("unicorn", {})
    project.add_device("lsl", {})
    window = MainWindow(project, simulate=True)
    window.show()
    window.pipeline.connect(list(window.devices.values()))
    assert all(d.running for d in window.devices.values())
    return app, window


def test_quitting_without_closing_the_window_disconnects(tmp_path):
    app, window = _connected_window(tmp_path)
    app.aboutToQuit.emit()
    assert not any(d.running for d in window.devices.values())
    window.shutdown_devices()  # a second call does nothing
    window.close()


def test_ctrl_c_closes_the_window_and_disconnects(tmp_path):
    import signal
    from brainstream.app import close_on_signals
    app, window = _connected_window(tmp_path)
    before = signal.getsignal(signal.SIGINT)
    try:
        timer = close_on_signals(app)
        signal.getsignal(signal.SIGINT)(signal.SIGINT, None)
        timer.stop()
    finally:
        signal.signal(signal.SIGINT, before)
    assert not window.isVisible()
    assert not any(d.running for d in window.devices.values())
