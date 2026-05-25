from subprocess import check_output


def get_current_song():

    song_data = check_output(
        [
            "playerctl",
            "metadata",
            "--format",
            "{{artist}} - {{title}}"
        ]
    ).decode().strip()

    return song_data


def get_current_time():

    current_time = float(
        check_output(
            [
                "playerctl",
                "position"
            ]
        ).decode().strip()
    )

    return current_time