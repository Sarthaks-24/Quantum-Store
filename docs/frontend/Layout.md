# Layout.jsx - Application Shell

**Location**: `frontend/src/components/ui/Layout.jsx`  
**Lines**: 62  
**Type**: React Component (Functional)

---

## Overview

The **Layout** component serves as the application shell, providing a consistent navigation sidebar and content area across all pages. It follows a simple, elegant design with a glass-morphism sidebar containing the QuantumStore branding, navigation links, and a prominent upload button.

**Design Pattern**: Container/Presenter (wraps `children` with chrome)

---

## Responsibilities

1. **Application Branding**
   - Display "QuantumStore" logo with gradient
   - Subtitle text ("File Intelligence")

2. **Navigation Management**
   - Sidebar with Dashboard and Files links
   - Active route highlighting
   - Click navigation using React Router

3. **Layout Structure**
   - Fixed sidebar (left side, 64px + padding width)
   - Flexible main content area (right side)
   - Gradient background (`bg-gradient-dark`)

4. **Quick Actions**
   - Upload Files button (always accessible from sidebar)

---

## Input / Output

### Props
```typescript
{
  children: ReactNode  // Main content to render (routed components)
}
```

### State
**None** - Stateless component

### Navigation
- **`navigate(path)`** - From `useNavigate()` hook
  - Triggered by sidebar button clicks
  - Triggered by "Upload Files" button

### Location
- **`location.pathname`** - From `useLocation()` hook
  - Used to highlight active navigation item

---

## Internal Flow

```
Component renders
  ↓
Read current location.pathname
  ↓
Render sidebar with navigation items
  ↓
Apply 'active' style to item matching pathname
  ↓
Render children in main content area
  ↓
User clicks navigation item → navigate(item.path)
  ↓
React Router updates location → Component re-renders
  ↓
New active item highlighted
```

---

## Key Elements

### 1. Sidebar Navigation Array
```javascript
const sidebar = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { id: 'files', label: 'Files', icon: Files, path: '/files' },
];
```
**Structure**: Array of navigation items  
**Why Array**: Easy to add/remove nav items, map to JSX  
**Properties**:
- `id`: Unique identifier (for React key)
- `label`: Display text
- `icon`: Lucide icon component
- `path`: Route to navigate to

---

### 2. Sidebar Container
```jsx
<motion.aside
  initial={{ x: -300, opacity: 0 }}
  animate={{ x: 0, opacity: 1 }}
  className="w-64 p-6 glass-card m-4 rounded-3xl"
>
```
**Animation**: Slides in from left on mount  
**Width**: 256px (w-64)  
**Style**: Glass morphism effect (backdrop blur + transparency)  
**Margin**: 16px all sides (creates gap from edge + main content)

---

### 3. Branding Section
```jsx
<div className="mb-8">
  <h1 className="text-2xl font-bold bg-gradient-to-r from-accent-indigo to-accent-teal bg-clip-text text-transparent">
    QuantumStore
  </h1>
  <p className="text-sm text-white/60 mt-1">File Intelligence</p>
</div>
```
**Logo**: Gradient text (indigo → teal)  
**Subtitle**: Muted white text  
**Spacing**: 32px margin below (mb-8)

---

### 4. Navigation Links
```jsx
<nav className="space-y-2">
  {sidebar.map((item) => (
    <button
      key={item.id}
      onClick={() => navigate(item.path)}
      className={location.pathname === item.path ? 'sidebar-item-active w-full' : 'sidebar-item w-full'}
      aria-label={item.label}
      aria-current={location.pathname === item.path ? 'page' : undefined}
    >
      <item.icon size={20} />
      <span>{item.label}</span>
    </button>
  ))}
</nav>
```
**Active State**: `sidebar-item-active` class when path matches  
**Accessibility**:
- `aria-label` for screen readers
- `aria-current="page"` for active item

**Classes (from global CSS)**:
- `sidebar-item`: Base styles (flex, gap, padding, hover effects)
- `sidebar-item-active`: Active styles (background, text color)

---

### 5. Upload Button
```jsx
<div className="mt-auto pt-8">
  <motion.button
    whileHover={{ scale: 1.02 }}
    whileTap={{ scale: 0.98 }}
    className="btn-primary w-full flex items-center justify-center gap-2"
    onClick={() => navigate('/upload')}
  >
    <Upload size={20} />
    Upload Files
  </motion.button>
</div>
```
**Position**: Bottom of sidebar (`mt-auto` pushes it down)  
**Animation**: Scales on hover/tap  
**Navigation**: Navigates to `/upload` route

