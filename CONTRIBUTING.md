# Contributing Guidelines

Thank you for your interest in contributing to the BotBooked AMD MI300 GPU AI Scheduling Assistant! This document provides guidelines for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation Guidelines](#documentation-guidelines)
- [Submission Process](#submission-process)

## Code of Conduct

### Our Pledge
We are committed to providing a welcoming and inclusive environment for all contributors, regardless of background, experience level, or identity.

### Expected Behavior
- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior
- Harassment, discrimination, or offensive comments
- Personal attacks or trolling
- Publishing private information without permission
- Other conduct which could reasonably be considered inappropriate

## Getting Started

### Prerequisites
Before contributing, ensure you have:
- [ ] Access to AMD MI300 GPU environment
- [ ] Python 3.8+ installed
- [ ] ROCm drivers and vLLM library
- [ ] Jupyter Notebook environment
- [ ] Git knowledge for version control

### Setting Up Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/BotBooked_AMD_MI300_GPU.git
   cd BotBooked_AMD_MI300_GPU
   ```

2. **Create Development Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Install Dependencies**
   ```bash
   pip install vllm openai flask google-api-python-client langchain-openai
   ```

4. **Verify Setup**
   - Run `rocm-smi` to check GPU availability
   - Test basic functionality with existing notebooks

## Development Workflow

### 1. Issue Selection
- Browse open issues in the GitHub repository
- Comment on issues you'd like to work on
- Wait for assignment before starting work
- For new features, create an issue first to discuss

### 2. Development Process

#### For AI Agent Improvements
1. **Modify Logic**: Edit `Sample_AI_Agent.ipynb`
2. **Test Changes**: Use `TestCases.ipynb` to validate
3. **Performance Check**: Ensure <10 second latency requirement
4. **Integration Test**: Verify with complete system

#### For API Enhancements
1. **Update Service**: Modify `Submission.ipynb`
2. **Test Endpoints**: Validate REST API functionality
3. **Error Handling**: Ensure graceful error responses
4. **Documentation**: Update API documentation

#### For Calendar Features
1. **Update Integration**: Modify `Calendar_Event_Extraction.ipynb`
2. **Test Authentication**: Verify Google OAuth flow
3. **Error Scenarios**: Handle API failures gracefully
4. **Performance**: Optimize API call efficiency

### 3. Testing Requirements

#### Unit Testing
```python
# Example test structure
def test_email_parsing():
    agent = AI_AGENT(client, model_path)
    result = agent.parse_email("Schedule meeting tomorrow at 2 PM")
    assert "participants" in result
    assert "meeting_duration" in result
    assert "time_constraints" in result
```

#### Integration Testing
- Test complete workflow from JSON input to output
- Verify calendar integration with mock data
- Test error handling and edge cases

#### Performance Testing
- Measure end-to-end latency
- Test with concurrent requests
- Monitor GPU utilization

## Coding Standards

### Python Code Style
- Follow PEP 8 conventions
- Use meaningful variable and function names
- Add type hints where appropriate
- Include docstrings for functions and classes

#### Example Function Structure
```python
def parse_meeting_request(email_content: str) -> dict:
    """
    Parse email content to extract meeting details.
    
    Args:
        email_content (str): Raw email text content
        
    Returns:
        dict: Parsed meeting information containing participants,
              duration, and time constraints
              
    Raises:
        ValueError: If email content cannot be parsed
    """
    # Implementation here
    pass
```

### Jupyter Notebook Standards
- Clear cell organization and comments
- Meaningful markdown explanations
- Remove debugging print statements
- Clear output before committing
- Use consistent variable naming

### JSON Schema Compliance
- Ensure input/output JSON matches specified schemas
- Validate all required fields are present
- Handle optional fields gracefully
- Maintain backward compatibility

## Testing Requirements

### Test Coverage
- All new functions must include unit tests
- Integration tests for new features
- Performance tests for critical paths
- Error handling tests for edge cases

### Test Data
- Use sample data from `JSON_Samples/` directory
- Create realistic test scenarios
- Include edge cases and error conditions
- Protect sensitive information in tests

### Performance Benchmarks
```python
import time

def test_latency_requirement():
    start_time = time.time()
    result = your_meeting_assistant(test_input)
    end_time = time.time()
    
    latency = end_time - start_time
    assert latency < 10.0, f"Latency {latency}s exceeds 10s requirement"
```

## Documentation Guidelines

### Code Documentation
- Inline comments for complex logic
- Docstrings for all public functions
- README updates for new features
- Architecture documentation for system changes

### Notebook Documentation
- Clear markdown cells explaining each section
- Step-by-step instructions for setup
- Example usage with expected outputs
- Troubleshooting sections for common issues

### API Documentation
- Update input/output examples
- Document new endpoints
- Include error response examples
- Provide client integration examples

## Submission Process

### Pull Request Requirements

1. **Branch Naming**
   - Feature: `feature/description`
   - Bug fix: `bugfix/description`
   - Documentation: `docs/description`

2. **Commit Messages**
   ```
   feat: add natural language processing for meeting duration
   
   - Implement regex parsing for time expressions
   - Add support for relative time (e.g., "tomorrow", "next week")
   - Include unit tests for various time formats
   
   Fixes #123
   ```

3. **Pull Request Template**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Performance improvement
   
   ## Testing
   - [ ] Unit tests pass
   - [ ] Integration tests pass
   - [ ] Performance tests pass
   - [ ] Manual testing completed
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] Tests added/updated
   ```

### Review Process

1. **Automated Checks**
   - Code style validation
   - Test execution
   - Performance benchmarks
   - Security scanning

2. **Human Review**
   - Code quality assessment
   - Architecture compliance
   - Documentation completeness
   - Test coverage validation

3. **Approval Process**
   - At least one reviewer approval required
   - All automated checks must pass
   - No unresolved review comments
   - Clean merge history

## Quality Standards

### Performance Requirements
- [ ] End-to-end latency < 10 seconds
- [ ] GPU utilization optimized
- [ ] Memory usage within limits
- [ ] Concurrent request handling

### Reliability Requirements
- [ ] Error handling for all edge cases
- [ ] Graceful degradation for service failures
- [ ] Input validation and sanitization
- [ ] Output format compliance

### Maintainability Requirements
- [ ] Clear code structure and organization
- [ ] Comprehensive documentation
- [ ] Automated testing coverage
- [ ] Consistent coding style

## Common Issues and Solutions

### GPU Memory Issues
```python
# Monitor GPU memory usage
def check_gpu_memory():
    # Implementation to monitor and manage GPU memory
    pass
```

### vLLM Server Connection
```python
# Handle server connection errors
def connect_with_retry(base_url, max_retries=3):
    # Implementation with exponential backoff
    pass
```

### Calendar API Rate Limits
```python
# Implement rate limiting and retry logic
def calendar_api_call_with_backoff(func, *args, **kwargs):
    # Implementation with rate limiting
    pass
```

## Getting Help

### Resources
- **Documentation**: Check `REPOSITORY_GUIDE.md` and `ARCHITECTURE.md`
- **Examples**: Review existing notebooks and test cases
- **Issues**: Search existing GitHub issues
- **Discussions**: Use GitHub Discussions for questions

### Contact
- **Technical Questions**: Create GitHub issues with detailed descriptions
- **Feature Requests**: Use GitHub issues with feature request template
- **Bug Reports**: Include reproduction steps and environment details

## Recognition

Contributors will be recognized through:
- GitHub contributor acknowledgments
- Project documentation credits
- Hackathon leaderboards (for competition submissions)
- Community showcases for significant contributions

---

Thank you for contributing to the BotBooked AMD MI300 GPU project! Your contributions help advance AI-powered scheduling technology and benefit the entire community.