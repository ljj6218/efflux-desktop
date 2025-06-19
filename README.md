## 🚀 Project Overview

**Efflux — An AI Copilot built for super-individuals.**

Efflux Desktop integrates multi-vendor models and tool invocation capabilities, supporting command-based tool access and plugin extensions. Designed for real-world tasks, Efflux brings human-AI collaboration back under your control — amplifying the judgment and execution power of super-individuals.

It doesn’t decide for you — it helps you stay in control.

## ✨ Core Features

### LLM-powered Conversations

*   Multi-vendor AI model integration (OpenAI, Anthropic, DeepSeek, etc.)
    
*   Natural-language-based conversations
    
*   Text-to-artifact capabilities
    
*   Real-time streaming chat responses
    
*   Chat history management
    

###  Tool Integration and Calling

*   Dynamic discovery and loading of MCP servers
    
*   Tool configuration management support
    
*   Exception handling and timeout control
    
*   Standardized tool calling interface
    

### Supported OS

*   Windows
*   macOS
    

## 🚀 Quick Start


### 1. Install Efflux Desktop

1. Download the package (e.g., efflux-desktop-mac-arm.zip for macOS) to your local disk.
   
2. Unzip the package and double-click the application file (e.g., EFFLUX-1.0.0-x64.dmg) to install Efflux Desktop.
   
3. Unzip the executable file (e.g., efflux_desktop) and double-click it to load the required services.
   
   Note that this extra executable file is only required at this moment and will be eliminated in future releases.

### 2. Configure Your Models

1.  In the navigation pane of Efflux Desktop, select **Models**.
    
2.  In the **Model Providers** page, find your desired model vendor, and click **API-KEY**.
    
3.  In the pop-up dialog, enter your endpoint and API key, and click **Save**.
    

### 3. Install Plugins

Optional: If you want to use existing MCP servers to complete your task, do the following:

1.  In the navigation pane, select **Plugins**.
    
2.  In the **Discover Plugins** tab, click **Add Custom Plugin**.
    
3.  In the pop-up dialog, do either of the following and click **Add**.
    
    1.  Enter the plugin name, command, environment variables, and arguments (if any), or 
        
    2.  If you've already got a JSON string, select JSON Mode and paste it.
        

> **Tip**
> 
> You can find the JSON resources of MCP servers from the following websites.
> - [https://mcp.so/](https://mcp.so/)
> - [https://mcpmarket.cn/](https://mcpmarket.cn/)
> - [https://www.pulsemcp.com/](https://www.pulsemcp.com/)
> - [https://mcp-servers-hub-website.pages.dev/](https://mcp-servers-hub-website.pages.dev/)
        

### Start Your Chat

1.  In the navigation pane, select **Chat**.
    
2.  In the chatbox, select the model you've configured, and:
    
    1.  Tell Efflux your question, or
        
    2.  Switch to the Build mode and describe what you want Efflux to build.
        
3.  To use the installed plugin, enter the **@** sign and select the target one.

4.  Press the **Enter** key to start your conversation with the selected model.
    

## 🏗️ Project Architecture

### Directory Structure

```plaintext
efflux-desktop/
├── adapter/          # Adapter layer
│   ├── mcp/          # MCP protocol adapters
│   ├── model_sdk/    # Model SDK adapters
│   ├── persistent/   # Persistence adapters
│   └── web/          # Web interface adapters
├── application/      # Application layer
│   ├── domain/       # Domain objects
│   ├── port/         # Port interfaces
│   └── service/      # Application services
├── common/           # Common components
│   ├── core/         # Core infrastructure
│   └── utils/        # Utility classes
└── main.py           # Application entry point
```

## 🔧 Development Guide


Note that this section is for developers who are interested in contributing to this project.

### 1. Clone the Project

```bash
git clone https://github.com/isoftstone-data-intelligence-ai/efflux-desktop.git
cd efflux-desktop
```

### 2. Install Dependencies


Install dependencies using the uv package manager:

```bash
pip install uv
uv sync --reinstall
```

### 3. Activate the virtual environment

Activate a virtual environment and configure environment variables.

```shell
# Activate virtual environment
source .venv/bin/activate   # MacOS/Linux

# Deactivate when needed
deactivate
```

### 4. Start the Service

```bash
uv run
```

The service will start at `http://127.0.0.1:8000`.

### API Usage Examples

```bash
POST /api/agent/chat/default_chat
Content-Type: application/json

{
  "firm": "openai",
  "model": "gpt-4",
  "system": "You are a helpful AI assistant",
  "query": "Hello, please introduce yourself",
  "mcp_name_list": ["example-server"]
}
```

## 🤝 Contributing

1.  Fork this project.
    
2.  Create a feature branch (`git checkout -b feature/AmazingFeature`).
    
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
    
4.  Push to the branch (`git push origin feature/AmazingFeature`).
    
5.  Submit a Pull Request.
    

## 📄 License

This project follows the appropriate open source license. Please refer to the LICENSE file for details.

## 🆘 Support & Help

For questions or suggestions, please contact us through:

*   Submit Issues
    
*   Start Discussions
    
