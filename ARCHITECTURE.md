# Architecture and Component Overview

## System Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 BotBooked AI Scheduling System                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────────┐  │
│  │   Client App    │    │   Flask API     │    │       AI Agent Layer       │  │
│  │                 │    │                 │    │                             │  │
│  │  • Web Client   │───▶│  POST /receive  │───▶│  • Email Parser            │  │
│  │  • Mobile App   │    │  Port: 5000     │    │  • Meeting Coordinator     │  │
│  │  • External API │    │                 │    │  • Conflict Resolver       │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────────┘  │
│           │                       │                           │                  │
│           │                       │                           ▼                  │
│           │                       │              ┌─────────────────────────────┐  │
│           │                       │              │     vLLM Inference Layer    │  │
│           │                       │              │                             │  │
│           │                       │              │  ┌─────────┐ ┌─────────────┐ │  │
│           │                       │              │  │DeepSeek │ │   LLaMA     │ │  │
│           │                       │              │  │Port:3000│ │  Port:4000  │ │  │
│           │                       │              │  └─────────┘ └─────────────┘ │  │
│           │                       │              └─────────────────────────────┘  │
│           │                       │                           │                  │
│           │                       │                           ▼                  │
│           │                       │              ┌─────────────────────────────┐  │
│           │                       └─────────────▶│      AMD MI300 GPU         │  │
│           │                                      │                             │  │
│           │                                      │  • ROCm Runtime            │  │
│           │                                      │  • GPU Memory Management   │  │
│           │                                      │  • Parallel Processing     │  │
│           │                                      └─────────────────────────────┘  │
│           │                                                   │                  │
│           ▼                                                   │                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                        External Services                                   │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐                           ┌─────────────────────────┐  │  │
│  │  │ Google Calendar │                           │    User Preferences     │  │  │
│  │  │                 │                           │                         │  │  │
│  │  │  • OAuth Auth   │◀─────────┬────────────────│  • Time Zones          │  │  │
│  │  │  • Event CRUD   │          │                │  • Meeting Patterns     │  │  │
│  │  │  • Availability │          │                │  • Priority Rules       │  │  │
│  │  └─────────────────┘          │                └─────────────────────────┘  │  │
│  └────────────────────────────────┼─────────────────────────────────────────────┘  │
│                                   │                                              │
│                                   ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                            Data Flow                                        │  │
│  │                                                                             │  │
│  │  Input JSON ──▶ AI Processing ──▶ Calendar Integration ──▶ Output JSON     │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Input Processing Layer

#### JSON API Interface
- **Input Format**: Structured meeting requests
- **Fields**: Request ID, DateTime, Attendees, Subject, Email Content
- **Validation**: Schema validation and data sanitization
- **Error Handling**: Graceful degradation for malformed requests

#### Request Processing Pipeline
```
Input JSON → Schema Validation → Email Parsing → Intent Extraction → Scheduling Logic
```

### 2. AI Agent Layer

#### Email Content Parser
- **Function**: Extract meeting details from natural language
- **Capabilities**:
  - Participant identification
  - Duration extraction
  - Time constraint parsing
  - Meeting type classification

#### Meeting Coordinator
- **Function**: Orchestrate scheduling decisions
- **Logic**:
  - Priority assessment
  - Attendee importance ranking
  - Optimal time slot selection
  - Alternative suggestion generation

#### Conflict Resolver
- **Function**: Handle scheduling conflicts intelligently
- **Strategies**:
  - Meeting rescheduling
  - Attendee prioritization
  - Alternative time suggestions
  - Automated conflict notifications

### 3. vLLM Inference Layer

#### Model Configuration

**DeepSeek Model Setup:**
```bash
Model: deepseek-llm-7b-chat
Memory Utilization: 90%
Max Model Length: 2048 tokens
Tensor Parallel Size: 1
Max Sequences: 128
Backend: Multi-processing
```

**LLaMA Model Setup:**
```bash
Model: Meta-Llama-3.1-8B-Instruct  
Memory Utilization: 30%
Max Model Length: 2048 tokens
Tensor Parallel Size: 1
Max Sequences: 128
Backend: Multi-processing
```

#### Performance Optimization
- **Batching**: Dynamic request batching for throughput
- **Caching**: Model state caching for repeated patterns
- **Memory Management**: Efficient GPU memory utilization
- **Load Balancing**: Request distribution across available resources

### 4. Calendar Integration Layer

