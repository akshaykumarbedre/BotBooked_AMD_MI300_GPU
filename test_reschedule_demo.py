#!/usr/bin/env python3
"""
Demo script to showcase recurrence-based rescheduling when conflicts occur.
"""

import json
from main_meeting_algo import schedule_meeting_with_json_output

def main():
    print("=" * 80)
    print("DEMO: Recurrence-Based Rescheduling with Conflicts")
    print("=" * 80)
    
    # High priority meeting that will conflict with existing meetings
    input_request = {
        "Request_id": "urgent-meeting-456",
        "Datetime": "24-07-2025T10:00:00",
        "Location": "Main Conference Room",
        "From": "ceo@company.com",
        "Attendees": [
            {"email": "manager@company.com"},
            {"email": "developer1@company.com"},
            {"email": "developer2@company.com"}
        ],
        "Subject": "URGENT: Critical Bug Fix Meeting",
        "EmailContent": "Team, we need to meet for 90 minutes to address the critical production issue immediately."
    }
    
    # Create calendars with conflicting meetings to force rescheduling
    user_calendars = {
        "ceo@company.com": [],
        "manager@company.com": [
            {
                'StartTime': '2025-07-24T10:00:00+05:30',
                'EndTime': '2025-07-24T11:00:00+05:30',
                'Attendees': ['manager@company.com'],
                'Summary': 'Team Standup',
                'Priority': 4  # Low priority - will be rescheduled
            }
        ],
        "developer1@company.com": [
            {
                'StartTime': '2025-07-24T10:30:00+05:30',
                'EndTime': '2025-07-24T11:30:00+05:30',
                'Attendees': ['developer1@company.com'],
                'Summary': 'Code Review',
                'Priority': 4  # Low priority - will be rescheduled
            }
        ],
        "developer2@company.com": [
            {
                'StartTime': '2025-07-24T11:00:00+05:30',
                'EndTime': '2025-07-24T12:00:00+05:30',
                'Attendees': ['developer2@company.com'],
                'Summary': 'Documentation Work',
                'Priority': 4  # Low priority - will be rescheduled
            }
        ]
    }
    
    # Recurrence details for rescheduling
    recurrence_details = {
        "pattern": "daily",
        "frequency": 1,
        "end_date": "2025-08-31T23:59:59+05:30",
        "description": "Daily recurrence for urgent rescheduled meetings"
    }
    
    print("\n1. HIGH PRIORITY INPUT REQUEST:")
    print(json.dumps(input_request, indent=2))
    
    print("\n2. RECURRENCE DETAILS FOR RESCHEDULING:")
    print(json.dumps(recurrence_details, indent=2))
    
    print("\n3. SCHEDULING PROCESS (with conflicts):")
    print("-" * 50)
    
    # Modify the meeting request to indicate high priority
    internal_request = input_request.copy()
    
    # Call the scheduling function - this should trigger rescheduling
    result = schedule_meeting_with_json_output(
        input_request,
        user_calendars=user_calendars,
        recurrence_details=recurrence_details
    )
    
    print("\n4. JSON OUTPUT WITH RESCHEDULING:")
    print("-" * 50)
    print(json.dumps(result, indent=2))
    
    print("\n5. ANALYSIS:")
    print("-" * 50)
    
    if result.get("MetaData", {}).get("success"):
        print("✅ Meeting successfully scheduled")
        print(f"   Event Start: {result.get('EventStart')}")
        print(f"   Event End: {result.get('EventEnd')}")
        print(f"   Duration: {result.get('Duration_mins')} minutes")
        
        metadata = result.get("MetaData", {})
        
        if metadata.get("rescheduling_required"):
            print("✅ Rescheduling was required and handled")
            if "rescheduled_meetings" in metadata:
                print(f"   Number of meetings rescheduled: {len(metadata['rescheduled_meetings'])}")
                
            if "recurrence_reschedule_suggestions" in metadata:
                print("✅ Recurrence-based reschedule suggestions generated")
                suggestions = metadata["recurrence_reschedule_suggestions"]
                for i, suggestion in enumerate(suggestions, 1):
                    status = suggestion.get('status', 'unknown')
                    original = suggestion.get('original_meeting', {})
                    print(f"   Suggestion {i}: {original.get('summary', 'Unknown')} - {status}")
            else:
                print("ℹ️  No specific recurrence reschedule suggestions (meetings found free slots)")
        else:
            print("ℹ️  No rescheduling was required")
            
        if metadata.get("recurrence_details"):
            print("✅ Recurrence details preserved in output")
            pattern = metadata["recurrence_details"].get("pattern", "N/A")
            print(f"   Recurrence pattern: {pattern}")
    else:
        print("❌ Meeting scheduling failed")
        error = result.get("MetaData", {}).get("error", "Unknown error")
        print(f"   Error: {error}")
    
    print("\n" + "=" * 80)
    print("RECURRENCE RESCHEDULING DEMO COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()