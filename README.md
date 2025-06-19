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
   OPENAI_MODERATION_API_KEY=your_moderation_api_key_here
   TICKETMASTER_API_KEY=your_ticketmaster_api_key_here
   SWAGGER_API_KEY=your_swagger_api_key_here
   ```
   
   Note: The `OPENAI_MODERATION_API_KEY` is optional. If not provided, the system will use the `OPENAI_API_KEY` for moderation.

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

## Content Moderation

This application uses OpenAI's Moderation API to ensure user inputs and assistant responses comply with content policies. The moderation service:

- Automatically filters inappropriate or harmful user inputs
- Prevents the assistant from generating problematic content
- Provides detailed moderation insights for administrators through the sidebar debug panel

### Moderation Categories

The OpenAI Moderation API checks content across multiple categories including:

- Hate speech
- Harassment
- Self-harm
- Sexual content
- Violence
- etc.

When content is flagged, the user will receive an appropriate message indicating that their request cannot be processed.