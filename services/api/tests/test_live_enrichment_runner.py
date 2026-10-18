from app.live_enrichment_runner import _formfav_race_numbers


def test_formfav_race_numbers_are_derived_from_the_selected_meeting_only() -> None:
    payload = {
        "meetings": [
            {"track": "Randwick", "races": [{"raceNumber": 1}, {"race_number": "3"}, {"number": 1}]},
            {"track": "Caulfield", "races": [{"raceNumber": 2}]},
        ]
    }

    assert _formfav_race_numbers(payload, "Randwick") == (1, 3)
    assert _formfav_race_numbers(payload, "Caulfield") == (2,)
    assert _formfav_race_numbers(payload, "Unknown") == ()
