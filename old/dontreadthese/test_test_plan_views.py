
from flask import render_template_string

# Mock View Function
def view_function(data):
    return render_template_string('<h1>{{ title }}</h1><p>{{ description }}</p>', **data)

# Test Function
def run_test(fake):
    mock_data = {
        "title": fake.word().title(),
        "description": fake.sentence(),
    }
    return view_function(mock_data)
