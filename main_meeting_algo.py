import datetime
import collections
import re

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

def find_earliest_slot(calendars, attendees, duration_minutes, new_meeting_priority, search_start_time=None):
    """
    Finds the earliest possible time slot, considering meeting priorities.

    It first searches for a completely empty slot. If none is found, it then
    looks for slots occupied by meetings of a lower priority that can be
    rescheduled.

    Args:
        calendars (dict): Parsed calendar data with priorities.
        attendees (list): List of user IDs for the meeting.
        duration_minutes (int): The required duration of the meeting.
        new_meeting_priority (int): The priority of the meeting to be scheduled.
        search_start_time (datetime.datetime, optional): The time to start searching from.

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
    
    # 1. Aggregate all busy slots from all attendees.
    all_busy_slots = []
    for user_id in attendees:
        if user_id in calendars:
            user_events = calendars[user_id]
            if isinstance(user_events, list):
                all_busy_slots.extend(user_events)
    
    # Sort by start time to allow chronological searching.
    all_busy_slots.sort(key=lambda x: x[0])

    # 2. First pass: Find a purely free slot (no conflicts).
    # This is the same logic as before, ignoring priority for now.
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
    if not first_busy_start or search_pointer + meeting_duration <= first_busy_start:
        return ((search_pointer, search_pointer + meeting_duration), [])

    # Check for free slots between busy periods
    for _, busy_end in merged_busy_slots:
        if search_pointer < busy_end:
            search_pointer = busy_end
        
        gap_start = search_pointer
        next_busy_start = next((s for s, e in merged_busy_slots if s >= gap_start), None)
        
        gap_end = next_busy_start if next_busy_start else search_pointer + meeting_duration * 2 # effectively infinite
        
        if gap_start + meeting_duration <= gap_end:
             return ((gap_start, gap_start + meeting_duration), [])

    # 3. Second pass: If no free slot, find a reschedulable slot.
    # We check every existing meeting as a potential start time for our new meeting.
    for start, end, priority, summary in all_busy_slots:
        # The potential slot starts when the existing meeting starts.
        potential_start = max(start, search_start_time)
        potential_end = potential_start + meeting_duration

        # Find all events that conflict with this potential new meeting time.
        conflicting_events = [
            event for event in all_busy_slots 
            if event[0] < potential_end and potential_start < event[1]
        ]

        # Check if all conflicting events have a lower priority.
        can_reschedule = all(
            new_meeting_priority < conf_priority 
            for _, _, conf_priority, _ in conflicting_events
        )

        if can_reschedule:
            # We found a slot where all conflicts are lower priority.
            return ((potential_start, potential_end), conflicting_events)

    return None # No free or reschedulable slot found.


def schedule_meeting_from_request(user_calendars, meeting_request):
    """
    High-level function to handle scheduling based on a specific request format.
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

    # Find suitable slot
    try:
        result = find_earliest_slot(parsed_calendars, attendees, duration_minutes, new_meeting_priority, search_start_time=desired_start_time)
    except Exception as e:
        print(f"Error: Failed to find available slot. Details: {e}")
        return None

    if result:
        slot, to_reschedule = result
        print(f"\nSuccess! Earliest slot found for '{meeting_request['Subject']}':")
        print(f"  Start: {slot[0].strftime('%Y-%m-%d %H:%M %Z%z')}")
        print(f"  End:   {slot[1].strftime('%Y-%m-%d %H:%M %Z%z')}")
        
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
                
                return {
                    'success': True,
                    'slot': slot,
                    'rescheduling_required': True,
                    'rescheduling_result': rescheduling_result
                }
            except Exception as e:
                print(f"Warning: Rescheduling notification failed. Details: {e}")
                return {
                    'success': True,
                    'slot': slot,
                    'rescheduling_required': True,
                    'rescheduling_result': None
                }
        else:
            print("\nThis is a free slot, no rescheduling needed.")
            return {
                'success': True,
                'slot': slot,
                'rescheduling_required': False
            }
    else:
        print("\nFailure: No available slot could be found, even with rescheduling.")
        return {
            'success': False,
            'error': 'No available slot found'
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
    schedule_meeting_from_request(USER_CALENDARS_INPUT, MEETING_REQUEST_INPUT)
    print("\n" + "="*50 + "\n")
