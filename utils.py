def timing_to_seconds(value):
    """
    Convert:

        754.064.940

    into:

        754.064940 seconds
    """

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    value = str(value).strip()

    if not value:
        return None

    parts = value.split(".")

    try:

        if len(parts) == 3:

            seconds = int(parts[0])
            milliseconds = int(parts[1])
            microseconds = int(parts[2])

            return (
                seconds
                + milliseconds / 1000.0
                + microseconds / 1000000.0
            )

        return float(value)

    except (ValueError, TypeError):

        return None


def seconds_to_timing(value):

    if value is None:
        return None

    try:
        value = float(value)
    except (ValueError, TypeError):
        return None

    seconds = int(value)

    remainder = value - seconds

    milliseconds = int(remainder * 1000)

    microseconds = int(
        round(
            remainder * 1000000
            - milliseconds * 1000
        )
    )

    if microseconds >= 1000:

        milliseconds += 1
        microseconds -= 1000

    return "{:02d}.{:03d}.{:03d}".format(
        seconds,
        milliseconds,
        microseconds
    )