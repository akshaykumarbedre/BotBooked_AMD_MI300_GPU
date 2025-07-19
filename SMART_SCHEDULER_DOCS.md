# Smart Meeting Scheduler Features Documentation

## Overview

The enhanced smart meeting scheduler provides intelligent scheduling capabilities with priority-based conflict resolution, participant preferences, and fallback strategies.

## Features

### 1. Priority-Based Conflict Resolution

- **Priority Scale**: 1 (highest) to 4 (lowest)
- **Automatic Priority Assignment**: Based on meeting keywords
  - "Client Call" → Priority 2
  - "Design Review" → Priority 3
  - Default → Priority 4
- **Conflict Resolution**: Lower priority meetings can be rescheduled for higher priority ones
- **Logging**: Full rescheduling notifications via `requirewna()` function

### 2. Participant Preferences (Hardcoded)

#### User Preferences Configuration:

```python
PARTICIPANT_PREFERENCES = {
    "user1": {
        "preferred_hours": {"start": 9, "end": 17},    # 9 AM - 5 PM
        "max_meetings_per_day": 6,
        "avoid_back_to_back": True,
        "buffer_minutes": 15
    },
    "user2": {
        "preferred_hours": {"start": 10, "end": 18},   # 10 AM - 6 PM
        "max_meetings_per_day": 4,
        "avoid_back_to_back": True,
        "buffer_minutes": 30
    },
    "user3": {
        "preferred_hours": {"start": 8, "end": 16},    # 8 AM - 4 PM
        "max_meetings_per_day": 8,
        "avoid_back_to_back": False,
        "buffer_minutes": 0
    }
}
```

#### Preference Scoring System:

- **Outside preferred hours**: +50 penalty points
- **Exceeding daily meeting limit**: +30 penalty points
- **Back-to-back meetings**: +20 penalty points
- **Default threshold**: 100 points (slots with higher scores are rejected)

### 3. Fallback Strategies

When primary scheduling fails, the system attempts these fallbacks in order:

1. **Shorter Duration**: Try 75% of original duration (minimum 15 minutes)
2. **Majority Attendees**: For meetings with 3+ people, try scheduling with majority
3. **Time Window Shifts**: Try ±30 and ±60 minute shifts from desired time
4. **Relaxed Preferences**: Allow higher preference violation scores (up to 200)

### 4. Working Hours Enforcement

- Automatically determines working hours based on attendee preferences
- Earliest start time: Minimum of all attendees' preferred start hours
- Latest end time: Maximum of all attendees' preferred end hours
- Rejects slots outside these boundaries

## Usage Examples

### Basic Scheduling

```python
from main_meeting_algo import schedule_meeting_from_request

user_calendars = {
    "user1": [
        {
            'StartTime': '2025-07-19T09:00:00+05:30',
            'EndTime': '2025-07-19T10:00:00+05:30',
            'Attendees': ['user1'],
            'Summary': 'Morning Standup',
            'Priority': 4
        }
    ],
    "user2": []
}

meeting_request = {
    "start time ": "19-07-2025T09:00:00",
    "Duration of meeting": "60 min",
    "Subject": "Team Meeting",
    "Priority": 2
}

result = schedule_meeting_from_request(user_calendars, meeting_request)
```

### Result Structure

```python
{
    'success': True,
    'slot': (start_datetime, end_datetime),
    'rescheduling_required': False,  # or True if conflicts exist
    'rescheduling_result': {...},    # Details of rescheduled meetings
    'fallback_used': None,           # or fallback strategy name
    'fallback_details': {...}       # Additional fallback information
}
```

## Functions

### Core Functions

- `schedule_meeting_from_request(user_calendars, meeting_request)`: Main scheduling function
- `find_earliest_slot(calendars, attendees, duration_minutes, priority, start_time, max_preference_score)`: Find optimal time slot
- `parse_calendar_data(raw_events)`: Parse and prioritize calendar events
- `requirewna(meetings_to_reschedule, new_meeting_info)`: Handle rescheduling notifications

### Helper Functions

- `get_user_preferences(user_id)`: Retrieve user preferences
- `calculate_preference_score(start_time, end_time, attendees, calendars)`: Score preference violations

## Testing

Run the comprehensive test suite:

```bash
python test_scheduler.py
```

### Test Coverage

- ✅ Free slot scheduling
- ✅ Priority-based rescheduling  
- ✅ High-priority conflict blocking
- ✅ Preference violation handling
- ✅ Fallback strategy execution
- ✅ Complete failure scenarios
- ✅ Priority assignment logic
- ✅ Rescheduling notification system

## Error Handling

The system provides comprehensive error handling for:

- Invalid input formats
- Timezone conversion issues
- Calendar parsing errors
- Preference constraint violations
- Scheduling conflicts
- Fallback strategy failures

All errors are logged with detailed messages for debugging.

## Performance Considerations

- Preference scoring is calculated for each potential slot
- Fallback strategies add computational overhead but improve success rates
- Working hours constraints reduce search space for better performance
- Priority-based conflict resolution minimizes unnecessary rescheduling

## Future Enhancements

Potential areas for extension:

1. **Dynamic Preferences**: Load preferences from external configuration
2. **Machine Learning**: Learn user preferences from historical data
3. **Multi-day Scheduling**: Support scheduling across multiple days
4. **Resource Constraints**: Consider room availability and equipment
5. **Notification Integration**: Real-time notifications for schedule changes