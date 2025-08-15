"""
Test script to verify template filters are working correctly.
"""
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the template filter functions from the utils module
from src.web.utils.template_utils import clean_literature_name, format_document_title


def test_clean_literature_name():
    """Test the clean_literature_name template filter."""
    test_cases = [
        # Test with full metadata
        (
            {'title': 'Test Document', 'author': 'John Doe'},
            'Untitled Document',
            'Test Document - John Doe'
        ),
        # Test with only title
        (
            {'title': 'Test Document'},
            'Untitled Document',
            'Test Document'
        ),
        # Test with only author
        (
            {'author': 'John Doe'},
            'Untitled Document',
            'John Doe'
        ),
        # Test with no metadata (should use default)
        (
            {},
            'Untitled Document',
            'Untitled Document'
        ),
        # Test with None metadata
        (
            None,
            'No Document',
            'No Document'
        ),
    ]
    
    print("\n=== Testing clean_literature_name ===")
    for i, (metadata, default, expected) in enumerate(test_cases, 1):
        result = clean_literature_name(metadata, default)
        status = "✓" if result == expected else "✗"
        print(f"  Test {i}: {status} {metadata} -> '{result}'")
        if status == "✗":
            print(f"     Expected: '{expected}'")


def test_format_document_title():
    """Test the format_document_title template filter."""
    test_cases = [
        # Test with full metadata
        (
            {'title': 'Test Document', 'author': 'John Doe'},
            'Test Document - John Doe'
        ),
        # Test with only title
        (
            {'title': 'Test Document'},
            'Test Document'
        ),
        # Test with only author
        (
            {'author': 'John Doe'},
            'John Doe'
        ),
        # Test with no metadata
        (
            {},
            'Untitled Document'
        ),
        # Test with None metadata
        (
            None,
            'Untitled Document'
        ),
        # Test with extra whitespace
        (
            {'title': '  Test Document  ', 'author': '  John Doe  '},
            'Test Document - John Doe'
        ),
    ]
    
    print("\n=== Testing format_document_title ===")
    for i, (metadata, expected) in enumerate(test_cases, 1):
        result = format_document_title(metadata)
        status = "✓" if result == expected else "✗"
        print(f"  Test {i}: {status} {metadata} -> '{result}'")
        if status == "✗":
            print(f"     Expected: '{expected}'")


def run_tests():
    """Run all test cases and print results."""
    print("Starting template filter tests...")
    test_clean_literature_name()
    test_format_document_title()
    print("\n✅ All template filter tests completed!")


if __name__ == "__main__":
    run_tests()

def test_clean_literature_name():
    """Test the clean_literature_name template filter."""
    test_cases = [
        # Test with full metadata
        (
            {'title': 'Test Document', 'author': 'John Doe'},
            'Untitled Document',
            'Test Document - John Doe'
        ),
        # Test with only title
        (
            {'title': 'Test Document'},
            'Untitled Document',
            'Test Document'
        ),
        # Test with only author
        (
            {'author': 'John Doe'},
            'Untitled Document',
            'John Doe'
        ),
        # Test with no metadata (should use default)
        (
            {},
            'Untitled Document',
            'Untitled Document'
        ),
        # Test with None metadata
        (
            None,
            'No Document',
            'No Document'
        ),
    ]
    
    print("\n=== Testing clean_literature_name ===")
    for i, (metadata, default, expected) in enumerate(test_cases, 1):
        result = clean_literature_name(metadata, default)
        status = "✓" if result == expected else "✗"
        print(f"  Test {i}: {status} {metadata} -> '{result}'")
        if status == "✗":
            print(f"     Expected: '{expected}'")


def test_format_document_title():
    """Test the format_document_title template filter."""
    test_cases = [
        # Test with full metadata
        (
            {'title': 'Test Document', 'author': 'John Doe'},
            'Test Document - John Doe'
        ),
        # Test with only title
        (
            {'title': 'Test Document'},
            'Test Document'
        ),
        # Test with only author
        (
            {'author': 'John Doe'},
            'John Doe'
        ),
        # Test with no metadata
        (
            {},
            'Untitled Document'
        ),
        # Test with None metadata
        (
            None,
            'Untitled Document'
        ),
        # Test with extra whitespace
        (
            {'title': '  Test Document  ', 'author': '  John Doe  '},
            'Test Document - John Doe'
        ),
    ]
    
    print("\n=== Testing format_document_title ===")
    for i, (metadata, expected) in enumerate(test_cases, 1):
        result = format_document_title(metadata)
        status = "✓" if result == expected else "✗"
        print(f"  Test {i}: {status} {metadata} -> '{result}'")
        if status == "✗":
            print(f"     Expected: '{expected}'")
