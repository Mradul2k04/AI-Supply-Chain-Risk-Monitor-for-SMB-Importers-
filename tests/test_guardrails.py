import pytest
from guardrails.validators import validate_source_url

def test_validate_source_url_allowed():
    # Arrange
    url1 = "https://reuters.com/news/article-123"
    url2 = "https://noaa.gov/warnings"
    url3 = "internal://playbooks/test"
    
    # Act & Assert
    assert validate_source_url(url1, "geopolitical") is True
    assert validate_source_url(url2, "weather") is True
    assert validate_source_url(url3, "geopolitical") is True

def test_validate_source_url_disallowed():
    # Arrange
    url1 = "https://malicious-source.xyz/fake-news"
    url2 = "https://blogspot.com/random-post"
    
    # Act & Assert
    assert validate_source_url(url1, "geopolitical") is False
    assert validate_source_url(url2, "weather") is False
