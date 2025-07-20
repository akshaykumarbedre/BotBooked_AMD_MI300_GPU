#!/usr/bin/env python3
"""
Test script to verify JSON output format
"""

from main_meeting_algo import schedule_meeting_from_request
import json

# Test data
USER_CALENDARS_INPUT = {
    "user1": [
        {'StartTime': '2025-07-19T09:00:00+05:30', 'EndTime': '2025-07-19T11:00:00+05:30', 'Attendees': ['user1'], 'Summary': 'Morning Standup'},
        {'StartTime': '2025-07-19T14:00:00+05:30', 'EndTime': '2025-07-19T15:30:00+05:30', 'Attendees': ['user1'], 'Summary': 'Design Review'}
    ],
    "user2": [
        {'StartTime': '2025-07-19T10:30:00+05:30', 'EndTime': '2025-07-19T11:30:00+05:30', 'Attendees': ['user2'], 'Summary': 'Client Call'}
    ],
    "user3": []
}

MEETING_REQUEST_INPUT = {
    "start time ": "19-07-2025T09:00:00",
    "Duration of meeting": "180 min",
    "Subject": "CRITICAL: Production Outage Debrief",
    "EmailContent": "Hi team, we must meet to discuss the production outage.",
    "Priority": 1
}

print("Testing JSON output format...")
result = schedule_meeting_from_request(USER_CALENDARS_INPUT, MEETING_REQUEST_INPUT)

if result and result.get('success') and 'meetings_json' in result:
    print("\n" + "="*60)
    print("JSON OUTPUT:")
    print("="*60)
    meetings_json = result['meetings_json']
    print(json.dumps(meetings_json, indent=2))
    print("="*60)
    
    print(f"\nNumber of meetings in output: {len(meetings_json)}")
    for i, meeting in enumerate(meetings_json, 1):
        print(f"{i}. {meeting['Subject']} - {meeting.get('MetaData', {}).get('type', 'unknown')}")
else:
    print("Failed to get JSON output or scheduling failed")
    if result:
        print(f"Result: {result}")