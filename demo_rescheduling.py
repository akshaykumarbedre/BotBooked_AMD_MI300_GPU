#!/usr/bin/env python3
"""
Demonstration script showing the enhanced meeting rescheduling functionality.
This script demonstrates various scenarios including successful rescheduling,
failed rescheduling, and JSON output formatting.
"""

import json
from main_meeting_algo import schedule_meeting_from_request


def print_scenario(title, description):
    """Print a formatted scenario header."""
    print("\n" + "="*80)
    print(f"SCENARIO: {title}")
    print("="*80)
    print(f"Description: {description}\n")


def print_json_output(result):
    """Print formatted JSON output if available."""
    if result and result.get('meetings_json'):
        print("\n" + "="*25 + " JSON OUTPUT " + "="*25)
        print(json.dumps(result['meetings_json'], indent=2))
        print("="*63)
    else:
        print("\nNo JSON output available (scheduling failed)")


def demo_scenario_1():
    """Successful rescheduling with multiple displaced meetings."""
    print_scenario(
        "Successful Rescheduling", 
        "High-priority meeting displaces multiple lower-priority meetings, and the system successfully finds new slots for them."
    )
    
    user_calendars = {
        "alice": [
            {'StartTime': '2025-07-20T09:00:00+05:30', 'EndTime': '2025-07-20T10:00:00+05:30', 
             'Attendees': ['alice'], 'Summary': 'Daily Standup', 'Priority': 4},
            {'StartTime': '2025-07-20T10:30:00+05:30', 'EndTime': '2025-07-20T11:30:00+05:30', 
             'Attendees': ['alice'], 'Summary': 'Code Review', 'Priority': 3}
        ],
        "bob": [
            {'StartTime': '2025-07-20T10:00:00+05:30', 'EndTime': '2025-07-20T11:00:00+05:30', 
             'Attendees': ['bob'], 'Summary': 'Design Discussion', 'Priority': 4}
        ]
    }
    
    meeting_request = {
        "start time ": "20-07-2025T09:30:00",
        "Duration of meeting": "120 min",
        "Subject": "URGENT: Security Incident Response",
        "EmailContent": "Critical security incident requires immediate team attention.",
        "Priority": 1
    }
    
    result = schedule_meeting_from_request(user_calendars, meeting_request)
    print_json_output(result)
    return result


def demo_scenario_2():
    """Scenario where some meetings can be rescheduled but others cannot."""
    print_scenario(
        "Partial Rescheduling Success",
        "Some displaced meetings can be rescheduled while others cannot due to calendar constraints."
    )
    
    user_calendars = {
        "charlie": [
            {'StartTime': '2025-07-20T14:00:00+05:30', 'EndTime': '2025-07-20T15:00:00+05:30', 
             'Attendees': ['charlie'], 'Summary': 'Team Meeting', 'Priority': 4},
            {'StartTime': '2025-07-20T15:00:00+05:30', 'EndTime': '2025-07-20T18:00:00+05:30', 
             'Attendees': ['charlie'], 'Summary': 'Long Workshop', 'Priority': 4}
        ]
    }
    
    meeting_request = {
        "start time ": "20-07-2025T14:00:00",
        "Duration of meeting": "90 min",
        "Subject": "Executive Review",
        "EmailContent": "Quarterly executive review meeting.",
        "Priority": 1
    }
    
    result = schedule_meeting_from_request(user_calendars, meeting_request)
    print_json_output(result)
    return result


def demo_scenario_3():
    """Scenario with no conflicts - just a normal booking."""
    print_scenario(
        "No Rescheduling Needed",
        "Meeting scheduled in a free slot with no conflicts."
    )
    
    user_calendars = {
        "diana": [
            {'StartTime': '2025-07-20T09:00:00+05:30', 'EndTime': '2025-07-20T10:00:00+05:30', 
             'Attendees': ['diana'], 'Summary': 'Morning Sync', 'Priority': 3}
        ]
    }
    
    meeting_request = {
        "start time ": "20-07-2025T11:00:00",
        "Duration of meeting": "60 min",
        "Subject": "Project Planning Session",
        "EmailContent": "Planning session for the new project initiative.",
        "Priority": 2
    }
    
    result = schedule_meeting_from_request(user_calendars, meeting_request)
    print_json_output(result)
    return result


def demo_scenario_4():
    """Scenario where scheduling completely fails."""
    print_scenario(
        "Complete Scheduling Failure",
        "Meeting cannot be scheduled due to high-priority conflicts or no available slots."
    )
    
    user_calendars = {
        "eve": [
            {'StartTime': '2025-07-20T08:00:00+05:30', 'EndTime': '2025-07-20T18:00:00+05:30', 
             'Attendees': ['eve'], 'Summary': 'All-Day Critical Project', 'Priority': 1}
        ]
    }
    
    meeting_request = {
        "start time ": "20-07-2025T10:00:00",
        "Duration of meeting": "60 min",
        "Subject": "Regular Team Check-in",
        "EmailContent": "Weekly team check-in meeting.",
        "Priority": 3
    }
    
    result = schedule_meeting_from_request(user_calendars, meeting_request)
    print_json_output(result)
    return result


def main():
    """Run all demonstration scenarios."""
    print("MEETING RESCHEDULING DEMONSTRATION")
    print("This demo shows the enhanced rescheduling functionality with JSON output")
    
    scenarios = [
        demo_scenario_1,
        demo_scenario_2,
        demo_scenario_3,
        demo_scenario_4
    ]
    
    results = []
    for scenario in scenarios:
        try:
            result = scenario()
            results.append(result)
            print("\n" + "-"*80)
        except Exception as e:
            print(f"Error in scenario: {e}")
            results.append(None)
    
    # Summary
    print("\n" + "="*80)
    print("DEMONSTRATION SUMMARY")
    print("="*80)
    
    successful_bookings = sum(1 for r in results if r and r.get('success'))
    rescheduling_scenarios = sum(1 for r in results if r and r.get('rescheduling_required'))
    json_outputs = sum(1 for r in results if r and r.get('meetings_json'))
    
    print(f"Total scenarios: {len(scenarios)}")
    print(f"Successful bookings: {successful_bookings}")
    print(f"Scenarios requiring rescheduling: {rescheduling_scenarios}")
    print(f"Scenarios with JSON output: {json_outputs}")
    
    print("\nKey Features Demonstrated:")
    print("✅ Actual rescheduling with new time slots (not just logging)")
    print("✅ JSON output for all booked and rescheduled meetings")
    print("✅ Same scheduling logic used for initial booking and rescheduling")
    print("✅ Graceful handling of partial and failed rescheduling")
    print("✅ Comprehensive metadata in JSON output")


if __name__ == "__main__":
    main()