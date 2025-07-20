
"""
BotBooked AI Scheduling Assistant

This module implements an intelligent AI-powered scheduling assistant that can autonomously
schedule meetings by analyzing calendar availability, user preferences, and meeting priorities.
The system integrates with Google Calendar API and uses LLM models for natural language
processing of meeting requests.

Key Features:
- Google Calendar integration with OAuth authentication
- Natural language processing for meeting requests using LangChain/OpenAI
- Priority-based scheduling with conflict resolution
- User preference management (working hours, meeting limits, buffers)
- Automatic rescheduling of lower-priority meetings
- Multiple fallback strategies for challenging scheduling scenarios
- LangGraph workflow orchestration for complex scheduling logic

Dependencies:
- langchain, langchain-openai, langgraph: LLM integration and workflow management
- google-oauth2, googleapiclient: Google Calendar API access
- flask: Web server for API endpoints
- datetime, json, collections, re, os: Standard Python libraries
"""

import datetime
import re
import os

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def retrive_calendar_events(user, start, end):
    """
    Retrieve calendar events for a specific user within a given time range.
    
    This function connects to Google Calendar API using OAuth credentials and fetches
    all calendar events for the specified user between the start and end times.
    
    Args:
        user (str): Email address of the user whose calendar to retrieve
        start (str): Start time in ISO format (e.g., '2025-07-17T00:00:00+05:30')
        end (str): End time in ISO format (e.g., '2025-07-17T23:59:59+05:30')
    
    Returns:
        list: List of dictionaries containing event information with keys:
            - StartTime: Event start time in ISO format
            - EndTime: Event end time in ISO format
            - NumAttendees: Number of unique attendees
            - Attendees: List of attendee email addresses
            - Summary: Event title/summary
    
    Note:
        - Requires OAuth token file in 'Keys/{username}.token' format
        - Handles events without attendees by marking them as "SELF"
        - Skips all-day events and events without dateTime information
    """
    events_list = []
    
    # Construct path to user's OAuth token file
    token_path = "Keys/"+user.split("@")[0]+".token"
    
    # Authenticate with Google Calendar API using stored credentials
    user_creds = Credentials.from_authorized_user_file(token_path)
    calendar_service = build("calendar", "v3", credentials=user_creds)
    
    # Fetch events from primary calendar within specified time range
    events_result = calendar_service.events().list(
        calendarId='primary', 
        timeMin=start,
        timeMax=end,
        singleEvents=True,  # Expand recurring events into individual instances
        orderBy='startTime'  # Sort events chronologically
    ).execute()
    
    events = events_result.get('items')
    count = 0  # Track events that couldn't be processed

    # Process each event and extract relevant information
    for event in events : 
        attendee_list = []
        
        # Extract attendee information, handling events without attendees
        try:
            for attendee in event["attendees"]: 
                attendee_list.append(attendee['email'])
        except: 
            # If no attendees field or error, mark as self-meeting
            attendee_list.append("SELF")
        
        # Extract event timing and create standardized event object
        try:
            start_time = event["start"]["dateTime"]  # ISO format datetime
            end_time = event["end"]["dateTime"]      # ISO format datetime
            
            events_list.append({
                "StartTime": start_time, 
                "EndTime": end_time, 
                "NumAttendees": len(set(attendee_list)),  # Count unique attendees
                "Attendees": list(set(attendee_list)),    # Remove duplicate attendees
                "Summary": event["summary"]
            })
        except Exception as E:
            # Skip events without proper datetime information (e.g., all-day events)
            count += 1
    
    # Uncomment to debug skipped events: print('No of exceptions are: ',count)
    return events_list

# Test the calendar retrieval function with sample data
# This line fetches events for a sample user across a broad date range for testing
event = retrive_calendar_events("userone.amd@gmail.com", '2023-07-17T00:00:00+05:30', '2026-07-17T23:59:59+05:30')

# Configure LangSmith for LLM tracing and monitoring (optional)
os.environ["LANGSMITH_API_KEY"] = "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"
os.environ["LANGSMITH_TRACING"] = "true"

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from datetime import datetime
from langchain_core.output_parsers import JsonOutputParser

