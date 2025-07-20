# Recurrence-Based Scheduling Enhancement

## Overview

This update adds **recurrence-based reschedule support** to the existing mail scheduling algorithm, maintaining all existing functionality while providing enhanced JSON output format.

## New Features

### 1. Recurrence-Based Rescheduling

When meetings need to be rescheduled due to conflicts, the algorithm can now accept recurrence details to intelligently find optimal reschedule times:

```python
recurrence_details = {
    "pattern": "weekly",      # "daily", "weekly", "monthly"
    "frequency": 1,           # Frequency multiplier
    "end_date": "2025-12-31T23:59:59+05:30"
}
```

### 2. Enhanced JSON Input/Output

**New Input Format:**
```json
{
    "Request_id": "6118b54f-907b-4451-8d48-dd13d76033a5",
    "Datetime": "24-07-2025T10:30:00",
    "Location": "IISc Bangalore", 
    "From": "userone.amd@gmail.com",
    "Attendees": [
        {"email": "usertwo.amd@gmail.com"},
        {"email": "userthree.amd@gmail.com"}
    ],
    "Subject": "Agentic AI Project Status Update",
    "EmailContent": "Hi team, let's meet on Thursday for 30 minutes to discuss the status of Agentic AI Project."
}
```

**New Output Format:**
```json
{
    "Subject": "Agentic AI Project Status Update",
    "EmailContent": "Hi team, let's meet on Thursday for 30 minutes to discuss the status of Agentic AI Project.",
    "EventStart": "2025-07-24T10:30:00+05:30",
    "EventEnd": "2025-07-24T11:00:00+05:30", 
    "Duration_mins": "30",
    "MetaData": {
        "success": true,
        "rescheduling_required": false,
        "recurrence_details": {
            "pattern": "weekly",
            "frequency": 1,
            "end_date": "2025-12-31T23:59:59+05:30"
        }
    }
}
```

## Usage

### Basic Scheduling with JSON Format

```python
from main_meeting_algo import schedule_meeting_with_json_output

input_request = {
    "Subject": "Team Meeting",
    "EmailContent": "Let's meet for 30 minutes",
    "Datetime": "24-07-2025T10:30:00",
    "From": "manager@company.com",
    "Attendees": [{"email": "dev@company.com"}]
}

result = schedule_meeting_with_json_output(input_request)
```

### Scheduling with Recurrence Support

```python
recurrence_details = {
    "pattern": "weekly",
    "frequency": 1,
    "end_date": "2025-12-31T23:59:59+05:30"
}

result = schedule_meeting_with_json_output(
    input_request, 
    recurrence_details=recurrence_details
)
```

### Advanced Recurrence Rescheduling

```python
from main_meeting_algo import reschedule_with_recurrence

# When conflicts occur, use recurrence to find new slots
meetings_to_reschedule = [(start_time, end_time, priority, summary)]
calendars = {"user1": [], "user2": []}

suggestions = reschedule_with_recurrence(
    calendars, 
    meetings_to_reschedule, 
    recurrence_details
)
```

## Recurrence Patterns Supported

- **Daily**: `{"pattern": "daily", "frequency": 1}` → Next day same time
- **Weekly**: `{"pattern": "weekly", "frequency": 1}` → Next week same time  
- **Monthly**: `{"pattern": "monthly", "frequency": 1}` → Next month same time

## Enhanced Algorithm Flow

1. **Standard Scheduling**: Algorithm attempts to find free slots using existing logic
2. **Conflict Detection**: If conflicts occur, identifies meetings that can be rescheduled
3. **Recurrence Application**: When `recurrence_details` provided, applies pattern-based rescheduling
4. **JSON Output**: Returns results in standardized JSON format with metadata

## Backward Compatibility

- All existing functions continue to work unchanged
- New functionality is additive only
- Original algorithm flow and logic preserved
- Existing tests continue to pass

## Demo Scripts

Run the demonstration scripts to see the functionality in action:

```bash
# Basic recurrence demo
python test_recurrence_demo.py

# Forced rescheduling demo
python test_forced_reschedule_demo.py

# Final comprehensive demo
python final_demo.py
```

## Testing

Enhanced test suite includes:

- Recurrence functionality tests
- JSON input/output validation  
- Integration with existing features
- Edge case handling

```bash
python test_scheduler.py
```

All tests pass, confirming the implementation maintains existing functionality while adding new capabilities.