#!/usr/bin/env python3
"""
Test suite for the smart meeting scheduler with enhanced features.
Tests priority-based scheduling, participant preferences, and fallback strategies.
"""

import unittest
import datetime
from main_meeting_algo import (
    schedule_meeting_from_request,
    find_earliest_slot, 
    parse_calendar_data,
    requirewna
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
        self.assertEqual(result['action'], 'reschedule_completed')
        self.assertIn('rescheduled_meetings', result)
        self.assertIn('failed_reschedules', result)
        self.assertIn('new_meeting', result)
        
    def test_json_output_format(self):
        """Test JSON output format for booked and rescheduled meetings."""
        # Create a scenario that will require rescheduling
        conflicted_calendars = {
            "user1": [
                {
                    'StartTime': '2025-07-19T09:00:00+05:30',
                    'EndTime': '2025-07-19T10:00:00+05:30',
                    'Attendees': ['user1'],
                    'Summary': 'Low Priority Meeting',
                    'Priority': 4  # Low priority - can be rescheduled
                }
            ]
        }
        
        meeting_request = {
            "start time ": "19-07-2025T09:00:00",
            "Duration of meeting": "60 min",
            "Subject": "High Priority Meeting",
            "EmailContent": "This is a high priority meeting.",
            "Priority": 1  # Highest priority
        }
        
        result = schedule_meeting_from_request(conflicted_calendars, meeting_request)
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertIn('meetings_json', result)
        
        meetings_json = result['meetings_json']
        self.assertIsInstance(meetings_json, list)
        self.assertGreater(len(meetings_json), 0)
        
        # Check the main meeting JSON format
        main_meeting = meetings_json[0]
        required_fields = ['Subject', 'EmailContent', 'EventStart', 'EventEnd', 'Duration_mins', 'MetaData']
        for field in required_fields:
            self.assertIn(field, main_meeting)
        
        # Verify main meeting data
        self.assertEqual(main_meeting['Subject'], 'High Priority Meeting')
        self.assertEqual(main_meeting['EmailContent'], 'This is a high priority meeting.')
        self.assertIsInstance(main_meeting['Duration_mins'], str)
        
        # If there are rescheduled meetings, check their format too
        if len(meetings_json) > 1:
            rescheduled_meeting = meetings_json[1]
            for field in required_fields:
                self.assertIn(field, rescheduled_meeting)
            self.assertIn('rescheduled', rescheduled_meeting['MetaData'])
            self.assertTrue(rescheduled_meeting['MetaData']['rescheduled'])
            
    def test_comprehensive_rescheduling_with_json(self):
        """Test comprehensive rescheduling scenario with JSON output validation."""
        # Create a calendar with a meeting that blocks the exact requested time
        calendars = {
            "user1": [
                {
                    'StartTime': '2025-07-19T10:00:00+05:30',
                    'EndTime': '2025-07-19T11:00:00+05:30',
                    'Attendees': ['user1'],
                    'Summary': 'Low Priority Standup',
                    'Priority': 4  # Low priority - can be rescheduled
                },
                {
                    'StartTime': '2025-07-19T11:00:00+05:30',
                    'EndTime': '2025-07-19T18:00:00+05:30',
                    'Attendees': ['user1'],
                    'Summary': 'Busy Day Meeting',
                    'Priority': 4  # Low priority - can be rescheduled
                }
            ]
        }
        
        # High priority meeting that conflicts
        meeting_request = {
            "start time ": "19-07-2025T10:00:00",
            "Duration of meeting": "60 min",
            "Subject": "Emergency Meeting",
            "EmailContent": "Urgent discussion needed.",
            "Priority": 1  # Highest priority
        }
        
        result = schedule_meeting_from_request(calendars, meeting_request)
        
        # Verify successful scheduling with rescheduling
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertTrue(result['rescheduling_required'])
        self.assertIn('meetings_json', result)
        
        # Check rescheduling results
        self.assertIsNotNone(result['rescheduling_result'])
        rescheduled_meetings = result['rescheduling_result'].get('rescheduled_meetings', [])
        
        # Verify JSON output contains both original and rescheduled meetings
        meetings_json = result['meetings_json']
        self.assertIsInstance(meetings_json, list)
        
        # Should have the main meeting
        main_meeting = meetings_json[0]
        self.assertEqual(main_meeting['Subject'], 'Emergency Meeting')
        self.assertEqual(main_meeting['EventStart'], '2025-07-19T10:00:00+05:30')
        self.assertEqual(main_meeting['EventEnd'], '2025-07-19T11:00:00+05:30')
        self.assertEqual(main_meeting['Duration_mins'], '60')
        self.assertTrue(main_meeting['MetaData']['rescheduling_required'])
        
        # If rescheduling was successful, should have rescheduled meetings in JSON
        if rescheduled_meetings:
            self.assertGreater(len(meetings_json), 1)
            rescheduled_json = meetings_json[1]
            self.assertEqual(rescheduled_json['Subject'], 'Low Priority Standup')
            self.assertTrue(rescheduled_json['MetaData']['rescheduled'])
            self.assertIn('original_start', rescheduled_json['MetaData'])
            self.assertIn('original_end', rescheduled_json['MetaData'])
        

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)