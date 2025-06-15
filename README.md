# Event Chatbot Demo

A chatbot application for finding and getting information about events using Ticketmaster API.

## Environment Setup

This application requires several API keys to function properly. These keys are loaded from environment variables.

### Setting up Environment Variables

1. Copy the `.env.template` file to a new file named `.env`:
   ```bash
   cp .env.template .env
   ```

2. Edit the `.env` file and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   TICKETMASTER_API_KEY=your_ticketmaster_api_key_here
   SWAGGER_API_KEY=your_swagger_api_key_here
   ```

3. Load the environment variables:

   **For macOS/Linux (Bash/Zsh)**:
   ```bash
   source .env
   ```
   
   **For Windows (PowerShell)**:
   ```powershell
   Get-Content .env | ForEach-Object {
       if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
           $key = $Matches[1].Trim()
           $value = $Matches[2].Trim()
           [Environment]::SetEnvironmentVariable($key, $value, "Process")
       }
   }
   ```

   **Alternatively**, you can use a package like `python-dotenv` to load the variables automatically in your Python code.

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
streamlit run main.py
```