import datetime
import collections
import re

# Hardcoded participant preferences
PARTICIPANT_PREFERENCES = {
    "user1": {
        "preferred_hours": {"start": 9, "end": 17},  # 9 AM to 5 PM
        "max_meetings_per_day": 6,
        "avoid_back_to_back": True,
        "buffer_minutes": 15  # Buffer between meetings
    },
    "user2": {
        "preferred_hours": {"start": 10, "end": 18},  # 10 AM to 6 PM
        "max_meetings_per_day": 4,
        "avoid_back_to_back": True,
        "buffer_minutes": 30
    },
    "user3": {
        "preferred_hours": {"start": 8, "end": 16},  # 8 AM to 4 PM
        "max_meetings_per_day": 8,
        "avoid_back_to_back": False,
        "buffer_minutes": 0
    }
}

def get_user_preferences(user_id):
    """
    Get preferences for a specific user.
    Returns default preferences if user not found.
    """
    default_preferences = {
        "preferred_hours": {"start": 9, "end": 17},
        "max_meetings_per_day": 5,
        "avoid_back_to_back": True,
        "buffer_minutes": 15
    }
    return PARTICIPANT_PREFERENCES.get(user_id, default_preferences)

def calculate_preference_score(start_time, end_time, attendees, calendars):
    """
    Calculate a preference score for a given time slot.
    Lower score is better (0 = perfect, higher = more violations).
    
    Args:
        start_time (datetime): Proposed meeting start time
        end_time (datetime): Proposed meeting end time
        attendees (list): List of attendee user IDs
        calendars (dict): Current calendar data
        
    Returns:
        int: Preference violation score (0 = no violations)
    """
    score = 0
    violations = []
    
    for user_id in attendees:
        preferences = get_user_preferences(user_id)
        user_events = calendars.get(user_id, [])
        
        # Check preferred hours violation
        meeting_start_hour = start_time.hour
        meeting_end_hour = end_time.hour
        pref_start = preferences["preferred_hours"]["start"]
        pref_end = preferences["preferred_hours"]["end"]
        
        if meeting_start_hour < pref_start or meeting_end_hour > pref_end:
            score += 50  # Heavy penalty for outside preferred hours
            violations.append(f"{user_id}: Outside preferred hours ({pref_start}-{pref_end})")
        
        # Check max meetings per day
        meeting_date = start_time.date()
        same_day_meetings = [
            event for event in user_events 
            if event[0].date() == meeting_date
        ]
        
        if len(same_day_meetings) >= preferences["max_meetings_per_day"]:
            score += 30  # Penalty for exceeding daily limit
            violations.append(f"{user_id}: Exceeds daily meeting limit ({preferences['max_meetings_per_day']})")
        
        # Check back-to-back meetings
        if preferences["avoid_back_to_back"]:
            buffer_delta = datetime.timedelta(minutes=preferences["buffer_minutes"])
            
            for event_start, event_end, _, _ in user_events:
                # Check if new meeting is too close to existing meetings
                time_diff_end = abs((event_end - start_time).total_seconds())
                time_diff_start = abs((end_time - event_start).total_seconds())
                
                if (time_diff_end < buffer_delta.total_seconds() or
                    time_diff_start < buffer_delta.total_seconds()):
                    score += 20  # Penalty for back-to-back meetings
                    violations.append(f"{user_id}: Back-to-back meeting (needs {preferences['buffer_minutes']}min buffer)")
                    break
    
    if violations:
        print(f"  Preference violations for slot {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')} (score: {score}):")
        for violation in violations:
            print(f"    - {violation}")
    
    return score

def requirewna(meetings_to_reschedule, new_meeting_info):
    """
    Handle necessary actions during rescheduling.
    This function processes meetings that need to be rescheduled and
    provides notifications or performs required actions.
    
    Args:
        meetings_to_reschedule (list): List of meeting tuples (start, end, priority, summary)
        new_meeting_info (dict): Information about the new meeting being scheduled
    
    Returns:
        dict: Result of rescheduling actions
    """
    print("\n--- RESCHEDULING REQUIRED ---")
    print(f"New meeting '{new_meeting_info.get('subject', 'Unknown')}' requires rescheduling of:")
    
    rescheduled_meetings = []
    for start, end, priority, summary in meetings_to_reschedule:
        print(f"  - (P{priority}) '{summary}' scheduled from {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}")
        rescheduled_meetings.append({
            'original_start': start,
            'original_end': end,
            'priority': priority,
            'summary': summary,
            'status': 'needs_rescheduling'
        })
    
    print("--- END RESCHEDULING NOTIFICATION ---\n")
    
    return {
        'action': 'reschedule_required',
        'meetings_to_reschedule': rescheduled_meetings,
        'new_meeting': new_meeting_info
    }


