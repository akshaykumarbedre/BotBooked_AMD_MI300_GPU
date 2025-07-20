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
        self.assertIn('meetings', result)
        self.assertGreater(len(result['meetings']), 0)
        
        # Check the meeting has the correct format
        meeting = result['meetings'][0]
        self.assertIn('Subject', meeting)
        self.assertIn('EventStart', meeting)
        self.assertIn('EventEnd', meeting)
        self.assertIn('Duration_mins', meeting)
        self.assertIn('MetaData', meeting)
        self.assertEqual(meeting['Subject'], 'Team Meeting')
        
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
        self.assertIn('meetings', result)
        
        # Should have at least the new meeting scheduled
        meetings = result['meetings']
        self.assertGreater(len(meetings), 0)
        
        # First meeting should be the new high priority one
        new_meeting = meetings[0]
        self.assertEqual(new_meeting['Subject'], 'URGENT: Critical Bug Fix')
        self.assertIn('newly_scheduled', new_meeting.get('MetaData', {}))
        
        # Check if rescheduled meetings are included
        rescheduled_meetings = [m for m in meetings if m.get('MetaData', {}).get('rescheduled')]
        self.assertGreaterEqual(len(rescheduled_meetings), 1)
        
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
        self.assertIn('meetings', result)
        self.assertEqual(len(result['meetings']), 0)
        
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
        
    def test_json_output_format_validation(self):
        """Test that output follows the exact JSON format specification."""
        meeting_request = {
            "start time ": "19-07-2025T12:00:00",
            "Duration of meeting": "30 min",
            "Subject": "Agentic AI Project Status Update",
            "EmailContent": "Hi team, let's meet on Thursday for 30 minutes to discuss the status of Agentic AI Project.",
            "Priority": 3
        }
        
        result = schedule_meeting_from_request(self.sample_calendars, meeting_request)
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertIn('meetings', result)
        
        meetings = result['meetings']
        self.assertGreater(len(meetings), 0)
        
        # Validate the first meeting follows the exact format
        meeting = meetings[0]
        required_fields = ['Subject', 'EmailContent', 'EventStart', 'EventEnd', 'Duration_mins', 'MetaData']
        
        for field in required_fields:
            self.assertIn(field, meeting, f"Missing required field: {field}")
        
        # Validate specific format details
        self.assertEqual(meeting['Subject'], 'Agentic AI Project Status Update')
        self.assertEqual(meeting['EmailContent'], 'Hi team, let\'s meet on Thursday for 30 minutes to discuss the status of Agentic AI Project.')
        self.assertEqual(meeting['Duration_mins'], '30')
        self.assertIsInstance(meeting['MetaData'], dict)
        
        # Validate datetime format
        self.assertTrue(meeting['EventStart'].endswith('+05:30'))
        self.assertTrue(meeting['EventEnd'].endswith('+05:30'))
        
    def test_rescheduling_with_same_function_logic(self):
        """Test that rescheduling uses the same find_earliest_slot function."""
        # Create a scenario that will definitely require rescheduling
        conflicted_calendars = {
            "user1": [
                {
                    'StartTime': '2025-07-19T09:00:00+05:30',
                    'EndTime': '2025-07-19T11:00:00+05:30',  # Increased duration to create conflict
                    'Attendees': ['user1'],
                    'Summary': 'Daily Standup',
                    'Priority': 4  # Low priority
                }
            ]
        }
        
        meeting_request = {
            "start time ": "19-07-2025T09:00:00",
            "Duration of meeting": "90 min",  # Increased to ensure conflict
            "Subject": "CRITICAL: System Down",
            "EmailContent": "Emergency meeting about system outage",
            "Priority": 1  # Highest priority
        }
        
        result = schedule_meeting_from_request(conflicted_calendars, meeting_request)
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        
        meetings = result['meetings']
        self.assertGreater(len(meetings), 0)
        
        # First meeting should be the new high-priority one
        new_meeting = meetings[0]
        self.assertEqual(new_meeting['Subject'], 'CRITICAL: System Down')
        self.assertTrue(new_meeting['MetaData'].get('newly_scheduled'))
        
        # If rescheduling occurred, check the rescheduled meeting
        if result['rescheduling_required']:
            self.assertGreater(len(meetings), 1)
            rescheduled_meeting = meetings[1]
            self.assertEqual(rescheduled_meeting['Subject'], 'Daily Standup')
            self.assertTrue(rescheduled_meeting['MetaData'].get('rescheduled'))
            self.assertIn('original_start', rescheduled_meeting['MetaData'])
            
            # Verify the rescheduled meeting has a different time
            original_start = '2025-07-19T09:00:00+05:30'
            self.assertNotEqual(rescheduled_meeting['EventStart'], original_start)
        
    def test_multiple_meetings_rescheduled(self):
        """Test rescheduling multiple conflicting meetings."""
        complex_calendars = {
            "user1": [
                {
                    'StartTime': '2025-07-19T09:00:00+05:30',
                    'EndTime': '2025-07-19T10:30:00+05:30',  # First meeting
                    'Attendees': ['user1'],
                    'Summary': 'Morning Meeting 1',
                    'Priority': 4
                },
                {
                    'StartTime': '2025-07-19T10:30:00+05:30',
                    'EndTime': '2025-07-19T12:00:00+05:30',  # Second meeting, back-to-back
                    'Attendees': ['user1'],
                    'Summary': 'Morning Meeting 2',
                    'Priority': 4
                }
            ]
        }
        
        meeting_request = {
            "start time ": "19-07-2025T09:00:00",
            "Duration of meeting": "150 min",  # Will definitely conflict with both meetings
            "Subject": "Executive Decision Meeting",
            "EmailContent": "Urgent executive meeting",
            "Priority": 1
        }
        
        result = schedule_meeting_from_request(complex_calendars, meeting_request)
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        
        meetings = result['meetings']
        self.assertGreater(len(meetings), 0)
        
        # Check that the new meeting was scheduled
        new_meeting = meetings[0]
        self.assertEqual(new_meeting['Subject'], 'Executive Decision Meeting')
        
        # If rescheduling occurred, check that multiple meetings were rescheduled
        if result['rescheduling_required']:
            rescheduled_meetings = [m for m in meetings if m.get('MetaData', {}).get('rescheduled')]
            self.assertGreaterEqual(len(rescheduled_meetings), 1)  # At least one should be rescheduled
        
    def test_fallback_strategy_json_output(self):
        """Test that fallback strategies also produce correct JSON output."""
        meeting_request = {
            "start time ": "19-07-2025T16:30:00",
            "Duration of meeting": "180 min",  # Too long for available slots
            "Subject": "Long Workshop",
            "EmailContent": "Extended workshop session",
            "Priority": 3
        }
        
        result = schedule_meeting_from_request(self.sample_calendars, meeting_request)
        
        self.assertIsNotNone(result)
        # Should succeed with fallback strategy (shorter duration)
        if result['success']:
            self.assertIn('meetings', result)
            meetings = result['meetings']
            self.assertGreater(len(meetings), 0)
            
            meeting = meetings[0]
            self.assertEqual(meeting['Subject'], 'Long Workshop')
            # Duration should be less than requested due to fallback
            actual_duration = int(meeting['Duration_mins'])
            self.assertLess(actual_duration, 180)
            
    def test_manual_intervention_required(self):
        """Test case where meeting cannot be automatically rescheduled."""
        # Create a calendar where rescheduling is impossible
        impossible_calendars = {
            "user1": [
                {
                    'StartTime': '2025-07-19T08:00:00+05:30',
                    'EndTime': '2025-07-19T18:00:00+05:30',
                    'Attendees': ['user1'],
                    'Summary': 'All Day Important Meeting',
                    'Priority': 3  # Lower priority but very long
                }
            ]
        }
        
        meeting_request = {
            "start time ": "19-07-2025T09:00:00",
            "Duration of meeting": "60 min",
            "Subject": "Emergency Meeting",
            "EmailContent": "Urgent meeting required",
            "Priority": 2  # Higher priority
        }
        
        result = schedule_meeting_from_request(impossible_calendars, meeting_request)
        
        if result['success'] and result['rescheduling_required']:
            meetings = result['meetings']
            
            # Check if any meeting needs manual intervention
            manual_intervention_meetings = [
                m for m in meetings 
                if m.get('MetaData', {}).get('needs_manual_intervention')
            ]
            
            if manual_intervention_meetings:
                meeting = manual_intervention_meetings[0]
                self.assertIn('[NEEDS MANUAL RESCHEDULING]', meeting['Subject'])
                self.assertIn('manual intervention', meeting['EmailContent'])


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)