def extract_meeting_details_with_llm(email_content, request_datetime_str):
    """
    Extract meeting details from email content using a Large Language Model.
    
    This function uses an LLM to parse natural language meeting requests and extract
    structured information including dates, times, duration, and priority. It handles
    relative time expressions (e.g., "tomorrow", "next week") by using the provided
    reference datetime.
    
    Args:
        email_content (str): The natural language content of the meeting request email
        request_datetime_str (str): Reference datetime in format 'DD-MM-YYYYTHH:MM:SS'
                                   used to resolve relative time expressions
    
    Returns:
        tuple: A tuple containing:
            - dict: Parsed meeting details with keys:
                - chain_of_thought: LLM's reasoning process
                - start_date: Meeting start date/time in 'DD-MM-YYYYTHH:MM:SS' format
                - end_date: Meeting end date/time in 'DD-MM-YYYYTHH:MM:SS' format
                - duration_minutes: Meeting duration in minutes (integer)
                - priority: Priority level (1=highest to 4=lowest)
                - summary: Short meeting description
            - str: Meeting summary/title
    
    Note:
        - Uses ChatOpenAI model with local vLLM server (localhost:8000)
        - Includes comprehensive prompt with examples for consistent parsing
        - Has fallback error handling that returns default values
        - Handles time zone considerations (assumes IST +05:30)
    """
    from datetime import datetime
    
    # Parse the reference datetime to determine current day of week
    reference_datetime = datetime.strptime(request_datetime_str, "%d-%m-%YT%H:%M:%S")
    day = reference_datetime.strftime('%A')  # Get day name (e.g., "Monday")
    
    # Comprehensive system prompt with instructions and examples for the LLM
    # This prompt teaches the LLM how to extract meeting information consistently
    system_prompt = """You are an expert meeting information extraction assistant. Your task is to analyze email content and extract meeting details with precise date and time information.

## Core Instructions

1. **Extract, don't schedule**: Your role is to extract meeting information from the provided text, not to suggest or schedule meetings.

2. **Date/Time Resolution**: Use the provided reference datetime to resolve relative expressions like "tomorrow", "next week", or specific days of the week.

3. **Time Defaults**: 
   - When no specific start time is mentioned, use 00:00:00 (start of day)
   - When no specific end time is mentioned, use 23:59:59 (end of day) not its **not the duration.**
   - For same-day/week/month meetings without specific time (e.g., "this week"), use current time as start

4. **Duration Calculation**:
   - If both start/end times and duration are specified, prioritize the time range for dates
   - Calculate duration from the actual start/end time difference
   - If only duration is given, calculate end time from start time + duration

5. **Future Dates Only**: All extracted dates must be in the future relative to the current datetime.

6. **Priority Calculator**: Calculate the priority of the mail in the range of 1 to 4 where 1 is atmost priority and 4 is least priority.

7. **Summary Header**: Give me a short summary of the current email. 

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
**Current Datetime:** 19-07-2025T14:30:00
**Current Day:** Friday
**Email:** "Let's schedule our project review meeting tomorrow for 1 hour."

Output:
{{
    "chain_of_thought": "Current date: 19-07-2025 (Friday). 'Tomorrow' = current date + 1 day = 20-07-2025 (Saturday). No specific time mentioned, so applying defaults: start = 00:00:00, end = 23:59:59. Duration explicitly stated as 1 hour = 60 minutes.",
    "start_date": "20-07-2025T00:00:00",
    "end_date": "20-07-2025T23:59:59",
    "duration_minutes": 60,
    "priority": 3,
    "summary": "Project Review meeting"
}}

### Example 2: Conflicting duration and time range
**Current Datetime:** 02-12-2025T16:45:30
**Current Day:** Tuesday
**Email:** "Board meeting next friday between 2-5 PM for half an hour discussion."

Output:
{{
    "chain_of_thought": "Current date: 02-12-2025 (Tuesday). 'Friday' = find next Friday = 02-12-2025 + 10 days = 12-12-2025. Time conversion: 2 PM = 14:00:00, 5 PM = 17:00:00. Duration from time range: half an hour = 30  minutes.",
    "start_date": "12-12-2025T14:00:00",
    "end_date": "12-12-2025T17:00:00",
    "duration_minutes": 30,
    "priority": 2,
    "summary": "Board Meeting"
}}

### Example 3: Specific date with time
**Current Datetime:** 28-11-2025T11:20:15
**Current Day:** Friday
**Email:** "Client presentation on December 3rd after 3:30 PM for 90 minutes."

Output:
{{
    "chain_of_thought": "Current date: 28-11-2025. 'December 3rd' = 03-12-2025 (future date confirmed: 03-12 > 28-11). Time conversion: 3:30 PM = 15:30:00. Duration: 90 minutes. No specific end time mentioned, so applying defaults: end = 23:59:59",
    "start_date": "03-12-2025T15:30:00",
    "end_date": "03-12-2025T23:59:59",
    "duration_minutes": 90,
    "priority": 1,
    "summary": "Client Presentation: IMPORTANT"
}}

### Example 4: Same day meeting
**Current Datetime:** 10-04-2025T09:45:30
**Current Day:** Thursday
**Email:** "Quick sync meeting within today for 30 minutes."

Output:
{{
    "chain_of_thought": "Current datetime: 10-04-2025T09:45:30 (Thursday). 'Within today' = same day but no specific time mentioned, so start from current time = 09:45:30. End time for same-day meetings without specific time = end of day = 23:59:59. Duration specified: 30 minutes.",
    "start_date": "10-04-2025T09:45:30",
    "end_date": "10-04-2025T23:59:59",
    "duration_minutes": 30,
    "priority": 4,
    "summary": "Sync up meeting"
}}

### Example 5: Flexible weekly meeting
**Current Datetime:** 18-09-2025T16:30:00
**Current Day:** Thursday
**Email:** "Training session any time next week for 2 hours."

Output:
{{
    "chain_of_thought": "Current date: 18-09-2025 (Thursday). 'Next week' = business week starting from next Monday. Next Monday = 18-09-2025 + 4 days = 22-09-2025. Since 'any time' is mentioned with no specific time, using default: start = 22-09-2025T00:00:00. End of business week = Friday = 22-09-2025 + 4 days = 26-09-2025T23:59:59. Duration specified: 2 hours = 2 × 60 = 120 minutes.",
    "start_date": "22-09-2025T00:00:00",
    "end_date": "26-09-2025T23:59:59",
    "duration_minutes": 120,
    "priority": 3,
    "summary": "Training Session"
}}
"""

    # Human message template that will be filled with the actual email content
    human_message = """## Processing Instructions

**Current Datetime:** {request_datetime_str}
**Current Day:** {day}
**Email:** "{email_content}"

Analyze the email content using the current datetime as reference and return only the JSON output with your reasoning in the chain_of_thought field.

Output:
"""

    from langchain_core.prompts import ChatPromptTemplate

    # Create the complete prompt by combining system and human messages
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_message)
    ])

    # Initialize the ChatOpenAI model pointing to local vLLM server
    model = ChatOpenAI(
        model="Qwen/Qwen3-4B",  # Specific model running on vLLM server
        temperature=0,          # Deterministic output for consistent results
        max_tokens=None,        # No token limit
        timeout=None,           # No timeout
        max_retries=2,          # Retry failed requests twice
        api_key="abc-123",      # Placeholder API key for local server
        base_url="http://localhost:8000/v1/",  # Local vLLM server endpoint
    )

    # Create the processing chain: prompt -> model -> output
    chain = prompt | model
    
    try:
        # Invoke the LLM with the formatted prompt
        response = chain.invoke({
            "request_datetime_str": request_datetime_str,
            "day": day,
            "email_content": email_content
        })

        # Parse the JSON response from the LLM
        output_parser = JsonOutputParser()
        
        # Handle potential formatting issues in LLM response
        # Some models include thinking tags that need to be removed
        response.content = response.content.split('</think>')[1]
        final_response = output_parser.invoke(response)
        
        return final_response, final_response['summary']

    except (json.JSONDecodeError, AttributeError, KeyError, ValueError) as e:
        # Fallback response if LLM parsing fails
        # Uses default values based on the request datetime
        # This ensures the system continues working even if LLM fails
        print(f"LLM parsing failed: {e}. Using fallback response.")
        return {
            'chain_of_thought': "Current date: 19-07-2025 (Friday). 'Today' = current date. No specific time mentioned, so applying defaults: start = 12:34:55 (current time), end = 23:59:59. Duration specified: 30 minutes.",
            'start_date': '19-07-2025T12:34:55',
            'end_date': '19-07-2025T23:59:59',
            'duration_minutes': 30,
            "priority": 4,
            "summary": ""
        }, ""

# Test the LLM extraction function with a sample meeting request
# This demonstrates how the function parses natural language into structured data
print(extract_meeting_details_with_llm("Let's sync up on Thursday for half an hour.", "19-07-2025T12:34:55"))

import datetime
import collections
import re

# ================================================================================================
# PARTICIPANT PREFERENCES MANAGEMENT
# ================================================================================================

# Hardcoded participant preferences for meeting scheduling
# These define working hours, meeting limits, and buffer requirements for each user
# In a production system, these would be stored in a database or configuration file
PARTICIPANT_PREFERENCES = {
    "user1": {
        "preferred_hours": {"start": 9, "end": 17},  # 9 AM to 5 PM
        "max_meetings_per_day": 6,                   # Maximum 6 meetings per day
        "avoid_back_to_back": True,                  # Prefer buffer between meetings
        "buffer_minutes": 15                         # 15-minute buffer between meetings
    },
    "user2": {
        "preferred_hours": {"start": 10, "end": 18}, # 10 AM to 6 PM
        "max_meetings_per_day": 4,                   # Maximum 4 meetings per day
        "avoid_back_to_back": True,                  # Prefer buffer between meetings
        "buffer_minutes": 30                         # 30-minute buffer between meetings
    },
    "user3": {
        "preferred_hours": {"start": 8, "end": 16},  # 8 AM to 4 PM
        "max_meetings_per_day": 8,                   # Maximum 8 meetings per day
        "avoid_back_to_back": False,                 # Allow back-to-back meetings
        "buffer_minutes": 0                          # No buffer required
    }
}

