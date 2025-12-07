# J-GOD Trading Command Center UI

React + TypeScript trading dashboard for J-GOD simulation system.

## Initialization

```bash
cd trading-ui
npm create vite@latest jgod-trading-ui -- --template react-ts
cd jgod-trading-ui
npm install
npm install axios react-i18next i18next
```

## Project Structure

```
jgod-trading-ui/
├── src/
│   ├── api/              # REST API client wrappers
│   ├── components/       # UI components (A1, A2, B1, E1 panels)
│   ├── layouts/          # Layout components
│   ├── pages/            # Page components (DashboardPage.tsx)
│   ├── i18n/             # Internationalization (zh-TW.json, en.json)
│   ├── types/            # TypeScript type definitions
│   └── App.tsx           # Main app component
└── package.json
```

## Development

```bash
# Start dev server
npm run dev

# Build for production
npm run build
```

## API Base URL

Default: `http://localhost:8000`

Configure in `src/api/client.ts` or via environment variable.

