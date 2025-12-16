# Карта Тривог - Telegram Bot

## Overview

This is a Ukrainian air raid alert Telegram bot ("Карта Тривог" - Alert Map) built with Python and aiogram 3.x framework. The bot provides users with air raid alert notifications for different regions of Ukraine, shelter locations, and personal alert settings. The project is currently in early development with basic structure in place.

**Creator:** Артем Процко

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Framework
- **Framework:** aiogram 3.x (modern async Telegram Bot API wrapper)
- **Language:** Python 3.x with asyncio for asynchronous operations
- **Parse Mode:** HTML for message formatting

### Core Components

1. **User Management**
   - Currently uses in-memory dictionary storage (`users = {}`)
   - User data structure: `{"regions": [], "role": "user"}`
   - Supports role-based access (user/moderator)
   - Moderator authentication via password

2. **Regional Alert System**
   - Predefined list of 8 Ukrainian regions (oblasts)
   - Users can subscribe to specific regions for alerts
   - Inline keyboard for region selection

3. **Menu System**
   - Reply keyboard with 6 main functions:
     - My region selection
     - Alert status check
     - Notification settings
     - Nearby shelter finder
     - User profile
     - About bot info

### Planned Features (Based on UI)
- Real-time air raid alert notifications
- Shelter location service ("Укриття поруч")
- User profile management
- Notification customization

### Data Storage
- **Current:** In-memory dictionary (temporary)
- **Planned:** Database integration needed for persistent storage
- Will require migration to proper database (SQLite, PostgreSQL, or similar)

## External Dependencies

### Python Packages
- **aiogram** - Telegram Bot API framework (version 3.x based on imports)
- **asyncio** - Async I/O operations (built-in)
- **logging** - Application logging (built-in)

### External Services
- **Telegram Bot API** - Core messaging platform
  - Requires bot token from @BotFather
  - Token stored in `TOKEN` variable (should be moved to environment variable)

### Future Integration Considerations
- Air raid alert data source API (e.g., alerts.in.ua or similar Ukrainian alert services)
- Geolocation services for shelter finder feature
- Database service for persistent user data storage

### Security Notes
- Bot token is currently hardcoded (should use environment variables)
- Moderator password is plaintext in code (needs secure handling)