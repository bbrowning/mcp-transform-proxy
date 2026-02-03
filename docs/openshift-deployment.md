# OpenShift Deployment Guide

This guide describes how to deploy mcp-transform-proxy on OpenShift to proxy and transform tools from another MCP server (such as openshift-filesystem-mcp).

## Architecture

```
┌──────────────────────────┐          ┌──────────────────────────────┐
│ mcp-transform-proxy pod  │          │ openshift-filesystem-mcp pod │
│  ┌────────────────────┐  │   SSE    │  (existing deployment)       │
│  │ proxy              │──┼─────────▶│  Service: :8080/sse          │
│  │ Port 8080 (HTTP)   │  │          │  hostPath: /etc,/proc,/sys   │
│  └────────────────────┘  │          └──────────────────────────────┘
└────────────┼─────────────┘
             │
      Route (HTTPS)
     (external MCP clients)
```

The proxy connects to the upstream MCP server via its cluster service URL, keeping deployments independent.

## Prerequisites

- OpenShift cluster with admin access
- `oc` CLI configured
- An upstream MCP server deployed (e.g., openshift-filesystem-mcp)

## Quick Start

Deploy using the provided Kustomize manifests:

```bash
# Apply all manifests
oc apply -k examples/openshift/

# Verify deployment
oc get pods -n mcp-transform-proxy

# Get the route URL
oc get route -n mcp-transform-proxy mcp-transform-proxy -o jsonpath='{.spec.host}'
```

## Configuration

The proxy configuration is stored in a ConfigMap. Edit `examples/openshift/configmap.yaml` to customize:

### Upstream Server URL

Update the `url` field to point to your upstream MCP server:

```json
{
  "mcpServers": {
    "filesystem": {
      "url": "http://your-mcp-server.namespace.svc:8080/sse"
    }
  }
}
```

### Tool Transformations

The example configuration renames tools and disables write operations:

```json
{
  "tools": {
    "read_text_file": {
      "name": "read_text_file_on_openshift_node",
      "description": "Read a text file from an OpenShift cluster node..."
    },
    "write_file": {
      "enabled": false
    }
  }
}
```

See the main README for full transformation options.

## Customization

### Using a Different Image

Edit `examples/openshift/deployment.yaml`:

```yaml
containers:
  - name: proxy
    image: your-registry/mcp-transform-proxy:v0.1.1
```

### Resource Limits

Adjust memory and CPU in the deployment:

```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "50m"
  limits:
    memory: "256Mi"
    cpu: "500m"
```

### Multiple Upstream Servers

Add additional servers to the ConfigMap:

```json
{
  "mcpServers": {
    "filesystem": {
      "url": "http://filesystem-mcp.ns1.svc:8080/sse"
    },
    "database": {
      "url": "http://db-mcp.ns2.svc:8080/sse"
    }
  }
}
```

## Troubleshooting

### Check Pod Status

```bash
oc get pods -n mcp-transform-proxy
oc describe pod -n mcp-transform-proxy -l app.kubernetes.io/name=mcp-transform-proxy
```

### View Logs

```bash
oc logs -n mcp-transform-proxy -l app.kubernetes.io/name=mcp-transform-proxy -f
```

### Test Connectivity

```bash
# Port-forward to test locally
oc port-forward -n mcp-transform-proxy svc/mcp-transform-proxy 8080:8080

# Test SSE endpoint
curl http://localhost:8080/sse
```

### Verify Upstream Connection

Ensure the upstream MCP server is accessible from the proxy pod:

```bash
oc exec -n mcp-transform-proxy deploy/mcp-transform-proxy -- \
  curl -s http://openshift-filesystem-mcp.openshift-filesystem-mcp.svc:8080/sse
```

## Security Considerations

- The container runs as non-root (UID 1001)
- TLS termination happens at the Route level
- Write operations are disabled by default in the example config
- Network policies can further restrict traffic between namespaces