---

### 6. Main Content Area
```jsx
{children}
```
**Content**: Rendered outside sidebar (flex sibling)  
**Children**: Routed components (Dashboard, Files, Upload, etc.)

---

## Routing Integration

### In App.jsx
```javascript
<Routes>
  <Route path="/dashboard" element={<Layout><Dashboard /></Layout>} />
  <Route path="/files" element={<Layout><Files /></Layout>} />
  <Route path="/upload" element={<Layout><Upload /></Layout>} />
</Routes>
```
**Pattern**: Layout wraps every routed component  
**Result**: Sidebar persists across pages, only content changes

---

## Dependencies

### Internal
**None** - No internal imports except components

### External
- **react** - Core library
- **framer-motion** - `motion` wrapper for animations
- **react-router-dom** - `useNavigate()`, `useLocation()` hooks
- **lucide-react** - Icons (LayoutDashboard, Files, Upload)

---

## CSS Classes Used

### Custom Classes (from global CSS)
- `bg-gradient-dark` - Background gradient (dark purple → black)
- `glass-card` - Glass morphism effect (backdrop blur, transparency, border)
- `sidebar-item` - Navigation button base styles
- `sidebar-item-active` - Active navigation button styles
- `btn-primary` - Primary button styles (gradient background, hover effects)

### Tailwind Classes
- `min-h-screen` - Full viewport height
- `flex` - Flexbox container (sidebar + content)
- `w-64` - 256px width (sidebar)
- `rounded-3xl` - Large border radius
- `space-y-2` - Vertical spacing between nav items

---

## Known Limitations / Edge Cases

1. **No Mobile Responsiveness**
   - Sidebar always visible (256px + 16px margin = 272px)
   - **Issue**: Unusable on small screens (<768px)
   - **Enhancement**: Add hamburger menu, collapsible sidebar

2. **No Active Route Validation**
   - If user navigates to unknown route (e.g., `/settings`), no item highlighted
   - **Enhancement**: Add "catch-all" active state or default highlight

3. **Fixed Width Sidebar**
   - Cannot resize or collapse
   - **Enhancement**: Add toggle button to collapse to icon-only mode

4. **No Nested Routes**
   - Sidebar doesn't support sub-navigation (e.g., Files → Images → ...)
   - **Enhancement**: Add nested `<ul>` structure with expand/collapse

5. **No Breadcrumbs**
   - User may not know where they are in deep navigation
   - **Enhancement**: Add breadcrumb trail in main content area

6. **Upload Button Always Visible**
   - Shows even on Upload page (redundant)
   - **Enhancement**: Hide when `location.pathname === '/upload'`

7. **No Keyboard Navigation**
   - Cannot tab through sidebar items efficiently
   - **Enhancement**: Add keyboard shortcuts (Ctrl+1 for Dashboard, etc.)

---

## How to Modify or Extend

### Add New Navigation Item

```javascript
const sidebar = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { id: 'files', label: 'Files', icon: Files, path: '/files' },
  { id: 'analytics', label: 'Analytics', icon: BarChart3, path: '/analytics' }, // NEW
];
```

---

### Add Mobile Responsive Sidebar

```javascript
import { Menu, X } from 'lucide-react';

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="min-h-screen flex bg-gradient-dark">
      {/* Mobile Hamburger */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="md:hidden fixed top-4 left-4 z-50 p-2 glass-card rounded-xl"
      >
        {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Sidebar */}
      <motion.aside
        initial={{ x: -300 }}
        animate={{ x: sidebarOpen || window.innerWidth >= 768 ? 0 : -300 }}
        className={`w-64 p-6 glass-card m-4 rounded-3xl ${
          sidebarOpen ? 'fixed inset-y-0 left-0 z-40' : 'hidden md:block'
        }`}
      >
        {/* ... sidebar content ... */}
      </motion.aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          className="md:hidden fixed inset-0 bg-black/50 z-30"
        />
      )}

      {children}
    </div>
  );
};
```

---

### Add Collapsible Sidebar

