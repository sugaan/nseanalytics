import pytest
from datetime import datetime
from src.parser import AnnouncementParser


def test_parse_datetime():
    parser = AnnouncementParser()
    
    # Test standard RSS date format
    date_str = "Mon, 11 Feb 2026 10:30:00 GMT"
    result = parser.parse_datetime(date_str)
    assert isinstance(result, datetime)
    assert result.day == 11
    assert result.month == 2


def test_extract_symbol():
    parser = AnnouncementParser()
    
    assert parser.extract_symbol("Reliance (RELIANCE) - Board Meeting") == "RELIANCE"
    assert parser.extract_symbol("Symbol: TCS - Announcement") == "TCS"
    assert parser.extract_symbol("INFY announces results") == "INFY"


def test_clean_html():
    parser = AnnouncementParser()
    
    html = "<p>This is <b>bold</b> text</p>"
    result = parser.clean_html(html)
    assert result == "This is bold text"
    assert "<" not in result


def test_determine_category():
    parser = AnnouncementParser()
    
    assert parser._determine_category("Dividend announcement", "", "announcements") == "Corporate Action"
    assert parser._determine_category("AGM Notice", "", "announcements") == "Meeting Notice"
    assert parser._determine_category("Q4 Results", "", "announcements") == "Financial Results"
