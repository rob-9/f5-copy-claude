# F5 API Security for AI Inference Endpoints

🔒 Secure AI model inference with enterprise-grade API protection using F5 Distributed Cloud Web App & API Protection (WAAP).

## Overview

This project demonstrates how to protect AI inference endpoints (LLM/vLLM) running on Red Hat OpenShift AI with F5 Distributed Cloud security features:

- **WAF Protection**: Block XSS attacks, injections, and other OWASP Top 10 threats
- **API Security**: OpenAPI schema validation, API discovery, and shadow API detection
- **Rate Limiting**: Per-endpoint, per-client request throttling
- **Bot Defense**: Protect against automated attacks
- **Sensitive Data Controls**: Detect and redact sensitive information

## Architecture

```
┌─────────────┐
│   User      │
└─────┬───────┘
      │
      ↓
┌─────────────────────────────────────┐
│  F5 Distributed Cloud (WAAP)        │
│  - WAF                               │
│  - API Security                      │
│  - Rate Limiting                     │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│  Streamlit UI (This Application)    │
│  - Chat Interface                    │
│  - RAG Integration                   │
│  - Configuration Management          │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│  LLaMA Stack Service                 │
│  - OpenAI-compatible API             │
│  - RAG Tool Integration              │
└─────────────┬───────────────────────┘
              │
    ┌─────────┼────────────┐
    │         │            │
    ↓         ↓            ↓
┌────────┐ ┌──────┐  ┌─────────┐
│ vLLM   │ │PGVec │  │Embedding│
│Service │ │ tor  │  │ Service │
└────────┘ └──────┘  └─────────┘
```

## Features

### Frontend (Streamlit UI)

- ✅ **Chat Interface**: Conversational AI with message history
- ✅ **Configuration Management**: Dynamic endpoint, model, and API key configuration
- ✅ **RAG Support**: Retrieval-Augmented Generation with vector databases
- ✅ **Document Upload**: PDF and GitHub repository ingestion
- ✅ **Debug Mode**: Detailed logging for troubleshooting
- ✅ **Security**: Input validation, sanitization, and XSS protection

### Security Features

- ✅ **WAF Protection**: XSS/injection blocking
- ✅ **API Schema Validation**: OpenAPI v3 specification enforcement
- ✅ **Shadow API Detection**: Block undocumented endpoints
- ✅ **Rate Limiting**: Configurable per-endpoint limits
- ✅ **Secure Deployment**: Non-root containers, security contexts

## Quick Start

### Prerequisites

