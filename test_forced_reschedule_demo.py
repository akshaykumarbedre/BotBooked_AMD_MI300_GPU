#!/usr/bin/env python3
"""
Demo script to force rescheduling and showcase recurrence-based suggestions.
"""

import json
from main_meeting_algo import (
    schedule_meeting_from_request, 
    reschedule_with_recurrence,
    format_scheduling_output
)

def main():
    print("=" * 80)
    print("DEMO: Forced Rescheduling with Recurrence-Based Suggestions")
    print("=" * 80)
    
    # Create a scenario with complete calendar blocking to force rescheduling
    user_calendars = {
        "user1": [
            {
                'StartTime': '2025-07-24T09:00:00+05:30',
                'EndTime': '2025-07-24T18:00:00+05:30',  # All day
                'Attendees': ['user1'],
                'Summary': 'Low Priority All Day Workshop',
                'Priority': 4  # Low priority - can be rescheduled
            }
        ],
        "user2": [
            {
                'StartTime': '2025-07-24T09:00:00+05:30',
                'EndTime': '2025-07-24T18:00:00+05:30',  # All day
                'Attendees': ['user2'],
                'Summary': 'Low Priority Training Session',
                'Priority': 4  # Low priority - can be rescheduled
            }
        ]
    }
    
    # High priority meeting request that will definitely need rescheduling
    meeting_request = {
        "start time ": "24-07-2025T10:00:00",  # Try to schedule in the middle
        "Duration of meeting": "60 min",  
        "Subject": "CRITICAL: Emergency Board Meeting",
        "EmailContent": "Urgent board meeting required for 1 hour.",
        "Priority": 1  # Highest priority
    }
    
    print("1. MEETING REQUEST (High Priority):")
    print(json.dumps(meeting_request, indent=2))
    
    print("\n2. EXISTING CALENDAR CONFLICTS:")
    print("-" * 40)
    for user, events in user_calendars.items():
        print(f"{user}:")
        for event in events:
            print(f"  - {event['Summary']} (P{event['Priority']}) {event['StartTime']} - {event['EndTime']}")
    
    print("\n3. SCHEDULING PROCESS:")
    print("-" * 40)
    
    # Schedule the meeting - this should trigger rescheduling
    result = schedule_meeting_from_request(user_calendars, meeting_request)
    
    if result and result.get('success') and result.get('rescheduling_required'):
        print("\n4. RESCHEDULING DETECTED - APPLYING RECURRENCE LOGIC:")
        print("-" * 60)
        
        # Get the meetings that need to be rescheduled
        rescheduling_result = result.get('rescheduling_result', {})
        meetings_to_reschedule = rescheduling_result.get('meetings_to_reschedule', [])
        
        if meetings_to_reschedule:
            # Convert to the format expected by reschedule_with_recurrence
            meetings_list = []
            for meeting in meetings_to_reschedule:
                meetings_list.append((
                    meeting['original_start'],
                    meeting['original_end'],
                    meeting['priority'],
                    meeting['summary']
                ))
            
            # Parse the user calendars to the format expected by the function
            from main_meeting_algo import parse_calendar_data
            
            # Convert user_calendars to raw events format first
            all_raw_events = []
            for user_id, events in user_calendars.items():
                for event in events:
                    all_raw_events.append(event)
            
            # Parse the calendars
            parsed_calendars = parse_calendar_data(all_raw_events)
            
            # Test different recurrence patterns
            recurrence_patterns = [
                {"pattern": "daily", "frequency": 1},
                {"pattern": "weekly", "frequency": 1},
                {"pattern": "monthly", "frequency": 1}
            ]
            
            for pattern in recurrence_patterns:
                print(f"\n   Testing {pattern['pattern']} recurrence pattern:")
                
                # Apply recurrence-based rescheduling
                suggestions = reschedule_with_recurrence(
                    parsed_calendars, meetings_list, pattern
                )
                
                # Show results
                for suggestion in suggestions:
                    original = suggestion['original_meeting']
                    status = suggestion['status']
                    
                    if status == 'rescheduled' and suggestion['new_slot']:
                        new_slot = suggestion['new_slot']
                        print(f"     ✅ {original['summary']}: {original['start'].strftime('%Y-%m-%d %H:%M')} → {new_slot['start'].strftime('%Y-%m-%d %H:%M')}")
                    elif status == 'error_rescheduling':
                        print(f"     ❌ {original['summary']}: Error - {suggestion.get('error', 'Unknown error')}")
                    else:
                        print(f"     ❌ {original['summary']}: Could not reschedule")
        
        print("\n5. FINAL JSON OUTPUT WITH RECURRENCE METADATA:")
        print("-" * 50)
        
        # Create the final JSON output with recurrence details
        final_recurrence_details = {"pattern": "weekly", "frequency": 1, "end_date": "2025-12-31T23:59:59+05:30"}
        
        # Update the result with recurrence information
        enhanced_result = result.copy()
        enhanced_result['recurrence_details'] = final_recurrence_details
        
        # Format as the required JSON output
        json_output = format_scheduling_output(enhanced_result, meeting_request, final_recurrence_details)
        
        print(json.dumps(json_output, indent=2))
        
        print("\n6. SUMMARY:")
        print("-" * 30)
        print(f"✅ High priority meeting scheduled: {json_output['EventStart']} - {json_output['EventEnd']}")
        print(f"✅ Duration: {json_output['Duration_mins']} minutes")
        print(f"✅ Rescheduling required: {json_output['MetaData']['rescheduling_required']}")
        print(f"✅ Recurrence pattern: {json_output['MetaData']['recurrence_details']['pattern']}")
        
        if 'rescheduled_meetings' in json_output['MetaData']:
            rescheduled_count = len(json_output['MetaData']['rescheduled_meetings'])
            print(f"✅ Meetings rescheduled: {rescheduled_count}")
            
    else:
        print("\n❌ Expected rescheduling scenario did not occur")
        if result:
            print(f"Result: {result}")
    
    print("\n" + "=" * 80)
    print("FORCED RESCHEDULING DEMO COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()