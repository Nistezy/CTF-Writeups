from pathlib import Path

data = Path("OBJECTS.DATA").read_bytes()

for needle in [
    b"ConfigData",
    b"HardwareTelemetry",
    b"EngineTelemetry",
]:
    print(f"\n=== {needle!r} ===")

    pos = 0
    count = 0

    while True:
        pos = data.find(needle, pos)

        if pos == -1:
            break

        print("offset:", hex(pos))
        print(data[max(0, pos-100):pos+300])

        pos += 1
        count += 1

    print("total:", count)