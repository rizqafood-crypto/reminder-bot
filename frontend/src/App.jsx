import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Layout
import Layout from './components/Layout';
import Login from './pages/Login';

// Pages
import Dashboard from './pages/Dashboard';
import ClientList from './pages/ClientList';
import ClientDetail from './pages/ClientDetail';
import CampaignList from './pages/CampaignList';
import CampaignDetail from './pages/CampaignDetail';
import ContentCalendar from './pages/ContentCalendar';
import ContentList from './pages/ContentList';
import TaskBoard from './pages/TaskBoard';
import TaskList from './pages/TaskList';
import InvoiceList from './pages/InvoiceList';
import InvoiceDetail from './pages/InvoiceDetail';
import Analytics from './pages/Analytics';
import TeamManagement from './pages/TeamManagement';
import Settings from './pages/Settings';

// Store
import { useAuthStore } from './stores/authStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1
    }
  }
});

function PrivateRoute({ children }) {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route path="/" element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }>
            <Route index element={<Dashboard />} />

            {/* Clients */}
            <Route path="clients" element={<ClientList />} />
            <Route path="clients/:id" element={<ClientDetail />} />

            {/* Campaigns */}
            <Route path="campaigns" element={<CampaignList />} />
            <Route path="campaigns/:id" element={<CampaignDetail />} />

            {/* Content */}
            <Route path="content/calendar" element={<ContentCalendar />} />
            <Route path="content" element={<ContentList />} />

            {/* Tasks */}
            <Route path="tasks/board" element={<TaskBoard />} />
            <Route path="tasks" element={<TaskList />} />

            {/* Finance */}
            <Route path="invoices" element={<InvoiceList />} />
            <Route path="invoices/:id" element={<InvoiceDetail />} />

            {/* Analytics */}
            <Route path="analytics" element={<Analytics />} />

            {/* Team */}
            <Route path="team" element={<TeamManagement />} />

            {/* Settings */}
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </Router>

      <ToastContainer position="top-right" autoClose={3000} />
    </QueryClientProvider>
  );
}

export default App;