#### Google Calendar API Interface
```python
class CalendarIntegration:
    def __init__(self, credentials_path):
        self.service = build('calendar', 'v3', credentials=credentials)
    
    def get_events(self, start_date, end_date):
        # Fetch events within date range
        
    def create_event(self, event_details):
        # Create new calendar event
        
    def check_availability(self, attendees, time_slot):
        # Check attendee availability
```

#### Event Management
- **Retrieval**: Fetch existing events and availability
- **Creation**: Schedule new meetings with proper invitations
- **Updates**: Modify existing events when conflicts arise
- **Notifications**: Send updates to attendees

### 5. AMD MI300 GPU Layer

#### Hardware Specifications
- **Architecture**: CDNA 3
- **Memory**: High-bandwidth memory (HBM)
- **Compute Units**: Multiple compute units for parallel processing
- **ROCm**: Open-source GPU computing platform

#### Resource Management
```python
# GPU utilization monitoring
def monitor_gpu_usage():
    return {
        "memory_used": get_gpu_memory_usage(),
        "utilization": get_gpu_utilization(),
        "temperature": get_gpu_temperature()
    }
```

## Data Flow Architecture

### Request Processing Flow

```
┌─────────────┐
│ Client App  │
└─────┬───────┘
      │ HTTP POST /receive
      │ Content-Type: application/json
      ▼
┌─────────────┐
│ Flask API   │
│ Port: 5000  │
└─────┬───────┘
      │ your_meeting_assistant(data)
      ▼
┌─────────────┐
│ AI Agent    │
│ Processing  │
└─────┬───────┘
      │ OpenAI API Call
      ▼
┌─────────────┐
│ vLLM Server │
│ Port: 3000  │
│    or       │
│ Port: 4000  │
└─────┬───────┘
      │ Model Inference
      ▼
┌─────────────┐
│ AMD MI300   │
│ GPU         │
└─────┬───────┘
      │ Processed Response
      ▼
┌─────────────┐
│ Calendar    │
│ Integration │
└─────┬───────┘
      │ Event Creation/Updates
      ▼
┌─────────────┐
│ Response    │
│ JSON        │
└─────────────┘
```

### Information Flow Between Components

#### 1. Input → AI Processing
- **Data**: Raw email content and attendee information
- **Processing**: Natural language understanding and intent extraction
- **Output**: Structured meeting requirements

#### 2. AI Processing → Calendar Integration
- **Data**: Meeting requirements and constraints
- **Processing**: Availability checking and conflict detection
- **Output**: Optimal scheduling recommendations

#### 3. Calendar Integration → Response Generation
- **Data**: Scheduled event details
- **Processing**: Response formatting and validation
- **Output**: Structured JSON response

## Performance Characteristics

### Latency Requirements
- **Target**: < 10 seconds end-to-end
- **Bottlenecks**: LLM inference time, Calendar API calls
- **Optimization**: Model caching, parallel processing, request batching

### Throughput Capabilities
- **Concurrent Requests**: Multiple requests via async processing
- **GPU Utilization**: Optimized batch processing
- **Memory Management**: Efficient resource allocation

### Scalability Considerations
- **Horizontal Scaling**: Multiple GPU instances
- **Load Balancing**: Request distribution strategies
- **Cache Management**: Intelligent caching for common patterns

## Security Architecture

### Authentication
- **Google OAuth**: Secure calendar access
- **API Keys**: Service-to-service authentication
- **Token Management**: Secure token storage and rotation

### Data Protection
- **Encryption**: Data in transit and at rest
- **Privacy**: Minimal data retention policies
- **Access Control**: Role-based permissions

### API Security
- **Rate Limiting**: Request throttling
- **Input Validation**: Sanitization and validation
- **Error Handling**: Secure error responses

## Monitoring and Observability

### System Metrics
```python
class SystemMonitor:
    def get_metrics(self):
        return {
            "api_latency": measure_api_response_time(),
            "gpu_utilization": get_gpu_metrics(),
            "calendar_api_calls": count_calendar_requests(),
            "error_rate": calculate_error_percentage(),
            "throughput": measure_requests_per_second()
        }
```

### Health Checks
- **Service Health**: API endpoint availability
- **Model Health**: LLM server responsiveness
- **Integration Health**: Calendar API connectivity
- **Resource Health**: GPU and memory utilization

### Logging Strategy
- **Request Logging**: Input/output tracking
- **Error Logging**: Detailed error information
- **Performance Logging**: Latency and throughput metrics
- **Audit Logging**: Security and access logs

---

This architecture overview provides a comprehensive understanding of how the BotBooked AI Scheduling System components interact and operate together to deliver intelligent meeting coordination capabilities.