#!/usr/bin/env python3
"""
Demo script to showcase the new recurrence-based scheduling functionality.
"""

import json
from main_meeting_algo import schedule_meeting_with_json_output

def main():
    print("=" * 80)
    print("DEMO: Recurrence-Based Reschedule Support with JSON Output")
    print("=" * 80)
    
    # Sample input matching the format from JSON_Samples/Input_Request.json
    input_request = {
        "Request_id": "demo-recurrence-123",
        "Datetime": "24-07-2025T10:30:00",
        "Location": "Conference Room A",
        "From": "manager@company.com",
        "Attendees": [
            {"email": "developer1@company.com"},
            {"email": "developer2@company.com"},
            {"email": "designer@company.com"}
        ],
        "Subject": "Agentic AI Project Status Update",
        "EmailContent": "Hi team, let's meet on Thursday for 30 minutes to discuss the status of Agentic AI Project."
    }
    
    # Create sample user calendars with some conflicts to trigger rescheduling
    user_calendars = {
        "manager@company.com": [
            {
                'StartTime': '2025-07-24T10:00:00+05:30',
                'EndTime': '2025-07-24T10:45:00+05:30',
                'Attendees': ['manager@company.com'],
                'Summary': 'Low Priority Admin Meeting',
                'Priority': 4  # Low priority - can be rescheduled
            }
        ],
        "developer1@company.com": [
            {
                'StartTime': '2025-07-24T10:15:00+05:30',
                'EndTime': '2025-07-24T11:15:00+05:30',
                'Attendees': ['developer1@company.com'],
                'Summary': 'Code Review Session',
                'Priority': 3  # Medium priority
            }
        ],
        "developer2@company.com": [],
        "designer@company.com": []
    }
    
    # Recurrence details for rescheduling conflicted meetings
    recurrence_details = {
        "pattern": "weekly",
        "frequency": 1,
        "end_date": "2025-12-31T23:59:59+05:30",
        "description": "Weekly recurring pattern for rescheduled meetings"
    }
    
    print("\n1. INPUT REQUEST:")
    print(json.dumps(input_request, indent=2))
    
    print("\n2. RECURRENCE DETAILS:")
    print(json.dumps(recurrence_details, indent=2))
    
    print("\n3. SCHEDULING PROCESS:")
    print("-" * 40)
    
    # Call the scheduling function with recurrence support
    result = schedule_meeting_with_json_output(
        input_request, 
        user_calendars=user_calendars,
        recurrence_details=recurrence_details
    )
    
    print("\n4. JSON OUTPUT (as required by issue):")
    print("-" * 40)
    print(json.dumps(result, indent=2))
    
    print("\n5. VERIFICATION:")
    print("-" * 40)
    
    # Verify the output format matches requirements
    required_fields = ["Subject", "EmailContent", "EventStart", "EventEnd", "Duration_mins", "MetaData"]
    
    for field in required_fields:
        if field in result:
            print(f"✅ {field}: {result[field]}")
        else:
            print(f"❌ Missing required field: {field}")
    
    # Check if recurrence details are properly handled
    if "recurrence_details" in result.get("MetaData", {}):
        print("✅ Recurrence details included in MetaData")
        recurrence_info = result["MetaData"]["recurrence_details"]
        print(f"   - Pattern: {recurrence_info.get('pattern', 'N/A')}")
        print(f"   - Frequency: {recurrence_info.get('frequency', 'N/A')}")
    else:
        print("❌ Recurrence details missing from MetaData")
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    main()