def reschedule_with_recurrence(calendars, meetings_to_reschedule, recurrence_details):
    """
    Reschedule meetings considering recurrence patterns.
    
    Args:
        calendars (dict): Current calendar data
        meetings_to_reschedule (list): List of meetings that need rescheduling
        recurrence_details (dict): Recurrence information including pattern, frequency, etc.
    
    Returns:
        list: List of new scheduling suggestions for the meetings
    """
    if not recurrence_details:
        return []
    
    print(f"\n--- RECURRENCE-BASED RESCHEDULING ---")
    print(f"Pattern: {recurrence_details.get('pattern', 'none')}")
    print(f"Frequency: {recurrence_details.get('frequency', 'none')}")
    
    reschedule_suggestions = []
    
    for meeting in meetings_to_reschedule:
        start, end, priority, summary = meeting
        duration = int((end - start).total_seconds() / 60)  # Duration in minutes
        
        # Extract attendees from the meeting - simplified approach
        attendees = list(calendars.keys())  # Use all available users as fallback
        
        # Try to find new slots based on recurrence pattern
        if recurrence_details.get('pattern') == 'weekly':
            # For weekly recurrence, try next week same time
            search_start = start + datetime.timedelta(weeks=1)
        elif recurrence_details.get('pattern') == 'daily':
            # For daily recurrence, try next day same time
            search_start = start + datetime.timedelta(days=1)
        elif recurrence_details.get('pattern') == 'monthly':
            # For monthly recurrence, try next month same time
            search_start = start + datetime.timedelta(days=30)
        else:
            # Default: try 1 hour later
            search_start = start + datetime.timedelta(hours=1)
        
        # Create a clean calendar without the conflicting meetings for rescheduling
        clean_calendars = {}
        for user_id in attendees:
            if user_id in calendars:
                # Filter out meetings that are being rescheduled
                user_events = []
                for event_tuple in calendars[user_id]:
                    if isinstance(event_tuple, tuple) and len(event_tuple) >= 4:
                        event_start, event_end, event_priority, event_summary = event_tuple
                        # Skip the meetings that are being rescheduled
                        if not (event_start == start and event_end == end and event_summary == summary):
                            user_events.append(event_tuple)
                clean_calendars[user_id] = user_events
            else:
                clean_calendars[user_id] = []
        
        # Find new slot for this meeting
        try:
            result = find_earliest_slot(
                clean_calendars, attendees, duration, priority, 
                search_start_time=search_start,
                recurrence_details=recurrence_details
            )
            
            if result:
                new_slot, _ = result
                reschedule_suggestions.append({
                    'original_meeting': {
                        'start': start,
                        'end': end,
                        'priority': priority,
                        'summary': summary
                    },
                    'new_slot': {
                        'start': new_slot[0],
                        'end': new_slot[1]
                    },
                    'status': 'rescheduled'
                })
                print(f"  Rescheduled '{summary}' to {new_slot[0].strftime('%Y-%m-%d %H:%M')} - {new_slot[1].strftime('%Y-%m-%d %H:%M')}")
            else:
                reschedule_suggestions.append({
                    'original_meeting': {
                        'start': start,
                        'end': end,
                        'priority': priority,
                        'summary': summary
                    },
                    'new_slot': None,
                    'status': 'could_not_reschedule'
                })
                print(f"  Could not reschedule '{summary}'")
        except Exception as e:
            print(f"  Error rescheduling '{summary}': {e}")
            reschedule_suggestions.append({
                'original_meeting': {
                    'start': start,
                    'end': end,
                    'priority': priority,
                    'summary': summary
                },
                'new_slot': None,
                'status': 'error_rescheduling',
                'error': str(e)
            })
    
    print("--- END RECURRENCE-BASED RESCHEDULING ---\n")
    return reschedule_suggestions


