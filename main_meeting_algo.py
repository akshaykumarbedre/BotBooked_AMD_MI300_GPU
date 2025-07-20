import datetime
import collections
import re
import json

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

def format_meeting_to_json(subject, email_content, start_time, end_time, duration_mins, metadata=None):
    """
    Format meeting information into the required JSON format.
    
    Args:
        subject (str): Meeting subject
        email_content (str): Email content for the meeting
        start_time (datetime): Meeting start time
        end_time (datetime): Meeting end time
        duration_mins (int): Duration in minutes
        metadata (dict): Additional metadata (optional)
    
    Returns:
        dict: Meeting information in required JSON format
    """
    if metadata is None:
        metadata = {}
    
    return {
        "Subject": subject,
        "EmailContent": email_content,
        "EventStart": start_time.isoformat(),
        "EventEnd": end_time.isoformat(),
        "Duration_mins": str(duration_mins),
        "MetaData": metadata
    }


def requirewna(meetings_to_reschedule, new_meeting_info, all_calendars=None):
    """
    Handle necessary actions during rescheduling.
    This function processes meetings that need to be rescheduled and
    actually finds new time slots for them using the same scheduling logic.
    
    Args:
        meetings_to_reschedule (list): List of meeting tuples (start, end, priority, summary)
        new_meeting_info (dict): Information about the new meeting being scheduled
        all_calendars (dict): Current calendar data to find rescheduling slots
    
    Returns:
        dict: Result of rescheduling actions with new time slots
    """
    print("\n--- RESCHEDULING REQUIRED ---")
    print(f"New meeting '{new_meeting_info.get('subject', 'Unknown')}' requires rescheduling of:")
    
    rescheduled_meetings = []
    failed_reschedules = []
    
    for start, end, priority, summary in meetings_to_reschedule:
        print(f"  - (P{priority}) '{summary}' scheduled from {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}")
        
        # Calculate duration for rescheduling
        duration_mins = int((end - start).total_seconds() / 60)
        
        # Try to find a new slot for this meeting
        # Start searching from the end of the new meeting
        search_start = new_meeting_info.get('end_time', start)
        
        # Use all_calendars if provided, otherwise create a simplified calendar structure
        if all_calendars:
            # Remove the current meeting from calendars to avoid conflicts during rescheduling
            temp_calendars = {}
            for user_id, events in all_calendars.items():
                temp_calendars[user_id] = [
                    event for event in events 
                    if not (event[0] == start and event[1] == end and event[3] == summary)
                ]
            
            # Add the new meeting to the calendars
            new_start = new_meeting_info.get('start_time')
            new_end = new_meeting_info.get('end_time')
            new_priority = new_meeting_info.get('priority', 1)
            new_subject = new_meeting_info.get('subject', 'New Meeting')
            
            if new_start and new_end:
                for user_id in temp_calendars.keys():
                    temp_calendars[user_id].append((new_start, new_end, new_priority, new_subject))
            
            # Try to find a new slot for the displaced meeting
            # Assume all current attendees for simplicity (this could be enhanced with actual attendee tracking)
            attendees = list(temp_calendars.keys())
            
            try:
                result = find_earliest_slot(
                    temp_calendars, 
                    attendees, 
                    duration_mins, 
                    priority, 
                    search_start_time=search_start,
                    max_preference_score=150  # Be more lenient for rescheduled meetings
                )
                
                if result:
                    new_slot, further_reschedules = result
                    if not further_reschedules:  # Avoid cascading reschedules for simplicity
                        rescheduled_meetings.append({
                            'original_start': start,
                            'original_end': end,
                            'priority': priority,
                            'summary': summary,
                            'status': 'rescheduled',
                            'new_start': new_slot[0],
                            'new_end': new_slot[1],
                            'duration_mins': duration_mins
                        })
                        print(f"    ✓ Rescheduled to: {new_slot[0].strftime('%Y-%m-%d %H:%M')} - {new_slot[1].strftime('%Y-%m-%d %H:%M')}")
                    else:
                        failed_reschedules.append({
                            'original_start': start,
                            'original_end': end,
                            'priority': priority,
                            'summary': summary,
                            'status': 'failed_cascading_reschedule',
                            'reason': 'Would require further reschedules'
                        })
                        print(f"    ✗ Could not reschedule '{summary}' - would require cascading reschedules")
                else:
                    failed_reschedules.append({
                        'original_start': start,
                        'original_end': end,
                        'priority': priority,
                        'summary': summary,
                        'status': 'failed_no_slot',
                        'reason': 'No available slot found'
                    })
                    print(f"    ✗ Could not find new slot for '{summary}'")
                    
            except Exception as e:
                failed_reschedules.append({
                    'original_start': start,
                    'original_end': end,
                    'priority': priority,
                    'summary': summary,
                    'status': 'failed_error',
                    'reason': str(e)
                })
                print(f"    ✗ Error rescheduling '{summary}': {e}")
        else:
            # Fallback: Mark as needs manual rescheduling
            failed_reschedules.append({
                'original_start': start,
                'original_end': end,
                'priority': priority,
                'summary': summary,
                'status': 'needs_manual_rescheduling',
                'reason': 'No calendar data provided for automatic rescheduling'
            })
            print(f"    ⚠ Needs manual rescheduling: '{summary}' (no calendar data provided)")
    
    print("--- END RESCHEDULING NOTIFICATION ---\n")
    
    return {
        'action': 'reschedule_completed',
        'rescheduled_meetings': rescheduled_meetings,
        'failed_reschedules': failed_reschedules,
        'new_meeting': new_meeting_info
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

def find_earliest_slot(calendars, attendees, duration_minutes, new_meeting_priority, search_start_time=None, max_preference_score=100):
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


def schedule_meeting_from_request(user_calendars, meeting_request):
    """
    High-level function to handle scheduling based on a specific request format.
    Includes fallback strategies for when initial scheduling fails.
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
        result = find_earliest_slot(parsed_calendars, attendees, duration_minutes, new_meeting_priority, search_start_time=desired_start_time)
        
        if result:
            return _handle_successful_booking(result, meeting_request, new_meeting_priority, parsed_calendars)
        
        # If primary approach fails, try fallback strategies
        print("\n=== ATTEMPTING FALLBACK STRATEGIES ===")
        
        # Fallback 1: Try shorter duration (75% of original)
        shorter_duration = int(duration_minutes * 0.75)
        if shorter_duration >= 15:  # Minimum 15 minutes
            print(f"\nFallback 1: Trying shorter duration ({shorter_duration} minutes instead of {duration_minutes})")
            result = find_earliest_slot(parsed_calendars, attendees, shorter_duration, new_meeting_priority, search_start_time=desired_start_time)
            
            if result:
                print(f"SUCCESS: Found slot with shorter duration ({shorter_duration} minutes)")
                return _handle_successful_booking(result, meeting_request, new_meeting_priority, parsed_calendars, fallback_used="shorter_duration")
        
        # Fallback 2: Try with majority attendees (if more than 2 attendees)
        if len(attendees) > 2:
            majority_attendees = attendees[:len(attendees)//2 + 1]  # Take majority
            print(f"\nFallback 2: Trying with majority attendees ({', '.join(majority_attendees)} out of {', '.join(attendees)})")
            
            result = find_earliest_slot(parsed_calendars, majority_attendees, duration_minutes, new_meeting_priority, search_start_time=desired_start_time)
            
            if result:
                print(f"SUCCESS: Found slot with majority attendees")
                return _handle_successful_booking(result, meeting_request, new_meeting_priority, parsed_calendars, fallback_used="majority_attendees", original_attendees=attendees)
        
        # Fallback 3: Try shifting time windows (±30 minutes, ±60 minutes)
        for shift_minutes in [30, -30, 60, -60]:
            shifted_start = desired_start_time + datetime.timedelta(minutes=shift_minutes)
            print(f"\nFallback 3: Trying shifted time window ({shift_minutes:+d} minutes -> {shifted_start.strftime('%H:%M')})")
            
            result = find_earliest_slot(parsed_calendars, attendees, duration_minutes, new_meeting_priority, search_start_time=shifted_start)
            
            if result:
                print(f"SUCCESS: Found slot with shifted time window ({shift_minutes:+d} minutes)")
                return _handle_successful_booking(result, meeting_request, new_meeting_priority, parsed_calendars, fallback_used="time_shift", shift_minutes=shift_minutes)
        
        # Fallback 4: Relax preference constraints (higher tolerance for violations)
        print(f"\nFallback 4: Relaxing preference constraints (allowing higher violation scores)")
        result = find_earliest_slot(parsed_calendars, attendees, duration_minutes, new_meeting_priority, 
                                  search_start_time=desired_start_time, max_preference_score=200)
        
        if result:
            print(f"SUCCESS: Found slot with relaxed preference constraints")
            return _handle_successful_booking(result, meeting_request, new_meeting_priority, parsed_calendars, fallback_used="relaxed_preferences")
        
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


def _handle_successful_booking(result, meeting_request, new_meeting_priority, parsed_calendars=None, fallback_used=None, **fallback_details):
    """
    Helper function to handle successful booking results and generate JSON output.
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
    
    # Prepare the main meeting JSON
    duration_mins = int((slot[1] - slot[0]).total_seconds() / 60)
    main_meeting_json = format_meeting_to_json(
        subject=meeting_request.get('Subject', 'Unknown Meeting'),
        email_content=meeting_request.get('EmailContent', f"Meeting scheduled for {meeting_request.get('Subject', 'Unknown Meeting')}"),
        start_time=slot[0],
        end_time=slot[1],
        duration_mins=duration_mins,
        metadata={
            'priority': new_meeting_priority,
            'fallback_used': fallback_used,
            'rescheduling_required': bool(to_reschedule)
        }
    )
    
    meetings_json = [main_meeting_json]
    rescheduling_result = None
    
    if to_reschedule:
        # Call requirewna function to handle rescheduling with calendar data
        meeting_info = {
            'subject': meeting_request.get('Subject', 'Unknown'),
            'start_time': slot[0],
            'end_time': slot[1],
            'priority': new_meeting_priority
        }
        
        try:
            rescheduling_result = requirewna(to_reschedule, meeting_info, parsed_calendars)
            print(f"\nNOTE: This time requires {len(to_reschedule)} lower-priority meeting(s) to be rescheduled:")
            for _, _, p, s in to_reschedule:
                print(f"  - (P{p}) '{s}'")
            
            # Add rescheduled meetings to JSON output
            for rescheduled in rescheduling_result.get('rescheduled_meetings', []):
                if rescheduled['status'] == 'rescheduled':
                    rescheduled_json = format_meeting_to_json(
                        subject=rescheduled['summary'],
                        email_content=f"Rescheduled meeting: {rescheduled['summary']}",
                        start_time=rescheduled['new_start'],
                        end_time=rescheduled['new_end'],
                        duration_mins=rescheduled['duration_mins'],
                        metadata={
                            'priority': rescheduled['priority'],
                            'rescheduled': True,
                            'original_start': rescheduled['original_start'].isoformat(),
                            'original_end': rescheduled['original_end'].isoformat()
                        }
                    )
                    meetings_json.append(rescheduled_json)
            
            return {
                'success': True,
                'slot': slot,
                'rescheduling_required': True,
                'rescheduling_result': rescheduling_result,
                'fallback_used': fallback_used,
                'fallback_details': fallback_details,
                'meetings_json': meetings_json
            }
        except Exception as e:
            print(f"Warning: Rescheduling failed. Details: {e}")
            return {
                'success': True,
                'slot': slot,
                'rescheduling_required': True,
                'rescheduling_result': None,
                'fallback_used': fallback_used,
                'fallback_details': fallback_details,
                'meetings_json': meetings_json
            }
    else:
        print("\nThis is a free slot, no rescheduling needed.")
        return {
            'success': True,
            'slot': slot,
            'rescheduling_required': False,
            'fallback_used': fallback_used,
            'fallback_details': fallback_details,
            'meetings_json': meetings_json
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
    
    # Print JSON output if available
    if result and result.get('meetings_json'):
        print("\n" + "="*20 + " JSON OUTPUT " + "="*20)
        print(json.dumps(result['meetings_json'], indent=2))
        print("="*52)
    
    print("\n" + "="*50 + "\n")
