# Design Document

## Overview

The Phase 4 Integration design transforms the current dual-server architecture into a unified web server that serves both the control interface and documentation through a single entry point. This design eliminates the need to run multiple server instances while providing seamless navigation between the two interfaces.

The current system runs separate servers on ports 3000 (control) and 3001 (docs). The new design will serve both interfaces from a single server on port 3000 using path-based routing (`/control` and `/docs`), eliminating the need for multiple ports while providing intelligent routing, a landing page for navigation, and cross-interface navigation components.

## Architecture

### Current Architecture
```
┌─────────────────┐    ┌─────────────────┐
│   Control Web   │    │   Docs Web      │
│   Server        │    │   Server        │
│   Port 3000     │    │   Port 3001     │
└─────────────────┘    └─────────────────┘
        │                       │
        ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   sites/control │    │   sites/docs    │
└─────────────────┘    └─────────────────┘
```

### New Unified Architecture
```
┌─────────────────────────────────────────┐
│           Unified Web Server            │
│              Port 3000                  │
├─────────────────────────────────────────┤
│  Route Handler & Navigation Manager     │
├─────────────────────────────────────────┤
│  /          │  /control  │  /docs       │
│  Landing    │  Control   │  Documentation│
│  Page       │  Interface │  Site        │
└─────────────────────────────────────────┘
        │              │           │
        ▼              ▼           ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Navigation  │ │sites/control│ │ sites/docs  │
│ Landing     │ │             │ │             │
└─────────────┘ └─────────────┘ └─────────────┘
```

## Components and Interfaces

### 1. Unified Web Server (`UnifiedMatrixWebServer`)

**Purpose**: Single server instance that handles routing to different interfaces

**Key Methods**:
- `__init__(port=3000)`: Initialize server with single port
- `start()`: Start the unified server
- `handle_request(path)`: Route requests to appropriate handlers
- `serve_landing_page()`: Serve the main navigation page
- `serve_control_interface()`: Serve control interface files
- `serve_docs_interface()`: Serve documentation files

**Routing Logic**:
- `/` → Landing page with navigation options
- `/control` and `/control/*` → Control interface files from `sites/control/`
- `/docs` and `/docs/*` → Documentation files from `sites/docs/`
- `/api/*` → API endpoints (proxy to existing controller)

**Key Benefits of Path-Based Routing**:
- Single port (3000) for all interfaces - no more port juggling
- Cleaner URLs: `localhost:3000/control` vs `localhost:3000` + `localhost:3001`
- Easier deployment and firewall configuration
- Simplified development and testing

### 2. Navigation Landing Page

**Purpose**: Main entry point providing navigation to both interfaces

**Features**:
- Clean, responsive design matching existing interface styling
- Quick access buttons to control and documentation interfaces
- Status indicators showing if services are running
- Brief description of each interface's purpose
- Consistent branding with existing interfaces

**Template Structure**:
```html
<!DOCTYPE html>
<html>
<head>
    <title>LED Matrix Project - Control Center</title>
    <!-- Shared CSS variables and styling -->
</head>
<body>
    <div class="landing-container">
        <header class="landing-header">
            <h1>LED Matrix Control Center</h1>
            <p>Choose your interface</p>
        </header>
        
        <div class="interface-cards">
            <div class="interface-card control-card">
                <h2>Control Interface</h2>
                <p>Real-time matrix control and monitoring</p>
                <a href="/control" class="interface-button">Launch Control</a>
            </div>
            
            <div class="interface-card docs-card">
                <h2>Documentation</h2>
                <p>Complete project guide and reference</p>
                <a href="/docs" class="interface-button">View Docs</a>
            </div>
        </div>
        
        <div class="status-indicators">
            <div class="status-item">
                <span class="status-dot" id="controller-status"></span>
                <span>Python Controller</span>
            </div>
        </div>
    </div>
</body>
</html>
```

### 3. Cross-Interface Navigation Component

**Purpose**: Provide seamless navigation between control and documentation interfaces

**Implementation**: JavaScript module that injects navigation elements into both interfaces

**Features**:
- Floating navigation button or header integration
- Consistent styling across both interfaces
- Smooth transitions between interfaces
- Breadcrumb navigation showing current location

**Integration Points**:
- Control Interface: Add navigation to documentation
- Documentation: Add navigation to control interface
- Both interfaces: Add "Home" link to landing page

