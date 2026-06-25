import apiClient from './client';

export interface AdminUser {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  role: 'admin' | 'compliance_officer' | 'security_lead' | 'executive' | 'auditor';
  is_active: boolean;
  is_verified: boolean;
  is_approved: boolean;
  created_at: string;
  last_login: string | null;
}

export const adminApi = {
  // Get list of pending users awaiting approval
  getPendingUsers: async (): Promise<{ pending_users: AdminUser[] }> => {
    const response = await apiClient.get('/admin/users/pending');
    return response.data;
  },

  // Get all users in the system
  getAllUsers: async (): Promise<{ users: AdminUser[] }> => {
    const response = await apiClient.get('/admin/users');
    return response.data;
  },

  // Approve a pending user
  approveUser: async (userId: number): Promise<{ message: string; user: AdminUser }> => {
    const response = await apiClient.post(`/admin/users/${userId}/approve`);
    return response.data;
  },

  // Reject and delete a pending user
  rejectUser: async (userId: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/admin/users/${userId}/reject`);
    return response.data;
  },

  // Update user role
  updateUserRole: async (userId: number, role: string): Promise<{ message: string; user: AdminUser }> => {
    const response = await apiClient.patch(`/admin/users/${userId}/role`, { role });
    return response.data;
  },
};