def format_scheduling_output(result, meeting_request, recurrence_details=None):
    """
    Format the scheduling result into the required JSON output format.
    
    Args:
        result (dict): Result from schedule_meeting_from_request
        meeting_request (dict): Original meeting request
        recurrence_details (dict, optional): Recurrence information
    
    Returns:
        dict: Formatted JSON output
    """
    if not result or not result.get('success'):
        return {
            "Subject": meeting_request.get('Subject', ''),
            "EmailContent": meeting_request.get('EmailContent', ''),
            "EventStart": None,
            "EventEnd": None,
            "Duration_mins": None,
            "MetaData": {
                "success": False,
                "error": result.get('error', 'Scheduling failed') if result else 'No result',
                "recurrence_details": recurrence_details or {}
            }
        }
    
    slot = result['slot']
    start_time = slot[0]
    end_time = slot[1]
    duration_mins = str(int((end_time - start_time).total_seconds() / 60))
    
    # Prepare metadata
    metadata = {
        "success": True,
        "rescheduling_required": result.get('rescheduling_required', False),
        "fallback_used": result.get('fallback_used'),
        "recurrence_details": recurrence_details or {}
    }
    
    # Add rescheduling information if applicable
    if result.get('rescheduling_required') and result.get('rescheduling_result'):
        rescheduled_meetings = result['rescheduling_result'].get('meetings_to_reschedule', [])
        # Convert datetime objects to ISO format strings for JSON serialization
        json_safe_meetings = []
        for meeting in rescheduled_meetings:
            json_safe_meeting = {
                'original_start': meeting['original_start'].isoformat() if hasattr(meeting['original_start'], 'isoformat') else str(meeting['original_start']),
                'original_end': meeting['original_end'].isoformat() if hasattr(meeting['original_end'], 'isoformat') else str(meeting['original_end']),
                'priority': meeting['priority'],
                'summary': meeting['summary'],
                'status': meeting['status']
            }
            json_safe_meetings.append(json_safe_meeting)
        
        metadata["rescheduled_meetings"] = json_safe_meetings
        
        # If recurrence details are provided, add note about recurrence-based rescheduling
        if recurrence_details:
            metadata["recurrence_reschedule_note"] = "Recurrence-based rescheduling would be applied to conflicted meetings based on the specified pattern"
    
    return {
        "Subject": meeting_request.get('Subject', ''),
        "EmailContent": meeting_request.get('EmailContent', ''),
        "EventStart": start_time.isoformat(),
        "EventEnd": end_time.isoformat(),
        "Duration_mins": duration_mins,
        "MetaData": metadata
    }

def parse_calendar_data(raw_events):
    """
    Parses a list of event dictionaries, including priority, and converts it
    into the format expected by the scheduling functions.

    It assigns default priorities if they are not specified.
    Priority Scale: Lower number is higher priority (1 is highest).
    - P2: 'Client Call'
    - P3: 'Design Review'
    - P4: Default for others

    Args:
        raw_events (list): A list of dictionaries representing calendar events.

    Returns:
        dict: A dictionary where keys are user IDs and values are lists of
              their scheduled meetings as (start, end, priority, summary) tuples.
    """
    if not raw_events:
        return {}
        
    parsed_calendars = collections.defaultdict(list)
    
    # Define default priorities based on summary keywords
    priority_map = {
        'Client Call': 2,
        'Design Review': 3,
    }

    for event in raw_events:
        try:
            # Validate required fields
            if not isinstance(event, dict):
                print(f"Skipping invalid event (not a dictionary): {event}")
                continue
                
            if 'StartTime' not in event or 'EndTime' not in event:
                print(f"Skipping event missing StartTime or EndTime: {event}")
                continue
                
            if 'Attendees' not in event or not event['Attendees']:
                print(f"Skipping event with no attendees: {event}")
                continue
            
            # Parse times
            start_time = datetime.datetime.fromisoformat(event['StartTime'])
            end_time = datetime.datetime.fromisoformat(event['EndTime'])
            
            # Validate time order
            if start_time >= end_time:
                print(f"Skipping event with invalid time order (start >= end): {event}")
                continue
            
            summary = event.get('Summary', 'No Title')
            
            # Determine priority: Use explicit priority if given, otherwise use map or default.
            priority = event.get('Priority')
            if priority is None:
                priority = next((p for keyword, p in priority_map.items() if keyword in summary), 4)
            
            # Validate priority
            if not isinstance(priority, int) or priority < 1 or priority > 4:
                print(f"Skipping event with invalid priority {priority}: {event}")
                continue

            # Add event to each attendee's calendar
            for attendee in event['Attendees']:
                if not attendee or not isinstance(attendee, str):
                    print(f"Skipping invalid attendee '{attendee}' in event: {event}")
                    continue
                    
                parsed_calendars[attendee].append((start_time, end_time, priority, summary))

        except (KeyError, TypeError, ValueError) as e:
            print(f"Skipping an event due to a parsing error: {e}. Event data: {event}")
            continue
            
    return dict(parsed_calendars)

