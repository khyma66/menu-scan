# Menu OCR Frontend

A modern Next.js frontend for the Menu OCR API.

## Features

- 🖼️ **Image Upload**: Upload menu images via URL
- 📝 **OCR Processing**: Extract menu items using AI-powered OCR
- 🎨 **Modern UI**: Beautiful, responsive design with Tailwind CSS
- ⚡ **Fast**: Built with Next.js 15 and React 19
- 🔄 **Real-time Updates**: Live status and processing feedback

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running (see `fastapi-menu-service`)

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.local.example .env.local

# Edit .env.local with your API URL
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

```bash
# Run development server
npm run dev

# Open http://localhost:3000
```

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Configuration

Set the `NEXT_PUBLIC_API_URL` in `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production:
```env
NEXT_PUBLIC_API_URL=https://your-api.onrender.com
```

## Project Structure

```
menu-ocr-frontend/
├── app/
│   ├── page.tsx          # Main page
│   ├── layout.tsx        # Root layout
│   └── globals.css       # Global styles
├── components/
│   ├── ImageUpload.tsx   # Upload component
│   ├── MenuDisplay.tsx   # Menu display
│   └── StatusDisplay.tsx # Status messages
├── lib/
│   └── api.ts           # API client
├── types/
│   └── menu.ts          # TypeScript types
└── public/              # Static assets
```

## API Integration

The frontend communicates with the FastAPI backend at `/api/v1/ocr/process`.

## License

MIT
