import React from 'react';
import { useQuery } from 'react-query';
import { TrendingUp, Users, Megaphone, FileText, CheckSquare, DollarSign } from 'lucide-react';
import { dashboardAPI } from '../services/api';

const StatCard = ({ title, value, change, icon: Icon, color }) => (
  <div className="bg-white rounded-lg shadow p-6">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-gray-600">{title}</p>
        <p className="text-2xl font-bold mt-1">{value}</p>
        {change && (
          <p className={`text-sm mt-1 ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {change >= 0 ? '+' : ''}{change}% from last month
          </p>
        )}
      </div>
      <div className={`p-3 rounded-full ${color}`}>
        <Icon size={24} className="text-white" />
      </div>
    </div>
  </div>
);

const Dashboard = () => {
  const { data: overview, isLoading } = useQuery('dashboard-overview', () =>
    dashboardAPI.getOverview().then(res => res.data)
  );

  const { data: activity } = useQuery('dashboard-activity', () =>
    dashboardAPI.getActivity({ limit: 10 }).then(res => res.data)
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Welcome back! Here's what's happening today.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatCard
          title="Active Clients"
          value={overview?.clients?.active || 0}
          icon={Users}
          color="bg-blue-500"
        />
        <StatCard
          title="Active Campaigns"
          value={overview?.campaigns?.active || 0}
          icon={Megaphone}
          color="bg-green-500"
        />
        <StatCard
          title="Scheduled Content"
          value={overview?.content?.scheduled || 0}
          icon={FileText}
          color="bg-purple-500"
        />
        <StatCard
          title="Pending Tasks"
          value={overview?.tasks?.pending || 0}
          icon={CheckSquare}
          color="bg-orange-500"
        />
        <StatCard
          title="Total Revenue"
          value={`$${(overview?.financial?.total_revenue || 0).toLocaleString()}`}
          icon={DollarSign}
          color="bg-emerald-500"
        />
        <StatCard
          title="Pending Revenue"
          value={`$${(overview?.financial?.pending_revenue || 0).toLocaleString()}`}
          icon={TrendingUp}
          color="bg-red-500"
        />
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold">Recent Activity</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {activity?.activities?.slice(0, 10).map((item, index) => (
            <div key={index} className="px-6 py-4 hover:bg-gray-50 transition-colors">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {item.action.replace(/_/g, ' ').toUpperCase()}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    {item.entity_type} #{item.entity_id}
                  </p>
                </div>
                <span className="text-xs text-gray-500">
                  {new Date(item.timestamp).toLocaleString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <button className="p-6 bg-white rounded-lg shadow hover:shadow-md transition-shadow text-left">
          <Users className="text-blue-600 mb-3" size={24} />
          <h3 className="font-semibold">Add New Client</h3>
          <p className="text-sm text-gray-600 mt-1">Create a new client profile</p>
        </button>
        <button className="p-6 bg-white rounded-lg shadow hover:shadow-md transition-shadow text-left">
          <Megaphone className="text-green-600 mb-3" size={24} />
          <h3 className="font-semibold">New Campaign</h3>
          <p className="text-sm text-gray-600 mt-1">Start a new marketing campaign</p>
        </button>
        <button className="p-6 bg-white rounded-lg shadow hover:shadow-md transition-shadow text-left">
          <FileText className="text-purple-600 mb-3" size={24} />
          <h3 className="font-semibold">Create Content</h3>
          <p className="text-sm text-gray-600 mt-1">Add new content item</p>
        </button>
        <button className="p-6 bg-white rounded-lg shadow hover:shadow-md transition-shadow text-left">
          <DollarSign className="text-emerald-600 mb-3" size={24} />
          <h3 className="font-semibold">New Invoice</h3>
          <p className="text-sm text-gray-600 mt-1">Generate an invoice</p>
        </button>
      </div>
    </div>
  );
};

export default Dashboard;
