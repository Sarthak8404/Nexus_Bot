# BusinessAI Platform 🤖

A complete business intelligence platform with AI-powered data extraction, Firebase authentication, and modern web interface. Extract structured data from files and websites using Google Gemini AI.

## ✨ Features

### 🔐 **Authentication**
- Firebase Authentication with email/password
- Google Sign-In integration
- Secure user sessions

### 📊 **Data Upload & Extraction**
- **File Upload**: Support for PDF, DOCX, TXT files (up to 16MB)
- **URL Scraping**: Extract data from any website
- **Content Types**: Products, Services, Contact Info, About/Company, FAQs, Policies, General
- **AI Processing**: Google Gemini 2.0 Flash for intelligent data extraction

### 🧪 **Data Testing & Analysis**
- Interactive data preview with editable tables
- Contextual AI chatbot for data insights
- Real-time data validation and correction

### 📈 **Business Analytics**
- AI-powered business insights and recommendations
- Query-based analytics with natural language processing
- Cost tracking and token usage statistics

### 🤖 **Telegram Bot Integration**
- **Customer Service Bot**: AI-powered Telegram bot for customer inquiries
- **Automatic Responses**: Uses your business data to answer customer questions
- **Easy Setup**: Simple token configuration and webhook setup
- **Real-time Chat**: Instant responses to customer messages
- **Multi-user Support**: Each user can have their own bot instance

