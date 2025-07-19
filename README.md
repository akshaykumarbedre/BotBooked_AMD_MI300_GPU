# BotBooked AMD MI300 GPU - AI Scheduling Assistant

## 🚀 Quick Navigation

| **Getting Started** | **Documentation** | **Examples** |
|-------------------|------------------|--------------|
| [🏃 Quick Start Guide](./QUICK_START.md) | [📋 Repository Summary](./REPOSITORY_SUMMARY.md) | [📋 Test Cases](./TestCases.ipynb) |
| [📖 Complete Guide](./REPOSITORY_GUIDE.md) | [🏗️ Architecture Overview](./ARCHITECTURE.md) | [🤖 Sample AI Agent](./Sample_AI_Agent.ipynb) |
| [📝 API Reference](#inputs--outputs) | [🤝 Contributing Guidelines](./CONTRIBUTING.md) | [📅 Calendar Integration](./Calendar_Event_Extraction.ipynb) |
| [📚 Documentation Index](./DOCUMENTATION_INDEX.md) | [📚 Input/Output Formats](./Input_Output_Formats.ipynb) | [📊 Demo Implementation](./Demo/) |

## Overview

Welcome to the **BotBooked AMD MI300 GPU** repository - an advanced Agentic AI Scheduling Assistant built for the AI Hackathon! This project leverages AMD's cutting-edge MI300 GPU infrastructure to create an intelligent scheduling system that autonomously coordinates meetings, resolves conflicts, and optimizes calendars with minimal human intervention.

### 🎯 Mission
Create an AI assistant that eliminates the back-and-forth of meeting coordination by autonomously scheduling, rescheduling, and optimizing calendars using state-of-the-art LLM technology.

### ✨ Key Features

- **🧠 Autonomous Coordination**: AI initiates scheduling without human micromanagement
- **🔄 Dynamic Adaptability**: Handles last-minute changes and conflicting priorities  
- **💬 Natural Language Interaction**: Users can interact with AI using natural language ("Schedule a meeting on Tuesday")
- **⚡ High Performance**: Sub-10 second latency requirement
- **📅 Google Calendar Integration**: Seamless integration with existing calendar systems
- **🚀 AMD MI300 GPU Powered**: Leverages cutting-edge GPU infrastructure for optimal performance

### 🏆 Success Metrics

- **Autonomy**: Minimal human intervention needed
- **Accuracy**: Few scheduling errors or conflicts
- **User Experience**: Intuitive and time-saving interface
- **Performance**: Processing latency < 10 seconds

## 📁 Repository Structure

```
BotBooked_AMD_MI300_GPU/
├── 📖 Documentation
│   ├── README.md                     # This file
│   ├── REPOSITORY_GUIDE.md           # Comprehensive guide
│   ├── ARCHITECTURE.md               # System architecture
│   └── QUICK_START.md                # 5-minute setup
├── 💻 Core Implementation
│   ├── Sample_AI_Agent.ipynb         # AI agent example
│   ├── Submission.ipynb              # Flask API service
│   └── Calendar_Event_Extraction.ipynb # Google Calendar integration
├── 🔧 Model Setup
│   ├── vLLM_Inference_Servering_DeepSeek.ipynb
│   └── vLLM_Inference_Servering_LLaMA.ipynb
├── 📊 Testing & Examples
│   ├── TestCases.ipynb               # Test scenarios
│   ├── Input_Output_Formats.ipynb    # Data formats
│   └── JSON_Samples/                 # Sample data
└── 🎨 Assets & Demo
    ├── Demo/                         # Demo implementations
    └── assets/                       # Images and resources
```

#### Why Agentic AI? 
Traditional scheduling tools rely on rule-based automation or human input. Your solution should go further by: 
- Reasoning like a human assistant (e.g., prioritizing attendees, resolving conflicts).
- Acting independently (e.g., sending follow-ups, adjusting for time zones).
- Learning from user preferences (e.g., preferred times, recurring meetings). 

#### Key Features to Consider:
##### Your solution should aim to include: <br>
✅ Autonomous Coordination: The AI initiates scheduling without human micromanagement. <br>
✅ Dynamic Adaptability: Handles last-minute changes or conflicting priorities. <br>
✅ Natural Language Interaction: Users may converse with the AI (e.g., “Schedule a meeting on Tuesday”).  <br>
✅ Latency: (Time taken from Sending Input JSON & getting Output JSON) should be < 10 sec. <br>

#### Success Metrics: 
#### A winning solution will excel in: <br>
✅ Autonomy: Minimal human intervention needed.  <br>
✅ Accuracy: Few scheduling errors or conflicts. <br>
✅ User Experience: Intuitive and time-saving. <br>

#### Setup & Requirements:
- Tools/APIs Needed: LLM ( vLLM server running on MI300 GPU). 
- Calendar APIs (Google Calendar). 
- Framework – May use License free tools & packages 
- Development Environment: Python

----------------

### To access MI300 Instance, follow the steps as mentioned below :

<img width="809" height="857" alt="{E739B41B-9914-45A1-8413-778E28C7F3E6}" src="https://github.com/user-attachments/assets/3b9d68c7-f994-486b-8734-ff61648bb192" />


----------------

### Prerequisite : 

##### Run the below command in your Notebook Terminal to update the scripts. 
```
git clone https://github.com/AMD-AI-HACKATHON/AI-Scheduling-Assistant.git
cp -r AI-Scheduling-Assistant/* ./
```
-------------

### Extracting Google Calendar Events :
#### The Notebook demonstrates how to programmatically retrieve and process Google Calendar events for a given user and date range.
#### You will be provided with Google Auth Tokens to pull Google Calendar Events.

##### Key Steps:
- Authentication: Load user credentials from a token file.
- API Call: Fetch events between specified start/end dates using the Google Calendar API.
- Data Processing: Extract event details (start/end times, attendees) and structure them into a clean format.
- Output: Return a list of events with attendee counts and time slots.

#### Follow the notebook for example usage : [Calendar_Event_Extraction](https://github.com/AMD-AI-HACKATHON/AI-Scheduling-Assistant/blob/main/Calendar_Event_Extraction.ipynb)

----------------

### Setting-Up vLLM Server with Large Language Models : 

vLLM is an open-source library designed to deliver high throughput and low latency for large language model (LLM) inference. It optimizes text generation workloads by efficiently batching requests and making full use of GPU resources, empowering developers to manage complex tasks like code generation and large-scale conversational AI.

#### Start the vLLM server with DeepSeek LLM 7B Chat Model

Open a new tab in this Jypyter server, click on the terminal icon to open a new terminal, then copy the following command to launch the vLLM server:

```bash
HIP_VISIBLE_DEVICES=0 vllm serve /home/user/Models/deepseek-ai/deepseek-llm-7b-chat \
        --gpu-memory-utilization 0.9 \
        --swap-space 16 \
        --disable-log-requests \
        --dtype float16 \
        --max-model-len 2048 \
        --tensor-parallel-size 1 \
        --host 0.0.0.0 \
        --port 3000 \
        --num-scheduler-steps 10 \
        --max-num-seqs 128 \
        --max-num-batched-tokens 2048 \
        --max-model-len 2048 \
        --distributed-executor-backend "mp"
```
#### For setting up vLLM server with DeepSeek Model & usage, please follow : [vLLM_Inference_Servering_DeepSeek](https://github.com/AMD-AI-HACKATHON/AI-Scheduling-Assistant/blob/main/vLLM_Inference_Servering_DeepSeek.ipynb)

#### Start the vLLM server with Meta-Llama-3.1-8B-Instruct Model

Open a new tab in this Jypyter server, click on the terminal icon to open a new terminal, then copy the following command to launch the vLLM server:

```bash
HIP_VISIBLE_DEVICES=0 vllm serve /home/user/Models/meta-llama/Meta-Llama-3.1-8B-Instruct \
        --gpu-memory-utilization 0.3 \
        --swap-space 16 \
        --disable-log-requests \
        --dtype float16 \
        --max-model-len 2048 \
        --tensor-parallel-size 1 \
        --host 0.0.0.0 \
        --port 4000 \
        --num-scheduler-steps 10 \
        --max-num-seqs 128 \
        --max-num-batched-tokens 2048 \
        --max-model-len 2048 \
        --distributed-executor-backend "mp"
```

#### For setting up vLLM server with LLama Model & usage, please follow : [vLLM_Inference_Servering_LLaMA](https://gitenterprise.xilinx.com/asirra/AI-Scheduling-Assistant/blob/main/vLLM_Inference_Servering_LLaMA.ipynb)
----------------

### Setting-Up AI Agent :


#### Start the vLLM server with DeepSeek Model

Open a new tab in this Jypyter server, click on the terminal icon to open a new terminal, then copy the following command to launch the vLLM server:

```bash
HIP_VISIBLE_DEVICES=0 vllm serve /home/user/Models/deepseek-ai/deepseek-llm-7b-chat \
        --gpu-memory-utilization 0.9 \
        --swap-space 16 \
        --disable-log-requests \
        --dtype float16 \
        --max-model-len 2048 \
        --tensor-parallel-size 1 \
        --host 0.0.0.0 \
        --port 3000 \
        --num-scheduler-steps 10 \
        --max-num-seqs 128 \
        --max-num-batched-tokens 2048 \
        --max-model-len 2048 \
        --distributed-executor-backend "mp"
```

#### Sample AI Agent that parse Email Input & Output the Processed JSON
```
class AI_AGENT:
    def __init__(self, client, MODEL_PATH):
        self.base_url = BASE_URL
        self.model_path = MODEL_PATH

    def parse_email(self, email_text):
        response = client.chat.completions.create(
            model=self.model_path,
            temperature=0.0,
            messages=[{
                "role": "user",
                "content": f"""
                Yor are an Agent that helps in scheduling meetings.
                Your job is to extracts Email ID's and Meeting Duration.
                You should return :
                1. List of email id's of participants (comma-separated).
                2. Meeting duration in minutes.
                3. Time constraints (e.g., 'next week').
                If the List of email id's of participants are just names, then append @amd.com at the end and return. 
                Return as json with 'participants', 'time_constraints' & 'meeting_duration'.
                Stricty follow the instructions. Strictly return dict with participents email id's, time constraints & meeting duration in minutes only. 
                Don not add any other instrctions or information. 
                
                Email: {email_text}
                
                """
            }]
        )
        return json.loads(response.choices[0].message.content)
```


#### Follow the Notebook for setting-up an example AI Agent : [Sample_AI_Agent](https://github.com/AMD-AI-HACKATHON/AI-Scheduling-Assistant/blob/main/Sample_AI_Agent.ipynb)

The Notebook demonstrates how to create a simple AI Agent that uses vLLM & OpenAI API to communicate with LLM Model.

----------------

### Inputs & Outputs : 
#### Input JSON : 

The input to your code will be in JSON format in the below structure. 
```
{
    "Request_id": "6118b54f-907b-4451-8d48-dd13d76033a5",
    "Datetime": "19-07-2025T12:34:55",
    "Location": "IISc Bangalore",
    "From": "userone.amd@gmail.com",
    "Attendees": [
        {
            "email": "usertwo.amd@gmail.com"
        },
        {
            "email": "userthree.amd@gmail.com"
        }
    ],
    "Subject": "Agentic AI Project Status Update",
    "EmailContent": "Hi team, let's meet on Thursday for 30 minutes to discuss the status of Agentic AI Project."
}
```

#### Final Output JSON : 
Your Final Output JSON should follow below structure.  <br>
##### Note : This output will be graded for quallifying & scoring. 
```
{
    "Request_id": "6118b54f-907b-4451-8d48-dd13d76033a5",
    "Datetime": "19-07-2025T12:34:55",
    "Location": "IISc Bangalore",
    "From": "userone.amd@gmail.com",
    "Attendees": [
        {
            "email": "userone.amd@gmail.com",
            "events": [
                {
                    "StartTime": "2025-07-24T10:30:00+05:30",
                    "EndTime": "2025-07-24T11:00:00+05:30",
                    "NumAttendees": 3,
                    "Attendees": [
                        "userone.amd@gmail.com",
                        "usertwo.amd@gmail.com",
                        "userthree.amd@gmail.com"
                    ],
                    "Summary": "Agentic AI Project Status Update"
                }
            ]
        },
        {
            "email": "usertwo.amd@gmail.com",
            "events": [
                {
                    "StartTime": "2025-07-24T10:00:00+05:30",
                    "EndTime": "2025-07-24T10:30:00+05:30",
                    "NumAttendees": 3,
                    "Attendees": [
                        "userone.amd@gmail.com",
                        "usertwo.amd@gmail.com",
                        "userthree.amd@gmail.com"
                    ],
                    "Summary": "Team Meet"
                },
                {
                    "StartTime": "2025-07-24T10:30:00+05:30",
                    "EndTime": "2025-07-24T11:00:00+05:30",
                    "NumAttendees": 3,
                    "Attendees": [
                        "userone.amd@gmail.com",
                        "usertwo.amd@gmail.com",
                        "userthree.amd@gmail.com"
                    ],
                    "Summary": "Agentic AI Project Status Update"
                }
            ]
        },
        {
            "email": "userthree.amd@gmail.com",
            "events": [
                {
                    "StartTime": "2025-07-24T10:00:00+05:30",
                    "EndTime": "2025-07-24T10:30:00+05:30",
                    "NumAttendees": 3,
                    "Attendees": [
                        "userone.amd@gmail.com",
                        "usertwo.amd@gmail.com",
                        "userthree.amd@gmail.com"
                    ],
                    "Summary": "Team Meet"
                },
                {
                    "StartTime": "2025-07-24T13:00:00+05:30",
                    "EndTime": "2025-07-24T14:00:00+05:30",
                    "NumAttendees": 1,
                    "Attendees": [
                        "SELF"
                    ],
                    "Summary": "Lunch with Customers"
                },
                {
                    "StartTime": "2025-07-24T10:30:00+05:30",
                    "EndTime": "2025-07-24T11:00:00+05:30",
                    "NumAttendees": 3,
                    "Attendees": [
                        "userone.amd@gmail.com",
                        "usertwo.amd@gmail.com",
                        "userthree.amd@gmail.com"
                    ],
                    "Summary": "Agentic AI Project Status Update"
                }
            ]
        }
    ],
    "Subject": "Agentic AI Project Status Update",
    "EmailContent": "Hi team, let's meet on Thursday for 30 minutes to discuss the status of Agentic AI Project.",
    "EventStart": "2025-07-24T10:30:00+05:30",
    "EventEnd": "2025-07-24T11:00:00+05:30",
    "Duration_mins": "30",
    "MetaData": {}
}
```

## 🚀 Getting Started

### Option 1: Quick Start (5 minutes)
Follow the [**Quick Start Guide**](./QUICK_START.md) for a rapid setup and testing.

### Option 2: Comprehensive Setup
For detailed understanding, see the [**Complete Repository Guide**](./REPOSITORY_GUIDE.md).

### Option 3: Architecture Deep Dive
To understand system design, check the [**Architecture Overview**](./ARCHITECTURE.md).

## 🔧 Core Components

| Component | Purpose | Notebook |
|-----------|---------|----------|
| **AI Agent** | Natural language processing and scheduling logic | [Sample_AI_Agent.ipynb](./Sample_AI_Agent.ipynb) |
| **API Service** | REST API for processing meeting requests | [Submission.ipynb](./Submission.ipynb) |
| **Calendar Integration** | Google Calendar connectivity | [Calendar_Event_Extraction.ipynb](./Calendar_Event_Extraction.ipynb) |
| **vLLM Servers** | GPU-accelerated language model inference | [DeepSeek](./vLLM_Inference_Servering_DeepSeek.ipynb) / [LLaMA](./vLLM_Inference_Servering_LLaMA.ipynb) |

---

## 📚 Original Hackathon Documentation

*The content below contains the original hackathon instructions and detailed setup procedures.*

### Setup & Requirements:
- Tools/APIs Needed: LLM ( vLLM server running on MI300 GPU). 
- Calendar APIs (Google Calendar). 
- Framework – May use License free tools & packages 
- Development Environment: Python

----------------

### To access MI300 Instance, follow the steps as mentioned below :

<img width="809" height="857" alt="{E739B41B-9914-45A1-8413-778E28C7F3E6}" src="https://github.com/user-attachments/assets/3b9d68c7-f994-486b-8734-ff61648bb192" />


----------------

### Prerequisite : 

##### Run the below command in your Notebook Terminal to update the scripts. 
```
git clone https://github.com/AMD-AI-HACKATHON/AI-Scheduling-Assistant.git
cp -r AI-Scheduling-Assistant/* ./
```
-------------

### Extracting Google Calendar Events :
#### The Notebook demonstrates how to programmatically retrieve and process Google Calendar events for a given user and date range.
#### You will be provided with Google Auth Tokens to pull Google Calendar Events.

##### Key Steps:
- Authentication: Load user credentials from a token file.
- API Call: Fetch events between specified start/end dates using the Google Calendar API.
- Data Processing: Extract event details (start/end times, attendees) and structure them into a clean format.
- Output: Return a list of events with attendee counts and time slots.

#### Follow the notebook for example usage : [Calendar_Event_Extraction](https://github.com/AMD-AI-HACKATHON/AI-Scheduling-Assistant/blob/main/Calendar_Event_Extraction.ipynb)

----------------

### Setting-Up vLLM Server with Large Language Models : 

vLLM is an open-source library designed to deliver high throughput and low latency for large language model (LLM) inference. It optimizes text generation workloads by efficiently batching requests and making full use of GPU resources, empowering developers to manage complex tasks like code generation and large-scale conversational AI.

#### Start the vLLM server with DeepSeek LLM 7B Chat Model

Open a new tab in this Jypyter server, click on the terminal icon to open a new terminal, then copy the following command to launch the vLLM server:

```bash
HIP_VISIBLE_DEVICES=0 vllm serve /home/user/Models/deepseek-ai/deepseek-llm-7b-chat \
        --gpu-memory-utilization 0.9 \
        --swap-space 16 \
        --disable-log-requests \
        --dtype float16 \
        --max-model-len 2048 \
        --tensor-parallel-size 1 \
        --host 0.0.0.0 \
        --port 3000 \
        --num-scheduler-steps 10 \
        --max-num-seqs 128 \
        --max-num-batched-tokens 2048 \
        --max-model-len 2048 \
        --distributed-executor-backend "mp"
```
#### For setting up vLLM server with DeepSeek Model & usage, please follow : [vLLM_Inference_Servering_DeepSeek](https://github.com/AMD-AI-HACKATHON/AI-Scheduling-Assistant/blob/main/vLLM_Inference_Servering_DeepSeek.ipynb)

#### Start the vLLM server with Meta-Llama-3.1-8B-Instruct Model

Open a new tab in this Jypyter server, click on the terminal icon to open a new terminal, then copy the following command to launch the vLLM server:

```bash
HIP_VISIBLE_DEVICES=0 vllm serve /home/user/Models/meta-llama/Meta-Llama-3.1-8B-Instruct \
        --gpu-memory-utilization 0.3 \
        --swap-space 16 \
        --disable-log-requests \
        --dtype float16 \
        --max-model-len 2048 \
        --tensor-parallel-size 1 \
        --host 0.0.0.0 \
        --port 4000 \
        --num-scheduler-steps 10 \
        --max-num-seqs 128 \
        --max-num-batched-tokens 2048 \
        --max-model-len 2048 \
        --distributed-executor-backend "mp"
```

#### For setting up vLLM server with LLama Model & usage, please follow : [vLLM_Inference_Servering_LLaMA](https://gitenterprise.xilinx.com/asirra/AI-Scheduling-Assistant/blob/main/vLLM_Inference_Servering_LLaMA.ipynb)
----------------

### Setting-Up AI Agent :


#### Start the vLLM server with DeepSeek Model

Open a new tab in this Jypyter server, click on the terminal icon to open a new terminal, then copy the following command to launch the vLLM server:

```bash
HIP_VISIBLE_DEVICES=0 vllm serve /home/user/Models/deepseek-ai/deepseek-llm-7b-chat \
        --gpu-memory-utilization 0.9 \
        --swap-space 16 \
        --disable-log-requests \
        --dtype float16 \
        --max-model-len 2048 \
        --tensor-parallel-size 1 \
        --host 0.0.0.0 \
        --port 3000 \
        --num-scheduler-steps 10 \
        --max-num-seqs 128 \
        --max-num-batched-tokens 2048 \
        --max-model-len 2048 \
        --distributed-executor-backend "mp"
```

#### Sample AI Agent that parse Email Input & Output the Processed JSON
```
class AI_AGENT:
    def __init__(self, client, MODEL_PATH):
        self.base_url = BASE_URL
        self.model_path = MODEL_PATH

    def parse_email(self, email_text):
        response = client.chat.completions.create(
            model=self.model_path,
            temperature=0.0,
            messages=[{
                "role": "user",
                "content": f"""
                Yor are an Agent that helps in scheduling meetings.
                Your job is to extracts Email ID's and Meeting Duration.
                You should return :
                1. List of email id's of participants (comma-separated).
                2. Meeting duration in minutes.
                3. Time constraints (e.g., 'next week').
                If the List of email id's of participants are just names, then append @amd.com at the end and return. 
                Return as json with 'participants', 'time_constraints' & 'meeting_duration'.
                Stricty follow the instructions. Strictly return dict with participents email id's, time constraints & meeting duration in minutes only. 
                Don not add any other instrctions or information. 
                
                Email: {email_text}
                
                """
            }]
        )
        return json.loads(response.choices[0].message.content)
```


#### Follow the Notebook for setting-up an example AI Agent : [Sample_AI_Agent](https://github.com/AMD-AI-HACKATHON/AI-Scheduling-Assistant/blob/main/Sample_AI_Agent.ipynb)

The Notebook demonstrates how to create a simple AI Agent that uses vLLM & OpenAI API to communicate with LLM Model.

----------------

### Inputs & Outputs : 
#### Input JSON : 

The input to your code will be in JSON format in the below structure. 
```
{
    "Request_id": "6118b54f-907b-4451-8d48-dd13d76033a5",
    "Datetime": "19-07-2025T12:34:55",
    "Location": "IISc Bangalore",
    "From": "userone.amd@gmail.com",
    "Attendees": [
        {
            "email": "usertwo.amd@gmail.com"
        },
        {
            "email": "userthree.amd@gmail.com"
        }
    ],
    "Subject": "Agentic AI Project Status Update",
    "EmailContent": "Hi team, let's meet on Thursday for 30 minutes to discuss the status of Agentic AI Project."
}
```

#### Final Output JSON : 
Your Final Output JSON should follow below structure.  <br>
##### Note : This output will be graded for quallifying & scoring. 
```
{
    "Request_id": "6118b54f-907b-4451-8d48-dd13d76033a5",
    "Datetime": "19-07-2025T12:34:55",
    "Location": "IISc Bangalore",
    "From": "userone.amd@gmail.com",
    "Attendees": [
        {
            "email": "userone.amd@gmail.com",
            "events": [
                {
                    "StartTime": "2025-07-24T10:30:00+05:30",
                    "EndTime": "2025-07-24T11:00:00+05:30",
                    "NumAttendees": 3,
                    "Attendees": [
                        "userone.amd@gmail.com",
                        "usertwo.amd@gmail.com",
                        "userthree.amd@gmail.com"
                    ],
                    "Summary": "Agentic AI Project Status Update"
                }
            ]
        },
        {
            "email": "usertwo.amd@gmail.com",
            "events": [
                {
                    "StartTime": "2025-07-24T10:00:00+05:30",
                    "EndTime": "2025-07-24T10:30:00+05:30",
                    "NumAttendees": 3,
                    "Attendees": [
                        "userone.amd@gmail.com",
                        "usertwo.amd@gmail.com",
                        "userthree.amd@gmail.com"
                    ],
                    "Summary": "Team Meet"
                },
                {
                    "StartTime": "2025-07-24T10:30:00+05:30",
                    "EndTime": "2025-07-24T11:00:00+05:30",
                    "NumAttendees": 3,
                    "Attendees": [
                        "userone.amd@gmail.com",
                        "usertwo.amd@gmail.com",
                        "userthree.amd@gmail.com"
                    ],
                    "Summary": "Agentic AI Project Status Update"
                }
            ]
        },
        {
            "email": "userthree.amd@gmail.com",
            "events": [
                {
                    "StartTime": "2025-07-24T10:00:00+05:30",
                    "EndTime": "2025-07-24T10:30:00+05:30",
                    "NumAttendees": 3,
                    "Attendees": [
                        "userone.amd@gmail.com",
                        "usertwo.amd@gmail.com",
                        "userthree.amd@gmail.com"
                    ],
                    "Summary": "Team Meet"
                },
                {
                    "StartTime": "2025-07-24T13:00:00+05:30",
                    "EndTime": "2025-07-24T14:00:00+05:30",
                    "NumAttendees": 1,
                    "Attendees": [
                        "SELF"
                    ],
                    "Summary": "Lunch with Customers"
                },
                {
                    "StartTime": "2025-07-24T10:30:00+05:30",
                    "EndTime": "2025-07-24T11:00:00+05:30",
                    "NumAttendees": 3,
                    "Attendees": [
                        "userone.amd@gmail.com",
                        "usertwo.amd@gmail.com",
                        "userthree.amd@gmail.com"
                    ],
                    "Summary": "Agentic AI Project Status Update"
                }
            ]
        }
    ],
    "Subject": "Agentic AI Project Status Update",
    "EmailContent": "Hi team, let's meet on Thursday for 30 minutes to discuss the status of Agentic AI Project.",
    "EventStart": "2025-07-24T10:30:00+05:30",
    "EventEnd": "2025-07-24T11:00:00+05:30",
    "Duration_mins": "30",
    "MetaData": {}
}
```
---------
### Submission :

#### Please follow : [Submission Notebook](https://github.com/AMD-AI-HACKATHON/AI-Scheduling-Assistant/blob/main/Submission.ipynb)
##### ```def your_meeting_assistant( )``` takes Meeting request JSON as Input
##### ```your_meeting_assistant( )``` returns with New Fields.  
#### At the end of the Hackathon time ( at 2:00 P.M), you must execute this code
#### We will send JSONs at Port 5000 & will receive your AI Assistant Response
#### Make sure that your Output strictly follows the specified format. 

---------
### Validation : 
#### You can Send Input JSON from your local Laptop to MI300 GPU instance and can validate the response. 

```
import requests
SERVER_URL = "<YOUR IP ADDRESSS>"
INPUT_JSON_FILE = "JSON_Samples/Input_Request.json"
with open(INPUT_JSON_FILE) as f:
        input_json = json.load(f)
response = requests.post(SERVER_URL+":5000/receive", json=input_json, timeout=10)
print(response.json())
```


### Evaluation Criteria for Scoring & Ranking :
- Correctness of Output – Accuracy and precision of the results 
- Roundtrip Latency – Speed and efficiency of processing and response 
- Maintenance of GitHub Repository – Code organization, documentation, and commit hygiene 
- Creativeness in Approach – Innovation, originality, and problem-solving uniqueness 
- Scoring Based on Performance – Combined assessment of correctness, latency, repo quality, and creativity 
- Ranking Methodology – Comparative evaluation to determine the best-performing solution



#### Please follow : [Submission Notebook](https://github.com/AMD-AI-HACKATHON/AI-Scheduling-Assistant/blob/main/Submission.ipynb)
##### ```def your_meeting_assistant( )``` takes Meeting request JSON as Input
##### ```your_meeting_assistant( )``` returns with New Fields.  
#### At the end of the Hackathon time ( at 2:00 P.M), you must execute this code
#### We will send JSONs at Port 5000 & will receive your AI Assistant Response
#### Make sure that your Output strictly follows the specified format. 

---------
### Validation : 
#### You can Send Input JSON from your local Laptop to MI300 GPU instance and can validate the response. 

```
import requests
SERVER_URL = "<YOUR IP ADDRESSS>"
INPUT_JSON_FILE = "JSON_Samples/Input_Request.json"
with open(INPUT_JSON_FILE) as f:
        input_json = json.load(f)
response = requests.post(SERVER_URL+":5000/receive", json=input_json, timeout=10)
print(response.json())
```


### Evaluation Criteria for Scoring & Ranking :
- Correctness of Output – Accuracy and precision of the results 
- Roundtrip Latency – Speed and efficiency of processing and response 
- Maintenance of GitHub Repository – Code organization, documentation, and commit hygiene 
- Creativeness in Approach – Innovation, originality, and problem-solving uniqueness 
- Scoring Based on Performance – Combined assessment of correctness, latency, repo quality, and creativity 
- Ranking Methodology – Comparative evaluation to determine the best-performing solution


