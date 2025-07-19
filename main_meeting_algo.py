import datetime
import collections
import re

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
    parsed_calendars = collections.defaultdict(list)
    
    # Define default priorities based on summary keywords
    priority_map = {
        'Client Call': 4,
        'Design Review': 4,
    }

    for event in raw_events:
        try:
            start_time = datetime.datetime.fromisoformat(event['StartTime'])
            end_time = datetime.datetime.fromisoformat(event['EndTime'])
            summary = event.get('Summary', 'No Title')
            
            # Determine priority: Use explicit priority if given, otherwise use map or default.
            priority = event.get('Priority')
            if priority is None:
                priority = next((p for keyword, p in priority_map.items() if keyword in summary), 4)

            for attendee in event['Attendees']:
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
    if search_start_time is None:
        search_start_time = datetime.datetime.now().astimezone()

    meeting_duration = datetime.timedelta(minutes=duration_minutes)
    
    # 1. Aggregate all busy slots from all attendees.
    all_busy_slots = []
    for user_id in attendees:
        if user_id in calendars:
            all_busy_slots.extend(calendars[user_id])
    
    # Sort by start time to allow chronological searching.
    all_busy_slots.sort(key=lambda x: x[0])

    # 2. First pass: Find a purely free slot (no conflicts).
    # This is the same logic as before, ignoring priority for now.
    merged_busy_slots = []
    if all_busy_slots:
        # We only care about the time intervals for this pass.
        time_intervals = [(s, e) for s, e, p, summ in all_busy_slots]
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
    
    try:
        duration_str = meeting_request["DUeing of meeting "]
        duration_minutes = int(re.match(r'\d+', duration_str).group())
        
        start_time_str = meeting_request["start time "]
        tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        desired_start_time = datetime.datetime.strptime(start_time_str, "%d-%m-%YT%H:%M:%S").replace(tzinfo=tz)

        # Priority of the new meeting. P1 (highest) if not specified.
        new_meeting_priority = meeting_request.get("Priority", 1)
        attendees = list(user_calendars.keys())
        
        print(f"Attempting to book for9: {', '.join(attendees)}")
        print(f"Required duration: {duration_minutes} minutes, Priority: P{new_meeting_priority}")
        print(f"Searching from: {desired_start_time.strftime('%Y-%m-%d %H:%M %Z')}")

    except (KeyError, ValueError, AttributeError) as e:
        print(f"Error: Could not parse meeting request. Invalid format. Details: {e}")
        return

    all_raw_events = [event for user_events in user_calendars.values() for event in user_events]
    parsed_calendars = parse_calendar_data(all_raw_events)

    result = find_earliest_slot(parsed_calendars, attendees, duration_minutes, new_meeting_priority, search_start_time=desired_start_time)

    if result:
        slot, to_reschedule = result
        print(f"\nSuccess! Earliest slot found for '{meeting_request['Subject']}':")
        print(f"  Start: {slot[0].strftime('%Y-%m-%d %H:%M %Z%z')}")
        print(f"  End:   {slot[1].strftime('%Y-%m-%d %H:%M %Z%z')}")
        
        if to_reschedule:
            print("\nNOTE: This time requires the following lower-priority meetings to be rescheduled:")
            for _, _, p, s in to_reschedule:
                print(f"  - (P{p}) '{s}'")
        else:
            print("\nThis is a free slot, no rescheduling needed.")
    else:
        print("\nFailure: No available slot could be found, even with rescheduling.")


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
        "DUeing of meeting ": "180 min",
        "Subject": "CRITICAL: Production Outage Debrief",
        "EmailContent": "Hi team, we must meet to discuss the production outage.",
        "Priority": 1 # Highest priority
    }
    
    print("\n" + "="*50 + "\n")
    schedule_meeting_from_request(USER_CALENDARS_INPUT, MEETING_REQUEST_INPUT)
    print("\n" + "="*50 + "\n")