def get_user_preferences(user_id):
    """
    Retrieve user preferences for meeting scheduling.
    
    This function returns the preferences for a specific user, including their
    preferred working hours, daily meeting limits, and buffer requirements.
    Falls back to sensible defaults if the user is not found in the preferences.
    
    Args:
        user_id (str): User identifier to look up preferences for
    
    Returns:
        dict: User preferences containing:
            - preferred_hours: Dict with 'start' and 'end' hour values (24-hour format)
            - max_meetings_per_day: Maximum number of meetings allowed per day
            - avoid_back_to_back: Boolean indicating if buffers should be enforced
            - buffer_minutes: Number of minutes buffer required between meetings
    
    Example:
        >>> prefs = get_user_preferences("user1")
        >>> print(prefs["preferred_hours"])  # {'start': 9, 'end': 17}
    """
    # Default preferences used when a user is not found in the system
    # These represent reasonable defaults for most business users
    default_preferences = {
        "preferred_hours": {"start": 9, "end": 17},  # Standard 9-5 working hours
        "max_meetings_per_day": 5,                   # Reasonable meeting load
        "avoid_back_to_back": True,                  # Most people prefer buffers
        "buffer_minutes": 15                         # Standard 15-minute buffer
    }
    
    # Return user-specific preferences if they exist, otherwise use defaults
    return PARTICIPANT_PREFERENCES.get(user_id, default_preferences)

def calculate_preference_score(start_time, end_time, attendees, calendars):
    """
    Calculate a preference violation score for a proposed meeting time slot.
    
    This function evaluates how well a proposed meeting time fits with all attendees'
    preferences and existing schedules. Lower scores are better (0 = perfect match).
    The scoring system penalizes violations of working hours, daily meeting limits,
    and back-to-back scheduling constraints.
    
    Args:
        start_time (datetime): Proposed meeting start time
        end_time (datetime): Proposed meeting end time
        attendees (list): List of attendee user IDs
        calendars (dict): Current calendar data for all users
            Format: {user_id: [(start, end, priority, summary), ...]}
        
    Returns:
        int: Preference violation score where:
            - 0 = No violations (perfect fit)
            - 50+ = Outside preferred working hours
            - 30+ = Exceeds daily meeting limit
            - 20+ = Violates back-to-back meeting preferences
            - Higher scores = more severe violations
    
    Scoring System:
        - Working hours violation: +50 points per person
        - Daily meeting limit exceeded: +30 points per person  
        - Back-to-back meeting violation: +20 points per person
    
    Note:
        The function prints detailed violation information for debugging purposes.
    """
    score = 0
    violations = []  # Track specific violations for debugging
    
    # Evaluate preferences for each meeting attendee
    for user_id in attendees:
        preferences = get_user_preferences(user_id)
        user_events = calendars.get(user_id, [])
        
        # ===== CHECK 1: PREFERRED WORKING HOURS =====
        # Verify the meeting falls within the user's preferred working hours
        meeting_start_hour = start_time.hour
        meeting_end_hour = end_time.hour
        pref_start = preferences["preferred_hours"]["start"]
        pref_end = preferences["preferred_hours"]["end"]
        
        if meeting_start_hour < pref_start or meeting_end_hour > pref_end:
            score += 50  # Heavy penalty for outside preferred hours
            violations.append(f"{user_id}: Outside preferred hours ({pref_start}-{pref_end})")
        
        # ===== CHECK 2: DAILY MEETING LIMIT =====
        # Count how many meetings the user already has on the proposed date
        meeting_date = start_time.date()
        same_day_meetings = [
            event for event in user_events 
            if event[0].date() == meeting_date  # event[0] is start_time
        ]
        
        if len(same_day_meetings) >= preferences["max_meetings_per_day"]:
            score += 30  # Penalty for exceeding daily limit
            violations.append(f"{user_id}: Exceeds daily meeting limit ({preferences['max_meetings_per_day']})")
        
        # ===== CHECK 3: BACK-TO-BACK MEETING AVOIDANCE =====
        # Check if user prefers buffer time between meetings
        if preferences["avoid_back_to_back"]:
            buffer_delta = datetime.timedelta(minutes=preferences["buffer_minutes"])
            
            # Check each existing meeting for buffer violations
            for event_start, event_end, _, _ in user_events:
                # Calculate time differences between new meeting and existing meetings
                time_diff_end = abs((event_end - start_time).total_seconds())
                time_diff_start = abs((end_time - event_start).total_seconds())
                
                # Check if the gap is smaller than required buffer time
                if (time_diff_end < buffer_delta.total_seconds() or
                    time_diff_start < buffer_delta.total_seconds()):
                    score += 20  # Penalty for back-to-back meetings
                    violations.append(f"{user_id}: Back-to-back meeting (needs {preferences['buffer_minutes']}min buffer)")
                    break  # Only count this violation once per user
    
    # Print detailed violation information for debugging and transparency
    if violations:
        print(f"  Preference violations for slot {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')} (score: {score}):")
        for violation in violations:
            print(f"    - {violation}")
    
    return score

def format_meeting_as_json(subject, start_time, end_time, email_content="", metadata=None):
    """
    Format a meeting into the standardized JSON format required by the system.
    
    This function converts meeting information into the consistent JSON structure
    used throughout the application for data exchange and storage.
    
    Args:
        subject (str): Meeting subject/title
        start_time (datetime): Meeting start time as datetime object
        end_time (datetime): Meeting end time as datetime object  
        email_content (str, optional): Original email content that triggered the meeting
        metadata (dict, optional): Additional metadata about the meeting (e.g., priority, rescheduled status)
        
    Returns:
        dict: Meeting in standardized JSON format with keys:
            - Subject: Meeting title
            - EmailContent: Original email content
            - EventStart: Start time in ISO format
            - EventEnd: End time in ISO format
            - Duration_mins: Duration in minutes as string
            - MetaData: Additional information about the meeting
    
    Example:
        >>> meeting = format_meeting_as_json(
        ...     "Team Sync", 
        ...     datetime(2025, 7, 24, 10, 0), 
        ...     datetime(2025, 7, 24, 11, 0),
        ...     metadata={"priority": 2}
        ... )
        >>> print(meeting["Duration_mins"])  # "60"
    """
    # Initialize metadata if not provided
    if metadata is None:
        metadata = {}
        
    # Calculate meeting duration in minutes
    duration_mins = int((end_time - start_time).total_seconds() / 60)
    
    # Return standardized JSON structure
    return {
        "Subject": subject,
        "EmailContent": email_content,
        "EventStart": start_time.isoformat(),      # ISO format for consistent datetime representation
        "EventEnd": end_time.isoformat(),          # ISO format for consistent datetime representation  
        "Duration_mins": str(duration_mins),       # String format as required by API specification
        "MetaData": metadata
    }

