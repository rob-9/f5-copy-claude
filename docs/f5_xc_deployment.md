# F5 Distributed Cloud Deployment Guide

This guide provides detailed instructions for deploying and configuring F5 Distributed Cloud (XC) to protect AI inference endpoints.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [HugePages Configuration](#hugepages-configuration)
4. [F5 XC Site Deployment](#f5-xc-site-deployment)
5. [F5 XC Console Configuration](#f5-xc-console-configuration)
6. [Security Policy Configuration](#security-policy-configuration)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

## Overview

F5 Distributed Cloud provides comprehensive API security for your AI inference endpoints:

- **Web Application Firewall (WAF)**: Protects against XSS, injection, and OWASP Top 10 threats
- **API Security**: Schema validation, API discovery, shadow API detection
- **Rate Limiting**: Per-endpoint and per-client request throttling
- **Bot Defense**: Protection against automated attacks
- **DDoS Protection**: Mitigates volumetric attacks

## Prerequisites

Before deploying F5 XC, ensure you have:

- ✅ F5 Distributed Cloud account (sign up at [F5 Cloud Console](https://console.ves.volterra.io/))
- ✅ OpenShift cluster 4.18+ with admin access
- ✅ At least one worker node with 8GB+ RAM
- ✅ Cluster connectivity to F5 Cloud (outbound HTTPS)
- ✅ Site registration token from F5 XC Console

## HugePages Configuration

F5 XC requires HugePages for kernel memory management. Configure this before deploying the site.

### Step 1: Label Worker Nodes

Select one or more worker nodes for F5 XC:

```bash
# List worker nodes
oc get nodes -l node-role.kubernetes.io/worker=

# Label a node for HugePages
oc label node <node-name> node-role.kubernetes.io/worker-hp=
```

### Step 2: Create MachineConfigPool

Apply the HugePages MachineConfigPool:

```bash
oc apply -f deploy/hugepages-mcp.yaml
```

This creates a new worker pool `worker-hp` for nodes with HugePages.

### Step 3: Apply Tuned Profile

Configure HugePages kernel parameters:

```bash
oc apply -f deploy/hugepages-tuned-boottime.yaml
```

This sets up:
- `hugepagesz=2M`: 2MB huge page size
- `hugepages=256`: 256 huge pages (512MB total)

### Step 4: Wait for Configuration

```bash
# Watch MachineConfigPool status
oc get mcp worker-hp -w

# Wait for UPDATED=True and UPDATING=False
```

This may take 10-15 minutes as nodes reboot with new kernel parameters.

### Step 5: Verify HugePages

```bash
# Check HugePages on the node
oc debug node/<node-name>
chroot /host
cat /proc/meminfo | grep Huge
```

Expected output:
```
HugePages_Total:     256
HugePages_Free:      256
HugePages_Rsvd:        0
HugePages_Surp:        0
Hugepagesize:       2048 kB
```

## F5 XC Site Deployment

### Step 1: Obtain Site Registration Token

1. Log in to [F5 Cloud Console](https://console.ves.volterra.io/)
2. Navigate to **Multi-Cloud Network Connect** → **Site Management** → **Site Tokens**
3. Click **Add Site Token**
4. Set expiration date and click **Generate**
5. Copy the token (you'll need this in the next step)

### Step 2: Configure Site Parameters

Edit `deploy/ce_ocp_gpu-ai.yml` and replace the following placeholders:

```yaml
ClusterName: your-cluster-name        # Unique identifier for your site
Latitude: 37.7749                      # Geographic latitude
Longitude: -122.4194                   # Geographic longitude
Token: <paste-token-here>              # Site registration token from Step 1
```

⚠️ **Security Note**: The site token is sensitive. Never commit it to version control.

### Step 3: Create ves-system Namespace

```bash
oc create namespace ves-system
```

### Step 4: Deploy F5 XC Site

```bash
oc create -f deploy/ce_ocp_gpu-ai.yml
```

### Step 5: Monitor Deployment

```bash
# Watch pod status
oc get pods -n ves-system -w

# Check site registration logs
oc logs -n ves-system -l app=vp-manager
```

The site should appear in F5 XC Console within 5-10 minutes.

## F5 XC Console Configuration

### Step 1: Approve Site Registration

1. In F5 XC Console, navigate to **Multi-Cloud Network Connect** → **Manage** → **Site Management** → **Registrations**
2. Find your site (ClusterName)
3. Click **Approve**
4. Wait for site status to become **Online** (may take 5-10 minutes)

### Step 2: Discover Kubernetes Services

1. Navigate to **Multi-Cloud App Connect** → **Manage** → **Load Balancers** → **Origin Pools**
2. Click **Add Origin Pool**
3. Configure:
   - **Name**: `llamastack-origin-pool`
   - **Origin Servers**:
     - **Type**: K8s Service Name of Origin Server on given Sites
     - **Service Name**: `llamastack.f5-ai-security`
     - **Site**: Select your site
     - **Select Network on the Site**: vK8s Networks on Site
   - **Port**: 8321
4. Click **Save and Exit**

### Step 3: Create HTTP Load Balancer

1. Navigate to **Multi-Cloud App Connect** → **Manage** → **Load Balancers** → **HTTP Load Balancers**
2. Click **Add HTTP Load Balancer**
3. Configure:
   - **Name**: `f5-ai-security-lb`
   - **Domains**: `your-domain.example.com` (or use system-generated)
   - **Load Balancer Type**: HTTP
   - **Default Origin Servers**: Select `llamastack-origin-pool`
4. Click **Save and Exit**

### Step 4: Import OpenAPI Specification

1. In the HTTP Load Balancer configuration, scroll to **API Protection**
2. Click **Configure**
3. Select **API Definition**:
   - Click **Add Item**
   - **Upload**: Select `deploy/openapi-swagger-v3-fixed2-version.json`
   - **Validation**: Enable **API Validation**
4. Click **Apply**

### Step 5: Enable API Security

1. In **API Protection** section:
   - **Enable API Discovery**: ON
   - **Enable API Inventory**: ON
   - **Fall Through Mode**: Custom (Block unmatched requests)
2. Click **Save and Exit**

### Step 6: Configure WAF Policy

1. Navigate to **Web App & API Protection** → **Web Application Firewall**
2. Click **Add Web Application Firewall**
3. Configure:
   - **Name**: `ai-inference-waf`
   - **Enforcement Mode**: Blocking
   - **Detection Settings**:
     - Enable **Attack Signatures**
     - Set **Signature Selection**: High Accuracy
     - Enable **Threat Campaigns**
   - **Allowed Response Codes**: Default
4. Click **Save and Exit**

### Step 7: Attach WAF to Load Balancer

1. Return to your HTTP Load Balancer
2. Scroll to **Web Application Firewall**
3. Select **Enable**
4. Choose the `ai-inference-waf` policy
5. Click **Save and Exit**

### Step 8: Configure Rate Limiting

1. In HTTP Load Balancer, scroll to **Rate Limiting**
2. Click **Configure**
3. Add rate limit rule:
   - **Name**: `chat-completion-limit`
   - **API Endpoint**: `/v1/inference/chat-completion`
   - **HTTP Method**: ANY
   - **Threshold**: 10 requests
   - **Duration**: 1 minute
   - **Action**: Block
4. Click **Apply** and **Save and Exit**

## Security Policy Configuration

### XSS Protection Test

Verify XSS blocking:

```bash
curl -X POST https://your-lb-domain/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "test",
    "messages": [{"role": "user", "content": "<script>alert(\"XSS\")</script>"}]
  }'
```

Expected: `403 Forbidden` with WAF signature violation

### Shadow API Detection Test

Test undocumented endpoint blocking:

```bash
curl https://your-lb-domain/v1/version
```

Expected: `403 Forbidden` (endpoint not in OpenAPI spec)

### Rate Limiting Test

Test rate limit enforcement:

```bash
# Send 15 requests rapidly
for i in {1..15}; do
  curl -X POST https://your-lb-domain/v1/inference/chat-completion \
    -H "Content-Type: application/json" \
    -d '{"model": "test", "messages": [{"role": "user", "content": "test"}]}'
  echo "Request $i"
done
```

Expected:
- Requests 1-10: `200 OK` or `400/401` (based on backend)
- Requests 11+: `429 Too Many Requests`

## Verification

### Check Site Status

```bash
# In OpenShift
oc get pods -n ves-system

# Expected: All pods Running
```

### Check Load Balancer Health

1. In F5 XC Console, navigate to your HTTP Load Balancer
2. Click **Performance Monitoring**
3. Verify:
   - Origin pool health: **Healthy**
   - Request success rate: > 0%
   - No error responses

### Check Security Events

1. Navigate to **Web App & API Protection** → **Overview** → **Security Events**
2. Send test attacks (XSS, SQL injection)
3. Verify events appear with:
   - Attack type
   - Signature ID
   - Action taken (Block/Alert)

## Troubleshooting

### Site Not Registering

**Symptoms**: Site doesn't appear in F5 XC Console

**Solutions**:
1. Check site token is correct
2. Verify outbound HTTPS connectivity:
   ```bash
   oc debug node/<node-name>
   chroot /host
   curl -I https://console.ves.volterra.io
   ```
3. Check vp-manager logs:
   ```bash
   oc logs -n ves-system -l app=vp-manager --tail=100
   ```

### Origin Pool Unhealthy

**Symptoms**: Origin pool shows as unhealthy

**Solutions**:
1. Verify LLaMA Stack service is running:
   ```bash
   oc get svc -n f5-ai-security
   ```
2. Check service name matches exactly: `llamastack.f5-ai-security`
3. Test connectivity from F5 XC site:
   ```bash
   oc exec -it -n ves-system <ver-pod> -- curl http://llamastack.f5-ai-security:8321/v1/models
   ```

### WAF Blocking Legitimate Requests

**Symptoms**: Normal requests getting 403 errors

**Solutions**:
1. Review security events in F5 XC Console
2. Identify false positive signatures
3. Create exclusions:
   - Navigate to WAF policy
   - Add signature exclusions for specific URLs/parameters
4. Consider lowering detection sensitivity

### Rate Limiting Not Working

**Symptoms**: Requests exceed configured limits

**Solutions**:
1. Verify requests are going through F5 XC (not direct to service)
2. Check rate limit rule matches the exact endpoint path
3. Ensure client IP is correctly identified
4. Review rate limit events in F5 XC Console

### API Validation Blocking Valid Requests

**Symptoms**: OpenAPI-compliant requests getting rejected

**Solutions**:
1. Verify OpenAPI spec is correctly formatted
2. Check request matches schema exactly:
   - Content-Type headers
   - Required fields
   - Data types
3. Review validation errors in security events
4. Update OpenAPI spec if needed

## Additional Resources

- [F5 Distributed Cloud Documentation](https://docs.cloud.f5.com/)
- [F5 XC Kubernetes Integration Guide](https://docs.cloud.f5.com/docs/how-to/app-networking/k8s-service-discovery)
- [WAF Configuration Best Practices](https://docs.cloud.f5.com/docs/how-to/app-security/web-app-firewall)
- [API Security Guide](https://docs.cloud.f5.com/docs/how-to/app-security/api-security)

---

For additional help, contact F5 support or consult the [F5 DevCentral Community](https://community.f5.com/).
