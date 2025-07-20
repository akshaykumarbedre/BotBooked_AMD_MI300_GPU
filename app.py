
"""
Intelligent meeting scheduling assistant.

This script leverages a Large Language Model (LLM) to extract meeting details 
from natural language, interacts with Google Calendar for availability, and uses a 
sophisticated scheduling algorithm to find optimal meeting times. The algorithm 
considers user preferences, meeting priorities, and can automatically reschedule 
lower-priority events. The workflow is orchestrated using LangGraph.
"""

# ==============================================================================
# 1. IMPORTS
# ==============================================================================

# Standard library imports
import collections
import datetime
import json
import os
from typing import Dict, List, Any, Tuple

# Third-party imports
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

# ==============================================================================
# 2. CONFIGURATION & CONSTANTS
# ==============================================================================

# NOTE: In a production environment, this configuration should be loaded from a 
# secure source like a config file or environment variables, not hardcoded.

# Default user preferences for scheduling constraints.
PARTICIPANT_PREFERENCES = {
    "user1": {
        "preferred_hours": {"start": 9, "end": 17},  # 9 AM to 5 PM
        "max_meetings_per_day": 6,
        "avoid_back_to_back": True,
        "buffer_minutes": 15
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

# Default timezone for operations (India Standard Time).
IST_TZ = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


# ==============================================================================
# 3. GOOGLE CALENDAR INTEGRATION
# ==============================================================================

def retrieve_calendar_events(user: str, start_iso: str, end_iso: str) -> List[Dict[str, Any]]:
    """
    Retrieves a list of calendar events for a given user within a time range.

    Args:
        user: The user's email address.
        start_iso: The start of the time range in ISO 8601 format.
        end_iso: The end of the time range in ISO 8601 format.

    Returns:
        A list of event dictionaries, each containing details of a single event.
    """
    events_list = []
    # NOTE: Token management should be robust. This path is for demonstration.
    token_path = f"Keys/{user.split('@')[0]}.token"
    if not os.path.exists(token_path):
        return []  # Return empty list if token file does not exist.

    user_creds = Credentials.from_authorized_user_file(token_path)
    calendar_service = build("calendar", "v3", credentials=user_creds)

    events_result = calendar_service.events().list(
        calendarId='primary',
        timeMin=start_iso,
        timeMax=end_iso,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])

    for event in events:
        attendees = [attendee['email'] for attendee in event.get("attendees", []) if 'email' in attendee]
        if not attendees:
            attendees.append("SELF")  # Default if no attendees are listed.

        try:
            events_list.append({
                "StartTime": event["start"]["dateTime"],
                "EndTime": event["end"]["dateTime"],
                "NumAttendees": len(set(attendees)),
                "Attendees": list(set(attendees)),
                "Summary": event.get("summary", "No Title")
            })
        except KeyError:
            # Skip all-day events or events missing start/end dateTime.
            continue
            
    return events_list


# ==============================================================================
# 4. LLM-BASED DETAIL EXTRACTION
# ==============================================================================

def extract_meeting_details_with_llm(email_content: str, request_datetime_str: str) -> Tuple[Dict[str, Any], str]:
    """
    Uses an LLM to extract structured meeting details from an email body.

    Args:
        email_content: The raw text content of the email.
        request_datetime_str: The timestamp of the request ('dd-mm-YYYYTHH:MM:SS').

    Returns:
        A tuple containing:
        - A dictionary with the extracted details (dates, duration, priority).
        - The summary of the meeting.
    """
    reference_datetime = datetime.datetime.strptime(request_datetime_str, "%d-%m-%YT%H:%M:%S")
    day = reference_datetime.strftime('%A')

    # The system prompt provides instructions and few-shot examples to the LLM.
    system_prompt = """
    You are an expert meeting information extraction assistant. Your task is to analyze email content and extract meeting details with precise date and time information.

    ## Core Instructions
    1.  **Extract, don't schedule**: Your role is to extract meeting information from the provided text, not to suggest or schedule meetings.
    2.  **Date/Time Resolution**: Use the provided reference datetime to resolve relative expressions like "tomorrow", "next week", or specific days of the week.
    3.  **Time Defaults**: 
        - When no specific start time is mentioned, use 00:00:00 (start of day)
        - When no specific end time is mentioned, use 23:59:59 (end of day) not its **not the duration.**
        - For same-day/week/month meetings without specific time (e.g., "this week"), use current time as start
    4.  **Duration Calculation**:
        - If both start/end times and duration are specified, prioritize the time range for dates
        - Calculate duration from the actual start/end time difference
        - If only duration is given, calculate end time from start time + duration
    5.  **Future Dates Only**: All extracted dates must be in the future relative to the current datetime.
    6.  **Priority Calculator**: Calculate the priority of the mail in the range of 1 to 4 where 1 is atmost priority and 4 is least priority.
    7.  **Summary Header**: Give me a short summary of the current email. 

    ## Output Format
    Return ONLY a valid JSON object with exactly these three keys:
    {{
        "chain_of_thought": "Your detailed reasoning for identifying dates, times, and duration calculations",
        "start_date": "Start datetime in 'dd-mm-YYYYTHH:MM:SS' format or null if not determinable",
        "end_date": "End datetime in 'dd-mm-YYYYTHH:MM:SS' format or null if not determinable", 
        "duration_minutes": "Total meeting duration in minutes (integer) or null if not determinable",
        "priority": "An integer in the range of 1 to 4",
        "summary": "A short high level meeting description for the email"
    }}

    ## Examples
    ### Example 1: Basic relative date with duration
    **Current Datetime:** 19-07-2025T14:30:00, **Current Day:** Friday
    **Email:** "Let's schedule our project review meeting tomorrow for 1 hour."
    Output:
    {{ "chain_of_thought": "...", "start_date": "20-07-2025T00:00:00", "end_date": "20-07-2025T23:59:59", "duration_minutes": 60, "priority": 3, "summary": "Project Review meeting" }}

    ### Example 2: Conflicting duration and time range
    **Current Datetime:** 02-12-2025T16:45:30, **Current Day:** Tuesday
    **Email:** "Board meeting next friday between 2-5 PM for half an hour discussion."
    Output:
    {{ "chain_of_thought": "...", "start_date": "12-12-2025T14:00:00", "end_date": "12-12-2025T17:00:00", "duration_minutes": 30, "priority": 2, "summary": "Board Meeting" }}
    """
    human_message = """
    ## Processing Instructions
    **Current Datetime:** {request_datetime_str}
    **Current Day:** {day}
    **Email:** "{email_content}"

    Analyze the email content using the current datetime as reference and return only the JSON output.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_message)
    ])
    
    # NOTE: API key and base URL should be in environment variables.
    model = ChatOpenAI(
        model="Qwen/Qwen3-4B",
        temperature=0,
        api_key="abc-123",  # Placeholder
        base_url="http://localhost:8000/v1/"
    )

    chain = prompt | model
    try:
        response = chain.invoke({
            "request_datetime_str": request_datetime_str,
            "day": day,
            "email_content": email_content
        })

        output_parser = JsonOutputParser()
        # NOTE: This parsing logic is brittle and depends on a specific model's output format.
        # A more robust solution would be to use a model that supports function calling or JSON mode.
        json_string = response.content.split('</think>')[-1]
        final_response = output_parser.invoke(json_string)

        # Default to a 60-minute duration if not specified.
        if final_response.get('duration_minutes') is None:
            final_response['duration_minutes'] = 60
            
        return final_response, final_response.get('summary', 'Meeting')

    except (json.JSONDecodeError, AttributeError, KeyError, ValueError):
        # Fallback response if LLM fails or output is malformed.
        return {
            'chain_of_thought': "Fallback due to processing error.",
            'start_date': reference_datetime.strftime("%d-%m-%YT%H:%M:%S"),
            'end_date': (reference_datetime.replace(hour=23, minute=59, second=59)).strftime("%d-%m-%YT%H:%M:%S"),
            'duration_minutes': 30,
            "priority": 4,
            "summary": "Sync Up"
        }, "Sync Up"

# ==============================================================================
# 5. CORE SCHEDULING LOGIC
# ==============================================================================

def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """
    Retrieves scheduling preferences for a user, returning defaults if not found.
    """
    default_preferences = {
        "preferred_hours": {"start": 9, "end": 17},
        "max_meetings_per_day": 5,
        "avoid_back_to_back": True,
        "buffer_minutes": 15
    }
    return PARTICIPANT_PREFERENCES.get(user_id, default_preferences)

def calculate_preference_score(start_time: datetime.datetime, end_time: datetime.datetime, attendees: List[str], calendars: Dict) -> int:
    """
    Calculates a preference violation score for a time slot. Lower is better.
    A score of 0 indicates a perfect slot with no preference violations.
    """
    score = 0
    for user_id in attendees:
        preferences = get_user_preferences(user_id)
        user_events = calendars.get(user_id, [])
        
        # Penalty for being outside preferred working hours.
        if (start_time.hour < preferences["preferred_hours"]["start"] or 
            end_time.hour > preferences["preferred_hours"]["end"]):
            score += 50
        
        # Penalty for exceeding the max number of meetings per day.
        meetings_on_day = [e for e in user_events if e[0].date() == start_time.date()]
        if len(meetings_on_day) >= preferences["max_meetings_per_day"]:
            score += 30
            
        # Penalty for back-to-back meetings if not preferred.
        if preferences["avoid_back_to_back"]:
            buffer = datetime.timedelta(minutes=preferences["buffer_minutes"])
            for event_start, event_end, _, _ in user_events:
                if (abs((event_end - start_time)) < buffer or 
                    abs((end_time - event_start)) < buffer):
                    score += 20
                    break
    return score

def format_meeting_as_json(subject: str, start_time: datetime.datetime, end_time: datetime.datetime, **kwargs) -> Dict[str, Any]:
    """Formats a meeting into a standardized JSON structure."""
    duration_mins = int((end_time - start_time).total_seconds() / 60)
    return {
        "Subject": subject,
        "EmailContent": kwargs.get("email_content", ""),
        "EventStart": start_time.isoformat(),
        "EventEnd": end_time.isoformat(),
        "Duration_mins": str(duration_mins),
        "MetaData": kwargs.get("metadata", {})
    }

def reschedule_meetings_recursively(meetings_to_move: List[Tuple], calendars: Dict, attendees_map: Dict, search_start: datetime.datetime) -> List[Dict]:
    """
    Recursively finds new slots for meetings that need to be rescheduled.
    """
    rescheduled = []
    for original_start, original_end, priority, summary in meetings_to_move:
        duration = int((original_end - original_start).total_seconds() / 60)
        attendees = attendees_map.get(summary, list(calendars.keys()))
        
        # Attempt to find a new slot with more lenient preference constraints.
        result = find_earliest_slot(
            calendars, attendees, duration, priority, 
            search_start_time=search_start, max_preference_score=150
        )
        
        if result:
            (new_start, new_end), conflicts = result
            # Update calendars with the newly rescheduled meeting.
            for user in attendees:
                if user in calendars:
                    calendars[user].append((new_start, new_end, priority, summary))
            
            rescheduled_meeting = format_meeting_as_json(
                summary, new_start, new_end,
                metadata={"rescheduled": True, "original_start": original_start.isoformat()}
            )
            rescheduled.append(rescheduled_meeting)
            
            # If this rescheduling causes further conflicts, resolve them.
            if conflicts:
                rescheduled.extend(reschedule_meetings_recursively(conflicts, calendars, attendees_map, new_end))
        else:
            # If no alternative slot is found, flag for manual intervention.
            failed_meeting = format_meeting_as_json(
                f"[NEEDS MANUAL RESCHEDULING] {summary}", original_start, original_end,
                metadata={"rescheduled": False, "needs_manual_intervention": True}
            )
            rescheduled.append(failed_meeting)
            
    return rescheduled

def handle_rescheduling(meetings_to_reschedule: List, new_meeting_info: Dict, calendars: Dict, attendees_map: Dict) -> Dict:
    """
    Manages the process of rescheduling meetings displaced by a new, higher-priority one.
    """
    # Create a copy of calendars to simulate the rescheduling.
    updated_calendars = {user: events.copy() for user, events in calendars.items()}
    
    # Remove the conflicting meetings that will be moved.
    conflicting_ids = {(s, e, summ) for s, e, _, summ in meetings_to_reschedule}
    for user, events in updated_calendars.items():
        updated_calendars[user] = [e for e in events if (e[0], e[1], e[3]) not in conflicting_ids]
    
    # Add the new high-priority meeting to the calendar.
    new_start = new_meeting_info['start_time']
    new_end = new_meeting_info['end_time']
    for user in updated_calendars.keys():
        updated_calendars[user].append((
            new_start, new_end, 
            new_meeting_info['priority'], 
            new_meeting_info['subject']
        ))
    
    rescheduled_meetings = reschedule_meetings_recursively(
        meetings_to_reschedule, updated_calendars, attendees_map, new_end
    )
    
    return {
        'action': 'reschedule_required',
        'meetings_to_reschedule': rescheduled_meetings,
        'new_meeting': new_meeting_info,
        'rescheduling_successful': True
    }

def parse_calendar_data(raw_events: List[Dict]) -> Dict[str, List[Tuple]]:
    """
    Parses raw event data into a structured format for the scheduling algorithm.
    Assigns default priorities to events based on keywords if not specified.
    """
    if not raw_events:
        return {}
        
    parsed_calendars = collections.defaultdict(list)
    priority_map = {'Client Call': 2, 'Design Review': 3}

    for event in raw_events:
        try:
            start = datetime.datetime.fromisoformat(event['StartTime'])
            end = datetime.datetime.fromisoformat(event['EndTime'])
            if start >= end: continue

            summary = event.get('Summary', 'No Title')
            priority = event.get('Priority')
            if priority is None:
                priority = next((p for kw, p in priority_map.items() if kw in summary), 4)

            for attendee in event['Attendees']:
                if isinstance(attendee, str):
                    parsed_calendars[attendee].append((start, end, priority, summary))

        except (KeyError, TypeError, ValueError):
            continue  # Skip events with malformed data.
            
    return dict(parsed_calendars)

def find_earliest_slot(calendars: Dict, attendees: List[str], duration_minutes: int, new_meeting_priority: int, **kwargs) -> Tuple[Tuple, List] | None:
    """
    Finds the earliest available slot, considering priorities and preferences.
    First, it looks for a completely free slot. If none exists, it checks for
    slots occupied by lower-priority meetings that can be rescheduled.
    """
    search_start_time = kwargs.get('search_start_time', datetime.datetime.now().astimezone())
    max_pref_score = kwargs.get('max_preference_score', 100)
    duration = datetime.timedelta(minutes=duration_minutes)

    # Determine collective working hours for all attendees.
    min_start_hour = min(get_user_preferences(u)["preferred_hours"]["start"] for u in attendees)
    max_end_hour = max(get_user_preferences(u)["preferred_hours"]["end"] for u in attendees)
    
    # Aggregate and sort all busy slots for the attendees.
    all_busy_slots = sorted([event for u in attendees if u in calendars for event in calendars[u]], key=lambda x: x[0])

    # Pass 1: Find a completely free slot.
    search_pointer = search_start_time
    # Check gap before the first meeting.
    first_busy_start = all_busy_slots[0][0] if all_busy_slots else None
    if not first_busy_start or search_pointer + duration <= first_busy_start:
        slot_start = search_pointer
        slot_end = slot_start + duration
        if slot_end.hour <= max_end_hour and calculate_preference_score(slot_start, slot_end, attendees, calendars) <= max_pref_score:
            return (slot_start, slot_end), []

    # Check gaps between meetings.
    for i, (_, busy_end, _, _) in enumerate(all_busy_slots):
        gap_start = max(search_pointer, busy_end)
        next_busy_start = all_busy_slots[i + 1][0] if i + 1 < len(all_busy_slots) else None
        
        if not next_busy_start or gap_start + duration <= next_busy_start:
            slot_start = gap_start
            slot_end = slot_start + duration
            if slot_start.hour >= min_start_hour and slot_end.hour <= max_end_hour:
                if calculate_preference_score(slot_start, slot_end, attendees, calendars) <= max_pref_score:
                    return (slot_start, slot_end), []

    # Pass 2: Find a reschedulable slot if no free slot was found.
    for start, _, _, _ in all_busy_slots:
        potential_start = max(start, search_start_time)
        potential_end = potential_start + duration

        if not (potential_start.hour >= min_start_hour and potential_end.hour <= max_end_hour):
            continue

        conflicting_events = [e for e in all_busy_slots if e[0] < potential_end and potential_start < e[1]]
        
        # Check if all conflicting events have a lower priority.
        can_reschedule = all(new_meeting_priority < conf_prio for _, _, conf_prio, _ in conflicting_events)
        
        if can_reschedule:
             if calculate_preference_score(potential_start, potential_end, attendees, calendars) <= max_pref_score:
                return ((potential_start, potential_end), conflicting_events)

    return None # No suitable slot found.

def _handle_successful_booking(result: Tuple, request: Dict, priority: int, calendars: Dict, attendees: List[str], **kwargs) -> Dict:
    """Helper function to format the output for a successfully scheduled meeting."""
    (start, end), to_reschedule = result
    
    all_meetings = []
    # Add the newly scheduled meeting to the output list.
    new_meeting_json = format_meeting_as_json(
        request.get('Subject', 'Unknown'), start, end, 
        metadata={"priority": priority, "newly_scheduled": True, "fallback_used": kwargs.get('fallback_used')}
    )
    all_meetings.append(new_meeting_json)
    
    rescheduling_result = None
    if to_reschedule:
        # If conflicts exist, handle the rescheduling process.
        attendees_map = {summ: attendees for _, _, _, summ in to_reschedule}
        meeting_info = {
            'subject': request.get('Subject', 'Unknown'),
            'start_time': start, 'end_time': end, 'priority': priority
        }
        rescheduling_result = handle_rescheduling(to_reschedule, meeting_info, calendars, attendees_map)
        if rescheduling_result.get('rescheduling_successful'):
            all_meetings.extend(rescheduling_result['meetings_to_reschedule'])

    return {
        'success': True,
        'meetings': all_meetings,
        'rescheduling_required': bool(to_reschedule),
        'rescheduling_result': rescheduling_result,
        **kwargs
    }

def schedule_meeting_from_request(user_calendars: Dict, meeting_request: Dict) -> Dict | None:
    """
    High-level function to schedule a meeting, with fallback strategies.
    Fallbacks include trying a shorter duration or relaxing constraints.
    """
    try:
        duration = meeting_request["Duration of meeting"]
        start_str = meeting_request["start time "]
        start_time = datetime.datetime.strptime(start_str, "%d-%m-%YT%H:%M:%S").replace(tzinfo=IST_TZ)
        priority = meeting_request.get("Priority", 1)
        attendees = list(user_calendars.keys())
        all_raw_events = [e for events in user_calendars.values() for e in events if e]
        parsed_calendars = parse_calendar_data(all_raw_events)
    except (KeyError, ValueError) as e:
        return {'success': False, 'error': f"Invalid meeting request format: {e}"}

    # Primary attempt to find a slot.
    result = find_earliest_slot(parsed_calendars, attendees, duration, priority, search_start_time=start_time)
    if result:
        return _handle_successful_booking(result, meeting_request, priority, parsed_calendars, attendees)

    # Fallback 1: Try a shorter duration (75% of original, min 15 mins).
    shorter_duration = max(15, int(duration * 0.75))
    if shorter_duration < duration:
        result = find_earliest_slot(parsed_calendars, attendees, shorter_duration, priority, search_start_time=start_time)
        if result:
            return _handle_successful_booking(result, meeting_request, priority, parsed_calendars, attendees, fallback_used="shorter_duration")
            
    # Fallback 2: Relax preference constraints.
    result = find_earliest_slot(parsed_calendars, attendees, duration, priority, search_start_time=start_time, max_preference_score=200)
    if result:
        return _handle_successful_booking(result, meeting_request, priority, parsed_calendars, attendees, fallback_used="relaxed_preferences")

    return {
        'success': False,
        'meetings': [],
        'error': 'No available slot found, even with fallback strategies.'
    }


# ==============================================================================
# 6. DATA TRANSFORMATION & WORKFLOW ADAPTERS
# ==============================================================================

def format_request_for_scheduler(request_data: Dict) -> Tuple[Dict, Dict]:
    """
    Transforms the initial user request into the format required by the scheduler.
    It calls the LLM, retrieves calendar data, and prepares the inputs.
    """
    details, summary = extract_meeting_details_with_llm(
        request_data["EmailContent"], request_data["Datetime"]
    )
    
    start_dt = datetime.datetime.strptime(details['start_date'], "%d-%m-%YT%H:%M:%S")
    end_dt = datetime.datetime.strptime(details['end_date'], "%d-%m-%YT%H:%M:%S")
    
    # Prepare the structured meeting request for the scheduling logic.
    scheduler_input = request_data.copy()
    scheduler_input.update({
        "start time ": start_dt.strftime("%d-%m-%YT%H:%M:%S"),
        "Duration of meeting": details['duration_minutes'],
        "Subject": summary,
        "Priority": details['priority']
    })
    
    # Fetch calendar data for all participants within the identified time window.
    all_emails = [request_data["From"]] + [p["email"] for p in request_data["Attendees"]]
    mappings = {'userone.amd@gmail.com': 'user1', 'usertwo.amd@gmail.com': 'user2', 'userthree.amd@gmail.com': 'user3'}
    
    user_calendars = {}
    day_start_utc = start_dt.replace(tzinfo=IST_TZ)
    day_end_utc = end_dt.replace(tzinfo=IST_TZ)
    for email in all_emails:
        events = retrieve_calendar_events(email, day_start_utc.isoformat(), day_end_utc.isoformat())
        # NOTE: Using a hardcoded mapping for user IDs. This should be dynamic.
        user_id = mappings.get(email, 'user_unknown')
        user_calendars[user_id] = events
            
    return scheduler_input, user_calendars

def format_final_output(input_request: Dict, scheduled_output: Dict) -> Dict:
    """
    Formats the final output by combining original request data with the
    scheduling results, including updated event lists for all attendees.
    """
    from copy import deepcopy
    output_format = deepcopy(input_request)
    
    new_meeting = next((m for m in scheduled_output['meetings'] if m["MetaData"].get('newly_scheduled')), None)
    if not new_meeting: return output_format # Return original request if scheduling failed.

    output_format.update({
        'EventStart': new_meeting['EventStart'],
        'EventEnd': new_meeting['EventEnd'],
        'Duration_mins': int(new_meeting['Duration_mins']),
        'Subject': new_meeting['Subject'],
        'metadata': {}
    })
    
    all_emails = [input_request["From"]] + [p["email"] for p in input_request["Attendees"]]
    events_by_email = {email: [] for email in all_emails}
    
    # Add the newly scheduled event for all attendees.
    for email in all_emails:
        events_by_email[email].append({
            "StartTime": new_meeting['EventStart'], "EndTime": new_meeting['EventEnd'],
            "NumAttendees": len(all_emails), "Attendees": all_emails,
            "Summary": new_meeting['Subject']
        })
        
    # Handle rescheduled meetings by updating their times in the final event list.
    for meeting in scheduled_output.get('meetings', []):
        if meeting['MetaData'].get('rescheduled'):
            for person_data in output_format.get('Attendees', []):
                for event in person_data.get('events', []):
                    if meeting['MetaData']['original_start'] == event.get('StartTime'):
                        event['StartTime'] = meeting['EventStart']
                        event['EndTime'] = meeting['EventEnd']
                        
    output_format['Attendees'] = [{'email': email, 'events': events} for email, events in events_by_email.items()]
    return output_format

# ==============================================================================
# 7. LANGGRAPH WORKFLOW DEFINITION
# ==============================================================================

class SchedulingState(TypedDict):
    """Defines the state passed between nodes in the LangGraph workflow."""
    user_request: Dict
    meeting_request_input: Dict
    user_calendars_input: Dict
    scheduled_meeting: Dict
    final_output: Dict

def node_parse_request(state: SchedulingState) -> Dict:
    """Node to parse the initial user request and prepare for scheduling."""
    request, calendars = format_request_for_scheduler(state['user_request'])
    return {"meeting_request_input": request, "user_calendars_input": calendars}

def node_schedule_meeting(state: SchedulingState) -> Dict:
    """Node to run the core scheduling algorithm."""
    scheduled = schedule_meeting_from_request(state['user_calendars_input'], state['meeting_request_input'])
    return {"scheduled_meeting": scheduled}

def node_format_output(state: SchedulingState) -> Dict:
    """Node to format the final JSON output."""
    final_output = format_final_output(state["user_request"], state["scheduled_meeting"])
    return {"final_output": final_output}

# Build the computation graph.
builder = StateGraph(SchedulingState)
builder.add_node("parse_request", node_parse_request)
builder.add_node("schedule_meeting", node_schedule_meeting)
builder.add_node("format_output", node_format_output)

# Define the workflow edges.
builder.add_edge(START, "parse_request")
builder.add_edge("parse_request", "schedule_meeting")
builder.add_edge("schedule_meeting", "format_output")
builder.add_edge("format_output", END)

# Compile the graph into a runnable object.
graph = builder.compile()

# Example of how to run the graph (uncomment to use):
# if __name__ == '__main__':
#     request_thursday = {
#         "Request_id": "a2", 
#         "Datetime": "19-07-2025T12:34:55", 
#         "From": "userone.amd@gmail.com",
#         "Attendees": [{"email": "usertwo.amd@gmail.com"}, {"email": "userthree.amd@gmail.com"}],
#         "EmailContent": "Let's sync up tomorrow for half an hour."
#     }
#     response = graph.invoke({"user_request": request_thursday})
#     print(json.dumps(response.get('final_output'), indent=2))