def find_earliest_slot(calendars, attendees, duration_minutes, new_meeting_priority, search_start_time=None, max_preference_score=100, recurrence_details=None):
    """
    Finds the earliest possible time slot, considering meeting priorities and participant preferences.

    It first searches for a completely empty slot with acceptable preference score. If none is found, 
    it then looks for slots occupied by meetings of a lower priority that can be rescheduled.
    Finally, it respects working hours and preference constraints.

    Args:
        calendars (dict): Parsed calendar data with priorities.
        attendees (list): List of user IDs for the meeting.
        duration_minutes (int): The required duration of the meeting.
        new_meeting_priority (int): The priority of the meeting to be scheduled.
        search_start_time (datetime.datetime, optional): The time to start searching from.
        max_preference_score (int): Maximum acceptable preference violation score.
        recurrence_details (dict, optional): Recurrence information for rescheduling meetings.
                                           Should include 'pattern', 'frequency', 'end_date', etc.

    Returns:
        tuple or None: A tuple of ( (start_time, end_time), list_of_meetings_to_reschedule ).
                       Returns None if no suitable slot is found.
    """
    # Validate inputs
    if not calendars:
        calendars = {}
        
    if not attendees:
        raise ValueError("No attendees provided")
        
    if duration_minutes <= 0:
        raise ValueError(f"Invalid duration: {duration_minutes} minutes. Must be positive.")
        
    if not isinstance(new_meeting_priority, int) or new_meeting_priority < 1 or new_meeting_priority > 4:
        raise ValueError(f"Invalid priority: {new_meeting_priority}. Must be between 1 (highest) and 4 (lowest).")
    
    if search_start_time is None:
        search_start_time = datetime.datetime.now().astimezone()
    
    # Validate search start time
    if not isinstance(search_start_time, datetime.datetime):
        raise ValueError("search_start_time must be a datetime object")

    meeting_duration = datetime.timedelta(minutes=duration_minutes)
    
    # Determine working hours constraints based on attendee preferences
    earliest_start_hour = min(get_user_preferences(user)["preferred_hours"]["start"] for user in attendees)
    latest_end_hour = max(get_user_preferences(user)["preferred_hours"]["end"] for user in attendees)
    
    # Adjust search start time to respect working hours
    if search_start_time.hour < earliest_start_hour:
        search_start_time = search_start_time.replace(hour=earliest_start_hour, minute=0, second=0, microsecond=0)
    
    print(f"  Working hours constraint: {earliest_start_hour}:00 - {latest_end_hour}:00")
    
    # Handle recurrence details if provided
    if recurrence_details:
        print(f"  Recurrence details provided: {recurrence_details.get('pattern', 'none')}")
        # For rescheduling with recurrence, we may need to consider multiple time slots
        # This will be used in the reschedule logic to find optimal slots
    
    # 1. Aggregate all busy slots from all attendees.
    all_busy_slots = []
    for user_id in attendees:
        if user_id in calendars:
            user_events = calendars[user_id]
            if isinstance(user_events, list):
                all_busy_slots.extend(user_events)
    
    # Sort by start time to allow chronological searching.
    all_busy_slots.sort(key=lambda x: x[0])

    # 2. First pass: Find a purely free slot with acceptable preference score.
    merged_busy_slots = []
    if all_busy_slots:
        # We only care about the time intervals for this pass.
        time_intervals = [(s, e) for s, e, p, summ in all_busy_slots]
        if time_intervals:
            merged_busy_slots.append(time_intervals[0])
            for current_start, current_end in time_intervals[1:]:
                last_merged_start, last_merged_end = merged_busy_slots[-1]
                if current_start < last_merged_end:
                    merged_busy_slots[-1] = (last_merged_start, max(last_merged_end, current_end))
                else:
                    merged_busy_slots.append((current_start, current_end))

    # Check for a free slot before the first busy period
    search_pointer = search_start_time
    first_busy_start = merged_busy_slots[0][0] if merged_busy_slots else None
    
    # Check if we can fit before first meeting and within working hours
    if not first_busy_start or search_pointer + meeting_duration <= first_busy_start:
        candidate_start = search_pointer
        candidate_end = candidate_start + meeting_duration
        
        # Check working hours constraint
        if candidate_end.hour <= latest_end_hour:
            preference_score = calculate_preference_score(candidate_start, candidate_end, attendees, calendars)
            if preference_score <= max_preference_score:
                return ((candidate_start, candidate_end), [])
            else:
                print(f"  Slot {candidate_start.strftime('%H:%M')}-{candidate_end.strftime('%H:%M')} rejected due to preference violations (score: {preference_score})")

    # Check for free slots between busy periods
    for i, (_, busy_end) in enumerate(merged_busy_slots):
        if search_pointer < busy_end:
            search_pointer = busy_end
        
        gap_start = search_pointer
        next_busy_start = merged_busy_slots[i + 1][0] if i + 1 < len(merged_busy_slots) else None
        
        # Check if we can fit a meeting in this gap and within working hours
        if gap_start + meeting_duration <= (next_busy_start or gap_start + meeting_duration + datetime.timedelta(hours=1)):
            candidate_start = gap_start
            candidate_end = candidate_start + meeting_duration
            
            # Check working hours constraint
            if candidate_start.hour >= earliest_start_hour and candidate_end.hour <= latest_end_hour:
                preference_score = calculate_preference_score(candidate_start, candidate_end, attendees, calendars)
                if preference_score <= max_preference_score:
                    return ((candidate_start, candidate_end), [])
                else:
                    print(f"  Slot {candidate_start.strftime('%H:%M')}-{candidate_end.strftime('%H:%M')} rejected due to preference violations (score: {preference_score})")

    # 3. Second pass: If no free slot, find a reschedulable slot.
    print("  No free slots with acceptable preferences found. Checking reschedulable slots...")
    
    for start, end, priority, summary in all_busy_slots:
        # The potential slot starts when the existing meeting starts.
        potential_start = max(start, search_start_time)
        potential_end = potential_start + meeting_duration

        # Check working hours constraint for potential slot
        if potential_start.hour < earliest_start_hour or potential_end.hour > latest_end_hour:
            continue

        # Find all events that conflict with this potential new meeting time.
        conflicting_events = [
            event for event in all_busy_slots 
            if event[0] < potential_end and potential_start < event[1]
        ]

        # Check if all conflicting events have a lower priority (higher number = lower priority).
        can_reschedule = all(
            new_meeting_priority < conf_priority 
            for _, _, conf_priority, _ in conflicting_events
        )

        if can_reschedule:
            # Check preference score for this rescheduled slot
            preference_score = calculate_preference_score(potential_start, potential_end, attendees, calendars)
            if preference_score <= max_preference_score:
                return ((potential_start, potential_end), conflicting_events)
            else:
                print(f"  Reschedulable slot {potential_start.strftime('%H:%M')}-{potential_end.strftime('%H:%M')} rejected due to preference violations (score: {preference_score})")

    return None # No free or reschedulable slot found.


