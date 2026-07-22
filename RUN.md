# Running the OBD Dashboard

The dashboard app lives in [obd-dash/](obd-dash/).

## Copy it to the Pi over SSH

The Pi logs in as `admin@pizero` (see [README.md](README.md)). Copy the app
folder from this machine to the Pi's home directory.

With `scp` (recurses the whole folder):

```bash
scp -r obd-dash admin@pizero:~/
```

Or with `rsync` (faster on re-copies — only sends changes, skips the preview image):

```bash
rsync -av --exclude 'docs-preview.png' obd-dash/ admin@pizero:~/obd-dash/
```

This lands the app at `/home/admin/obd-dash` on the Pi, matching the paths in the
autostart service.

## On the Pi (fullscreen on the 3.5" TFT)

```bash
sudo apt install -y python3-pygame        # or: pip3 install -r obd-dash/requirements.txt
python3 obd-dash/dashboard.py
```

## Preview on a desktop (windowed)

```bash
python3 obd-dash/dashboard.py --windowed
```

Press **ESC** or **Q** to quit.

## Autostart on boot

See the systemd service in [obd-dash/README.md](obd-dash/README.md#autostart-on-boot).
