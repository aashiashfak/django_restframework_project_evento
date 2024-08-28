# myapp/parsers.py

from rest_framework.parsers import BaseParser
from django.http import QueryDict

class CustomEventParser(BaseParser):
    """
    Custom parser to handle form data with nested structures and arrays.
    """
    media_type = 'application/x-www-form-urlencoded'

    def parse(self, stream, media_type=None, parser_context=None):
        # Read the stream and convert it to a QueryDict
        data = QueryDict(stream.read(), encoding='utf-8')
        print("Raw Data from Stream:", data)  # Debugging: Print raw data

        # Extract categories list
        categories = data.getlist('categories[]')
        print("Parsed Categories:", categories)  # Debugging: Print parsed categories

        # Extract ticket types list
        ticket_types = []
        i = 0
        while f'ticket_types[{i}][type_name]' in data:
            ticket_type = {
                'type_name': data.get(f'ticket_types[{i}][type_name]'),
                'price': data.get(f'ticket_types[{i}][price]'),
                'count': data.get(f'ticket_types[{i}][count]'),
                'sold_count': data.get(f'ticket_types[{i}][sold_count]'),
                'ticket_image': data.get(f'ticket_types[{i}][ticket_image]'),
            }
            print(f"Parsed Ticket Type {i}:", ticket_type)  # Debugging: Print each ticket type
            ticket_types.append(ticket_type)
            i += 1

        # Organize the parsed data
        parsed_data = {
            'event_name': data.get('event_name'),
            'categories': categories,
            'start_date': data.get('start_date'),
            'end_date': data.get('end_date'),
            'time': data.get('time'),
            'location': data.get('location'),
            'venue': data.get('venue'),
            'about': data.get('about'),
            'instruction': data.get('instruction'),
            'terms_and_conditions': data.get('terms_and_conditions'),
            'location_url': data.get('location_url'),
            'ticket_types': ticket_types,
            'event_img_1': data.get('event_img_1')
        }

        print("Final Parsed Data:", parsed_data)  # Debugging: Print final parsed data
        return parsed_data
