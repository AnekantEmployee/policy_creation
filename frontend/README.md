# GRC AI Policy Creator - Frontend

A modern React/Next.js frontend for the GRC AI Policy Creation tool. Built with TypeScript, Tailwind CSS, and best practices for a scalable, maintainable codebase.

## Project Structure

```
frontend/
├── app/                    # Next.js app router
├── api/                    # API client and endpoints
├── types/                  # TypeScript type definitions
├── store/                  # Zustand state management
├── hooks/                  # Custom React hooks
├── lib/                    # Utility functions
├── components/             # Reusable React components (to be created)
├── public/                 # Static assets
├── .env.local             # Environment variables
└── package.json           # Dependencies and scripts
```

## Tech Stack

- **Framework**: Next.js 16.2.9
- **React**: 19.2.4
- **TypeScript**: Latest
- **Styling**: Tailwind CSS 4
- **State Management**: Zustand
- **HTTP Client**: Axios
- **UI Icons**: Lucide React
- **Notifications**: React Hot Toast
- **Date Utilities**: date-fns

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Environment Variables

Edit `.env.local` to configure:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_TIMEOUT=30000

# App Configuration
NEXT_PUBLIC_APP_NAME=GRC AI Policy Creator
NEXT_PUBLIC_APP_VERSION=1.0.0
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

```bash
npm run build
npm start
```

### Linting

```bash
npm run lint
```

## API Integration

The frontend connects to the backend API at `http://localhost:8000`. Available endpoints:

### Organizations
- `GET /organizations` - List all organizations
- `GET /organizations/:id` - Get organization details
- `POST /organizations` - Create organization
- `PUT /organizations/:id` - Update organization
- `GET /organizations/:id/profile` - Get organization profile
- `POST /organizations/:id/profile` - Profile organization

### Policies
- `GET /policies?organization_id=:id` - List policies
- `GET /policies/:id` - Get policy details
- `POST /policies/generate` - Generate new policy
- `PUT /policies/:id` - Update policy
- `DELETE /policies/:id` - Delete policy
- `GET /policies/:id/status` - Get policy status

### Procedures
- `GET /procedures?policy_id=:id` - List procedures
- `GET /procedures/:id` - Get procedure details
- `POST /procedures` - Create procedure
- `PUT /procedures/:id` - Update procedure
- `DELETE /procedures/:id` - Delete procedure

## State Management

Using Zustand for global state:

```typescript
import { useAppStore } from "@/store/appStore";

// In your component
const { currentOrganization, policies } = useAppStore();
```

## Custom Hooks

### useApi
Handle API calls with loading, error, and success states:

```typescript
const { data, loading, error, execute } = useApi<Policy>();

const handleFetch = async () => {
  await execute(
    () => policiesApi.getById("policy-id"),
    { successMessage: "Policy loaded!" }
  );
};
```

## Utility Functions

Located in `lib/utils.ts`:
- `cn()` - Tailwind CSS class merging
- `formatDate()` - Format dates
- `formatDateTime()` - Format dates with time
- `truncate()` - Truncate strings
- `getStatusColor()` - Get color class for status
- `getStatusIcon()` - Get emoji icon for status

## Component Development Guidelines

When creating components:

1. Use functional components with TypeScript
2. Place reusable components in `app/components/`
3. Use Tailwind CSS for styling
4. Export types alongside components
5. Keep components focused and single-responsibility
6. Use custom hooks for business logic

Example:

```typescript
// app/components/PolicyCard.tsx
import React from 'react';
import { Policy } from '@/types';

interface PolicyCardProps {
  policy: Policy;
  onEdit?: (policy: Policy) => void;
  onDelete?: (policyId: string) => void;
}

export const PolicyCard: React.FC<PolicyCardProps> = ({
  policy,
  onEdit,
  onDelete,
}) => {
  return (
    <div className="p-4 border rounded-lg">
      {/* Component implementation */}
    </div>
  );
};
```

## Contributing

1. Keep commits focused and descriptive
2. Follow TypeScript and React best practices
3. Update types as you add features
4. Test API integration before submitting
5. Use meaningful variable and function names

## Next Steps

1. Design and implement page layouts (dashboard, policies, organizations)
2. Create reusable UI components (buttons, forms, cards, tables)
3. Implement organization and policy management flows
4. Add policy generation UI
5. Build procedure management features
6. Implement user authentication
7. Add error handling and validation

## License

Proprietary - GRC AI
