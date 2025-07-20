#!/usr/bin/env python3
"""
Edge case tests for the enhanced meeting rescheduling functionality.
Tests various edge cases and corner scenarios.
"""

import unittest
import datetime
import json
from main_meeting_algo import (
    schedule_meeting_from_request,
    format_meeting_to_json,
    requirewna,
    parse_calendar_data
)


class TestReschedulingEdgeCases(unittest.TestCase):
    """Test edge cases for the rescheduling functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    
    def test_json_format_compliance(self):
        """Test that JSON output strictly follows the required format."""
        start_time = datetime.datetime(2025, 7, 20, 10, 0).replace(tzinfo=self.tz)
        end_time = datetime.datetime(2025, 7, 20, 11, 0).replace(tzinfo=self.tz)
        
        json_output = format_meeting_to_json(
            subject="Test Meeting",
            email_content="Test email content",
            start_time=start_time,
            end_time=end_time,
            duration_mins=60,
            metadata={"priority": 1}
        )
        
        # Check required fields
        required_fields = ["Subject", "EmailContent", "EventStart", "EventEnd", "Duration_mins", "MetaData"]
        for field in required_fields:
            self.assertIn(field, json_output)
        
        # Check field types and formats
        self.assertIsInstance(json_output["Subject"], str)
        self.assertIsInstance(json_output["EmailContent"], str)
        self.assertIsInstance(json_output["EventStart"], str)
        self.assertIsInstance(json_output["EventEnd"], str)
        self.assertIsInstance(json_output["Duration_mins"], str)
        self.assertIsInstance(json_output["MetaData"], dict)
        
        # Check ISO format for dates
        self.assertEqual(json_output["EventStart"], "2025-07-20T10:00:00+05:30")
        self.assertEqual(json_output["EventEnd"], "2025-07-20T11:00:00+05:30")
        self.assertEqual(json_output["Duration_mins"], "60")
    
    def test_rescheduling_cascading_prevention(self):
        """Test that rescheduling doesn't create cascading reschedules."""
        # This test ensures the system avoids infinite rescheduling loops
        calendars = {
            "user1": [
                {
                    'StartTime': '2025-07-20T09:00:00+05:30',
                    'EndTime': '2025-07-20T10:00:00+05:30',
                    'Attendees': ['user1'],
                    'Summary': 'Meeting A',
                    'Priority': 4
                },
                {
                    'StartTime': '2025-07-20T10:00:00+05:30',
                    'EndTime': '2025-07-20T11:00:00+05:30',
                    'Attendees': ['user1'],
                    'Summary': 'Meeting B',
                    'Priority': 4
                },
                {
                    'StartTime': '2025-07-20T11:00:00+05:30',
                    'EndTime': '2025-07-20T17:00:00+05:30',
                    'Attendees': ['user1'],
                    'Summary': 'Long Meeting C',
                    'Priority': 4
                }
            ]
        }
        
        meeting_request = {
            "start time ": "20-07-2025T09:30:00",
            "Duration of meeting": "120 min",
            "Subject": "High Priority Urgent",
            "EmailContent": "Very urgent meeting",
            "Priority": 1
        }
        
        result = schedule_meeting_from_request(calendars, meeting_request)
        
        # Should successfully schedule, but may not reschedule all meetings
        # due to cascading prevention
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
    
    def test_multiple_attendees_rescheduling(self):
        """Test rescheduling when multiple attendees are involved."""
        calendars = {
            "alice": [
                {
                    'StartTime': '2025-07-20T10:00:00+05:30',
                    'EndTime': '2025-07-20T11:00:00+05:30',
                    'Attendees': ['alice', 'bob'],
                    'Summary': 'Shared Meeting',
                    'Priority': 4
                }
            ],
            "bob": [
                {
                    'StartTime': '2025-07-20T10:00:00+05:30',
                    'EndTime': '2025-07-20T11:00:00+05:30',
                    'Attendees': ['alice', 'bob'],
                    'Summary': 'Shared Meeting',
                    'Priority': 4
                }
            ]
        }
        
        meeting_request = {
            "start time ": "20-07-2025T10:00:00",
            "Duration of meeting": "60 min",
            "Subject": "Emergency Meeting",
            "EmailContent": "Emergency discussion needed",
            "Priority": 1
        }
        
        result = schedule_meeting_from_request(calendars, meeting_request)
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertIn('meetings_json', result)
    
    def test_boundary_time_scheduling(self):
        """Test scheduling at working hours boundaries."""
        calendars = {
            "user1": [
                {
                    'StartTime': '2025-07-20T16:30:00+05:30',
                    'EndTime': '2025-07-20T17:00:00+05:30',
                    'Attendees': ['user1'],
                    'Summary': 'End of Day Meeting',
                    'Priority': 4
                }
            ]
        }
        
        meeting_request = {
            "start time ": "20-07-2025T16:30:00",
            "Duration of meeting": "60 min",
            "Subject": "Boundary Test",
            "EmailContent": "Testing boundary conditions",
            "Priority": 1
        }
        
        result = schedule_meeting_from_request(calendars, meeting_request)
        
        # Should handle boundary conditions gracefully
        self.assertIsNotNone(result)
    
    def test_empty_calendar_scheduling(self):
        """Test scheduling with completely empty calendars."""
        calendars = {
            "user1": [],
            "user2": []
        }
        
        meeting_request = {
            "start time ": "20-07-2025T10:00:00",
            "Duration of meeting": "60 min",
            "Subject": "Empty Calendar Test",
            "EmailContent": "Testing with empty calendars",
            "Priority": 2
        }
        
        result = schedule_meeting_from_request(calendars, meeting_request)
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertFalse(result['rescheduling_required'])
        self.assertIn('meetings_json', result)
        self.assertEqual(len(result['meetings_json']), 1)
    
    def test_invalid_input_handling(self):
        """Test handling of invalid inputs gracefully."""
        # Test with invalid duration
        calendars = {"user1": []}
        
        invalid_requests = [
            {
                "start time ": "20-07-2025T10:00:00",
                "Duration of meeting": "invalid duration",
                "Subject": "Invalid Duration",
                "Priority": 2
            },
            {
                "start time ": "invalid-date",
                "Duration of meeting": "60 min",
                "Subject": "Invalid Date",
                "Priority": 2
            },
            {
                "start time ": "20-07-2025T10:00:00",
                "Duration of meeting": "60 min",
                "Subject": "Invalid Priority",
                "Priority": "invalid"
            }
        ]
        
        for request in invalid_requests:
            result = schedule_meeting_from_request(calendars, request)
            # Should return None or error result for invalid inputs
            if result is not None:
                self.assertFalse(result.get('success', False))
    
    def test_json_serialization(self):
        """Test that the JSON output can be properly serialized."""
        calendars = {
            "user1": [
                {
                    'StartTime': '2025-07-20T10:00:00+05:30',
                    'EndTime': '2025-07-20T11:00:00+05:30',
                    'Attendees': ['user1'],
                    'Summary': 'Test Meeting',
                    'Priority': 4
                }
            ]
        }
        
        meeting_request = {
            "start time ": "20-07-2025T10:00:00",
            "Duration of meeting": "60 min",
            "Subject": "Serialization Test",
            "EmailContent": "Testing JSON serialization",
            "Priority": 1
        }
        
        result = schedule_meeting_from_request(calendars, meeting_request)
        
        if result and result.get('meetings_json'):
            # Test that it can be serialized to JSON string
            try:
                json_string = json.dumps(result['meetings_json'])
                # And then parsed back
                parsed_json = json.loads(json_string)
                self.assertIsInstance(parsed_json, list)
                if parsed_json:
                    self.assertIn('Subject', parsed_json[0])
            except (TypeError, ValueError) as e:
                self.fail(f"JSON serialization failed: {e}")
    
    def test_priority_edge_cases(self):
        """Test edge cases with priority values."""
        # Test extreme priority values
        calendars = {
            "user1": [
                {
                    'StartTime': '2025-07-20T10:00:00+05:30',
                    'EndTime': '2025-07-20T11:00:00+05:30',
                    'Attendees': ['user1'],
                    'Summary': 'Extreme Priority Meeting',
                    'Priority': 1  # Highest priority
                }
            ]
        }
        
        # Try to schedule with same priority (should not reschedule)
        meeting_request = {
            "start time ": "20-07-2025T10:00:00",
            "Duration of meeting": "60 min",
            "Subject": "Same Priority Test",
            "EmailContent": "Testing same priority",
            "Priority": 1  # Same priority
        }
        
        result = schedule_meeting_from_request(calendars, meeting_request)
        
        # Should find alternative slot or fail, not reschedule same priority
        self.assertIsNotNone(result)
        if result['success'] and result.get('rescheduling_required'):
            # Should not reschedule meetings of same or higher priority
            rescheduled = result.get('rescheduling_result', {}).get('rescheduled_meetings', [])
            for meeting in rescheduled:
                self.assertGreater(meeting['priority'], 1, 
                    "Should not reschedule same or higher priority meetings")


if __name__ == '__main__':
    unittest.main(verbosity=2)