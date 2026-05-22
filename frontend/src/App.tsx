import { Routes, Route, Navigate } from "react-router-dom";

import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import PricingPage from "./pages/PricingPage";
import BlogPage from "./pages/BlogPage";
import BlogArticlePage from "./pages/BlogArticlePage";
import DashboardPage from "./pages/DashboardPage";
import CampaignsPage from "./pages/CampaignsPage";
import CampaignPage from "./pages/CampaignPage";
import AudiencePage from "./pages/AudiencePage";
import AttributionPage from "./pages/AttributionPage";
import SettingsIntegrationsPage from "./pages/SettingsIntegrationsPage";
import SettingsProfilePage from "./pages/SettingsProfilePage";
import SettingsDomainsPage from "./pages/SettingsDomainsPage";
import ReportsPage from "./pages/ReportsPage";
import LogisticsTrackerPage from "./pages/LogisticsTrackerPage";
import LinksPage from "./pages/LinksPage";
import LinkStatsPage from "./pages/LinkStatsPage";
import LandingRedirectPage from "./pages/LandingRedirectPage";
import CanvasPage from "./pages/CanvasPage";
import Layout from "./components/shared/Layout";
import ProtectedRoute from "./components/shared/ProtectedRoute";

import AdminLoginPage from "./pages/admin/AdminLoginPage";
import AdminDashboardPage from "./pages/admin/AdminDashboardPage";
import AdminUsersPage from "./pages/admin/AdminUsersPage";
import AdminSettingsPage from "./pages/admin/AdminSettingsPage";
import AdminBillingPage from "./pages/admin/AdminBillingPage";
import AdminSegmentsPage from "./pages/admin/AdminSegmentsPage";
import AdminAuditPage from "./pages/admin/AdminAuditPage";
import AdminBlogPage from "./pages/admin/AdminBlogPage";
import AdminBlogArticlePage from "./pages/admin/AdminBlogArticlePage";
import AdminDomainsPage from "./pages/admin/AdminDomainsPage";
import AdminLayout from "./components/admin/AdminLayout";
import AdminProtectedRoute from "./components/admin/AdminProtectedRoute";

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/pricing" element={<PricingPage />} />
      <Route path="/blog" element={<BlogPage />} />
      <Route path="/blog/:slug" element={<BlogArticlePage />} />
      <Route path="/l/:code" element={<LandingRedirectPage />} />

      {/* Canvas — full-screen, outside Layout (no sidebar) */}
      <Route element={<ProtectedRoute />}>
        <Route path="/canvas" element={<CanvasPage />} />
        <Route path="/canvas/:boardId" element={<CanvasPage />} />
      </Route>

      {/* Protected user app */}
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/campaigns" element={<CampaignsPage />} />
          <Route path="/campaigns/:id" element={<CampaignPage />} />
          <Route path="/audience" element={<AudiencePage />} />
          <Route path="/attribution" element={<AttributionPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/logistics" element={<LogisticsTrackerPage />} />
          <Route path="/links" element={<LinksPage />} />
          <Route path="/links/:id/stats" element={<LinkStatsPage />} />
          <Route path="/settings/integrations" element={<SettingsIntegrationsPage />} />
          <Route path="/settings/profile" element={<SettingsProfilePage />} />
          <Route path="/settings/domains" element={<SettingsDomainsPage />} />
        </Route>
      </Route>

      {/* Admin panel — isolated auth, separate layout */}
      <Route path="/admin/login" element={<AdminLoginPage />} />
      <Route element={<AdminProtectedRoute />}>
        <Route element={<AdminLayout />}>
          <Route path="/admin" element={<AdminDashboardPage />} />
          <Route path="/admin/users" element={<AdminUsersPage />} />
          <Route path="/admin/billing" element={<AdminBillingPage />} />
          <Route path="/admin/segments" element={<AdminSegmentsPage />} />
          <Route path="/admin/audit" element={<AdminAuditPage />} />
          <Route path="/admin/settings" element={<AdminSettingsPage />} />
          <Route path="/admin/blog" element={<AdminBlogPage />} />
          <Route path="/admin/blog/:id" element={<AdminBlogArticlePage />} />
          <Route path="/admin/domains" element={<AdminDomainsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