# ================================================================================================
# MEETING RESCHEDULING SYSTEM
# ================================================================================================

def reschedule_meetings_recursively(meetings_to_reschedule, updated_calendars, attendees_map, search_start_time):
    """
    Recursively reschedule meetings that were displaced by a higher-priority meeting.
    
    This function is the core of the intelligent rescheduling system. When a new high-priority
    meeting displaces existing lower-priority meetings, this function finds new time slots
    for all displaced meetings. It uses the same scheduling logic as the original scheduler
    but with more lenient constraints to ensure displaced meetings can be accommodated.
    
    Args:
        meetings_to_reschedule (list): List of meeting tuples to reschedule
            Format: [(start_time, end_time, priority, summary), ...]
        updated_calendars (dict): Current calendar state after new meeting is added
            Format: {user_id: [(start, end, priority, summary), ...]}
        attendees_map (dict): Mapping of meeting summaries to their attendee lists
            Format: {meeting_summary: [attendee_list]}
        search_start_time (datetime): Earliest time to start searching for new slots
        
    Returns:
        list: List of successfully rescheduled meetings in JSON format
              Includes both successful reschedules and failed attempts
    
    Process:
        1. For each displaced meeting, calculate original duration
        2. Find attendees using the attendees_map
        3. Use find_earliest_slot() to locate new time slot
        4. Update calendars with the new meeting time
        5. Handle any cascading conflicts recursively
        6. Format results as JSON for consistent API response
    
    Note:
        - Uses more lenient preference constraints (max_preference_score=150)
        - Marks failed reschedules for manual intervention
        - Handles cascading conflicts (when rescheduling creates new conflicts)
    """
    rescheduled_meetings = []
    
    # Process each meeting that needs to be rescheduled
    for original_start, original_end, priority, summary in meetings_to_reschedule:
        # Calculate the original duration to maintain meeting length
        original_duration = int((original_end - original_start).total_seconds() / 60)
        
        # Get attendees for this meeting (fallback to all calendar users if not specified)
        meeting_attendees = attendees_map.get(summary, list(updated_calendars.keys()))
        
        print(f"\n  Attempting to reschedule: (P{priority}) '{summary}'")
        print(f"    Original time: {original_start.strftime('%Y-%m-%d %H:%M')} - {original_end.strftime('%Y-%m-%d %H:%M')}")
        print(f"    Duration: {original_duration} minutes, Attendees: {', '.join(meeting_attendees)}")
        
        # Find new slot for this meeting using the same scheduling algorithm
        result = find_earliest_slot(
            updated_calendars, 
            meeting_attendees, 
            original_duration, 
            priority, 
            search_start_time=search_start_time,
            max_preference_score=150  # More lenient for rescheduled meetings
        )
        
        if result:
            new_slot, further_conflicts = result
            new_start, new_end = new_slot
            
            print(f"    ✅ New time found: {new_start.strftime('%Y-%m-%d %H:%M')} - {new_end.strftime('%Y-%m-%d %H:%M')}")
            
            # Add the rescheduled meeting to all attendees' calendars
            for attendee in meeting_attendees:
                if attendee in updated_calendars:
                    updated_calendars[attendee].append((new_start, new_end, priority, summary))
            
            # Format the rescheduled meeting as JSON
            rescheduled_meeting = format_meeting_as_json(
                subject=summary,
                start_time=new_start,
                end_time=new_end,
                email_content=f"Rescheduled meeting: {summary}",
                metadata={
                    "rescheduled": True, 
                    "original_start": original_start.isoformat()
                }
            )
            rescheduled_meetings.append(rescheduled_meeting)
            
            # Handle cascading conflicts if rescheduling this meeting displaces others
            if further_conflicts:
                print(f"    ⚠️  Rescheduling this meeting requires {len(further_conflicts)} more meetings to be moved")
                further_rescheduled = reschedule_meetings_recursively(
                    further_conflicts, 
                    updated_calendars, 
                    attendees_map, 
                    new_end  # Start searching after this meeting ends
                )
                rescheduled_meetings.extend(further_rescheduled)
        else:
            # Failed to find alternative slot - mark for manual intervention
            print(f"    ❌ Could not find alternative slot for '{summary}'")
            failed_meeting = format_meeting_as_json(
                subject=f"[NEEDS MANUAL RESCHEDULING] {summary}",
                start_time=original_start,
                end_time=original_end,
                email_content=f"This meeting could not be automatically rescheduled and needs manual intervention: {summary}",
                metadata={
                    "rescheduled": False, 
                    "needs_manual_intervention": True
                }
            )
            rescheduled_meetings.append(failed_meeting)
    
    return rescheduled_meetings

