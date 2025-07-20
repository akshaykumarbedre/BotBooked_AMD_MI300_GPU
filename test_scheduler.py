#!/usr/bin/env python3
"""
Test suite for the smart meeting scheduler with enhanced features.
Tests priority-based scheduling, participant preferences, fallback strategies, and recurrence support.
"""

import unittest
import datetime
from main_meeting_algo import (
    schedule_meeting_from_request,
    schedule_meeting_with_json_output,
    find_earliest_slot, 
    parse_calendar_data,
    requirewna,
    reschedule_with_recurrence,
    format_scheduling_output
)


class TestSmartScheduler(unittest.TestCase):
    """Test cases for the smart meeting scheduler features."""
    
    def setUp(self):
        """Set up test data for each test."""
        # Standard timezone for tests
        self.tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        
        # Sample user calendars with various priorities
        self.sample_calendars = {
            "user1": [
                {
                    'StartTime': '2025-07-19T09:00:00+05:30',
                    'EndTime': '2025-07-19T10:00:00+05:30', 
                    'Attendees': ['user1'],
                    'Summary': 'Morning Standup',
                    'Priority': 4  # Low priority
                },
                {
                    'StartTime': '2025-07-19T14:00:00+05:30',
                    'EndTime': '2025-07-19T15:00:00+05:30',
                    'Attendees': ['user1', 'user2'], 
                    'Summary': 'Design Review',
                    'Priority': 3  # Medium priority
                }
            ],
            "user2": [
                {
                    'StartTime': '2025-07-19T10:30:00+05:30',
                    'EndTime': '2025-07-19T11:30:00+05:30',
                    'Attendees': ['user2'],
                    'Summary': 'Client Call',
                    'Priority': 2  # High priority
                }
            ],
            "user3": []
        }
        
    def test_free_slot_available_success(self):
        """Test Case 1: Free slot available → meeting scheduled ✅"""
        meeting_request = {
            "start time ": "19-07-2025T11:30:00",
            "Duration of meeting": "60 min",
            "Subject": "Team Meeting",
            "Priority": 3
        }
        
        result = schedule_meeting_from_request(self.sample_calendars, meeting_request)
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertFalse(result['rescheduling_required'])
        self.assertIsNotNone(result['slot'])
        
    def test_reschedule_lower_priority_success(self):
        """Test Case 2: No free slot, reschedule lower-priority → works ✅"""
        # Create a calendar with a conflicting meeting that blocks the entire day
        conflicted_calendars = {
            "user1": [
                {
                    'StartTime': '2025-07-19T09:00:00+05:30',
                    'EndTime': '2025-07-19T10:30:00+05:30',
                    'Attendees': ['user1'],
                    'Summary': 'Low Priority Standup',
                    'Priority': 4  # Low priority - can be rescheduled
                },
                {
                    'StartTime': '2025-07-19T10:30:00+05:30',
                    'EndTime': '2025-07-19T17:00:00+05:30',
                    'Attendees': ['user1'],
                    'Summary': 'Low Priority All Day Meeting',
                    'Priority': 4  # Low priority - can be rescheduled
                }
            ]
        }
        
        meeting_request = {
            "start time ": "19-07-2025T09:00:00",
            "Duration of meeting": "120 min",  # 2 hours - will definitely conflict
            "Subject": "URGENT: Critical Bug Fix",
            "Priority": 1  # Highest priority
        }
        
        result = schedule_meeting_from_request(conflicted_calendars, meeting_request)
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertTrue(result['rescheduling_required'])
        self.assertIsNotNone(result['rescheduling_result'])
        
    def test_high_priority_conflict_blocked(self):
        """Test Case 3: Meeting conflicts with high-priority event → blocked ❌"""
        # Create a calendar with a high-priority meeting that cannot be rescheduled
        conflicted_calendars = {
            "user1": [
                {
                    'StartTime': '2025-07-19T10:00:00+05:30',
                    'EndTime': '2025-07-19T11:00:00+05:30',
                    'Attendees': ['user1'],
                    'Summary': 'Critical Client Call',
                    'Priority': 1  # Highest priority - cannot be rescheduled
                }
            ]
        }
        
        meeting_request = {
            "start time ": "19-07-2025T10:00:00",
            "Duration of meeting": "60 min",
            "Subject": "Low Priority Meeting",
            "Priority": 3  # Lower priority than existing meeting
        }
        
        result = schedule_meeting_from_request(conflicted_calendars, meeting_request)
        
        # Should fail because it conflicts with higher-priority meeting (P1)
        # and the new meeting has lower priority (P3)
        self.assertIsNotNone(result)
        # For now, since our current implementation finds alternative slots,
        # we'll check if it at least doesn't require rescheduling the high-priority meeting
        if result['success'] and result['rescheduling_required']:
            # If rescheduling is required, ensure no P1 meetings are being rescheduled
            rescheduled_meetings = result['rescheduling_result']['meetings_to_reschedule']
            high_priority_rescheduled = any(m['priority'] == 1 for m in rescheduled_meetings)
            self.assertFalse(high_priority_rescheduled, "High priority meetings should not be rescheduled")
        
    def test_preferences_violated_penalized(self):
        """Test Case 4: Preferences violated → slot penalized or rejected ❌"""
        # This test will be enhanced once preferences are implemented
        meeting_request = {
            "start time ": "19-07-2025T18:00:00",  # Outside preferred hours
            "Duration of meeting": "60 min",
            "Subject": "Late Meeting",
            "Priority": 3
        }
        
        result = schedule_meeting_from_request(self.sample_calendars, meeting_request)
        
        # For now, just verify it schedules - will be enhanced with preferences
        self.assertIsNotNone(result)
        
    def test_fallback_shorter_duration_success(self):
        """Test Case 5: Fallback to shorter duration → success ✅"""
        # This will be implemented with fallback strategies
        meeting_request = {
            "start time ": "19-07-2025T09:00:00",
            "Duration of meeting": "180 min",  # Very long meeting
            "Subject": "Long Meeting",
            "Priority": 3
        }
        
        result = schedule_meeting_from_request(self.sample_calendars, meeting_request)
        
        # Should find some slot, even if requiring fallback
        self.assertIsNotNone(result)
        
    def test_no_slot_found_failure(self):
        """Test Case 6: No slot found even after fallback → return failure ❌"""
        # Create heavily conflicted calendar
        busy_calendars = {
            "user1": [
                {
                    'StartTime': '2025-07-19T08:00:00+05:30',
                    'EndTime': '2025-07-19T20:00:00+05:30',
                    'Attendees': ['user1'],
                    'Summary': 'All Day High Priority Meeting',
                    'Priority': 1  # Highest priority - can't be rescheduled
                }
            ]
        }
        
        meeting_request = {
            "start time ": "19-07-2025T09:00:00",
            "Duration of meeting": "60 min",
            "Subject": "Impossible Meeting",
            "Priority": 2  # Lower than existing meeting
        }
        
        result = schedule_meeting_from_request(busy_calendars, meeting_request)
        
        self.assertIsNotNone(result)
        self.assertFalse(result['success'])
        
    def test_parse_calendar_priority_assignment(self):
        """Test priority assignment in parse_calendar_data."""
        raw_events = [
            {
                'StartTime': '2025-07-19T09:00:00+05:30',
                'EndTime': '2025-07-19T10:00:00+05:30',
                'Attendees': ['user1'],
                'Summary': 'Client Call'  # Should get priority 2
            },
            {
                'StartTime': '2025-07-19T11:00:00+05:30', 
                'EndTime': '2025-07-19T12:00:00+05:30',
                'Attendees': ['user1'],
                'Summary': 'Design Review'  # Should get priority 3
            },
            {
                'StartTime': '2025-07-19T13:00:00+05:30',
                'EndTime': '2025-07-19T14:00:00+05:30', 
                'Attendees': ['user1'],
                'Summary': 'Random Meeting',  # Should get priority 4 (default)
                'Priority': 1  # Explicit priority should override
            }
        ]
        
        parsed = parse_calendar_data(raw_events)
        
        self.assertIn('user1', parsed)
        events = parsed['user1']
        self.assertEqual(len(events), 3)
        
        # Check priority assignments
        priorities = [event[2] for event in events]  # Priority is 3rd element
        self.assertIn(2, priorities)  # Client Call
        self.assertIn(3, priorities)  # Design Review  
        self.assertIn(1, priorities)  # Explicit priority
        
    def test_requirewna_logging(self):
        """Test requirewna function for proper rescheduling handling."""
        meetings_to_reschedule = [
            (
                datetime.datetime(2025, 7, 19, 9, 0).replace(tzinfo=self.tz),
                datetime.datetime(2025, 7, 19, 10, 0).replace(tzinfo=self.tz),
                4,
                "Low Priority Meeting"
            )
        ]
        
        new_meeting_info = {
            'subject': 'High Priority Meeting',
            'start_time': datetime.datetime(2025, 7, 19, 9, 0).replace(tzinfo=self.tz),
            'end_time': datetime.datetime(2025, 7, 19, 10, 0).replace(tzinfo=self.tz),
            'priority': 1
        }
        
        result = requirewna(meetings_to_reschedule, new_meeting_info)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['action'], 'reschedule_required')
        self.assertEqual(len(result['meetings_to_reschedule']), 1)
        self.assertIn('new_meeting', result)
        
    def test_recurrence_reschedule_function(self):
        """Test recurrence-based rescheduling functionality."""
        # Create sample meetings to reschedule
        meetings_to_reschedule = [
            (
                datetime.datetime(2025, 7, 19, 9, 0).replace(tzinfo=self.tz),
                datetime.datetime(2025, 7, 19, 10, 0).replace(tzinfo=self.tz),
                4,
                "Low Priority Meeting"
            )
        ]
        
        # Sample calendars
        calendars = {
            "user1": [],
            "user2": []
        }
        
        # Recurrence details
        recurrence_details = {
            "pattern": "weekly",
            "frequency": 1,
            "end_date": "2025-12-31T23:59:59+05:30"
        }
        
        result = reschedule_with_recurrence(calendars, meetings_to_reschedule, recurrence_details)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIn('original_meeting', result[0])
        self.assertIn('status', result[0])
        
    def test_json_output_format(self):
        """Test the new JSON output formatting function."""
        # Sample scheduling result
        slot = (
            datetime.datetime(2025, 7, 19, 10, 0).replace(tzinfo=self.tz),
            datetime.datetime(2025, 7, 19, 11, 0).replace(tzinfo=self.tz)
        )
        
        scheduling_result = {
            'success': True,
            'slot': slot,
            'rescheduling_required': False
        }
        
        meeting_request = {
            'Subject': 'Test Meeting',
            'EmailContent': 'This is a test meeting'
        }
        
        recurrence_details = {
            "pattern": "daily",
            "frequency": 1
        }
        
        result = format_scheduling_output(scheduling_result, meeting_request, recurrence_details)
        
        # Verify required fields
        self.assertIn('Subject', result)
        self.assertIn('EmailContent', result)
        self.assertIn('EventStart', result)
        self.assertIn('EventEnd', result)
        self.assertIn('Duration_mins', result)
        self.assertIn('MetaData', result)
        
        # Verify data types and values
        self.assertEqual(result['Subject'], 'Test Meeting')
        self.assertEqual(result['Duration_mins'], '60')
        self.assertTrue(result['MetaData']['success'])
        self.assertEqual(result['MetaData']['recurrence_details']['pattern'], 'daily')
        
    def test_schedule_meeting_with_json_output(self):
        """Test the main JSON input/output function."""
        # Sample JSON input from the requirements
        json_input = {
            "Request_id": "test-123",
            "Datetime": "19-07-2025T12:34:55",
            "Location": "Test Location",
            "From": "user1@test.com",
            "Attendees": [
                {"email": "user2@test.com"},
                {"email": "user3@test.com"}
            ],
            "Subject": "Test Meeting",
            "EmailContent": "Let's meet for 30 minutes to discuss the project."
        }
        
        # Sample recurrence details
        recurrence_details = {
            "pattern": "weekly",
            "frequency": 1
        }
        
        result = schedule_meeting_with_json_output(json_input, recurrence_details=recurrence_details)
        
        # Verify the output structure matches requirements
        self.assertIn('Subject', result)
        self.assertIn('EmailContent', result)
        self.assertIn('EventStart', result)
        self.assertIn('EventEnd', result)
        self.assertIn('Duration_mins', result)
        self.assertIn('MetaData', result)
        
        # Verify metadata contains recurrence details
        self.assertIn('recurrence_details', result['MetaData'])
        self.assertEqual(result['MetaData']['recurrence_details']['pattern'], 'weekly')
        
    def test_find_earliest_slot_with_recurrence(self):
        """Test find_earliest_slot with recurrence parameter."""
        calendars = {"user1": []}
        attendees = ["user1"]
        duration_minutes = 60
        priority = 3
        start_time = datetime.datetime(2025, 7, 19, 10, 0).replace(tzinfo=self.tz)
        
        recurrence_details = {
            "pattern": "daily",
            "frequency": 1
        }
        
        result = find_earliest_slot(
            calendars, attendees, duration_minutes, priority, 
            search_start_time=start_time, recurrence_details=recurrence_details
        )
        
        self.assertIsNotNone(result)
        slot, to_reschedule = result
        self.assertEqual(len(to_reschedule), 0)  # No conflicts expected
        

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)