### ⚙️ **Settings & Configuration**
- Customizable AI model selection
- Notification preferences
- Data refresh settings

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Google Gemini API key ([Get it here](https://makersuite.google.com/app/apikey))
- Firebase project ([Create one here](https://console.firebase.google.com/))
- Modern web browser

### 1. Setup Backend (Python Flask)

```bash
# Clone or download the project
cd BusinessAI-Platform

# Run the automated setup
python setup.py

# Or manual setup:
pip install -r requirements.txt

# Copy environment configuration
cp config.example.env .env

# Edit .env file and add your API keys
nano .env  # or use your preferred editor
```

### 2. Configure Environment

Edit the `.env` file:
```env
# Google Gemini API Key (Required)
GEMINI_API_KEY=your_gemini_api_key_here

# Flask Configuration (Optional)
FLASK_DEBUG=True
FLASK_PORT=5000
```

### 3. Configure Firebase

Edit `index.html` and `dashboard.html` to update Firebase configuration:
```javascript
const firebaseConfig = {
    apiKey: "your-api-key",
    authDomain: "your-project.firebaseapp.com",
    projectId: "your-project-id",
    // ... other config
};
```

### 4. Start the Backend Server

```bash
# Using the runner script
python run_server.py

# Or directly
python app.py
```

The backend will be available at: `http://localhost:5000`

### 5. Open the Frontend

Open `index.html` in your web browser or serve it using a local web server:

```bash
# Using Python's built-in server
python -m http.server 8080

# Using Node.js http-server (if installed)
npx http-server

# Using Live Server extension in VS Code
# Right-click on index.html and select "Open with Live Server"
```

## 🤖 Telegram Bot Setup

### 1. Create a Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Send `/newbot`** to create a new bot
3. **Choose a name** for your bot (e.g., "My Bakery Assistant")
4. **Choose a username** (must end with 'bot', e.g., "mybakery_bot")
5. **Copy the bot token** provided by BotFather

### 2. Configure Bot in Dashboard

1. **Open the dashboard** and go to the "Analytics" section
2. **Find the "Integration Settings"** card on the right side
3. **Enable Telegram Bot** by checking the toggle
4. **Enter your bot token** in the "Telegram Bot Token" field
5. **Click "Save Settings"**
6. **Click "Setup Webhook"** to connect your bot to the platform

### 3. Test Your Bot

1. **Send a message** to your bot on Telegram
2. **The bot should respond** using your business data
3. **Make sure you have uploaded and stored data** in the dashboard first

### 4. Advanced Testing

Use the provided test script to verify your setup:

```bash
python test_telegram.py
```

This script will:
- Validate your bot token
- Test the webhook setup
- Check bot status
- Test chat functionality

### 5. Production Deployment

For production use, you'll need to:

1. **Deploy the backend** to a server with HTTPS
2. **Update the webhook URL** in the code to use your domain
3. **Configure environment variables** for production
4. **Set up proper database storage** for settings

## 📁 Project Structure

```
BusinessAI-Platform/
├── app.py                 # Main Flask application
├── run_server.py          # Server runner script
├── setup.py               # Automated setup script
├── requirements.txt       # Python dependencies
├── config.example.env     # Environment configuration template
├── index.html            # Authentication page
├── dashboard.html        # Main dashboard
├── styles.css            # CSS styles
├── auth.js              # Authentication logic
├── dashboard.js         # Dashboard functionality
└── README.md            # This file
```

## 🔧 Backend API Endpoints

### Authentication
- Frontend handles Firebase authentication
- Backend processes authenticated requests

### File Processing
- `POST /api/upload` - Upload and process files
- Parameters: `file` (multipart), `content_type` (string)

### Web Scraping
- `POST /api/scrape` - Scrape and extract data from URLs
- Body: `{"url": "website-url", "content_type": "products"}`

### Utilities
- `GET /api/health` - Health check and system status
- `GET /api/content-types` - Available content types
- `GET /` - API documentation

### Telegram Bot
- `GET /api/settings` - Get user settings
- `POST /api/settings/telegram` - Save Telegram bot settings
- `POST /api/telegram/webhook` - Handle incoming Telegram messages
- `POST /api/telegram/setup` - Setup Telegram webhook
- `GET /api/telegram/status` - Get bot status

## 🎯 Content Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Products** | E-commerce items, catalogs | Extract product names, prices, descriptions |
| **Services** | Service offerings | Extract service details, pricing, features |
| **Contact** | Contact information | Extract emails, phones, addresses |
| **About** | Company information | Extract company details, mission, team |
| **FAQ** | Frequently Asked Questions | Extract Q&A pairs |
| **Policies** | Terms, Privacy policies | Extract policy documents |
| **General** | Any content | General-purpose extraction |

## 💰 Cost & Usage

The platform uses Google Gemini AI for processing:
- **Input tokens**: Content sent to AI
- **Output tokens**: AI response
- **Cost tracking**: Automatic cost calculation
- **Token limits**: ~15,000 characters per request

Example costs (approximate):
- Small file (1-2 pages): $0.001-0.005
- Medium file (5-10 pages): $0.01-0.02
- Large file (20+ pages): $0.05-0.10
- Website scraping: $0.005-0.03

## 🔒 Security Features

### Backend Security
- CORS enabled for frontend integration
- File type validation and size limits
- Input sanitization and validation
- Secure filename handling
- Temporary file cleanup

### Frontend Security
- Firebase Authentication
- Secure token handling
- Input validation
- Error handling and user feedback

## 🛠️ Development

### Adding New Content Types

1. Update `get_content_type_options()` in `app.py`
2. Add extraction prompt in `get_extraction_prompts()`
3. Update frontend dropdowns in HTML files

### Customizing AI Prompts

Edit the `get_extraction_prompts()` method in `app.py` to modify how the AI extracts data for each content type.

### Frontend Customization

- **Styling**: Edit `styles.css`
- **Functionality**: Edit `dashboard.js`
- **Authentication**: Edit `auth.js`
- **Layout**: Edit HTML files

## 📊 Example Usage

### File Upload
1. Select content type (e.g., "Products")
2. Upload PDF/DOCX/TXT file
3. AI extracts structured data
4. View results with cost statistics

### URL Scraping
1. Select content type (e.g., "Services")
2. Enter website URL
3. AI scrapes and extracts data
4. Export results as JSON

### Data Analysis
1. View extracted data in tables
2. Chat with AI about your data
3. Get business insights and recommendations
4. Export data for further analysis

## 🐛 Troubleshooting

### Common Issues

**Backend won't start:**
- Check Python version (3.8+ required)
- Verify GEMINI_API_KEY in .env file
- Install missing dependencies: `pip install -r requirements.txt`

**Frontend authentication issues:**
- Verify Firebase configuration
- Check browser console for errors
- Ensure Firebase project is properly configured

**AI extraction fails:**
- Verify API key is valid and has credits
- Check file size (max 16MB)
- Ensure content is extractable (not images/scanned PDFs)

**CORS errors:**
- Backend must be running on http://localhost:5000
- Check CORS configuration in `app.py`

### Getting Help

1. Check the console output for error messages
2. Verify all configuration files are properly set up
3. Test the health endpoint: `http://localhost:5000/api/health`
4. Check Firebase console for authentication issues

## 🔄 Updates & Maintenance

### Updating Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Backup & Export
- All extraction results can be exported as JSON
- User data is stored in Firebase
- Settings saved in browser localStorage

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- **Google Gemini AI** for intelligent data extraction
- **Firebase** for authentication and hosting
- **Flask** for the backend framework
- **BeautifulSoup** for web scraping
- **LiteLLM** for AI model integration

---

**Made with ❤️ for business intelligence and data extraction**

🌟 **Star this project if you find it useful!** 