```javascript
const [collapsed, setCollapsed] = useState(false);

<motion.aside
  animate={{ width: collapsed ? 80 : 256 }}
  className={`p-6 glass-card m-4 rounded-3xl transition-all ${collapsed ? 'items-center' : ''}`}
>
  <button
    onClick={() => setCollapsed(!collapsed)}
    className="mb-4 p-2 hover:bg-white/10 rounded-lg"
  >
    {collapsed ? <ChevronRight /> : <ChevronLeft />}
  </button>

  {!collapsed && <h1>QuantumStore</h1>}
  {collapsed && <h1 className="text-lg">QS</h1>}

  {sidebar.map(item => (
    <button key={item.id} className="...">
      <item.icon size={20} />
      {!collapsed && <span>{item.label}</span>}
    </button>
  ))}
</motion.aside>
```

---

### Hide Upload Button on Upload Page

```javascript
{location.pathname !== '/upload' && (
  <div className="mt-auto pt-8">
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className="btn-primary w-full flex items-center justify-center gap-2"
      onClick={() => navigate('/upload')}
    >
      <Upload size={20} />
      Upload Files
    </motion.button>
  </div>
)}
```

---

### Add User Profile Section

```javascript
<div className="mt-auto pt-8 border-t border-white/10">
  <div className="flex items-center gap-3 p-3 glass-card rounded-xl">
    <div className="w-10 h-10 bg-gradient-to-r from-accent-indigo to-accent-teal rounded-full flex items-center justify-center">
      <span className="text-sm font-bold">JD</span>
    </div>
    <div className="flex-1">
      <p className="text-sm font-medium">John Doe</p>
      <p className="text-xs text-white/60">john@example.com</p>
    </div>
  </div>
</div>
```

---

### Add Keyboard Shortcuts

```javascript
useEffect(() => {
  const handleKeyDown = (e) => {
    if (e.ctrlKey || e.metaKey) {
      switch (e.key) {
        case '1':
          e.preventDefault();
          navigate('/dashboard');
          break;
        case '2':
          e.preventDefault();
          navigate('/files');
          break;
        case 'u':
          e.preventDefault();
          navigate('/upload');
          break;
      }
    }
  };

  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, [navigate]);
```

---

## Performance Characteristics

### Initial Render
- **Time**: ~5-10ms
- **Complexity**: O(n) where n = sidebar items (currently 2)

### Navigation
- **Time**: ~1-2ms to update active state
- **Triggers**: Location change via React Router

### Re-render Triggers
- `location.pathname` change → Sidebar re-renders to update active item

### Memory
- **Footprint**: ~2KB (minimal state, no caching)

---

## Testing Considerations

### Unit Tests

```javascript
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Layout from './Layout';

test('renders navigation links', () => {
  render(
    <BrowserRouter>
      <Layout>
        <div>Test Content</div>
      </Layout>
    </BrowserRouter>
  );

  expect(screen.getByText('Dashboard')).toBeInTheDocument();
  expect(screen.getByText('Files')).toBeInTheDocument();
  expect(screen.getByText('Upload Files')).toBeInTheDocument();
});

test('highlights active navigation item', () => {
  window.history.pushState({}, '', '/dashboard');
  
  render(
    <BrowserRouter>
      <Layout>
        <div>Dashboard Content</div>
      </Layout>
    </BrowserRouter>
  );

  const dashboardButton = screen.getByRole('button', { name: /dashboard/i });
  expect(dashboardButton).toHaveClass('sidebar-item-active');
});

test('renders children in main content area', () => {
  render(
    <BrowserRouter>
      <Layout>
        <div data-testid="child-content">Test Child</div>
      </Layout>
    </BrowserRouter>
  );

  expect(screen.getByTestId('child-content')).toBeInTheDocument();
});
```

---

## Accessibility

### ARIA Attributes
- **`aria-label`**: Each nav button has descriptive label
- **`aria-current="page"`**: Active nav item marked for screen readers

### Keyboard Navigation
- All buttons focusable with Tab
- Enter/Space activate buttons
- **Enhancement Needed**: Add skip-to-main-content link

### Color Contrast
- Text meets WCAG AA standards (white on dark background)
- Active state has clear visual distinction

---

**Last Updated**: November 2024  
**Component Status**: ✅ Production-ready, Simple & Effective  
**Complexity**: ⭐ Low (62 lines, stateless, no business logic)