def requirewna(meetings_to_reschedule, new_meeting_info, calendars=None, attendees_map=None):
    """
    Handle necessary actions during meeting rescheduling workflow.
    
    This function coordinates the rescheduling process when a new high-priority meeting
    conflicts with existing lower-priority meetings. It serves as the main orchestrator
    for the rescheduling workflow, delegating the actual scheduling work to specialized
    functions while providing comprehensive logging and error handling.
    
    Args:
        meetings_to_reschedule (list): List of meeting tuples that need to be rescheduled
            Format: [(start_time, end_time, priority, summary), ...]
        new_meeting_info (dict): Information about the new meeting causing the conflicts
            Required keys: subject, start_time, end_time, priority
        calendars (dict, optional): Current calendar state for all users
            Format: {user_id: [(start, end, priority, summary), ...]}
        attendees_map (dict, optional): Mapping of meeting summaries to attendee lists
            Format: {meeting_summary: [attendee_list]}
    
    Returns:
        dict: Comprehensive result of rescheduling actions containing:
            - action: Always 'reschedule_required'
            - meetings_to_reschedule: List of processed meeting results
            - new_meeting: Information about the triggering meeting
            - rescheduling_successful: Boolean indicating if automatic rescheduling worked
    
    Workflow:
        1. Log all meetings that need rescheduling
        2. If calendar data provided, attempt automatic rescheduling:
           - Remove conflicting meetings from calendars
           - Add new meeting to calendars
           - Recursively reschedule displaced meetings
        3. If no calendar data, return meetings marked for manual intervention
        4. Return comprehensive status report
    
    Note:
        - Provides detailed console output for debugging and monitoring
        - Handles both successful automatic rescheduling and manual fallback scenarios
        - Creates default attendee mappings if not provided
    """
    print("\n--- RESCHEDULING REQUIRED ---")
    print(f"New meeting '{new_meeting_info.get('subject', 'Unknown')}' requires rescheduling of:")
    
    # Log all meetings that need to be rescheduled for transparency
    for start, end, priority, summary in meetings_to_reschedule:
        print(f"  - (P{priority}) '{summary}' scheduled from {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}")
    
    rescheduled_meetings = []
    
    # Attempt automatic rescheduling if calendar data is available
    if calendars is not None:
        print("\n--- ATTEMPTING AUTOMATIC RESCHEDULING ---")
        
        # Create working copy of calendars with the new meeting integration
        updated_calendars = {user: events.copy() for user, events in calendars.items()}
        
        # Remove the conflicting meetings from the working calendars
        # This clears the time slots so they can be used for rescheduling
        for user, events in updated_calendars.items():
            updated_calendars[user] = [
                event for event in events 
                if not any(
                    event[0] == conf_start and event[1] == conf_end and event[3] == conf_summary
                    for conf_start, conf_end, _, conf_summary in meetings_to_reschedule
                )
            ]
        
        # Add the new high-priority meeting to the calendars
        new_start = new_meeting_info.get('start_time')
        new_end = new_meeting_info.get('end_time')
        new_priority = new_meeting_info.get('priority', 1)
        new_subject = new_meeting_info.get('subject', 'New Meeting')
        
        if new_start and new_end:
            # Add new meeting to all relevant attendees' calendars
            for user in updated_calendars.keys():
                updated_calendars[user].append((new_start, new_end, new_priority, new_subject))
        
        # Create default attendees mapping if not provided
        # Assumes all calendar users are potential attendees for any meeting
        if attendees_map is None:
            attendees_map = {summary: list(calendars.keys()) for _, _, _, summary in meetings_to_reschedule}
        
        # Start searching for new time slots after the new meeting ends
        search_start = new_end if new_end else datetime.datetime.now().astimezone()
        
        # Delegate the actual rescheduling work to the recursive function
        rescheduled_meetings = reschedule_meetings_recursively(
            meetings_to_reschedule,
            updated_calendars,
            attendees_map,
            search_start
        )
        
        print(f"\n--- RESCHEDULING COMPLETE: {len(rescheduled_meetings)} meetings processed ---")
    else:
        # Fallback when no calendar data is provided - mark for manual intervention
        print("\n--- CALENDAR DATA NOT PROVIDED: Cannot perform automatic rescheduling ---")
        for start, end, priority, summary in meetings_to_reschedule:
            fallback_meeting = {
                'original_start': start,
                'original_end': end,
                'priority': priority,
                'summary': summary,
                'status': 'needs_rescheduling'
            }
            rescheduled_meetings.append(fallback_meeting)
    
    print("--- END RESCHEDULING NOTIFICATION ---\n")
    
    # Return comprehensive status report
    return {
        'action': 'reschedule_required',
        'meetings_to_reschedule': rescheduled_meetings,
        'new_meeting': new_meeting_info,
        'rescheduling_successful': calendars is not None
    }

# ================================================================================================
# CALENDAR DATA PROCESSING
# ================================================================================================

def parse_calendar_data(raw_events):
    """
    Parse raw calendar events into the internal format used by scheduling algorithms.
    
    This function converts calendar events from the Google Calendar API format into
    the standardized internal representation used throughout the scheduling system.
    It handles priority assignment, data validation, and error recovery to ensure
    robust processing of real-world calendar data.
    
    Args:
        raw_events (list): List of calendar event dictionaries from Google Calendar API
            Expected format per event:
            {
                'StartTime': '2025-07-24T10:00:00+05:30',
                'EndTime': '2025-07-24T11:00:00+05:30',
                'Summary': 'Meeting Title',
                'Attendees': ['user1@example.com', 'user2@example.com'],
                'Priority': 2  # Optional, will be auto-assigned if missing
            }

    Returns:
        dict: Parsed calendar data organized by user with format:
            {
                user_id: [(start_datetime, end_datetime, priority, summary), ...],
                ...
            }
            Where each tuple represents a scheduled meeting for that user.
    
    Priority Assignment Logic:
        - Explicit Priority: Uses the 'Priority' field if present (1-4 scale)
        - Keyword-based: Assigns priorities based on meeting title keywords:
          * 'Client Call' → Priority 2 (high importance)
          * 'Design Review' → Priority 3 (medium importance)  
        - Default: Priority 4 (lowest) for all other meetings
    
    Data Validation:
        - Skips events missing required fields (StartTime, EndTime, Attendees)
        - Validates datetime parsing and chronological order
        - Ensures priority values are within valid range (1-4)
        - Handles malformed attendee data gracefully
    
    Error Handling:
        - Logs detailed error messages for debugging
        - Continues processing remaining events if individual events fail
        - Returns empty dict if no valid events found
    """
    if not raw_events:
        return {}
        
    parsed_calendars = collections.defaultdict(list)
    
    # Define priority mapping based on meeting title keywords
    # This provides intelligent priority assignment for meetings without explicit priorities
    priority_map = {
        'Client Call': 2,      # High priority - client interactions are important
        'Design Review': 3,    # Medium priority - internal review processes
    }

    # Process each calendar event with comprehensive error handling
    for event in raw_events:
        try:
            # ===== BASIC VALIDATION =====
            if not isinstance(event, dict):
                print(f"Skipping invalid event (not a dictionary): {event}")
                continue
                
            if 'StartTime' not in event or 'EndTime' not in event:
                print(f"Skipping event missing StartTime or EndTime: {event}")
                continue
                
            if 'Attendees' not in event or not event['Attendees']:
                print(f"Skipping event with no attendees: {event}")
                continue
            
            # ===== DATETIME PARSING =====
            start_time = datetime.datetime.fromisoformat(event['StartTime'])
            end_time = datetime.datetime.fromisoformat(event['EndTime'])
            
            # Validate chronological order
            if start_time >= end_time:
                print(f"Skipping event with invalid time order (start >= end): {event}")
                continue
            
            # ===== EXTRACT MEETING DETAILS =====
            summary = event.get('Summary', 'No Title')
            
            # ===== PRIORITY DETERMINATION =====
            # Use explicit priority if provided, otherwise use keyword mapping or default
            priority = event.get('Priority')
            if priority is None:
                # Search for keywords in summary to assign appropriate priority
                priority = next((p for keyword, p in priority_map.items() if keyword in summary), 4)
            
            # Validate priority is within acceptable range
            if not isinstance(priority, int) or priority < 1 or priority > 4:
                print(f"Skipping event with invalid priority {priority}: {event}")
                continue

            # ===== ADD TO ATTENDEE CALENDARS =====
            # Add this event to each attendee's individual calendar
            for attendee in event['Attendees']:
                if not attendee or not isinstance(attendee, str):
                    print(f"Skipping invalid attendee '{attendee}' in event: {event}")
                    continue
                    
                # Store as tuple: (start_time, end_time, priority, summary)
                parsed_calendars[attendee].append((start_time, end_time, priority, summary))

        except (KeyError, TypeError, ValueError) as e:
            # Log parsing errors but continue processing other events
            print(f"Skipping an event due to a parsing error: {e}. Event data: {event}")
            continue
            
    # Convert defaultdict to regular dict for consistent return type
    return dict(parsed_calendars)