def schedule_meeting_from_request(user_calendars, meeting_request, recurrence_details=None):
    """
    High-level function to handle scheduling based on a specific request format.
    Includes fallback strategies for when initial scheduling fails.
    
    Args:
        user_calendars (dict): Calendar data for all users
        meeting_request (dict): Meeting request details  
        recurrence_details (dict, optional): Recurrence information for rescheduling
    
    Returns:
        dict: Scheduling result with enhanced metadata
    """
    print(f"--- Received new meeting request: '{meeting_request.get('Subject', 'No Subject')}' ---")
    
    # Validate input parameters
    if not user_calendars:
        print("Error: No user calendars provided.")
        return None
    
    if not meeting_request:
        print("Error: No meeting request provided.")
        return None
    
    try:
        # Parse duration
        duration_str = meeting_request.get("Duration of meeting", "")
        if not duration_str:
            print("Error: Meeting duration not specified.")
            return None
            
        duration_match = re.match(r'\d+', duration_str)
        if not duration_match:
            print(f"Error: Invalid duration format '{duration_str}'. Expected format: '60 min' or '120 minutes'.")
            return None
            
        duration_minutes = int(duration_match.group())
        if duration_minutes <= 0:
            print(f"Error: Invalid duration {duration_minutes} minutes. Must be positive.")
            return None
        
        # Parse start time
        start_time_str = meeting_request.get("start time ", "")
        if not start_time_str:
            print("Error: Start time not specified.")
            return None
            
        tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        try:
            desired_start_time = datetime.datetime.strptime(start_time_str, "%d-%m-%YT%H:%M:%S").replace(tzinfo=tz)
        except ValueError as e:
            print(f"Error: Invalid start time format '{start_time_str}'. Expected format: 'DD-MM-YYYYTHH:MM:SS'. Details: {e}")
            return None

        # Validate priority
        new_meeting_priority = meeting_request.get("Priority", 1)
        if not isinstance(new_meeting_priority, int) or new_meeting_priority < 1 or new_meeting_priority > 4:
            print(f"Error: Invalid priority {new_meeting_priority}. Must be an integer between 1 (highest) and 4 (lowest).")
            return None
            
        # Get attendees from calendar keys
        attendees = list(user_calendars.keys())
        if not attendees:
            print("Error: No attendees found in user calendars.")
            return None
        
        print(f"Attempting to book for: {', '.join(attendees)}")
        print(f"Required duration: {duration_minutes} minutes, Priority: P{new_meeting_priority}")
        print(f"Searching from: {desired_start_time.strftime('%Y-%m-%d %H:%M %Z')}")

    except (KeyError, ValueError, AttributeError) as e:
        print(f"Error: Could not parse meeting request. Invalid format. Details: {e}")
        return None

    # Parse calendar data with error handling
    try:
        all_raw_events = [event for user_events in user_calendars.values() for event in user_events if event]
        parsed_calendars = parse_calendar_data(all_raw_events)
        
        if not parsed_calendars:
            print("Warning: No valid calendar events found. Proceeding with empty calendars.")
            parsed_calendars = {attendee: [] for attendee in attendees}
    except Exception as e:
        print(f"Error: Failed to parse calendar data. Details: {e}")
        return None

    # Try primary scheduling approach
    try:
        result = find_earliest_slot(parsed_calendars, attendees, duration_minutes, new_meeting_priority, 
                                  search_start_time=desired_start_time, recurrence_details=recurrence_details)
        
        if result:
            return _handle_successful_booking(result, meeting_request, new_meeting_priority, parsed_calendars, recurrence_details)
        
        # If primary approach fails, try fallback strategies
        print("\n=== ATTEMPTING FALLBACK STRATEGIES ===")
        
        # Fallback 1: Try shorter duration (75% of original)
        shorter_duration = int(duration_minutes * 0.75)
        if shorter_duration >= 15:  # Minimum 15 minutes
            print(f"\nFallback 1: Trying shorter duration ({shorter_duration} minutes instead of {duration_minutes})")
            result = find_earliest_slot(parsed_calendars, attendees, shorter_duration, new_meeting_priority, 
                                      search_start_time=desired_start_time, recurrence_details=recurrence_details)
            
            if result:
                print(f"SUCCESS: Found slot with shorter duration ({shorter_duration} minutes)")
                return _handle_successful_booking(result, meeting_request, new_meeting_priority, parsed_calendars, 
                                                recurrence_details, fallback_used="shorter_duration")
        
        # Fallback 2: Try with majority attendees (if more than 2 attendees)
        if len(attendees) > 2:
            majority_attendees = attendees[:len(attendees)//2 + 1]  # Take majority
            print(f"\nFallback 2: Trying with majority attendees ({', '.join(majority_attendees)} out of {', '.join(attendees)})")
            
            result = find_earliest_slot(parsed_calendars, majority_attendees, duration_minutes, new_meeting_priority, 
                                      search_start_time=desired_start_time, recurrence_details=recurrence_details)
            
            if result:
                print(f"SUCCESS: Found slot with majority attendees")
                return _handle_successful_booking(result, meeting_request, new_meeting_priority, parsed_calendars,
                                                recurrence_details, fallback_used="majority_attendees", original_attendees=attendees)
        
        # Fallback 3: Try shifting time windows (±30 minutes, ±60 minutes)
        for shift_minutes in [30, -30, 60, -60]:
            shifted_start = desired_start_time + datetime.timedelta(minutes=shift_minutes)
            print(f"\nFallback 3: Trying shifted time window ({shift_minutes:+d} minutes -> {shifted_start.strftime('%H:%M')})")
            
            result = find_earliest_slot(parsed_calendars, attendees, duration_minutes, new_meeting_priority, 
                                      search_start_time=shifted_start, recurrence_details=recurrence_details)
            
            if result:
                print(f"SUCCESS: Found slot with shifted time window ({shift_minutes:+d} minutes)")
                return _handle_successful_booking(result, meeting_request, new_meeting_priority, parsed_calendars,
                                                recurrence_details, fallback_used="time_shift", shift_minutes=shift_minutes)
        
        # Fallback 4: Relax preference constraints (higher tolerance for violations)
        print(f"\nFallback 4: Relaxing preference constraints (allowing higher violation scores)")
        result = find_earliest_slot(parsed_calendars, attendees, duration_minutes, new_meeting_priority, 
                                  search_start_time=desired_start_time, max_preference_score=200, 
                                  recurrence_details=recurrence_details)
        
        if result:
            print(f"SUCCESS: Found slot with relaxed preference constraints")
            return _handle_successful_booking(result, meeting_request, new_meeting_priority, parsed_calendars,
                                            recurrence_details, fallback_used="relaxed_preferences")
        
        print("\n=== ALL FALLBACK STRATEGIES FAILED ===")
        
    except Exception as e:
        print(f"Error: Failed to find available slot. Details: {e}")
        return None

    print("\nFailure: No available slot could be found, even with fallback strategies.")
    return {
        'success': False,
        'error': 'No available slot found after trying all fallback strategies',
        'fallbacks_attempted': ['shorter_duration', 'majority_attendees', 'time_shift', 'relaxed_preferences']
    }


def _handle_successful_booking(result, meeting_request, new_meeting_priority, calendars=None, recurrence_details=None, fallback_used=None, **fallback_details):
    """
    Helper function to handle successful booking results.
    """
    slot, to_reschedule = result
    
    print(f"\nSuccess! Earliest slot found for '{meeting_request['Subject']}':")
    print(f"  Start: {slot[0].strftime('%Y-%m-%d %H:%M %Z%z')}")
    print(f"  End:   {slot[1].strftime('%Y-%m-%d %H:%M %Z%z')}")
    
    if fallback_used:
        print(f"  Note: Used fallback strategy '{fallback_used}'")
        if fallback_details:
            for key, value in fallback_details.items():
                print(f"    {key}: {value}")
    
    if to_reschedule:
        # Call requirewna function to handle rescheduling
        meeting_info = {
            'subject': meeting_request.get('Subject', 'Unknown'),
            'start_time': slot[0],
            'end_time': slot[1],
            'priority': new_meeting_priority
        }
        
        try:
            rescheduling_result = requirewna(to_reschedule, meeting_info)
            print(f"\nNOTE: This time requires {len(to_reschedule)} lower-priority meeting(s) to be rescheduled:")
            for _, _, p, s in to_reschedule:
                print(f"  - (P{p}) '{s}'")
            
            # If recurrence details are provided, generate reschedule suggestions
            if recurrence_details and calendars:
                reschedule_suggestions = reschedule_with_recurrence(calendars, to_reschedule, recurrence_details)
                rescheduling_result['recurrence_reschedule_suggestions'] = reschedule_suggestions
            
            return {
                'success': True,
                'slot': slot,
                'rescheduling_required': True,
                'rescheduling_result': rescheduling_result,
                'fallback_used': fallback_used,
                'fallback_details': fallback_details,
                'recurrence_details': recurrence_details
            }
        except Exception as e:
            print(f"Warning: Rescheduling notification failed. Details: {e}")
            return {
                'success': True,
                'slot': slot,
                'rescheduling_required': True,
                'rescheduling_result': None,
                'fallback_used': fallback_used,
                'fallback_details': fallback_details,
                'recurrence_details': recurrence_details
            }
    else:
        print("\nThis is a free slot, no rescheduling needed.")
        return {
            'success': True,
            'slot': slot,
            'rescheduling_required': False,
            'fallback_used': fallback_used,
            'fallback_details': fallback_details,
            'recurrence_details': recurrence_details
        }


def schedule_meeting_with_json_output(input_request, user_calendars=None, recurrence_details=None):
    """
    Main entry function that accepts the new JSON input format and returns the required JSON output.
    
    Args:
        input_request (dict): Input request in the format from JSON_Samples/Input_Request.json
        user_calendars (dict, optional): User calendar data. If None, will use sample data.
        recurrence_details (dict, optional): Recurrence information for rescheduling
    
    Returns:
        dict: JSON output in the required format
    """
    
    # Convert input format to the format expected by schedule_meeting_from_request
    try:
        # Extract duration from EmailContent using basic parsing
        email_content = input_request.get('EmailContent', '')
        duration_minutes = 60  # Default duration
        
        # Simple duration extraction from email content
        import re
        duration_match = re.search(r'(\d+)\s*minutes?', email_content, re.IGNORECASE)
        if duration_match:
            duration_minutes = int(duration_match.group(1))
        
        # Convert to internal meeting request format
        meeting_request = {
            "start time ": input_request.get('Datetime', ''),
            "Duration of meeting": f"{duration_minutes} min",
            "Subject": input_request.get('Subject', ''),
            "EmailContent": input_request.get('EmailContent', ''),
            "Priority": 3  # Default priority, could be derived from Subject keywords
        }
        
        # Use provided user_calendars or create sample data
        if user_calendars is None:
            # Create sample user calendars from attendees
            attendee_emails = [input_request.get('From', '')] + [att.get('email', '') for att in input_request.get('Attendees', [])]
            user_calendars = {email: [] for email in attendee_emails if email}
        
        # Call the existing scheduling function
        result = schedule_meeting_from_request(user_calendars, meeting_request, recurrence_details)
        
        # Format output using the new formatter
        return format_scheduling_output(result, input_request, recurrence_details)
        
    except Exception as e:
        print(f"Error in schedule_meeting_with_json_output: {e}")
        return {
            "Subject": input_request.get('Subject', ''),
            "EmailContent": input_request.get('EmailContent', ''),
            "EventStart": None,
            "EventEnd": None,
            "Duration_mins": None,
            "MetaData": {
                "success": False,
                "error": str(e),
                "recurrence_details": recurrence_details or {}
            }
        }


# --- Example Usage ---
if __name__ == "__main__":
    # Note: Priorities are now included or will be inferred.
    # P2 for 'Client Call', P3 for 'Design Review', P4 for others.
    USER_CALENDARS_INPUT = {
        "user1": [
            {'StartTime': '2025-07-19T09:00:00+05:30', 'EndTime': '2025-07-19T11:00:00+05:30', 'Attendees': ['user1'], 'Summary': 'Morning Standup'}, # Will get P4
            {'StartTime': '2025-07-19T14:00:00+05:30', 'EndTime': '2025-07-19T15:30:00+05:30', 'Attendees': ['user1'], 'Summary': 'Design Review'} # Will get P3
        ],
        "user2": [
            {'StartTime': '2025-07-19T10:30:00+05:30', 'EndTime': '2025-07-19T11:30:00+05:30', 'Attendees': ['user2'], 'Summary': 'Client Call'} # Will get P2
        ],
        "user3": []
    }

    # This is a high-priority request (P1) that conflicts with the P4 and P2 meetings.
    # The algorithm should find the slot at 10:30, suggesting the P2 Client Call be moved.
    MEETING_REQUEST_INPUT = {
        "start time ": "19-07-2025T09:00:00",
        "Duration of meeting": "180 min",
        "Subject": "CRITICAL: Production Outage Debrief",
        "EmailContent": "Hi team, we must meet to discuss the production outage.",
        "Priority": 1 # Highest priority
    }
    
    print("\n" + "="*50 + "\n")
    result = schedule_meeting_from_request(USER_CALENDARS_INPUT, MEETING_REQUEST_INPUT)
    print("\n" + "="*50 + "\n")
    
    # Test the new JSON format functionality
    print("\n" + "="*50 + " NEW JSON FORMAT TEST " + "="*50 + "\n")
    
    # Test with sample input from JSON_Samples
    SAMPLE_JSON_INPUT = {
        "Request_id": "6118b54f-907b-4451-8d48-dd13d76033a5",
        "Datetime": "19-07-2025T12:34:55",
        "Location": "IISc Bangalore",
        "From": "userone.amd@gmail.com",
        "Attendees": [
            {"email": "usertwo.amd@gmail.com"},
            {"email": "userthree.amd@gmail.com"}
        ],
        "Subject": "Agentic AI Project Status Update",
        "EmailContent": "Hi team, let's meet on Thursday for 30 minutes to discuss the status of Agentic AI Project."
    }
    
    # Test with recurrence details
    RECURRENCE_DETAILS = {
        "pattern": "weekly",
        "frequency": 1,
        "end_date": "2025-12-31T23:59:59+05:30"
    }
    
    json_result = schedule_meeting_with_json_output(SAMPLE_JSON_INPUT, recurrence_details=RECURRENCE_DETAILS)
    
    import json
    print("JSON Output:")
    print(json.dumps(json_result, indent=2))
    
    print("\n" + "="*50 + " END JSON FORMAT TEST " + "="*50 + "\n")
