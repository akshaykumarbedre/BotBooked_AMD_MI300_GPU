# BotBooked AMD MI300 GPU - Complete Repository Guide

## Table of Contents
- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [Architecture](#architecture)
- [Components](#components)
- [Setup and Installation](#setup-and-installation)
- [Usage Guide](#usage-guide)
- [API Reference](#api-reference)
- [Development Workflow](#development-workflow)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)

## Overview

The **BotBooked AMD MI300 GPU** repository is a comprehensive AI-powered scheduling assistant built for the Agentic AI Scheduling Assistant Hackathon. This project leverages AMD's MI300 GPU infrastructure to create an autonomous scheduling system that can intelligently coordinate meetings, resolve conflicts, and optimize calendars with minimal human intervention.

### Key Features
- **Autonomous Coordination**: AI initiates scheduling without human micromanagement
- **Dynamic Adaptability**: Handles last-minute changes and conflicting priorities
- **Natural Language Processing**: Users can interact with AI using natural language
- **High Performance**: Sub-10 second latency for processing requests
- **Google Calendar Integration**: Seamless integration with existing calendar systems
- **Multi-Model Support**: Compatible with DeepSeek and LLaMA models

### Success Metrics
- **Autonomy**: Minimal human intervention required
- **Accuracy**: Few scheduling errors or conflicts
- **User Experience**: Intuitive and time-saving interface
- **Performance**: Processing latency < 10 seconds

## Repository Structure

```
BotBooked_AMD_MI300_GPU/
├── README.md                              # Main project documentation
├── REPOSITORY_GUIDE.md                    # This comprehensive guide
├── .gitignore                            # Git ignore rules
├── AI-Scheduling-Assistant/              # Core project directory
├── assets/                               # Project assets and images
│   ├── ocr.gif
│   ├── rocm-smi.png
│   └── together_we_advance_.png
├── backup/                               # Backup files
├── Demo/                                 # Demo implementations
│   └── LLM_server_langchain-Copy1.ipynb
├── JSON_Samples/                         # Sample JSON files
│   ├── Input_Request.json               # Sample input format
│   └── Output_Event.json                # Sample output format
├── Calendar_Event_Extraction.ipynb      # Google Calendar integration
├── Input_Output_Formats.ipynb           # Data format documentation
├── Sample_AI_Agent.ipynb                # Example AI agent implementation
├── Submission.ipynb                     # Final submission template
├── TestCases.ipynb                      # Test scenarios and cases
├── Sai_LangGraph.ipynb                  # LangGraph implementation
├── vLLM_Inference_Servering_DeepSeek.ipynb  # DeepSeek model setup
└── vLLM_Inference_Servering_LLaMA.ipynb     # LLaMA model setup
```

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │    │   AI Agent      │    │  AMD MI300 GPU  │
│   (JSON API)    │───▶│   Processing    │───▶│   vLLM Server   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │ Google Calendar │              │
         └──────────────│   Integration   │◀─────────────┘
                        └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ Scheduled Event │
                        │   (JSON API)    │
                        └─────────────────┘
```

### Component Interaction Flow

1. **Input Processing**: Meeting requests arrive as JSON via REST API
2. **AI Analysis**: vLLM processes natural language content to extract scheduling requirements
3. **Calendar Integration**: Google Calendar API fetches existing events and availability
4. **Conflict Resolution**: AI agent identifies optimal time slots and resolves conflicts
5. **Event Creation**: New events are scheduled and attendees are notified
6. **Response Generation**: Structured JSON response with event details

## Components

### Core Components

#### 1. AI Agent (`Sample_AI_Agent.ipynb`)
- **Purpose**: Central AI processing unit that handles meeting request analysis
- **Functionality**: 
  - Parses email content using natural language processing
  - Extracts participant emails, duration, and time constraints
  - Makes intelligent scheduling decisions
- **Technology**: OpenAI-compatible API with vLLM backend

#### 2. vLLM Inference Servers
- **DeepSeek Implementation** (`vLLM_Inference_Servering_DeepSeek.ipynb`)
  - Model: deepseek-llm-7b-chat
  - Port: 3000
  - GPU Memory: 90% utilization
  
- **LLaMA Implementation** (`vLLM_Inference_Servering_LLaMA.ipynb`)
  - Model: Meta-Llama-3.1-8B-Instruct
  - Port: 4000
  - GPU Memory: 30% utilization

#### 3. Calendar Integration (`Calendar_Event_Extraction.ipynb`)
- **Purpose**: Interface with Google Calendar API
- **Functionality**:
  - Authenticate users via OAuth tokens
  - Fetch existing events within date ranges
  - Extract attendee information and time slots
  - Process availability data

#### 4. Web Service (`Submission.ipynb`)
- **Purpose**: Flask-based REST API for receiving and processing requests
- **Endpoints**:
  - `POST /receive`: Accepts meeting request JSON
- **Port**: 5000

### Supporting Components

#### 5. Test Framework (`TestCases.ipynb`)
- Comprehensive test scenarios
- Validation of different scheduling conflicts
- Performance benchmarking

#### 6. LangGraph Implementation (`Sai_LangGraph.ipynb`)
- Advanced workflow orchestration
- Multi-step AI agent processing
- Enhanced decision-making capabilities

#### 7. Format Documentation (`Input_Output_Formats.ipynb`)
- Detailed JSON schema specifications
- Input/output format examples
- API contract definitions

## Setup and Installation

### Prerequisites

1. **Hardware Requirements**:
   - Access to AMD MI300 GPU instance
   - Minimum 16GB GPU memory
   - ROCm-compatible environment

2. **Software Requirements**:
   - Python 3.8+
   - Jupyter Notebook/Lab
   - ROCm drivers
   - vLLM library
   - Required Python packages (see individual notebooks)

### Installation Steps

#### 1. Repository Setup
```bash
# Clone the repository
git clone https://github.com/akshaykumarbedre/BotBooked_AMD_MI300_GPU.git
cd BotBooked_AMD_MI300_GPU

# Update with latest hackathon materials (if needed)
git clone https://github.com/AMD-AI-HACKATHON/AI-Scheduling-Assistant.git
cp -r AI-Scheduling-Assistant/* ./
```

#### 2. Environment Configuration
```bash
# Install required packages
pip install vllm openai flask google-api-python-client langchain-openai
```

#### 3. GPU Setup
```bash
# Check GPU availability
rocm-smi

# Set GPU visibility
export HIP_VISIBLE_DEVICES=0
```

#### 4. Model Setup
Models are pre-installed on MI300 instances:
- DeepSeek: `/home/user/Models/deepseek-ai/deepseek-llm-7b-chat`
- LLaMA: `/home/user/Models/meta-llama/Meta-Llama-3.1-8B-Instruct`

### Google Calendar Setup

1. **Authentication**:
   - Obtain Google Calendar API credentials
   - Place token files in appropriate directories
   - Configure OAuth scope for calendar access

2. **API Configuration**:
   - Enable Google Calendar API in Google Cloud Console
   - Set up service account or OAuth2 credentials
   - Configure calendar permissions

## Usage Guide

### Starting the System

#### 1. Launch vLLM Server
Choose one of the following models:

**DeepSeek Model:**
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
    --distributed-executor-backend "mp"
```

**LLaMA Model:**
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
    --distributed-executor-backend "mp"
```

#### 2. Start the Flask Service
Run the submission notebook to start the REST API service on port 5000.

#### 3. Test the System
```python
import requests
import json

# Test with sample input
SERVER_URL = "<YOUR_IP_ADDRESS>"
INPUT_JSON_FILE = "JSON_Samples/Input_Request.json"

with open(INPUT_JSON_FILE) as f:
    input_json = json.load(f)

response = requests.post(SERVER_URL + ":5000/receive", json=input_json, timeout=10)
print(response.json())
```

### Example Workflow

1. **Input**: Meeting request arrives as JSON
2. **Processing**: AI agent analyzes the request
3. **Calendar Check**: System fetches existing events
4. **Scheduling**: AI finds optimal time slot
5. **Output**: Structured response with event details

## API Reference

### Input Format

```json
{
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
```

### Output Format

```json
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
                    "Attendees": ["userone.amd@gmail.com", "usertwo.amd@gmail.com", "userthree.amd@gmail.com"],
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

### API Endpoints

#### POST /receive
- **Purpose**: Process meeting requests
- **Input**: JSON meeting request
- **Output**: JSON with scheduled event details
- **Timeout**: 10 seconds maximum

## Development Workflow

### 1. Development Environment
- Use Jupyter notebooks for interactive development
- Test components individually before integration
- Monitor GPU utilization with `rocm-smi`

### 2. Testing Approach
- Unit tests for individual components
- Integration tests for end-to-end workflows
- Performance tests for latency requirements
- Load tests for concurrent requests

### 3. Debugging
- Check vLLM server logs for model issues
- Verify Google Calendar API authentication
- Monitor network connectivity and timeouts
- Use GPU monitoring tools for resource usage

## Contributing

### Code Style
- Follow Python PEP 8 conventions
- Use meaningful variable and function names
- Add docstrings for functions and classes
- Comment complex logic and algorithms

### Development Process
1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit pull request with detailed description
5. Address review feedback

### Testing Requirements
- All new features must include tests
- Maintain test coverage above 80%
- Performance tests for critical paths
- Integration tests for API endpoints

### Documentation
- Update relevant notebooks with changes
- Add examples for new features
- Update API documentation
- Include performance benchmarks

## Troubleshooting

### Common Issues

#### 1. vLLM Server Issues
```bash
# Check GPU availability
rocm-smi

# Verify model path
ls -la /home/user/Models/

# Check server logs
tail -f /var/log/vllm.log
```

#### 2. Google Calendar API Issues
- Verify OAuth token validity
- Check API quota limits
- Confirm calendar permissions
- Test with simple API calls

#### 3. Performance Issues
- Monitor GPU memory usage
- Check network latency
- Optimize batch sizes
- Profile code bottlenecks

#### 4. JSON Format Errors
- Validate input JSON schema
- Check date/time formats
- Verify email address formats
- Test with sample data

### Support Resources
- AMD ROCm Documentation
- vLLM Official Documentation
- Google Calendar API Reference
- OpenAI API Documentation

### Contact Information
For technical support and questions:
- Repository Issues: GitHub Issues section
- Documentation: This guide and inline comments
- Community: AMD AI Hackathon Discord/Forums

---

*This guide provides comprehensive coverage of the BotBooked AMD MI300 GPU repository. For specific implementation details, refer to the individual Jupyter notebooks and code examples.*