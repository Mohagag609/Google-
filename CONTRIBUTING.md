# Contributing to Musharaka Pro

Thank you for your interest in contributing to Musharaka Pro! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Git
- Basic knowledge of Flask and SQLAlchemy

### Setup Development Environment
```bash
# Clone the repository
git clone https://github.com/yourusername/musharaka-pro.git
cd musharaka-pro

# Install dependencies
make install

# Run the application
make run

# Run tests
make test
```

## 📋 Development Workflow

### 1. Fork and Clone
```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/yourusername/musharaka-pro.git
cd musharaka-pro

# Add upstream remote
git remote add upstream https://github.com/original/musharaka-pro.git
```

### 2. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 3. Make Changes
- Write clean, readable code
- Follow existing code style
- Add comments for complex logic
- Update documentation if needed

### 4. Test Your Changes
```bash
# Run tests
make test

# Check health
make health

# Test locally
make run
```

### 5. Commit Changes
```bash
git add .
git commit -m "feat: add new feature description"
```

### 6. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
# Create PR on GitHub
```

## 📝 Code Style

### Python
- Follow PEP 8
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions small and focused

### Example
```python
def calculate_stage_cost(stage_id: str) -> Dict[str, Decimal]:
    """
    Calculate total cost for a stage including expenses and material costs.
    
    Args:
        stage_id: The ID of the stage
        
    Returns:
        Dictionary with expenses, materials, and total cost
    """
    # Implementation here
    pass
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
make test

# Run specific test
python3 test_deployment.py

# Health check
make health
```

### Writing Tests
- Test all new functionality
- Include edge cases
- Test error conditions
- Ensure tests are deterministic

## 📚 Documentation

### Code Documentation
- Add docstrings to all functions
- Include type hints
- Explain complex business logic
- Update README if needed

### API Documentation
- Document new endpoints
- Include request/response examples
- Update API documentation

## 🐛 Bug Reports

### Before Reporting
1. Check existing issues
2. Try latest version
3. Test with minimal reproduction

### Bug Report Template
```markdown
**Bug Description**
Brief description of the bug

**Steps to Reproduce**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: 
- Python version:
- Flask version:
- Database:

**Additional Context**
Any other relevant information
```

## ✨ Feature Requests

### Before Requesting
1. Check existing issues
2. Consider if it fits project scope
3. Think about implementation

### Feature Request Template
```markdown
**Feature Description**
Brief description of the feature

**Use Case**
Why is this feature needed?

**Proposed Solution**
How should it work?

**Alternatives Considered**
Other approaches considered

**Additional Context**
Any other relevant information
```

## 🔧 Development Guidelines

### Database Changes
- Always create migrations
- Test with sample data
- Consider backward compatibility
- Update models documentation

### API Changes
- Maintain backward compatibility
- Version APIs if breaking changes
- Update documentation
- Test all endpoints

### Security
- Never commit secrets
- Validate all inputs
- Use parameterized queries
- Follow security best practices

## 📦 Release Process

### Version Numbering
- Major.Minor.Patch (e.g., 1.2.3)
- Major: Breaking changes
- Minor: New features
- Patch: Bug fixes

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped
- [ ] Tagged in git
- [ ] Deployed to staging
- [ ] Deployed to production

## 🤝 Community Guidelines

### Be Respectful
- Use welcoming language
- Be respectful of differing viewpoints
- Accept constructive criticism
- Focus on what's best for the community

### Communication
- Use clear, concise language
- Provide context for questions
- Be patient with newcomers
- Help others learn

## 📞 Getting Help

### Resources
- 📖 Documentation: README.md
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions
- 📧 Email: support@musharaka-pro.com

### Questions
- Check existing issues first
- Provide clear problem description
- Include relevant code snippets
- Share error messages

## 🏆 Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation
- GitHub contributors list

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Musharaka Pro! 🎉