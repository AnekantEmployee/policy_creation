'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardBody } from '../components/Card';
import { Header } from '../components/Header';
import { Modal } from '../components/Modal';
import { Badge } from '../components/Badge';
import { Button } from '../components/Button';
import {
  CheckCircle,
  XCircle,
  AlertCircle,
  Users,
  Clock,
  Shield,
  Filter,
  ChevronDown,
  Loader,
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { adminApi, AdminUser } from '@/api/admin';
import toast from 'react-hot-toast';

type FilterTab = 'pending' | 'all';
type RoleType = 'admin' | 'compliance_officer' | 'security_lead' | 'executive' | 'auditor';

const ROLE_LABELS: Record<RoleType, string> = {
  admin: 'Administrator',
  compliance_officer: 'Compliance Officer',
  security_lead: 'Security Lead',
  executive: 'Executive',
  auditor: 'Auditor',
};

const ROLE_COLORS: Record<RoleType, string> = {
  admin: 'bg-red-100 text-red-700',
  compliance_officer: 'bg-blue-100 text-blue-700',
  security_lead: 'bg-purple-100 text-purple-700',
  executive: 'bg-emerald-100 text-emerald-700',
  auditor: 'bg-amber-100 text-amber-700',
};

export default function AdminDashboard() {
  const router = useRouter();
  const { user, isAuthenticated, initializeFromStorage } = useAuthStore();

  const [filter, setFilter] = useState<FilterTab>('pending');
  const [pendingUsers, setPendingUsers] = useState<AdminUser[]>([]);
  const [allUsers, setAllUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [actionInProgress, setActionInProgress] = useState<number | null>(null);
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [selectedRole, setSelectedRole] = useState<RoleType>('compliance_officer');

  // Initialize auth and check permission
  useEffect(() => {
    initializeFromStorage();
  }, [initializeFromStorage]);

  useEffect(() => {
    if (isAuthenticated && user?.role !== 'admin') {
      toast.error('Access denied. Admin only.');
      router.push('/');
    }
  }, [isAuthenticated, user, router]);

  // Load data
  useEffect(() => {
    if (!isAuthenticated || user?.role !== 'admin') return;

    const loadData = async () => {
      try {
        setLoading(true);
        const [pending, all] = await Promise.all([
          adminApi.getPendingUsers(),
          adminApi.getAllUsers(),
        ]);
        setPendingUsers(pending.pending_users);
        setAllUsers(all.users);
      } catch (error) {
        toast.error('Failed to load admin data');
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [isAuthenticated, user?.role]);

  // Handle approve
  const handleApprove = async (userId: number) => {
    if (actionInProgress) return;
    setActionInProgress(userId);
    try {
      const result = await adminApi.approveUser(userId);
      toast.success(`User ${result.user.username} approved`);

      // Remove from pending
      setPendingUsers((prev) => prev.filter((u) => u.id !== userId));

      // Add to all users if not there
      if (!allUsers.find((u) => u.id === userId)) {
        setAllUsers((prev) => [...prev, result.user]);
      } else {
        setAllUsers((prev) =>
          prev.map((u) => (u.id === userId ? result.user : u))
        );
      }

      if (selectedUser?.id === userId) {
        setSelectedUser(result.user);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to approve user');
    } finally {
      setActionInProgress(null);
    }
  };

  // Handle reject
  const handleReject = async (userId: number) => {
    if (actionInProgress) return;
    setActionInProgress(userId);
    try {
      await adminApi.rejectUser(userId);
      toast.success('User rejected and removed');

      setPendingUsers((prev) => prev.filter((u) => u.id !== userId));
      setAllUsers((prev) => prev.filter((u) => u.id !== userId));

      if (selectedUser?.id === userId) {
        setSelectedUser(null);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to reject user');
    } finally {
      setActionInProgress(null);
    }
  };

  // Handle role change
  const handleRoleChange = async () => {
    if (!selectedUser || actionInProgress) return;
    setActionInProgress(selectedUser.id);
    try {
      const result = await adminApi.updateUserRole(selectedUser.id, selectedRole);
      toast.success(`Role updated to ${ROLE_LABELS[selectedRole]}`);

      // Update in lists
      setAllUsers((prev) =>
        prev.map((u) => (u.id === selectedUser.id ? result.user : u))
      );
      setSelectedUser(result.user);
      setShowRoleModal(false);
    } catch (error: any) {
      toast.error(error.message || 'Failed to update role');
    } finally {
      setActionInProgress(null);
    }
  };

  // Permission check
  if (isAuthenticated && user?.role !== 'admin') {
    return null;
  }

  // Display data
  const displayUsers = filter === 'pending' ? pendingUsers : allUsers;

  return (
    <>
      <Header title="Admin Dashboard" subtitle="Manage users, roles, and approvals" />

      <main className="flex-1 p-4 lg:p-8 space-y-6 max-w-6xl mx-auto w-full">
        {/* Stats cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardBody className="p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-neutral-600">Pending Approval</span>
                <Clock className="h-4 w-4 text-amber-500" />
              </div>
              <div className="text-2xl font-bold text-neutral-900">{pendingUsers.length}</div>
            </CardBody>
          </Card>

          <Card>
            <CardBody className="p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-neutral-600">Total Users</span>
                <Users className="h-4 w-4 text-primary-500" />
              </div>
              <div className="text-2xl font-bold text-neutral-900">{allUsers.length}</div>
            </CardBody>
          </Card>

          <Card>
            <CardBody className="p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-neutral-600">Approved</span>
                <CheckCircle className="h-4 w-4 text-emerald-500" />
              </div>
              <div className="text-2xl font-bold text-neutral-900">
                {allUsers.filter((u) => u.is_approved).length}
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Filter tabs */}
        <div className="flex border-b border-neutral-200">
          {(['pending', 'all'] as FilterTab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`px-4 py-3 text-sm font-semibold transition-colors border-b-2 ${
                filter === tab
                  ? 'text-primary-600 border-primary-600'
                  : 'text-neutral-400 border-transparent hover:text-neutral-600'
              }`}
            >
              {tab === 'pending' ? (
                <>
                  <Clock className="h-4 w-4 inline mr-2" />
                  Pending ({pendingUsers.length})
                </>
              ) : (
                <>
                  <Users className="h-4 w-4 inline mr-2" />
                  All Users ({allUsers.length})
                </>
              )}
            </button>
          ))}
        </div>

        {/* Users table/list */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader className="h-6 w-6 text-primary-500 animate-spin" />
          </div>
        ) : displayUsers.length === 0 ? (
          <Card>
            <CardBody className="p-12 text-center">
              <AlertCircle className="h-12 w-12 text-neutral-300 mx-auto mb-3" />
              <p className="text-neutral-600 text-sm">
                {filter === 'pending' ? 'No pending approvals' : 'No users found'}
              </p>
            </CardBody>
          </Card>
        ) : (
          <div className="space-y-3">
            {displayUsers.map((u) => {
              const isPending = !u.is_approved;
              return (
                <Card key={u.id}>
                  <CardBody className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0 space-y-1.5">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white text-sm font-bold shrink-0">
                            {u.full_name ? u.full_name.charAt(0).toUpperCase() : u.username.charAt(0).toUpperCase()}
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="font-semibold text-neutral-900 truncate">{u.full_name || u.username}</p>
                            <p className="text-xs text-neutral-500 truncate">{u.email}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 flex-wrap pl-13">
                          <Badge
                            variant={isPending ? 'warning' : 'success'}
                            icon={isPending ? <Clock className="h-3.5 w-3.5" /> : <CheckCircle className="h-3.5 w-3.5" />}
                          >
                            {isPending ? 'Pending' : 'Approved'}
                          </Badge>
                          <Badge variant="info" icon={<Shield className="h-3.5 w-3.5" />}>
                            {ROLE_LABELS[u.role as RoleType]}
                          </Badge>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2 ml-4 shrink-0">
                        {isPending && (
                          <>
                            <button
                              onClick={() => handleApprove(u.id)}
                              disabled={actionInProgress === u.id}
                              className="p-2 rounded-lg text-emerald-600 hover:bg-emerald-50 transition-colors disabled:opacity-50"
                              title="Approve"
                            >
                              {actionInProgress === u.id ? (
                                <Loader className="h-4 w-4 animate-spin" />
                              ) : (
                                <CheckCircle className="h-4 w-4" />
                              )}
                            </button>
                            <button
                              onClick={() => handleReject(u.id)}
                              disabled={actionInProgress === u.id}
                              className="p-2 rounded-lg text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
                              title="Reject"
                            >
                              {actionInProgress === u.id ? (
                                <Loader className="h-4 w-4 animate-spin" />
                              ) : (
                                <XCircle className="h-4 w-4" />
                              )}
                            </button>
                          </>
                        )}

                        {!isPending && (
                          <button
                            onClick={() => {
                              setSelectedUser(u);
                              setSelectedRole(u.role as RoleType);
                              setShowRoleModal(true);
                            }}
                            disabled={actionInProgress === u.id}
                            className="px-3 py-1.5 text-xs rounded-lg bg-neutral-100 text-neutral-700 hover:bg-neutral-200 transition-colors flex items-center gap-1.5"
                          >
                            <Shield className="h-3.5 w-3.5" />
                            Change Role
                          </button>
                        )}
                      </div>
                    </div>
                  </CardBody>
                </Card>
              );
            })}
          </div>
        )}
      </main>

      {/* Role change modal */}
      <Modal isOpen={showRoleModal} onClose={() => setShowRoleModal(false)}>
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-bold text-neutral-900">Change User Role</h2>
            <p className="text-sm text-neutral-600 mt-1">
              {selectedUser?.full_name || selectedUser?.username}
            </p>
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-2">
              New Role
            </label>
            <div className="relative">
              <select
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value as RoleType)}
                className="w-full px-3 py-2 rounded-lg border border-neutral-200 text-sm appearance-none bg-white cursor-pointer hover:border-neutral-300 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {(Object.keys(ROLE_LABELS) as RoleType[]).map((role) => (
                  <option key={role} value={role}>
                    {ROLE_LABELS[role]}
                  </option>
                ))}
              </select>
              <ChevronDown className="h-4 w-4 text-neutral-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>

          <div className="flex gap-2 pt-4">
            <button
              onClick={() => setShowRoleModal(false)}
              className="flex-1 px-4 py-2 text-sm font-semibold rounded-lg bg-neutral-100 text-neutral-700 hover:bg-neutral-200 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleRoleChange}
              disabled={actionInProgress === selectedUser?.id}
              className="flex-1 px-4 py-2 text-sm font-semibold rounded-lg bg-primary-600 text-white hover:bg-primary-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {actionInProgress === selectedUser?.id && <Loader className="h-4 w-4 animate-spin" />}
              Update Role
            </button>
          </div>
        </div>
      </Modal>
    </>
  );
}
