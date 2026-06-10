import pytest
from loopforge.services.duration_service import (
    parse_duration, format_duration, calculate_loops, DurationParseError,
)


class TestParseDuration:
    def test_hours_format(self):
        assert parse_duration("1h") == 3600
        assert parse_duration("2h") == 7200
        assert parse_duration("24h") == 86400

    def test_minutes_format(self):
        assert parse_duration("90m") == 5400
        assert parse_duration("120m") == 7200

    def test_seconds_format(self):
        assert parse_duration("3600s") == 3600
        assert parse_duration("60s") == 60

    def test_hms_format(self):
        assert parse_duration("01:30:00") == 5400
        assert parse_duration("10:00:00") == 36000
        assert parse_duration("00:01:30") == 90

    def test_ms_format(self):
        assert parse_duration("01:30") == 90
        assert parse_duration("90:00") == 5400

    def test_numeric(self):
        assert parse_duration(3600) == 3600
        assert parse_duration(60.5) == 60.5

    def test_invalid_format(self):
        with pytest.raises(DurationParseError):
            parse_duration("invalid")
        with pytest.raises(DurationParseError):
            parse_duration("abc")
        with pytest.raises(DurationParseError):
            parse_duration("")


class TestFormatDuration:
    def test_basic_format(self):
        assert format_duration(3600) == "01:00:00"
        assert format_duration(3661) == "01:01:01"

    def test_zero(self):
        assert format_duration(0) == "00:00:00"

    def test_large_duration(self):
        assert format_duration(86400) == "24:00:00"
        assert format_duration(172800) == "48:00:00"


class TestCalculateLoops:
    def test_exact_division(self):
        assert calculate_loops(60, 3600) == 60
        assert calculate_loops(120, 3600) == 30

    def test_with_remainder(self):
        assert calculate_loops(50, 3600) == 72
        assert calculate_loops(90, 3600) == 40

    def test_invalid_source(self):
        with pytest.raises(DurationParseError):
            calculate_loops(0, 3600)

    def test_source_larger_than_target(self):
        assert calculate_loops(7200, 3600) == 1