- OpenShift 4.18+ cluster
- `oc` CLI (logged in to cluster)
- Helm 3.x
- F5 Distributed Cloud account (for full security features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/rob-9/f5-copy-claude.git
   cd f5-copy-claude
   ```

2. **Configure values** (optional)
   ```bash
   cd deploy
   cp f5-ai-security-values.yaml.example f5-ai-security-values.yaml
   # Edit f5-ai-security-values.yaml with your configuration
   ```

3. **Deploy**
   ```bash
   ./deploy.sh [namespace]
   ```
   Default namespace: `f5-ai-security`

4. **Access the application**
   ```bash
   oc get route -n f5-ai-security
   ```
   Open the displayed URL in your browser.

### Cleanup

```bash
cd deploy
./undeploy.sh [namespace]
```

## Configuration

### Environment Variables

The application supports the following environment variables (configured via Helm values):

| Variable | Description | Default |
|----------|-------------|---------|
| `DEFAULT_CHAT_ENDPOINT` | LLaMA Stack endpoint URL | `http://llamastack:8321/v1/openai/v1` |
| `DEFAULT_MODEL` | Default model ID | `remote-llm/RedHatAI/Llama-3.2-1B-Instruct-quantized.w8a8` |
| `DEFAULT_API_KEY` | API key for authentication | `dummy-key` |
| `LLAMA_STACK_ENDPOINT` | LLaMA Stack base URL | `http://llamastack:8321` |

### Helm Values

Key configuration options in `f5-ai-security-values.yaml`:

```yaml
# Image configuration
image:
  repository: quay.io/rh-ai-quickstart/f5-security-ui
  tag: latest

# Resources
resources:
  limits:
    cpu: 1000m
    memory: 1Gi

# Autoscaling
autoscaling:
  enabled: false
  maxReplicas: 5

# Security context
securityContext:
  runAsNonRoot: true
  runAsUser: 1001
```

## F5 Distributed Cloud Setup

For detailed F5 XC deployment instructions, see [docs/f5_xc_deployment.md](docs/f5_xc_deployment.md).

### Quick Setup

1. **Configure HugePages** (required for F5 XC)
   ```bash
   oc label node <node-name> node-role.kubernetes.io/worker-hp=
   oc apply -f deploy/hugepages-mcp.yaml
   oc apply -f deploy/hugepages-tuned-boottime.yaml
   ```

2. **Deploy F5 XC Site**
   ```bash
   # Edit ce_ocp_gpu-ai.yml with your site token
   oc create -f deploy/ce_ocp_gpu-ai.yml
   ```

3. **Configure F5 XC Console**
   - Approve site registration
   - Create Origin Pool for `llamastack` service
   - Create HTTP Load Balancer
   - Import OpenAPI specification (`deploy/openapi-swagger-v3-fixed2-version.json`)
   - Enable API Security and WAF
   - Configure rate limiting

## Security Use Cases

### 1. XSS Attack Protection

**Test**: Send a message with XSS payload
```
<script>alert("XSS")</script>
```

**Expected**: Request blocked by F5 WAF, security event logged

### 2. Shadow API Detection

**Test**: Access undocumented endpoint
```bash
curl https://your-endpoint/v1/version
```

**Expected**: `403 Forbidden` (endpoint not in OpenAPI spec)

### 3. Rate Limiting

**Test**: Send 11+ requests within 1 minute to rate-limited endpoint

**Expected**:
- Requests 1-10: `200 OK`
- Request 11+: `429 Too Many Requests`

## Development

### Project Structure

```
F5-copy/
├── frontend/                    # Streamlit application
│   ├── f5_security_ui/
│   │   ├── chat.py             # Main chat interface
│   │   ├── constants.py        # Configuration constants
│   │   ├── modules/
│   │   │   ├── api.py          # API client
│   │   │   └── utils.py        # Utility functions
│   │   └── pages/
│   │       └── upload.py       # Document upload page
│   ├── Containerfile           # Docker build file
│   └── requirements.txt        # Python dependencies
├── deploy/                     # Deployment configurations
│   ├── f5-ai-security/        # Helm chart
│   │   ├── Chart.yaml
│   │   ├── values.yaml
│   │   └── templates/
│   ├── deploy.sh              # Deployment script
│   ├── undeploy.sh            # Cleanup script
│   ├── openapi-swagger-v3-fixed2-version.json  # API spec
│   └── ce_ocp_gpu-ai.yml      # F5 XC config
├── docs/                      # Documentation
└── README.md                  # This file
```

### Building the Container Image

```bash
cd frontend
podman build -t f5-security-ui:latest -f Containerfile .
```

### Local Development

```bash
cd frontend
pip install -r requirements.txt
streamlit run f5_security_ui/chat.py
```

## Supported Models

| Model | Hardware | Purpose |
|-------|----------|---------|
| all-MiniLM-L6-v2 | CPU/GPU | Text embeddings |
| Llama-3.2-3B-Instruct | L4/HPU | Generation (small) |
| Llama-3.1-8B-Instruct | L4/HPU | Generation (medium) |
| Meta-Llama-3-70B-Instruct | A100x2 | Generation (large) |

## Performance

- **Chat Response Time**: < 5 seconds (excluding LLM inference)
- **Vector Search**: < 500ms
- **Concurrent Users**: 10+ simultaneous sessions
- **Document Size**: Up to 50MB per file

## Security Notes

⚠️ **Important Security Considerations**:

- Never commit API keys or tokens to version control
- Use Kubernetes Secrets for sensitive data in production
- Rotate credentials regularly
- Enable HTTPS/TLS for all external endpoints
- Review F5 XC security policies regularly
- Monitor security event logs

## Troubleshooting

### Application won't start

1. Check pod logs:
   ```bash
   oc logs -l app.kubernetes.io/name=f5-ai-security -n f5-ai-security
   ```

2. Verify resource availability:
   ```bash
   oc describe pod -l app.kubernetes.io/name=f5-ai-security -n f5-ai-security
   ```

### Can't connect to LLaMA Stack

1. Verify LLaMA Stack is running
2. Check endpoint URL in configuration
3. Test connectivity from within the pod:
   ```bash
   oc exec -it <pod-name> -- curl http://llamastack:8321/v1/models
   ```

### Rate limiting not working

1. Verify F5 XC Load Balancer configuration
2. Check rate limiting rules in F5 XC Console
3. Ensure requests are going through F5 XC (not direct to service)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is provided as-is for demonstration purposes.

## Resources

- [F5 Distributed Cloud Documentation](https://docs.cloud.f5.com/)
- [Red Hat OpenShift AI Documentation](https://docs.redhat.com/en/documentation/red_hat_openshift_ai)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [LLaMA Stack Documentation](https://llama-stack.readthedocs.io/)

## Contact

For questions or issues, please open an issue on GitHub.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
