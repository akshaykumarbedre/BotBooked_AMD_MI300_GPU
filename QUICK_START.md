# Quick Start Guide

This guide will help you get the BotBooked AI Scheduling Assistant up and running quickly.

## Prerequisites Checklist

- [ ] Access to AMD MI300 GPU instance
- [ ] Python 3.8+ installed
- [ ] Jupyter Notebook/Lab environment
- [ ] ROCm drivers installed
- [ ] Google Calendar API credentials (optional for basic testing)

## 5-Minute Setup

### Step 1: Clone and Setup Repository
```bash
# Clone the repository
git clone https://github.com/akshaykumarbedre/BotBooked_AMD_MI300_GPU.git
cd BotBooked_AMD_MI300_GPU

# Install required packages
pip install vllm openai flask google-api-python-client langchain-openai
```

### Step 2: Verify GPU Access
```bash
# Check GPU availability
rocm-smi

# You should see MI300 GPU information
```

### Step 3: Start vLLM Server (Choose One)

**Option A: DeepSeek Model (Recommended for beginners)**
```bash
HIP_VISIBLE_DEVICES=0 vllm serve /home/user/Models/deepseek-ai/deepseek-llm-7b-chat \
    --gpu-memory-utilization 0.9 \
    --host 0.0.0.0 \
    --port 3000 \
    --max-model-len 2048
```

**Option B: LLaMA Model**
```bash
HIP_VISIBLE_DEVICES=0 vllm serve /home/user/Models/meta-llama/Meta-Llama-3.1-8B-Instruct \
    --gpu-memory-utilization 0.3 \
    --host 0.0.0.0 \
    --port 4000 \
    --max-model-len 2048
```

### Step 4: Test Basic Functionality

Open `Sample_AI_Agent.ipynb` and run the cells to test basic AI functionality.

### Step 5: Start the Flask API

Open `Submission.ipynb` and run all cells to start the REST API service on port 5000.

### Step 6: Test End-to-End

```python
import requests
import json

# Test input
test_input = {
    "Request_id": "test-123",
    "Datetime": "2025-01-15T12:00:00",
    "Location": "Virtual",
    "From": "test@amd.com",
    "Attendees": [{"email": "user1@amd.com"}, {"email": "user2@amd.com"}],
    "Subject": "Quick Test Meeting",
    "EmailContent": "Let's have a 30-minute meeting tomorrow at 2 PM."
}

# Send request
response = requests.post("http://localhost:5000/receive", json=test_input, timeout=10)
print(response.json())
```

## What's Next?

1. **Explore Notebooks**: Check out the detailed implementation in each Jupyter notebook
2. **Google Calendar**: Set up Google Calendar integration using `Calendar_Event_Extraction.ipynb`
3. **Custom AI Agents**: Modify the AI agent logic in `Sample_AI_Agent.ipynb`
4. **Test Cases**: Run through various scenarios in `TestCases.ipynb`
5. **Performance**: Monitor and optimize using the guidelines in `REPOSITORY_GUIDE.md`

## Troubleshooting Quick Fixes

**vLLM server won't start:**
```bash
# Check if models exist
ls -la /home/user/Models/

# Check GPU memory
rocm-smi
```

**API not responding:**
```bash
# Check if Flask is running
curl http://localhost:5000/receive
```

**Import errors:**
```bash
# Install missing packages
pip install <missing-package>
```

## Getting Help

- **Detailed Documentation**: See `REPOSITORY_GUIDE.md`
- **Architecture Overview**: See `ARCHITECTURE.md`
- **Issues**: Create GitHub issues for bugs
- **Examples**: Check `JSON_Samples/` for input/output examples

## Development Workflow

1. **Modify AI Logic**: Edit `Sample_AI_Agent.ipynb`
2. **Test Changes**: Use `TestCases.ipynb`
3. **Update API**: Modify `Submission.ipynb`
4. **Validate**: Test with sample JSON files
5. **Deploy**: Run the complete system

---

*This quick start guide gets you running in under 5 minutes. For detailed information, refer to the comprehensive documentation files.*