### 4. Enhanced Request Handler

**Purpose**: Intelligent routing and file serving with proper MIME types and caching

**Key Features**:
- Static file serving with correct MIME types
- Route-based request handling
- Error handling with user-friendly error pages
- CORS headers for API integration
- Caching headers for optimal performance

**Route Handlers**:
```python
class RouteHandler:
    def handle_root(self, request):
        """Serve landing page"""
        
    def handle_control(self, request):
        """Serve control interface files"""
        
    def handle_docs(self, request):
        """Serve documentation files"""
        
    def handle_api(self, request):
        """Proxy API requests to controller"""
        
    def handle_404(self, request):
        """Serve custom 404 page with navigation"""
```

## Data Models

### Server Configuration
```python
@dataclass
class ServerConfig:
    port: int = 3000
    host: str = "localhost"
    control_path: str = "sites/control"
    docs_path: str = "sites/docs"
    api_proxy_port: int = 8080
    enable_cors: bool = True
    enable_caching: bool = True
```

### Route Definition
```python
@dataclass
class Route:
    path: str
    handler: callable
    methods: List[str]
    content_type: str = "text/html"
```

### Navigation Item
```python
@dataclass
class NavigationItem:
    title: str
    url: str
    description: str
    icon: str = ""
    active: bool = False
```

## Error Handling

### 1. Route Not Found (404)
- Custom 404 page with navigation back to landing page
- Suggestions for correct URLs
- Search functionality for documentation

### 2. Service Unavailable (503)
- Graceful degradation when Python controller is not running
- Clear error messages with troubleshooting steps
- Retry mechanisms for API calls

### 3. File Not Found
- Fallback to index.html for single-page applications
- Proper error logging for debugging
- User-friendly error messages

### 4. CORS and Security
- Proper CORS headers for cross-origin requests
- Content Security Policy headers
- Input validation for all routes

## Testing Strategy

### 1. Unit Tests
- Route handler functionality
- File serving with correct MIME types
- Navigation component integration
- Error handling scenarios

### 2. Integration Tests
- Full server startup and shutdown
- Cross-interface navigation flows
- API proxy functionality
- Static file serving performance

### 3. End-to-End Tests
- Complete user workflows
- Browser compatibility testing
- Mobile responsiveness
- Performance under load

### 4. Manual Testing Scenarios
```python
test_scenarios = [
    "Navigate from landing page to control interface",
    "Navigate from control interface to documentation",
    "Navigate from documentation back to control",
    "Access direct URLs for each interface",
    "Test 404 handling with invalid URLs",
    "Verify API proxy functionality",
    "Test mobile responsiveness",
    "Verify consistent styling across interfaces"
]
```

## Implementation Phases

### Phase 1: Core Server Infrastructure
- Create `UnifiedMatrixWebServer` class
- Implement basic routing system
- Add static file serving with MIME types
- Create landing page template

### Phase 2: Interface Integration
- Modify existing interfaces to work with new routing
- Add cross-interface navigation components
- Implement API proxy functionality
- Update error handling

### Phase 3: Enhanced Features
- Add status indicators and health checks
- Implement caching and performance optimizations
- Create custom error pages
- Add logging and monitoring

### Phase 4: Documentation and Testing
- Update README with new architecture
- Create comprehensive test suite
- Add troubleshooting documentation
- Performance optimization

## Migration Strategy

### Backward Compatibility
- Maintain existing command-line interface with updated behavior
- Redirect legacy port 3001 requests to `/docs` path during transition
- Update all documentation to use path-based URLs
- Provide migration guide showing URL changes (port 3001 → `/docs`)

### Deployment Process
1. Deploy unified server alongside existing servers
2. Test all functionality with both systems running
3. Update documentation and user guides
4. Switch default behavior to unified server
5. Remove legacy dual-server code after validation period

## Performance Considerations

### Optimization Strategies
- Static file caching with appropriate headers
- Gzip compression for text-based files
- Connection pooling for API proxy
- Lazy loading of interface components

### Resource Management
- Single server process reduces memory footprint
- Shared static assets between interfaces
- Efficient routing to minimize request processing time
- Connection reuse for API calls

### Monitoring
- Request logging and performance metrics
- Error rate monitoring
- Resource usage tracking
- User navigation pattern analysis