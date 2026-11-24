"""The g.HIamp through g.Pype's real GHIamp source, on the simulated
amplifier."""
import json
import time

import pytest
import numpy as np
import pyedflib

from conftest import connect_all
from brainstream.bids import read_tsv
from brainstream.devices import make_device
from brainstream.project import Project
from brainstream.recording import Session, Subject


@pytest.mark.slow
def test_records_named_channels_and_trigger_onsets(tmp_path):
    project = Project.create(tmp_path / "p", "P")
    project.add_device("hiamp", {"simulate": True, "channel_count": 16,
                                 "sampling_rate": 512,
                                 "electrodes": ["Fp1", "Fp2", "F3"],
                                 # A bipolar EOG lead on the last channel.
                                 "channel_types": ["16=EOG"]})
    amp = make_device("hiamp", project.devices["hiamp"], project.folder)
    amp.start()
    try:
        time.sleep(1.0)
        assert len(amp.signal_columns()) == 16
        assert amp.trigger_column() == 16
        session = Session(project, [amp])
        session.start(Subject(sub="01", task="rest"))
        time.sleep(4.5)
        result = session.stop()
    finally:
        amp.stop()
    assert not result.problems
    eeg = project.output_path / "sub-01" / "eeg"
    reader = pyedflib.EdfReader(str(eeg / "sub-01_task-rest_eeg.bdf"))
    labels = reader.getSignalLabels()
    assert labels[:4] == ["Fp1", "Fp2", "F3", "Ch4"]
    assert labels[-1] == "TRIG" and len(labels) == 17
    assert reader.getSampleFrequency(0) == 512
    trig = reader.readSignal(labels.index("TRIG"))
    reader.close()
    # The pulse holds for 100 ms, but it is one event: its rising edge.
    rising = np.flatnonzero((trig != 0) & (np.r_[0, trig[:-1]] != trig))
    _, events = read_tsv(eeg / "sub-01_task-rest_events.tsv")
    assert [int(e["sample"]) for e in events] == list(rising)
    assert 1 <= len(events) <= 3
    assert all(e["source"] == "digital input" for e in events)
    meta = json.loads((eeg / "sub-01_task-rest_eeg.json").read_text())
    assert meta["SamplingFrequency"] == 512
    assert meta["EEGChannelCount"] == 15 and meta["EOGChannelCount"] == 1
    assert meta["TriggerChannelCount"] == 1
    assert meta["RecordingTiming"]["Method"] == "fit"
    _, channels = read_tsv(eeg / "sub-01_task-rest_channels.tsv")
    assert channels[0]["name"] == "Fp1" and channels[-1]["type"] == "TRIG"
    assert [c["type"] for c in channels[14:16]] == ["EEG", "EOG"]
    # The amplifier's filters act on the EOG too.
    assert channels[15]["units"] == "uV"


@pytest.mark.slow
def test_two_eeg_amplifiers_get_their_own_acq(tmp_path):
    project = Project.create(tmp_path / "p", "P")
    project.add_device("unicorn", {"simulate": True})
    project.add_device("hiamp", {"simulate": True, "channel_count": 8})
    devices = [make_device(t, c, project.folder)
               for t, c in project.devices.items()]
    pipeline = connect_all(devices)
    try:
        time.sleep(1.0)
        session = Session(project, devices)
        session.start(Subject(sub="01", task="rest"))
        time.sleep(2.5)
        result = session.stop()
    finally:
        pipeline.stop()
    assert not result.problems
    eeg = project.output_path / "sub-01" / "eeg"
    for acq in ("unicorn", "hiamp"):
        assert (eeg / f"sub-01_task-rest_acq-{acq}_eeg.bdf").exists()
        assert (eeg / f"sub-01_task-rest_acq-{acq}_eeg.json").exists()


@pytest.mark.parametrize("platform, hinted", [("win32", True),
                                              ("darwin", False)])
def test_failed_connection_suggests_restarting_the_service_on_windows(
        tmp_path, monkeypatch, platform, hinted):
    from brainstream.devices import hiamp

    def unreachable(*args, **kwargs):
        raise RuntimeError("No g.HIamp found")
    monkeypatch.setattr(hiamp, "StampedGHIamp", unreachable)
    monkeypatch.setattr(hiamp.sys, "platform", platform)
    project = Project.create(tmp_path / "p", "P")
    project.add_device("hiamp", {"simulate": False})
    amp = make_device("hiamp", project.devices["hiamp"], project.folder)
    with pytest.raises(RuntimeError) as failed:
        amp._open()
    assert "No g.HIamp found" in str(failed.value)
    assert ("services.msc" in str(failed.value)) == hinted


def test_restarting_the_service_asks_for_consent_and_reports_a_refusal(
        monkeypatch):
    import base64
    import subprocess
    from types import SimpleNamespace
    from brainstream.devices import hiamp

    calls = []

    def run(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=returncodes.pop(0), stdout="",
                               stderr="")
    monkeypatch.setattr(hiamp.sys, "platform", "win32")
    monkeypatch.setattr(subprocess, "run", run)
    returncodes = [0, 2, 1]
    hiamp.restart_windows_service()
    command = calls[0][-1]
    assert "-Verb RunAs" in command
    encoded = command.split("'-EncodedCommand','")[1].split("'")[0]
    restart = base64.b64decode(encoded).decode("utf-16-le")
    assert restart.startswith(
        "Restart-Service -DisplayName 'g.tec Device Service (GDS)'")
    with pytest.raises(RuntimeError, match="consent was refused"):
        hiamp.restart_windows_service()
    with pytest.raises(RuntimeError, match="services.msc"):
        hiamp.restart_windows_service()


def test_restarting_the_service_is_only_for_windows(monkeypatch):
    from brainstream.devices import hiamp
    monkeypatch.setattr(hiamp.sys, "platform", "darwin")
    with pytest.raises(RuntimeError, match="Windows service"):
        hiamp.restart_windows_service()