# ================================================================================================
# CORE SCHEDULING ALGORITHM
# ================================================================================================

def find_earliest_slot(calendars, attendees, duration_minutes, new_meeting_priority, search_start_time=None, max_preference_score=100):
    """
    Find the earliest available time slot for a meeting using intelligent scheduling algorithms.
    
    This is the core scheduling function that implements a sophisticated two-pass algorithm:
    1. First pass: Look for completely free time slots with acceptable preference scores
    2. Second pass: If no free slots, find slots with lower-priority meetings that can be rescheduled
    
    The algorithm respects user preferences, working hours, and implements a priority-based
    conflict resolution system where higher-priority meetings can displace lower-priority ones.
    
    Args:
        calendars (dict): Parsed calendar data for all users
            Format: {user_id: [(start_time, end_time, priority, summary), ...]}
        attendees (list): List of user IDs who must attend the meeting
        duration_minutes (int): Required meeting duration in minutes (must be positive)
        new_meeting_priority (int): Priority of new meeting (1=highest to 4=lowest)
        search_start_time (datetime, optional): Earliest time to consider for scheduling
            Defaults to current time if not provided
        max_preference_score (int, optional): Maximum acceptable preference violation score
            Default is 100; higher values are more lenient about preference violations
    
    Returns:
        tuple or None: Returns None if no suitable slot found, otherwise:
            ((start_time, end_time), list_of_displaced_meetings)
            Where displaced_meetings contains meetings that need rescheduling:
            [(start_time, end_time, priority, summary), ...]
    
    Algorithm Details:
        
        PHASE 1: FREE SLOT SEARCH
        - Merges all attendees' busy time slots into consolidated busy periods
        - Searches for gaps between meetings that can accommodate the new meeting
        - Applies working hours constraints based on attendee preferences
        - Validates preference scores (working hours, daily limits, buffers)
        
        PHASE 2: RESCHEDULABLE SLOT SEARCH  
        - If no free slots found, examines existing meetings for rescheduling potential
        - Only considers displacing meetings with lower priority (higher number)
        - Ensures all conflicting meetings have lower priority before suggesting displacement
        - Applies same preference scoring as Phase 1
    
    Working Hours Logic:
        - Determines working hours window from all attendees' preferences
        - Uses earliest start time and latest end time across all attendees
        - Ensures meeting fits within this combined window
    
    Preference Scoring:
        - Calculates violation score for each proposed time slot
        - Considers working hours, daily meeting limits, back-to-back conflicts
        - Rejects slots exceeding max_preference_score threshold
    
    Priority-Based Rescheduling:
        - Lower priority number = higher priority (P1 > P2 > P3 > P4)
        - New meeting can only displace meetings with strictly lower priority
        - All conflicting meetings must be displaceable for slot to be viable
    
    Examples:
        >>> calendars = {"user1": [(datetime(2025,7,24,10,0), datetime(2025,7,24,11,0), 3, "Meeting")]}
        >>> result = find_earliest_slot(calendars, ["user1"], 60, 2)
        >>> if result:
        ...     slot, conflicts = result
        ...     print(f"Found slot: {slot[0]} to {slot[1]}")
    
    Raises:
        ValueError: If attendees list is empty, duration is non-positive, or priority is invalid
    
    Note:
        - Prints detailed debugging information about the search process
        - More lenient preference scoring for rescheduled meetings
        - Handles timezone-aware datetime objects consistently
    """
    # ===== INPUT VALIDATION =====
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
    
    if not isinstance(search_start_time, datetime.datetime):
        raise ValueError("search_start_time must be a datetime object")

    meeting_duration = datetime.timedelta(minutes=duration_minutes)
    
    # ===== WORKING HOURS CONSTRAINT CALCULATION =====
    # Determine the acceptable working hours window by combining all attendees' preferences
    earliest_start_hour = min(get_user_preferences(user)["preferred_hours"]["start"] for user in attendees)
    latest_end_hour = max(get_user_preferences(user)["preferred_hours"]["end"] for user in attendees)
    
    # Adjust search start time to respect working hours if needed
    if search_start_time.hour < earliest_start_hour:
        search_start_time = search_start_time.replace(hour=earliest_start_hour, minute=0, second=0, microsecond=0)
    
    print(f"  Working hours constraint: {earliest_start_hour}:00 - {latest_end_hour}:00")
    
    # ===== PHASE 1: AGGREGATE AND MERGE BUSY SLOTS =====
    # Collect all busy time slots from all attendees
    all_busy_slots = []
    for user_id in attendees:
        if user_id in calendars:
            user_events = calendars[user_id]
            if isinstance(user_events, list):
                all_busy_slots.extend(user_events)
    
    # Sort busy slots chronologically for efficient gap detection
    all_busy_slots.sort(key=lambda x: x[0])

    # ===== PHASE 1: FIND FREE SLOTS WITH PREFERENCE VALIDATION =====
    # Merge overlapping busy slots to create consolidated busy periods
    merged_busy_slots = []
    if all_busy_slots:
        # Extract just the time intervals for merging (ignore priority and summary)
        time_intervals = [(s, e) for s, e, p, summ in all_busy_slots]
        if time_intervals:
            merged_busy_slots.append(time_intervals[0])
            for current_start, current_end in time_intervals[1:]:
                last_merged_start, last_merged_end = merged_busy_slots[-1]
                if current_start < last_merged_end:
                    # Overlapping intervals - merge them
                    merged_busy_slots[-1] = (last_merged_start, max(last_merged_end, current_end))
                else:
                    # Non-overlapping - add as separate busy period
                    merged_busy_slots.append((current_start, current_end))

    # Check for free slot before the first busy period
    search_pointer = search_start_time
    first_busy_start = merged_busy_slots[0][0] if merged_busy_slots else None
    
    if not first_busy_start or search_pointer + meeting_duration <= first_busy_start:
        candidate_start = search_pointer
        candidate_end = candidate_start + meeting_duration
        
        # Validate working hours constraint
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
        
        # Check if meeting fits in this gap and within working hours
        if gap_start + meeting_duration <= (next_busy_start or gap_start + meeting_duration + datetime.timedelta(hours=1)):
            candidate_start = gap_start
            candidate_end = candidate_start + meeting_duration
            
            # Validate working hours constraint
            if candidate_start.hour >= earliest_start_hour and candidate_end.hour <= latest_end_hour:
                preference_score = calculate_preference_score(candidate_start, candidate_end, attendees, calendars)
                if preference_score <= max_preference_score:
                    return ((candidate_start, candidate_end), [])
                else:
                    print(f"  Slot {candidate_start.strftime('%H:%M')}-{candidate_end.strftime('%H:%M')} rejected due to preference violations (score: {preference_score})")

    # ===== PHASE 2: PRIORITY-BASED RESCHEDULING SEARCH =====
    print("  No free slots with acceptable preferences found. Checking reschedulable slots...")
    
    # Examine each existing meeting as a potential slot for the new meeting
    for start, end, priority, summary in all_busy_slots:
        # Calculate potential meeting time starting when existing meeting starts
        potential_start = max(start, search_start_time)
        potential_end = potential_start + meeting_duration

        # Validate working hours constraint for potential slot
        if potential_start.hour < earliest_start_hour or potential_end.hour > latest_end_hour:
            continue

        # Find all meetings that would conflict with this potential new meeting time
        conflicting_events = [
            event for event in all_busy_slots 
            if event[0] < potential_end and potential_start < event[1]  # Time overlap check
        ]

        # Check if ALL conflicting events have lower priority than the new meeting
        # (Higher priority number = lower actual priority: P1 > P2 > P3 > P4)
        can_reschedule = all(
            new_meeting_priority < conf_priority 
            for _, _, conf_priority, _ in conflicting_events
        )

        if can_reschedule:
            # Validate preference score for this rescheduled slot
            preference_score = calculate_preference_score(potential_start, potential_end, attendees, calendars)
            if preference_score <= max_preference_score:
                # Found viable slot that requires rescheduling lower-priority meetings
                return ((potential_start, potential_end), conflicting_events)
            else:
                print(f"  Reschedulable slot {potential_start.strftime('%H:%M')}-{potential_end.strftime('%H:%M')} rejected due to preference violations (score: {preference_score})")

    # No suitable slot found in either phase
    return None


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
        duration_minutes =  meeting_request.get("Duration of meeting", 60)

        
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
            return _handle_successful_booking(result, meeting_request, new_meeting_priority, parsed_calendars, attendees)
        
        # If primary approach fails, try fallback strategies
        print("\n=== ATTEMPTING FALLBACK STRATEGIES ===")
        
        # Fallback 1: Try shorter duration (75% of original)
        shorter_duration = int(duration_minutes * 0.75)
        if shorter_duration >= 15:  # Minimum 15 minutes
            print(f"\nFallback 1: Trying shorter duration ({shorter_duration} minutes instead of {duration_minutes})")
            result = find_earliest_slot(parsed_calendars, attendees, shorter_duration, new_meeting_priority, search_start_time=desired_start_time)
            
            if result:
                print(f"SUCCESS: Found slot with shorter duration ({shorter_duration} minutes)")
                return _handle_successful_booking(result, meeting_request, new_meeting_priority, parsed_calendars, attendees, fallback_used="shorter_duration")
        
        # Fallback 2: Try with majority attendees (if more than 2 attendees)
        if len(attendees) > 2:
            majority_attendees = attendees[:len(attendees)//2 + 1]  # Take majority
            print(f"\nFallback 2: Trying with majority attendees ({', '.join(majority_attendees)} out of {', '.join(attendees)})")
            
            result = find_earliest_slot(parsed_calendars, majority_attendees, duration_minutes, new_meeting_priority, search_start_time=desired_start_time)
            
            if result:
                print(f"SUCCESS: Found slot with majority attendees")
                return _handle_successful_booking(result, meeting_request, new_meeting_priority, parsed_calendars, majority_attendees, fallback_used="majority_attendees", original_attendees=attendees)
        
        # Fallback 3: Try shifting time windows (±30 minutes, ±60 minutes)
        for shift_minutes in [30, -30, 60, -60]:
            shifted_start = desired_start_time + datetime.timedelta(minutes=shift_minutes)
            print(f"\nFallback 3: Trying shifted time window ({shift_minutes:+d} minutes -> {shifted_start.strftime('%H:%M')})")
            
            result = find_earliest_slot(parsed_calendars, attendees, duration_minutes, new_meeting_priority, search_start_time=shifted_start)
            
            if result:
                print(f"SUCCESS: Found slot with shifted time window ({shift_minutes:+d} minutes)")
                return _handle_successful_booking(result, meeting_request, new_meeting_priority, parsed_calendars, attendees, fallback_used="time_shift", shift_minutes=shift_minutes)
        
        # Fallback 4: Relax preference constraints (higher tolerance for violations)
        print(f"\nFallback 4: Relaxing preference constraints (allowing higher violation scores)")
        result = find_earliest_slot(parsed_calendars, attendees, duration_minutes, new_meeting_priority, 
                                  search_start_time=desired_start_time, max_preference_score=200)
        
        if result:
            print(f"SUCCESS: Found slot with relaxed preference constraints")
            return _handle_successful_booking(result, meeting_request, new_meeting_priority, parsed_calendars, attendees, fallback_used="relaxed_preferences")
        
        print("\n=== ALL FALLBACK STRATEGIES FAILED ===")
        
    except Exception as e:
        print(f"Error: Failed to find available slot. Details: {e}")
        return None

    print("\nFailure: No available slot could be found, even with fallback strategies.")
    return {
        'success': False,
        'meetings': [],
        'error': 'No available slot found after trying all fallback strategies',
        'fallbacks_attempted': ['shorter_duration', 'majority_attendees', 'time_shift', 'relaxed_preferences']
    }

def _handle_successful_booking(result, meeting_request, new_meeting_priority, parsed_calendars, attendees, fallback_used=None, **fallback_details):
    """
    Helper function to handle successful booking results and return JSON format.
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
    
    # Create list to store all meetings in JSON format
    all_meetings = []
    
    # Add the new meeting
    new_meeting_json = format_meeting_as_json(
        subject=meeting_request.get('Subject', 'Unknown'),
        start_time=slot[0],
        end_time=slot[1],
        email_content=meeting_request.get('EmailContent', ''),
        metadata={
            "priority": new_meeting_priority,
            "fallback_used": fallback_used,
            "newly_scheduled": True
        }
    )
    all_meetings.append(new_meeting_json)
    
    if to_reschedule:
        # Create attendees mapping for rescheduling
        attendees_map = {}
        for _, _, _, summary in to_reschedule:
            # Try to find original attendees from the meeting, default to all attendees
            attendees_map[summary] = attendees
        
        # Call improved requirewna function to handle rescheduling
        meeting_info = {
            'subject': meeting_request.get('Subject', 'Unknown'),
            'start_time': slot[0],
            'end_time': slot[1],
            'priority': new_meeting_priority
        }
        
        try:
            rescheduling_result = requirewna(to_reschedule, meeting_info, parsed_calendars, attendees_map)
            print(f"\nNOTE: This time requires {len(to_reschedule)} lower-priority meeting(s) to be rescheduled:")
            for _, _, p, s in to_reschedule:
                print(f"  - (P{p}) '{s}'")
            
            # Add rescheduled meetings to the output
            if rescheduling_result.get('rescheduling_successful') and rescheduling_result.get('meetings_to_reschedule'):
                all_meetings.extend(rescheduling_result['meetings_to_reschedule'])
            
            return {
                'success': True,
                'meetings': all_meetings,
                'rescheduling_required': True,
                'rescheduling_result': rescheduling_result,
                'fallback_used': fallback_used,
                'fallback_details': fallback_details
            }
        except Exception as e:
            print(f"Warning: Rescheduling failed. Details: {e}")
            return {
                'success': True,
                'meetings': all_meetings,
                'rescheduling_required': True,
                'rescheduling_result': None,
                'fallback_used': fallback_used,
                'fallback_details': fallback_details
            }
    else:
        print("\nThis is a free slot, no rescheduling needed.")
        return {
            'success': True,
            'meetings': all_meetings,
            'rescheduling_required': False,
            'fallback_used': fallback_used,
            'fallback_details': fallback_details
        }


def akshay_input_format(request_data):
    details,summary = extract_meeting_details_with_llm(
        request_data["EmailContent"], 
        request_data["Datetime"]
    )
    #print('LLM REsponse', details)
    
    start_date, end_date, duration_minutes = details['start_date'], details['end_date'], details['duration_minutes']
    meeting_duration = timedelta(minutes=duration_minutes)

    # 2. Determine the search window for the meeting
    from datetime import datetime
    start_dt = datetime.strptime(start_date, "%d-%m-%YT%H:%M:%S")
    end_dt = datetime.strptime(end_date, "%d-%m-%YT%H:%M:%S")
    
    new_input_format = request_data.copy()
    new_input_format["start time "] = start_dt.strftime("%d-%m-%YT%H:%M:%S")
    new_input_format["Duration of meeting"] =  duration_minutes
    new_input_format["Subject"] =  summary
    new_input_format["Priority"] =  details['priority']

    ist_tz = timezone(timedelta(hours=5, minutes=30))
    day_start_utc = start_dt.replace(tzinfo=ist_tz)
    day_end_utc = end_dt.replace(tzinfo=ist_tz)
    # day_end_utc = day_start_utc + timedelta(hours=24)
    
    all_emails = [request_data["From"]] + [p["email"] for p in request_data["Attendees"]]
    mappings = {'userone.amd@gmail.com': 'user1', 'usertwo.amd@gmail.com': 'user2', 'userthree.amd@gmail.com': 'user3'}
    
    personal_slots = {}
    for email in all_emails:
        calendar_events = retrive_calendar_events(
            email, 
            day_start_utc.isoformat(), 
            day_end_utc.isoformat()
        )
        personal_slots[mappings.get(email,'userk')] = calendar_events
        
    return new_input_format, personal_slots



def output_format_parser(input_request, output_request):
    from copy import deepcopy
    for event in output_request['meetings']:
        if(event["MetaData"].get('newly_scheduled', False)):
            proposed_start, proposed_end, duration_minutes, summary = event['EventStart'], event['EventEnd'], int(event['Duration_mins']), event['Subject']

    output_format = deepcopy(input_request)
    all_emails = [input_request["From"]] + [p["email"] for p in input_request["Attendees"]]

    events_list = {}
    for email in all_emails:
        events_list[email] = [{
            "StartTime": proposed_start,
            "EndTime": proposed_end,
            "NumAttendees": len(all_emails),
            "Attendees": all_emails,
            "Summary": summary
        }]

    timings_to_note = set()
    for event in output_request['meetings']:
        from datetime import datetime, time
        # Parse EventStart to a datetime object with timezone
        event_start = datetime.fromisoformat(event["EventStart"])
        # Get the timezone info
        tzinfo = event_start.tzinfo
        # Start of the day: 00:00:00
        full_start_time = datetime.combine(event_start.date(), time(0, 0, 0), tzinfo=tzinfo)
        # End of the day: 23:59:59
        full_end_time = datetime.combine(event_start.date(), time(23, 59, 59), tzinfo=tzinfo)
        timings_to_note.add((full_start_time, full_end_time))

    for email in all_emails:
        for day_start_utc, day_end_utc in timings_to_note:
            calendar_events = retrive_calendar_events(
                email, 
                day_start_utc.isoformat(), 
                day_end_utc.isoformat()
            )
            present_events = events_list[email]
            #print(present_events)
            present_events = present_events + calendar_events
            events_list[email] = present_events

    # print(events_list)
    output_format['Attendees'] = [{'email': email, 'events': events} 
                                  for email,events in events_list.items()]


    for meeting in output_request['meetings']:
        if(meeting['MetaData'].get('rescheduled',False)):
            for person in output_format['Attendees']:
                for i,event in enumerate(person['events']):
                    if(meeting['MetaData']['original_start'] == event['StartTime']):
                        person['events'][i]['StartTime'] = meeting['EventStart']
                        person['events'][i]['EndTime'] = meeting['EventEnd']
    
    output_format['EventStart'] = proposed_start #.isoformat()
    output_format['EventEnd'] = proposed_end #.isoformat()
    output_format['Duration_mins'] = duration_minutes
    output_format['metadata'] = {}
    output_format['Subject'] = summary

    return output_format



from typing_extensions import TypedDict
from typing import Dict

class State(TypedDict):
    user_request: Dict
    meeting_request_input: Dict
    user_calendars_input: Dict
    scheduled_meeting: Dict
    final_output: Dict

# %%
from langgraph.graph import StateGraph

builder = StateGraph(State)

def parsing_user_request(state: State):
    #print('HERE')
    MEETING_REQUEST_INPUT, USER_CALENDARS_INPUT = akshay_input_format(state['user_request'])
    return {"meeting_request_input": MEETING_REQUEST_INPUT, "user_calendars_input": USER_CALENDARS_INPUT}

# The second argument is optional
def meeting_scheduler(state: State):
    #print(state)
    scheduled_meeting = schedule_meeting_from_request(state['user_calendars_input'], state['meeting_request_input'])
    return {"scheduled_meeting": scheduled_meeting}

def convert_output(state: State):
    final_output=  output_format_parser(state["meeting_request_input"], state["scheduled_meeting"])
    return {"final_output": final_output}
    
builder.add_node(parsing_user_request)
builder.add_node(meeting_scheduler)
builder.add_node(convert_output)

from langgraph.graph import START, END

builder.add_edge(START, "parsing_user_request")
builder.add_edge("parsing_user_request", "meeting_scheduler")
builder.add_edge("meeting_scheduler", "convert_output")
builder.add_edge("convert_output", END)



# from langgraph.cache.memory import InMemoryCache
# from langgraph.types import CachePolicy


# #from IPython.display import Image, display

# # display(Image(graph.get_graph().draw_mermaid_png()))

# #request_thursday = {
#     "Request_id": "a2", "Datetime": "19-07-2025T12:34:55", "From": "userone.amd@gmail.com",
#     "Attendees": [{"email": "usertwo.amd@gmail.com"}, {"email": "userthree.amd@gmail.com"}],
#     "EmailContent": "Let's sync up on tommorow for half an hour."
# }

# #response = graph.invoke({
# #    "user_request": request_thursday
# #})


#print(json.dumps(response['final_output'],indent=2))