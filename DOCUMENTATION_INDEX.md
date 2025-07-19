# Documentation Index

Welcome to the BotBooked AMD MI300 GPU repository documentation! This index helps you navigate through all available documentation.

## 📋 Documentation Overview

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [**README.md**](./README.md) | Main project overview and hackathon instructions | Start here for project introduction |
| [**QUICK_START.md**](./QUICK_START.md) | 5-minute setup guide | When you want to get running quickly |
| [**REPOSITORY_GUIDE.md**](./REPOSITORY_GUIDE.md) | Comprehensive project documentation | For complete understanding of the system |
| [**ARCHITECTURE.md**](./ARCHITECTURE.md) | System design and component interactions | To understand how components work together |
| [**CONTRIBUTING.md**](./CONTRIBUTING.md) | Development and contribution guidelines | When you want to contribute to the project |

## 🎯 User Journey

### New Users (First Time)
1. Start with [README.md](./README.md) - Get project overview
2. Follow [QUICK_START.md](./QUICK_START.md) - Get system running
3. Explore [Sample_AI_Agent.ipynb](./Sample_AI_Agent.ipynb) - Understand AI implementation
4. Test with [JSON_Samples/](./JSON_Samples/) - Validate functionality

### Developers (Contributing)
1. Read [REPOSITORY_GUIDE.md](./REPOSITORY_GUIDE.md) - Understand complete system
2. Study [ARCHITECTURE.md](./ARCHITECTURE.md) - Learn system design
3. Follow [CONTRIBUTING.md](./CONTRIBUTING.md) - Development guidelines
4. Review [TestCases.ipynb](./TestCases.ipynb) - Testing strategies

### System Administrators (Deployment)
1. Check [REPOSITORY_GUIDE.md](./REPOSITORY_GUIDE.md) - Setup requirements
2. Review [ARCHITECTURE.md](./ARCHITECTURE.md) - Performance considerations
3. Use [vLLM_Inference_Servering_*.ipynb](./vLLM_Inference_Servering_DeepSeek.ipynb) - Model deployment

### Researchers (Understanding)
1. Start with [ARCHITECTURE.md](./ARCHITECTURE.md) - System design
2. Explore [Sample_AI_Agent.ipynb](./Sample_AI_Agent.ipynb) - AI implementation
3. Review [TestCases.ipynb](./TestCases.ipynb) - Performance benchmarks
4. Study [Calendar_Event_Extraction.ipynb](./Calendar_Event_Extraction.ipynb) - Integration patterns

## 📚 Code Documentation

### Core Implementation Files
- [**Sample_AI_Agent.ipynb**](./Sample_AI_Agent.ipynb) - AI agent implementation with OpenAI API
- [**Submission.ipynb**](./Submission.ipynb) - Flask REST API service
- [**Calendar_Event_Extraction.ipynb**](./Calendar_Event_Extraction.ipynb) - Google Calendar integration

### Model Setup Files
- [**vLLM_Inference_Servering_DeepSeek.ipynb**](./vLLM_Inference_Servering_DeepSeek.ipynb) - DeepSeek model configuration
- [**vLLM_Inference_Servering_LLaMA.ipynb**](./vLLM_Inference_Servering_LLaMA.ipynb) - LLaMA model configuration

### Testing and Examples
- [**TestCases.ipynb**](./TestCases.ipynb) - Comprehensive test scenarios
- [**Input_Output_Formats.ipynb**](./Input_Output_Formats.ipynb) - API format documentation
- [**JSON_Samples/**](./JSON_Samples/) - Sample input/output data

## 🔍 Quick Reference

### Common Commands
```bash
# Check GPU status
rocm-smi

# Start DeepSeek model
HIP_VISIBLE_DEVICES=0 vllm serve /home/user/Models/deepseek-ai/deepseek-llm-7b-chat --port 3000

# Start LLaMA model  
HIP_VISIBLE_DEVICES=0 vllm serve /home/user/Models/meta-llama/Meta-Llama-3.1-8B-Instruct --port 4000

# Test API endpoint
curl -X POST http://localhost:5000/receive -H "Content-Type: application/json" -d @JSON_Samples/Input_Request.json
```

### Key Concepts
- **Agentic AI**: Autonomous AI that acts independently to achieve goals
- **vLLM**: High-performance LLM inference library optimized for GPUs
- **MI300 GPU**: AMD's advanced GPU architecture for AI workloads
- **Calendar Integration**: Google Calendar API for scheduling functionality

### Performance Targets
- **Latency**: < 10 seconds end-to-end processing
- **Accuracy**: Minimal scheduling conflicts and errors
- **Autonomy**: Minimal human intervention required
- **Throughput**: Support for concurrent scheduling requests

## 🆘 Troubleshooting Quick Links

### Common Issues
| Problem | Solution Document | Section |
|---------|------------------|---------|
| vLLM server won't start | [REPOSITORY_GUIDE.md](./REPOSITORY_GUIDE.md) | Troubleshooting |
| GPU not detected | [QUICK_START.md](./QUICK_START.md) | Step 2 |
| Calendar API errors | [REPOSITORY_GUIDE.md](./REPOSITORY_GUIDE.md) | Google Calendar Setup |
| Performance issues | [ARCHITECTURE.md](./ARCHITECTURE.md) | Performance Characteristics |
| JSON format errors | [Input_Output_Formats.ipynb](./Input_Output_Formats.ipynb) | Format Examples |

### Support Resources
- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: Comprehensive guides in this repository
- **Sample Code**: Working examples in Jupyter notebooks
- **Test Cases**: Validation scenarios and expected outputs

## 📈 Evaluation Criteria

As outlined in the hackathon requirements, submissions are evaluated on:
1. **Correctness**: Accuracy and precision of scheduling results
2. **Performance**: Speed and efficiency (< 10 second latency)
3. **Repository Quality**: Code organization and documentation
4. **Innovation**: Creative approaches to scheduling challenges

## 🤝 Contributing

Ready to contribute? Follow this path:
1. Read [CONTRIBUTING.md](./CONTRIBUTING.md) - Guidelines and standards
2. Check open issues on GitHub
3. Fork the repository and create a feature branch
4. Follow the development workflow
5. Submit a pull request with comprehensive testing

---

*This index provides a roadmap through all documentation. Choose the appropriate document based on your role and current needs.*