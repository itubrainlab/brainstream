# Validating the lab's setup

This is the [validation procedure](README.md) for the lab's booth: two
computers, a 64-channel g.HIamp, a Gazepoint GP3 HD, OBS and a camera. One
session with any participant (about 15 minutes) checks five things:

1. **EEG alpha:** eyes closed against eyes open (band power, first).
2. **EEG signal quality:** every channel's noise.
3. **Eye-tracker accuracy:** at the fixation crosses.
4. **N170:** to faces.
5. **Synchronisation:** of the EEG, the eye tracker, the screen recording,
   the camera and the LSL markers, with each other.

PsychoPy runs the whole procedure, including the eye tracker's calibration.
The analysis then gives each check PASS or FAIL.

### Why validate

brAInStream records several streams at the same time, from different
devices on two computers: the EEG, the eye tracker, the screen, the camera
and the experiment's markers. Each device has its own clock and its own
delay (USB, Bluetooth, the network, OBS's rendering), and brAInStream puts
them all on one timeline. A study can only compare them (a fixation with
the EEG it evoked, a face on the screen with the gaze that found it) if
that timeline is right.

The validation shows two things with a real participant:

- **each signal is good on its own:** the EEG shows alpha and an N170, the
  eye tracker is accurate;
- **the streams are in step with each other:** the same moment (a flash, a
  jump of the eyes, a face) lands at the same time in every recording.

Run it when the booth is set up, and again whenever a device, a computer,
a driver or OBS's settings change.

## The setup

```
 STIMULUS COMPUTER                          RECORDING COMPUTER
 ┌──────────────────────────┐   network    ┌──────────────────────────┐
 │ PsychoPy  (procedure,    │── LSL ──────▶│ brAInStream               │
 │           LSL markers,   │              │  ├ g.HIamp (USB)         │
 │           GP3 calibration)│              │  │   64 ch, 64 = HEOG    │
 │ opengp3 server ◀ GP3 HD  │── Open Gaze ▶│  ├ GP3 (remote)          │
 │           (USB)          │    API       │  ├ LSL markers           │
 │ OBS + DistroAV (NDI)     │── NDI ──────▶│  ├ Screen Capture (OBS)  │
 │ the participant's screen │              │  └ Video Stream (camera) │
 └──────────────────────────┘              └──────────────────────────┘
```

| Device | Where | Settings |
|---|---|---|
| g.HIamp | recording computer, USB | 64 channels at 512 Hz. Channels 1–63 EEG, channel 64 bipolar (horizontal EOG). Amplifier filters 0.01–100 Hz band-pass and 50 Hz notch |
| GP3 HD | stimulus computer, USB, under `opengp3 server` | read by brAInStream over the network (Open Gaze API, port 4242). PsychoPy runs its calibration on the same server |
| OBS | stimulus computer: Display Capture of the participant's screen, NDI output (DistroAV) | received by brAInStream's Screen Capture over the network |
| Camera | recording computer, USB, pointed at the participant | brAInStream's Video Stream, recording as `recording-camera` |
| PsychoPy | stimulus computer | sends the markers over LSL (stream `brAInStreamValidation`) |

Both computers must be on the same wired network, with LSL, NDI and port
4242 allowed through their firewalls. Use wired Ethernet: Wi-Fi makes NDI's
and the eye tracker's delays uneven.

## Once: setting up

### Recording computer

1. **brAInStream from source**, in its own virtual environment, with the
   analysis's figures. From the repository's folder:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate          # Windows
   source .venv/bin/activate       # macOS and Linux
   pip install -e ".[validation]"
   ```

   Activate the environment again (the second line) in every new terminal
   before running brAInStream or the scripts below.

2. **g.tec's driver.** brAInStream installs gtec-gds. On Windows, also
   install g.tec's g.HIamp driver (g.NEEDaccess).
3. **The cap's channel names.** Write them in a text file, in the order of
   the amplifier's inputs: one per line, 64 lines, the last one `HEOG`. For
   example:

   ```
   Fp1
   Fp2
   …
   PO7
   PO8
   …
   HEOG
   ```

   The analysis looks for PO7 and PO8 (N170) and for O1, Oz, O2, POz and Pz
   (alpha) by name. Without names, it falls back to every EEG channel and
   the checks get weaker.
4. **The project.** With the g.HIamp switched on and connected:

   ```bash
   python validation/make_project.py "~/brAInStream/lab-validation" --lab \
       --stimulus-host <stimulus computer's address> \
       --electrodes cap64.txt --screen-width-cm <screen width>
   ```

   `--lab` sets up:
   - **g.HIamp:** 64 channels at 512 Hz; channel 64 recorded as EOG
     (`--channel-type 64=EOG`); the amplifier's 0.01–100 Hz band-pass and
     50 Hz notch, chosen from those the amplifier offers. If it doesn't
     offer them, the script lists the ones it does.
   - **GP3:** remote, at the stimulus computer.
   - **LSL streams:** listening for `brAInStreamValidation`.
   - **Screen Capture:** OBS over NDI.
   - **Video Stream:** the first camera. Give `--webcam "<name>"` to choose
     another.

   Give the participant's screen's physical width: accuracy is measured in
   degrees. Add `--reference`/`--ground` to describe them in the recording.
   To check the settings, open the project in brAInStream: the g.HIamp's
   page, Settings, shows the channels and the amplifier's filters.

### Stimulus computer

1. **A virtual environment** for the procedure's Python packages, in a
   folder of your choice:

   ```bash
   python -m venv validation-env
   validation-env\Scripts\activate          # Windows
   source validation-env/bin/activate       # macOS and Linux
   ```

   Activate it again in every new terminal on this computer.
2. **OpenGP3** for the GP3 HD, in that environment:

   ```bash
   pip install "opengp3 @ git+https://github.com/itubrainlab/opengp3@v0.5.0"
   ```

   (On Windows, install UsbDk once; see OpenGP3's README.)
3. **PsychoPy and pylsl**, in the same environment:

   ```bash
   pip install psychopy pylsl
   ```

   Check PsychoPy's documentation for the Python versions it supports. The
   [standalone PsychoPy](https://www.psychopy.org/download.html) also
   works: it includes pylsl, and runs the procedure with its own Python.
4. **The procedure.** Copy `validation/face_validation.py` onto this
   computer, with a folder of **at least 30 face photographs**. The lab's
   set is in the uncanny-face-questionnaire study; this repository doesn't
   include them.
5. **OBS**, which sends the participant's screen to brAInStream:
   1. Install [OBS Studio](https://obsproject.com) and the
      [DistroAV](https://github.com/DistroAV/DistroAV) plugin. DistroAV also
      needs the NDI Runtime; its README says where to get it. Restart OBS
      afterwards.
   2. In a scene, add a **Display Capture** source and choose the
      participant's screen (the one the procedure runs on).
   3. In **Settings → Video**, set both the **Base (Canvas)** and the
      **Output (Scaled)** resolution to the screen's own resolution (e.g.
      1920×1080), so the canvas has the screen's shape. A canvas of another
      shape makes OBS scale every frame, which adds delay: in the first
      session it made the screen recording 391 ms late instead of about
      40 ms.
   4. Select the source and choose **Edit → Transform → Fit to screen**, so
      the whole screen fills the canvas.
   5. Turn on **Tools → NDI Output Settings → Main Output**. Its name is
      the NDI source brAInStream's Screen Capture looks for (by default,
      the first one with "OBS" in its name).
   6. On the recording computer, connect the Screen Capture in brAInStream:
      it should show the participant's screen. If it finds no source, check
      that both computers are on the same wired network and that the
      firewalls let NDI through.

   The Screen Capture's **Delay** (Settings) is taken off the screen
   recording's time stamps. It defaults to 50 ms, measured on the lab's
   setup; the report says when to change it.

### The camera

It films the participant. Its timing is measured on the participant's
eyes: the analysis finds them in its video (MediaPipe's face landmarks, as
OpenGP3's webcam eye tracking does) and times each jump to a new cross,
against the same jump in the eye tracker's gaze. For that, the face should
fill a good part of the picture, lit from the front, with the eyes
visible (no glare on glasses).

The screen's flashes are a second measure, when their light on the
participant shows in the video. That happens in a dim room; in a bright
one they are simply not counted.

### The EOG (channel 64)

A bipolar pair at the outer corners of the eyes (horizontal EOG), wired to
channel 64. The analysis compares it with the eye tracker's gaze, sample by
sample, with no marker in between. This is the most direct check that the
EEG and the eye tracker are on one clock. If the lab wires channel 64
vertically (above and below an eye), the analysis follows the vertical
gaze instead.

## A session

The eye tracker's server and the procedure both keep running until the
end, so each gets its own terminal. On the stimulus computer, open two
terminals and activate the virtual environment in both (or use separate
tabs or panes in one terminal app).

On the **stimulus computer**:

1. In the **first terminal**, start the eye tracker's server on the
   participant's screen (display 1 on the lab's stimulus computer):

   ```bash
   opengp3 server --display 1
   ```

   Leave it running.
2. Start OBS, and check its NDI output is on.

On the **recording computer**:

3. Start brAInStream and open the lab-validation project.
4. Fit the EEG headset (the g.HIamp's 64-channel cap) and the EOG
   electrodes. Connect the g.HIamp: every channel in the data viewer should
   show clean EEG, without drift or 50 Hz.
5. **Connect all** (the plug button).
   - **GP3 page:** the eye view shows both eyes and the distance bar is
     green. Seat the participant about 65 cm from the screen.
   - **Screen Capture:** shows the participant's screen.
   - **Video Stream:** shows the participant (and the screen).

On the **stimulus computer**:

6. In the **second terminal**, start the procedure (with the standalone
   PsychoPy, use its Python, or open the script in PsychoPy's Coder and
   Run):

   ```bash
   python face_validation.py --faces <faces folder> --participant 01 --screen 0
   ```

   It waits until brAInStream receives its markers.

On the **recording computer**:

7. Press **Record**, with participant `01` and task `facevalidation`.

On the **stimulus computer**:

8. Press space, and give the participant the keyboard. The procedure runs:

   | Step | |
   |---|---|
   | Flashes | 10 white flashes of the whole screen |
   | Eyes open | 30 s, looking at a dot |
   | Eyes closed | 30 s, until a tone |
   | Calibration | 9 points, drawn by PsychoPy and run by the GP3 HD's server |
   | Moving targets | 2 × 10 s, a dot to follow with the eyes |
   | Faces | 30: a cross at a random place (2 s), the face there (1 s), a blank (1 s) |
   | Moving targets | 2 × 10 s again |
   | Flashes | 10 again |

9. After the debriefing screen, stop recording in brAInStream.

## Checking the recording

On the recording computer, in a terminal with brAInStream's environment
activated:

```bash
python validation/analyse.py "~/brAInStream/lab-validation/bids" --sub 01
```

It prints each check and writes `report.md`, with figures, in
`bids/derivatives/validation/sub-01/`. It exits non-zero if any check fails.

| # | Check | Passes when |
|---|---|---|
| 1 | Alpha | posterior alpha (8–13 Hz) ≥ 1.5 × with the eyes closed |
| 2 | EEG signal quality | ≥ 90 % of the EEG channels, and every alpha and N170 site, under 50 µV of 1–30 Hz noise during the faces |
| 3 | Gaze accuracy | median error ≤ 1.5° at the crosses, ≥ 80 % of crosses within 1.5° |
| 4 | N170 | a negative peak at PO7/PO8 (average reference, EOG left out) at 130–200 ms, p < 0.05 |
| 5 | Synchronisation | all of the following |

What the synchronisation check compares:

| Pair | How | Passes when |
|---|---|---|
| markers in `eeg/` and `beh/` | identical | within 1 ms |
| eye tracker ↔ markers | saccades to each new cross | 80–500 ms after it |
| eye tracker ↔ markers | the gaze following the moving targets | −50 to 150 ms behind them |
| **EEG ↔ eye tracker** | the EOG (channel 64) against the gaze, cross-correlated | within 40 ms |
| EEG ↔ markers | the N170's latency | inside 130–200 ms (check 4) |
| screen recording ↔ markers | the faces and the flashes in OBS's video | −20 to 200 ms, IQR < 50 ms |
| **camera ↔ eye tracker** | the eyes' jumps to each new cross, in the camera's video and in the gaze | within 60 ms, IQR < 100 ms |
| camera ↔ markers | the flashes' light on the participant, when it shows | within 60 ms, IQR < 70 ms |
| markers | each recorded once | no duplicates |
| every recording | covers the procedure | start to end |

When the screen recording or the camera is late but steady, the report
says how many ms to add to its **Delay** in brAInStream (Screen Capture or
Video Stream, Settings). Record again after changing it.

### When a check fails

| Failing | Look at |
|---|---|
| Alpha | The posterior electrodes (check 2); whether the participant closed the eyes. A few people have little alpha. |
| EEG signal quality | The channels listed: gel, reseat, check the reference and ground. |
| Gaze accuracy | The valid gaze by screen height in the report. If the top or the bottom is lost, change the GP3 HD's angle or the participant's height and distance, then recalibrate. Check the screen width given to the project. |
| N170 | Too few clean epochs (beyond ±100 µV are left out), PO7/PO8 named wrong, or a timing offset (see synchronisation). |
| EOG ↔ gaze | Late gaze: the eye tracker's samples are out of step with the EEG. Check the network (wired), and that `opengp3 server` is 0.5 or later. If the EOG doesn't follow the gaze at all (r below 0.3), check its electrodes and that it is channel 64. |
| Moving targets | Gaze far behind (or ahead of) the targets with the saccades fine: the same as above. |
| Flashes in the screen recording | Not found: OBS isn't capturing the participant's screen, or NDI isn't arriving. Late and steady: set the Screen Capture's Delay to the value given. |
| Camera ↔ eye tracker | Too few jumps found: the face is too small or too dark in the picture; move the camera closer or light the face. Late and steady: add the value given to the Video Stream's Delay. Uneven (large IQR): the camera buffers frames; try a lower resolution or frame rate, or another camera. |
| Markers recorded once | A marker recorded twice is a brAInStream problem: report it. The other checks count each marker once. |

## Trying it without the hardware

On one computer, everything simulated:

```bash
python validation/make_project.py /tmp/lab-try --lab --simulate
python face_validation.py --faces <faces folder> --dry-run --auto
```

`--dry-run` runs a short version in a window: 4 s rests, 6 faces, 3 flashes
and 1 moving target each time. With simulated devices, the analysis finds
every file and checks the markers and coverage. The physiological checks
fail, because a simulator has no eyes to close or faces to see.
`tests/test_validation_analysis.py` tests the analysis itself on synthetic
lab recordings with known timing.
